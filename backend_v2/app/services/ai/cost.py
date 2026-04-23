"""
MindPal Backend V2 - Cost Tracker
AI服务成本追踪
"""

import os
from typing import Dict, Optional, Any
from datetime import datetime, date
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class UsageRecord:
    """使用记录"""
    service: str
    input_tokens: int
    output_tokens: int
    cost: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class DailyUsage:
    """每日使用统计"""
    date: date
    by_service: Dict[str, Dict[str, float]] = field(default_factory=dict)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost: float = 0.0
    request_count: int = 0


@dataclass
class PlayerQuota:
    """玩家配额"""
    player_id: int
    daily_token_limit: int = 50000       # 每日token限额
    daily_cost_limit: float = 0.10       # 每日成本限额（元）
    used_tokens_today: int = 0
    used_cost_today: float = 0.0
    last_reset: date = field(default_factory=date.today)


# 价格表（元/1K tokens）
PRICING: Dict[str, Dict[str, float]] = {
    "qwen.turbo": {"input": 0.008, "output": 0.008},
    "qwen.plus": {"input": 0.04, "output": 0.04},
    "qwen.max": {"input": 0.12, "output": 0.12},
    "claude.haiku": {"input": 0.00025, "output": 0.00125},
    "claude.sonnet": {"input": 0.003, "output": 0.015},
    "claude.opus": {"input": 0.015, "output": 0.075},
    "volcengine.lite": {"input": 0.0003, "output": 0.0003},
    "volcengine.pro": {"input": 0.0008, "output": 0.0008}
}

# 会员配额配置
MEMBERSHIP_QUOTAS: Dict[str, Dict[str, Any]] = {
    "free": {
        "daily_token_limit": 50000,
        "daily_cost_limit": 0.10,
        "daily_request_limit": 50
    },
    "monthly": {
        "daily_token_limit": 500000,
        "daily_cost_limit": 1.00,
        "daily_request_limit": 500
    },
    "yearly": {
        "daily_token_limit": 2000000,
        "daily_cost_limit": 5.00,
        "daily_request_limit": 2000
    },
    "svip": {
        "daily_token_limit": -1,  # 无限
        "daily_cost_limit": -1,
        "daily_request_limit": -1
    }
}


