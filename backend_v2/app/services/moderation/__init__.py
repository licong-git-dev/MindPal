"""
MindPal Backend V2 - Content Moderation Package

对应 DEEP_AUDIT_V3 P3-2:
  输入过滤（用户发送消息前）
  输出过滤（LLM 生成回复后）

设计:
  - 本地规则先行（关键词 + 正则，毫秒级响应，不产生云调用成本）
  - 云端兜底可选（阿里云绿网 / 腾讯云天御，通过 env 开关打开）
  - 统一入口 Moderator.check(text, scene) 返回 ModerationResult
"""

from app.services.moderation.moderator import (
    Moderator,
    ModerationResult,
    ModerationCategory,
    get_moderator,
    SAFE_FALLBACK_REPLY,
)

__all__ = [
    "Moderator",
    "ModerationResult",
    "ModerationCategory",
    "get_moderator",
    "SAFE_FALLBACK_REPLY",
]
