"""
MindPal Backend V2 - LLM Health Checker
LLM服务健康检查与熔断
"""

import asyncio
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import time


class ServiceStatus(str, Enum):
    """服务状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    RECOVERING = "recovering"


@dataclass
class ServiceHealth:
    """服务健康状态"""
    name: str
    status: ServiceStatus = ServiceStatus.HEALTHY
    last_check: datetime = field(default_factory=datetime.utcnow)
    last_success: datetime = field(default_factory=datetime.utcnow)
    last_error: Optional[datetime] = None
    last_error_message: Optional[str] = None

    # 统计
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0

    # 性能
    avg_latency_ms: float = 0.0
    min_latency_ms: float = float('inf')
    max_latency_ms: float = 0.0

    # 熔断配置
    failure_threshold: int = 5          # 连续失败阈值
    success_threshold: int = 3          # 恢复需要的连续成功次数
    recovery_timeout_seconds: int = 60  # 熔断恢复等待时间

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def is_available(self) -> bool:
        """检查服务是否可用"""
        if self.status == ServiceStatus.HEALTHY:
            return True

        if self.status == ServiceStatus.UNHEALTHY:
            # 检查是否可以尝试恢复
            if self.last_error:
                recovery_time = self.last_error + timedelta(seconds=self.recovery_timeout_seconds)
                if datetime.utcnow() > recovery_time:
                    return True  # 允许尝试
            return False

        if self.status == ServiceStatus.RECOVERING:
            return True

        return self.status == ServiceStatus.DEGRADED


class LLMHealthChecker:
    """LLM服务健康检查器"""

    def __init__(self):
        self._services: Dict[str, ServiceHealth] = {}
        self._running = False
        self._check_interval = 30  # 秒
        self._check_task: Optional[asyncio.Task] = None

    def register_service(self, name: str, **config) -> ServiceHealth:
        """注册服务"""
        if name not in self._services:
            self._services[name] = ServiceHealth(
                name=name,
                failure_threshold=config.get("failure_threshold", 5),
                success_threshold=config.get("success_threshold", 3),
                recovery_timeout_seconds=config.get("recovery_timeout", 60)
            )
        return self._services[name]

    def get_service(self, name: str) -> Optional[ServiceHealth]:
        """获取服务状态"""
        return self._services.get(name)

    def record_success(self, service_name: str, latency_ms: float):
        """记录成功请求"""
        health = self._services.get(service_name)
        if not health:
            health = self.register_service(service_name)

        health.total_requests += 1
        health.successful_requests += 1
        health.consecutive_successes += 1
        health.consecutive_failures = 0
        health.last_success = datetime.utcnow()
        health.last_check = datetime.utcnow()

        # 更新延迟统计
        health.avg_latency_ms = (health.avg_latency_ms * 0.9) + (latency_ms * 0.1)
        health.min_latency_ms = min(health.min_latency_ms, latency_ms)
        health.max_latency_ms = max(health.max_latency_ms, latency_ms)

        # 状态转换
        if health.status == ServiceStatus.RECOVERING:
            if health.consecutive_successes >= health.success_threshold:
                health.status = ServiceStatus.HEALTHY
        elif health.status == ServiceStatus.UNHEALTHY:
            health.status = ServiceStatus.RECOVERING
            health.consecutive_successes = 1

    def record_failure(self, service_name: str, error_message: str = ""):
        """记录失败请求"""
        health = self._services.get(service_name)
        if not health:
            health = self.register_service(service_name)

        health.total_requests += 1
        health.failed_requests += 1
        health.consecutive_failures += 1
        health.consecutive_successes = 0
        health.last_error = datetime.utcnow()
        health.last_error_message = error_message[:500] if error_message else None
        health.last_check = datetime.utcnow()

        # 状态转换 - 熔断
        if health.consecutive_failures >= health.failure_threshold:
            health.status = ServiceStatus.UNHEALTHY
        elif health.consecutive_failures >= health.failure_threshold // 2:
            health.status = ServiceStatus.DEGRADED

    def is_available(self, service_name: str) -> bool:
        """检查服务是否可用"""
        health = self._services.get(service_name)
        if not health:
            return True  # 未知服务默认可用
        return health.is_available

    def get_best_service(self, candidates: List[str]) -> Optional[str]:
        """从候选服务中选择最佳的"""
        available = [s for s in candidates if self.is_available(s)]

        if not available:
            # 所有服务都不可用，选择最可能恢复的
            recovering = [
                (s, self._services.get(s))
                for s in candidates
                if self._services.get(s)
            ]
            if recovering:
                # 选择最近出错时间最早的（更可能已恢复）
                recovering.sort(
                    key=lambda x: x[1].last_error or datetime.min
                )
                return recovering[0][0]
            return candidates[0] if candidates else None

        # 选择延迟最低且成功率最高的
        def score(name: str) -> float:
            health = self._services.get(name)
            if not health:
                return 0.5
            # 成功率权重0.6 + 延迟权重0.4（延迟越低分越高）
            latency_score = 1.0 / (1.0 + health.avg_latency_ms / 1000.0)
            return health.success_rate * 0.6 + latency_score * 0.4

        return max(available, key=score)

    def get_all_status(self) -> Dict[str, Dict]:
        """获取所有服务状态"""
        return {
            name: {
                "status": health.status.value,
                "is_available": health.is_available,
                "success_rate": f"{health.success_rate:.1%}",
                "avg_latency_ms": f"{health.avg_latency_ms:.0f}",
                "total_requests": health.total_requests,
                "consecutive_failures": health.consecutive_failures,
                "last_check": health.last_check.isoformat(),
                "last_error": health.last_error.isoformat() if health.last_error else None,
                "last_error_message": health.last_error_message
            }
            for name, health in self._services.items()
        }

    async def start_background_check(self):
        """启动后台健康检查"""
        if self._running:
            return

        self._running = True
        self._check_task = asyncio.create_task(self._background_check_loop())

    async def stop_background_check(self):
        """停止后台健康检查"""
        self._running = False
        if self._check_task:
            self._check_task.cancel()
            try:
                await self._check_task
            except asyncio.CancelledError:
                pass

    async def _background_check_loop(self):
        """后台检查循环"""
        while self._running:
            try:
                await self._check_all_services()
            except Exception as e:
                print(f"Health check error: {e}")

            await asyncio.sleep(self._check_interval)

    async def _check_all_services(self):
        """检查所有服务"""
        # 这里可以实现实际的健康检查ping
        # 目前仅基于请求记录判断
        for name, health in self._services.items():
            # 检查是否长时间没有请求
            if health.last_check:
                idle_time = (datetime.utcnow() - health.last_check).total_seconds()
                if idle_time > 300:  # 5分钟无请求
                    # 重置连续计数
                    health.consecutive_failures = 0
                    health.consecutive_successes = 0


# 单例实例
_health_checker: Optional[LLMHealthChecker] = None


def get_health_checker() -> LLMHealthChecker:
    """获取健康检查器实例"""
    global _health_checker
    if _health_checker is None:
        _health_checker = LLMHealthChecker()
    return _health_checker