class CostTracker:
    """AI服务成本追踪器"""

    def __init__(self):
        self._daily_usage: Dict[date, DailyUsage] = {}
        self._player_quotas: Dict[int, PlayerQuota] = {}
        self._pricing = PRICING

    def calculate_cost(
        self,
        service: str,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """计算成本"""
        pricing = self._pricing.get(service, {"input": 0, "output": 0})
        cost = (
            input_tokens / 1000 * pricing["input"] +
            output_tokens / 1000 * pricing["output"]
        )
        return round(cost, 6)

    def record_usage(
        self,
        player_id: int,
        service: str,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, Any]:
        """记录使用量"""
        today = date.today()
        cost = self.calculate_cost(service, input_tokens, output_tokens)

        # 更新每日统计
        if today not in self._daily_usage:
            self._daily_usage[today] = DailyUsage(date=today)

        daily = self._daily_usage[today]
        daily.total_input_tokens += input_tokens
        daily.total_output_tokens += output_tokens
        daily.total_cost += cost
        daily.request_count += 1

        if service not in daily.by_service:
            daily.by_service[service] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0.0,
                "requests": 0
            }

        daily.by_service[service]["input_tokens"] += input_tokens
        daily.by_service[service]["output_tokens"] += output_tokens
        daily.by_service[service]["cost"] += cost
        daily.by_service[service]["requests"] += 1

        # 更新玩家配额
        quota = self._get_or_create_quota(player_id)
        self._reset_quota_if_needed(quota)
        quota.used_tokens_today += input_tokens + output_tokens
        quota.used_cost_today += cost

        return {
            "cost": cost,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "player_remaining_tokens": max(0, quota.daily_token_limit - quota.used_tokens_today) if quota.daily_token_limit > 0 else -1,
            "player_remaining_cost": max(0, quota.daily_cost_limit - quota.used_cost_today) if quota.daily_cost_limit > 0 else -1
        }

    def check_quota(
        self,
        player_id: int,
        estimated_tokens: int = 0
    ) -> Dict[str, Any]:
        """检查配额"""
        quota = self._get_or_create_quota(player_id)
        self._reset_quota_if_needed(quota)

        # 无限配额
        if quota.daily_token_limit < 0:
            return {
                "allowed": True,
                "reason": None,
                "remaining_tokens": -1,
                "remaining_cost": -1
            }

        # 检查token配额
        if quota.used_tokens_today + estimated_tokens > quota.daily_token_limit:
            return {
                "allowed": False,
                "reason": "daily_token_limit_exceeded",
                "remaining_tokens": max(0, quota.daily_token_limit - quota.used_tokens_today),
                "remaining_cost": max(0, quota.daily_cost_limit - quota.used_cost_today)
            }

        # 检查成本配额
        if quota.daily_cost_limit > 0 and quota.used_cost_today >= quota.daily_cost_limit:
            return {
                "allowed": False,
                "reason": "daily_cost_limit_exceeded",
                "remaining_tokens": max(0, quota.daily_token_limit - quota.used_tokens_today),
                "remaining_cost": 0
            }

        return {
            "allowed": True,
            "reason": None,
            "remaining_tokens": quota.daily_token_limit - quota.used_tokens_today,
            "remaining_cost": quota.daily_cost_limit - quota.used_cost_today
        }

    def set_player_quota(
        self,
        player_id: int,
        membership_type: str = "free"
    ):
        """设置玩家配额"""
        quota_config = MEMBERSHIP_QUOTAS.get(membership_type, MEMBERSHIP_QUOTAS["free"])
        quota = self._get_or_create_quota(player_id)
        quota.daily_token_limit = quota_config["daily_token_limit"]
        quota.daily_cost_limit = quota_config["daily_cost_limit"]

    def get_player_usage(self, player_id: int) -> Dict[str, Any]:
        """获取玩家使用情况"""
        quota = self._get_or_create_quota(player_id)
        self._reset_quota_if_needed(quota)

        return {
            "player_id": player_id,
            "date": quota.last_reset.isoformat(),
            "used_tokens": quota.used_tokens_today,
            "used_cost": round(quota.used_cost_today, 4),
            "daily_token_limit": quota.daily_token_limit,
            "daily_cost_limit": quota.daily_cost_limit,
            "remaining_tokens": max(0, quota.daily_token_limit - quota.used_tokens_today) if quota.daily_token_limit > 0 else -1,
            "remaining_cost": max(0, quota.daily_cost_limit - quota.used_cost_today) if quota.daily_cost_limit > 0 else -1,
            "usage_percent": (quota.used_tokens_today / quota.daily_token_limit * 100) if quota.daily_token_limit > 0 else 0
        }

    def get_daily_report(self, report_date: Optional[date] = None) -> Dict[str, Any]:
        """获取每日报告"""
        target_date = report_date or date.today()
        daily = self._daily_usage.get(target_date)

        if not daily:
            return {
                "date": target_date.isoformat(),
                "total_cost": 0,
                "total_tokens": 0,
                "request_count": 0,
                "by_service": {}
            }

        return {
            "date": daily.date.isoformat(),
            "total_cost": round(daily.total_cost, 4),
            "total_input_tokens": daily.total_input_tokens,
            "total_output_tokens": daily.total_output_tokens,
            "total_tokens": daily.total_input_tokens + daily.total_output_tokens,
            "request_count": daily.request_count,
            "by_service": {
                service: {
                    "input_tokens": data["input_tokens"],
                    "output_tokens": data["output_tokens"],
                    "cost": round(data["cost"], 4),
                    "requests": data["requests"]
                }
                for service, data in daily.by_service.items()
            }
        }

    def get_service_stats(self) -> Dict[str, Any]:
        """获取服务统计"""
        today = date.today()
        daily = self._daily_usage.get(today)

        if not daily:
            return {"services": {}, "total_cost_today": 0}

        return {
            "services": {
                service: {
                    "requests": data["requests"],
                    "total_tokens": data["input_tokens"] + data["output_tokens"],
                    "cost": round(data["cost"], 4)
                }
                for service, data in daily.by_service.items()
            },
            "total_cost_today": round(daily.total_cost, 4)
        }

    def _get_or_create_quota(self, player_id: int) -> PlayerQuota:
        """获取或创建玩家配额"""
        if player_id not in self._player_quotas:
            self._player_quotas[player_id] = PlayerQuota(player_id=player_id)
        return self._player_quotas[player_id]

    def _reset_quota_if_needed(self, quota: PlayerQuota):
        """如果需要则重置配额"""
        today = date.today()
        if quota.last_reset != today:
            quota.used_tokens_today = 0
            quota.used_cost_today = 0.0
            quota.last_reset = today


# 单例实例
_cost_tracker: Optional[CostTracker] = None


def get_cost_tracker() -> CostTracker:
    """获取成本追踪器实例"""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker
