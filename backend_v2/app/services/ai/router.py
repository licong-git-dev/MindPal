"""
MindPal Backend V2 - LLM Router
智能LLM路由器 - 根据场景和健康状态选择最佳模型
"""

import os
import time
from typing import Dict, List, Optional, AsyncGenerator, Any, Tuple
from dataclasses import dataclass
from enum import Enum

from app.services.ai.health import LLMHealthChecker, get_health_checker


class ModelTier(str, Enum):
    """模型层级"""
    LITE = "lite"       # 轻量级 - 快速、低成本
    STANDARD = "standard"  # 标准级 - 平衡
    PREMIUM = "premium"    # 高级 - 最佳质量
    CRISIS = "crisis"      # 危机专用 - 最安全


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    provider: str           # qwen, claude, volcengine
    model_id: str
    tier: ModelTier
    max_tokens: int = 2000
    default_temperature: float = 0.7
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    rate_limit_rpm: int = 60
    supports_streaming: bool = True


# 预定义模型配置
MODEL_CONFIGS: Dict[str, ModelConfig] = {
    # 阿里云通义千问
    "qwen.turbo": ModelConfig(
        name="qwen.turbo",
        provider="qwen",
        model_id="qwen-turbo",
        tier=ModelTier.LITE,
        max_tokens=1500,
        default_temperature=0.8,
        cost_per_1k_input=0.008,
        cost_per_1k_output=0.008,
        rate_limit_rpm=60
    ),
    "qwen.plus": ModelConfig(
        name="qwen.plus",
        provider="qwen",
        model_id="qwen-plus",
        tier=ModelTier.STANDARD,
        max_tokens=2000,
        default_temperature=0.7,
        cost_per_1k_input=0.04,
        cost_per_1k_output=0.04,
        rate_limit_rpm=60
    ),
    "qwen.max": ModelConfig(
        name="qwen.max",
        provider="qwen",
        model_id="qwen-max",
        tier=ModelTier.PREMIUM,
        max_tokens=4000,
        default_temperature=0.6,
        cost_per_1k_input=0.12,
        cost_per_1k_output=0.12,
        rate_limit_rpm=30
    ),

    # Anthropic Claude
    "claude.haiku": ModelConfig(
        name="claude.haiku",
        provider="claude",
        model_id="claude-3-haiku-20240307",
        tier=ModelTier.LITE,
        max_tokens=1000,
        default_temperature=0.7,
        cost_per_1k_input=0.00025,
        cost_per_1k_output=0.00125,
        rate_limit_rpm=50
    ),
    "claude.sonnet": ModelConfig(
        name="claude.sonnet",
        provider="claude",
        model_id="claude-3-sonnet-20240229",
        tier=ModelTier.STANDARD,
        max_tokens=2000,
        default_temperature=0.6,
        cost_per_1k_input=0.003,
        cost_per_1k_output=0.015,
        rate_limit_rpm=50
    ),
    "claude.opus": ModelConfig(
        name="claude.opus",
        provider="claude",
        model_id="claude-3-opus-20240229",
        tier=ModelTier.CRISIS,
        max_tokens=4000,
        default_temperature=0.5,
        cost_per_1k_input=0.015,
        cost_per_1k_output=0.075,
        rate_limit_rpm=30
    ),

    # 火山引擎豆包
    "volcengine.lite": ModelConfig(
        name="volcengine.lite",
        provider="volcengine",
        model_id="doubao-lite-32k",
        tier=ModelTier.LITE,
        max_tokens=1500,
        default_temperature=0.8,
        cost_per_1k_input=0.0003,
        cost_per_1k_output=0.0003,
        rate_limit_rpm=100
    ),
    "volcengine.pro": ModelConfig(
        name="volcengine.pro",
        provider="volcengine",
        model_id="doubao-pro-32k",
        tier=ModelTier.STANDARD,
        max_tokens=2000,
        default_temperature=0.7,
        cost_per_1k_input=0.0008,
        cost_per_1k_output=0.0008,
        rate_limit_rpm=100
    ),
}


# NPC路由配置
NPC_ROUTING: Dict[str, Dict[str, List[str]]] = {
    "aela": {  # 向导NPC
        "primary": ["qwen.plus"],
        "fallback": ["volcengine.pro", "claude.haiku"],
        "crisis": ["claude.opus"]
    },
    "bei": {  # 情感陪伴NPC
        "primary": ["claude.sonnet"],
        "fallback": ["qwen.max", "volcengine.pro"],
        "crisis": ["claude.opus"]
    },
    "momo": {  # 商人NPC
        "primary": ["qwen.plus"],
        "fallback": ["volcengine.pro"],
        "crisis": ["claude.sonnet"]
    },
    "chronos": {  # 任务NPC
        "primary": ["qwen.plus"],
        "fallback": ["claude.haiku", "volcengine.pro"],
        "crisis": ["claude.sonnet"]
    },
    "sesame": {  # 宠物
        "primary": ["qwen.turbo"],
        "fallback": ["volcengine.lite"],
        "crisis": ["qwen.plus"]
    },
    "default": {
        "primary": ["qwen.plus"],
        "fallback": ["volcengine.pro", "claude.haiku"],
        "crisis": ["claude.opus"]
    }
}


