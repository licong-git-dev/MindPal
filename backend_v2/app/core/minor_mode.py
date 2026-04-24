"""
MindPal Backend V2 - Minor Mode Guard

青少年模式运行时守卫。对应 DEEP_AUDIT_V3 GAP-5 及
《未成年人保护法》第 74-77 条、《未成年人网络保护条例》。

规则:
  1. 禁用浪漫陪伴人格（romantic_* 预设）
  2. 每日累计对话时长 ≤ 40 分钟（用 Redis 计数，不用时降级为 InMemory）
  3. 22:00-06:00 禁用对话

调用契约:
  MinorModeGuard.check_dialogue_allowed(user_id) → {allowed, reason}

如果用户未开启青少年模式则直接放行（is_enabled=False）。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, time
from typing import Dict, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cache
from app.models.user import User


DAILY_MINUTE_LIMIT = int(os.getenv("MINOR_MODE_DAILY_MINUTES", "40"))
NIGHT_BLOCK_START = time(22, 0)  # 22:00
NIGHT_BLOCK_END = time(6, 0)     # 06:00


@dataclass
class MinorModeResult:
    """青少年守卫检查结果"""
    allowed: bool
    reason: str = ""
    user_message: str = ""
    remaining_minutes: Optional[int] = None


class MinorModeGuard:
    """青少年模式运行时守卫"""

    @staticmethod
    def _is_night_time(now: Optional[datetime] = None) -> bool:
        """是否处于 22:00-06:00 夜间禁用时段"""
        now = now or datetime.now()
        t = now.time()
        return t >= NIGHT_BLOCK_START or t < NIGHT_BLOCK_END

    @staticmethod
    def _today_key(user_id: int) -> str:
        today = datetime.utcnow().strftime("%Y%m%d")
        return f"minor:usage:{user_id}:{today}"

    async def is_enabled_for_user(
        self,
        user_id: int,
        db: AsyncSession,
    ) -> bool:
        """查询用户是否开启了青少年模式"""
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return False
        # minor_mode_forced 或 minor_mode_enabled 任一为 True 都算开启
        return bool(getattr(user, "minor_mode_enabled", False)
                    or getattr(user, "minor_mode_forced", False))

    async def check_personality(
        self,
        user_id: int,
        personality_key: str,
        db: AsyncSession,
    ) -> MinorModeResult:
        """检查当前用户能否使用某性格预设。

        青少年模式下禁用 romantic_* 系列。
        """
        if not await self.is_enabled_for_user(user_id, db):
            return MinorModeResult(allowed=True)

        if personality_key and personality_key.startswith("romantic_"):
            return MinorModeResult(
                allowed=False,
                reason="minor_mode_romantic_disabled",
                user_message="青少年模式下不支持浪漫陪伴类预设，请选择基础陪伴。",
            )
        return MinorModeResult(allowed=True)

    async def check_time_window(
        self,
        user_id: int,
        db: AsyncSession,
    ) -> MinorModeResult:
        """检查是否处于夜间禁用时段"""
        if not await self.is_enabled_for_user(user_id, db):
            return MinorModeResult(allowed=True)

        if self._is_night_time():
            return MinorModeResult(
                allowed=False,
                reason="minor_mode_night_block",
                user_message="青少年模式下 22:00-06:00 禁止使用，请明天继续。",
            )
        return MinorModeResult(allowed=True)

    async def check_daily_quota(
        self,
        user_id: int,
        db: AsyncSession,
    ) -> MinorModeResult:
        """检查今日累计对话时长"""
        if not await self.is_enabled_for_user(user_id, db):
            return MinorModeResult(allowed=True)

        cache = get_cache()
        key = self._today_key(user_id)
        try:
            used_str = await cache.get(key)
            used = int(used_str) if used_str else 0
        except Exception:
            used = 0

        if used >= DAILY_MINUTE_LIMIT:
            return MinorModeResult(
                allowed=False,
                reason="minor_mode_daily_limit",
                user_message=f"青少年模式下每日使用时长已达 {DAILY_MINUTE_LIMIT} 分钟上限，请明天继续。",
                remaining_minutes=0,
            )

        return MinorModeResult(
            allowed=True,
            remaining_minutes=DAILY_MINUTE_LIMIT - used,
        )

    async def record_usage(
        self,
        user_id: int,
        minutes_used: int = 1,
    ):
        """记录用户使用时长（每次对话调用加 1 分钟近似）"""
        cache = get_cache()
        key = self._today_key(user_id)
        try:
            used_str = await cache.get(key)
            used = int(used_str) if used_str else 0
            # 24 小时过期（T+1 自然重置）
            await cache.set(key, str(used + minutes_used), ttl=86400)
        except Exception:
            pass  # 计数故障不阻塞主流程


_guard: Optional[MinorModeGuard] = None


def get_minor_mode_guard() -> MinorModeGuard:
    global _guard
    if _guard is None:
        _guard = MinorModeGuard()
    return _guard
