"""
MindPal Backend V2 - Quota Middleware / Dependency

提供两种配额拦截方式:
  1. FastAPI Dependency: 适用于非流式端点（超限直接抛 HTTP 402）
  2. QuotaGuard.check(): 适用于 SSE / WebSocket 流式端点（在流已开启后
     需要手动发送 error 事件，不能靠异常返回 402）

配额底层由 ai/cost.py 的 CostTracker 管理，内存态 + 每日重置 + 会员等级。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user_id
from app.services.ai.cost import get_cost_tracker


# 默认对话消耗估算 (token)
DEFAULT_CHAT_TOKENS = 1000

# 知识库上传估算（embedding 成本折算）
DEFAULT_UPLOAD_TOKENS = 2000

# 语音合成/识别估算
DEFAULT_VOICE_TOKENS = 500


class QuotaGuard:
    """供流式端点手动调用的配额守卫。

    用法:
        async def stream_endpoint(...):
            guard = QuotaGuard(user_id, DEFAULT_CHAT_TOKENS)
            if not guard.check():
                return guard.as_sse_error()
            # ... 正常生成流
    """

    def __init__(self, user_id: int, estimated_tokens: int = DEFAULT_CHAT_TOKENS):
        self.user_id = user_id
        self.estimated_tokens = estimated_tokens
        self._tracker = get_cost_tracker()
        self._result: Optional[Dict[str, Any]] = None

    def check(self) -> bool:
        """返回是否允许继续。结果缓存到 self._result 以便构造响应。"""
        self._result = self._tracker.check_quota(self.user_id, self.estimated_tokens)
        return bool(self._result.get("allowed"))

    @property
    def reason(self) -> Optional[str]:
        return (self._result or {}).get("reason")

    def as_http_402(self) -> HTTPException:
        r = self._result or {}
        return HTTPException(
            status_code=402,
            detail={
                "code": "QUOTA_EXCEEDED",
                "reason": r.get("reason", "daily quota exceeded"),
                "remaining_tokens": r.get("remaining_tokens"),
                "remaining_cost": r.get("remaining_cost"),
                "upgrade_url": "/pricing.html",
            },
        )

    def as_sse_error_payload(self) -> Dict[str, Any]:
        r = self._result or {}
        return {
            "error": "quota_exceeded",
            "reason": r.get("reason", "daily quota exceeded"),
            "remaining_tokens": r.get("remaining_tokens"),
            "remaining_cost": r.get("remaining_cost"),
            "upgrade_url": "/pricing.html",
        }


def _make_dependency(estimated_tokens: int):
    """构造不同 token 预算的 Dependency。"""
    async def _dep(user_id: int = Depends(get_current_user_id)) -> int:
        tracker = get_cost_tracker()
        result = tracker.check_quota(user_id, estimated_tokens)
        if not result.get("allowed"):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "code": "QUOTA_EXCEEDED",
                    "reason": result.get("reason", "daily quota exceeded"),
                    "remaining_tokens": result.get("remaining_tokens"),
                    "remaining_cost": result.get("remaining_cost"),
                    "upgrade_url": "/pricing.html",
                },
            )
        return user_id
    return _dep


# 预定义 Dependency（可直接用 Depends(check_chat_quota)）
check_chat_quota = _make_dependency(DEFAULT_CHAT_TOKENS)
check_upload_quota = _make_dependency(DEFAULT_UPLOAD_TOKENS)
check_voice_quota = _make_dependency(DEFAULT_VOICE_TOKENS)


__all__ = [
    "QuotaGuard",
    "check_chat_quota",
    "check_upload_quota",
    "check_voice_quota",
    "DEFAULT_CHAT_TOKENS",
    "DEFAULT_UPLOAD_TOKENS",
    "DEFAULT_VOICE_TOKENS",
]