class LLMRouter:
    """LLM智能路由器"""

    def __init__(
        self,
        health_checker: Optional[LLMHealthChecker] = None
    ):
        self.health = health_checker or get_health_checker()
        self.model_configs = MODEL_CONFIGS
        self.npc_routing = NPC_ROUTING

        # 注册所有模型到健康检查器
        for name in self.model_configs:
            self.health.register_service(name)

    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """获取模型配置"""
        return self.model_configs.get(model_name)

    def select_model(
        self,
        npc_id: str,
        is_crisis: bool = False,
        preferred_tier: Optional[ModelTier] = None
    ) -> Tuple[str, ModelConfig]:
        """
        选择最佳模型

        Args:
            npc_id: NPC ID
            is_crisis: 是否危机模式
            preferred_tier: 偏好的模型层级

        Returns:
            (model_name, ModelConfig)
        """
        routing = self.npc_routing.get(npc_id, self.npc_routing["default"])

        # 危机模式使用专用模型
        if is_crisis:
            candidates = routing.get("crisis", routing["primary"])
        else:
            candidates = routing["primary"] + routing.get("fallback", [])

        # 如果有层级偏好，过滤候选
        if preferred_tier and not is_crisis:
            tier_filtered = [
                c for c in candidates
                if self.model_configs.get(c, ModelConfig("", "", "", ModelTier.LITE)).tier == preferred_tier
            ]
            if tier_filtered:
                candidates = tier_filtered

        # 使用健康检查选择最佳服务
        selected = self.health.get_best_service(candidates)

        if not selected:
            # 所有服务都不可用，使用第一个候选
            selected = candidates[0] if candidates else "qwen.plus"

        config = self.model_configs.get(selected)
        if not config:
            # 默认配置
            config = self.model_configs["qwen.plus"]
            selected = "qwen.plus"

        return selected, config

    def get_fallback_chain(
        self,
        npc_id: str,
        is_crisis: bool = False
    ) -> List[str]:
        """获取降级链"""
        routing = self.npc_routing.get(npc_id, self.npc_routing["default"])

        if is_crisis:
            return routing.get("crisis", []) + routing["primary"]
        else:
            return routing["primary"] + routing.get("fallback", [])

    async def route_request(
        self,
        npc_id: str,
        messages: List[Dict[str, str]],
        system_prompt: str,
        is_crisis: bool = False,
        temperature: Optional[float] = None,
        max_retries: int = 3
    ) -> AsyncGenerator[str, None]:
        """
        路由请求到最佳模型（带自动降级）

        Args:
            npc_id: NPC ID
            messages: 对话消息
            system_prompt: 系统提示词
            is_crisis: 是否危机模式
            temperature: 温度参数
            max_retries: 最大重试次数

        Yields:
            回复文本片段
        """
        fallback_chain = self.get_fallback_chain(npc_id, is_crisis)

        last_error = None
        retries = 0

        for model_name in fallback_chain:
            if retries >= max_retries:
                break

            if not self.health.is_available(model_name):
                continue

            config = self.model_configs.get(model_name)
            if not config:
                continue

            start_time = time.time()

            try:
                # 调用实际的LLM服务
                async for chunk in self._call_llm(
                    config=config,
                    messages=messages,
                    system_prompt=system_prompt,
                    temperature=temperature or config.default_temperature
                ):
                    yield chunk

                # 记录成功
                latency_ms = (time.time() - start_time) * 1000
                self.health.record_success(model_name, latency_ms)
                return  # 成功完成

            except Exception as e:
                last_error = e
                self.health.record_failure(model_name, str(e))
                retries += 1
                continue

        # 所有模型都失败
        error_msg = f"[系统] 服务暂时不可用，请稍后再试"
        if last_error:
            error_msg += f" ({str(last_error)[:100]})"
        yield error_msg

    async def _call_llm(
        self,
        config: ModelConfig,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float
    ) -> AsyncGenerator[str, None]:
        """调用具体的LLM服务"""
        # 根据provider选择不同的调用方式
        # 这里需要与现有的LLM服务集成

        if config.provider == "qwen":
            from app.services.llm.qwen import QwenService
            service = QwenService()
            async for chunk in service.stream_chat(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature
            ):
                yield chunk

        elif config.provider == "claude":
            from app.services.llm.claude import ClaudeService
            service = ClaudeService()
            async for chunk in service.stream_chat(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature
            ):
                yield chunk

        elif config.provider == "volcengine":
            # TODO: 实现火山引擎服务
            # 暂时降级到qwen
            from app.services.llm.qwen import QwenService
            service = QwenService()
            async for chunk in service.stream_chat(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature
            ):
                yield chunk

        else:
            raise ValueError(f"Unknown provider: {config.provider}")

    def get_routing_status(self) -> Dict[str, Any]:
        """获取路由状态"""
        return {
            "models": {
                name: {
                    "provider": config.provider,
                    "tier": config.tier.value,
                    "cost": f"${config.cost_per_1k_input}/1k in, ${config.cost_per_1k_output}/1k out"
                }
                for name, config in self.model_configs.items()
            },
            "health": self.health.get_all_status(),
            "npc_routing": self.npc_routing
        }


# 单例实例
_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """获取LLM路由器实例"""
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
