"""
MindPal Backend V2 - Unified Moderator

Moderator 是对外唯一入口。调用方只需:

    from app.services.moderation import get_moderator
    result = await get_moderator().check(text, scene="user_input")
    if result.blocked:
        ...

## 场景

- user_input:    用户发送的对话消息
- llm_output:    LLM 生成的回复（非流式全量 or 流式收束后）
- knowledge:     用户上传的知识库文档
- profile:       数字人名字/性格自定义描述等

不同场景可能对同一类别的宽容度不同（例如 user_input 对 PROMPT_INJECTION 严格，
llm_output 更关心 PORN/POLITICS）。当前实现用同一套规则，将来可分场景加权。

## 执行顺序

1. Local filter（毫秒级）
2. 如果 local 命中且是高风险类别 → 直接 block
3. 否则调用阿里云（如启用）做二审
4. 合并结果返回

## 返回

ModerationResult 结构化告诉调用方:
  - blocked: 是否阻断
  - category: 主要类别
  - reason: 人类可读原因（日志 + 运营审计）
  - user_message: 给终端用户的安全提示文案
  - hits: 本地命中详情（埋点 / 运营复盘）
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional

from app.services.moderation.aliyun import (
    AliyunModeration,
    get_aliyun_moderation,
)
from app.services.moderation.filters import (
    FilterHit,
    FilterResult,
    LocalFilter,
    ModerationCategory,
    get_local_filter,
)


# 命中后给终端用户看的提示语（按类别分）
USER_MESSAGE_BY_CATEGORY = {
    ModerationCategory.POLITICS:         "这个话题比较敏感，我们聊点别的好吗？",
    ModerationCategory.PORN:              "抱歉，我没办法聊这个。",
    ModerationCategory.VIOLENCE:          "这部分内容我不能讨论，请换个话题。",
    ModerationCategory.ILLEGAL:           "涉及违法内容，我没办法继续这个话题。",
    ModerationCategory.HATE:              "对不起，我希望我们之间的对话保持尊重。",
    ModerationCategory.MINOR:             "这个话题涉及未成年保护，我必须停下来。",
    ModerationCategory.CONTACT_SCAM:      "为了你的账户安全，请不要分享联系方式或可疑链接。",
    ModerationCategory.PROMPT_INJECTION:  "我感觉到你在试着绕过我的设定，我们回到正常聊天吧。",
    ModerationCategory.SAFE:              "",
}

# AI 被迫替换回复时用的兜底文案
SAFE_FALLBACK_REPLY = "这个话题可能不太合适呢，我们换个方向聊聊？"

# 高风险类别 - 本地命中即 block，不再等云审
HIGH_RISK_CATEGORIES = {
    ModerationCategory.POLITICS,
    ModerationCategory.PORN,
    ModerationCategory.MINOR,
    ModerationCategory.HATE,
    ModerationCategory.ILLEGAL,
}


@dataclass
class ModerationResult:
    """对外统一的审核结果"""
    blocked: bool
    category: ModerationCategory = ModerationCategory.SAFE
    reason: str = ""
    user_message: str = ""
    hits: List[FilterHit] = field(default_factory=list)
    # 调用元信息（埋点用）
    local_blocked: bool = False
    cloud_blocked: bool = False
    cloud_suggestion: str = "pass"
    score: float = 0.0


def is_moderation_enabled() -> bool:
    """全局审核开关。生产环境应为 true。"""
    return os.getenv("MODERATION_ENABLED", "true").lower() != "false"


def is_dry_run() -> bool:
    """Dry-run 模式：返回命中信息但不阻断。用于运营调优。"""
    return os.getenv("MODERATION_DRY_RUN", "false").lower() == "true"


class Moderator:
    """内容审核统一入口"""

    def __init__(
        self,
        local_filter: Optional[LocalFilter] = None,
        aliyun: Optional[AliyunModeration] = None,
    ):
        self.local = local_filter or get_local_filter()
        self.aliyun = aliyun or get_aliyun_moderation()

    async def check(self, text: str, scene: str = "user_input") -> ModerationResult:
        """检查文本。返回结构化结果。"""
        # 全局开关关闭
        if not is_moderation_enabled():
            return ModerationResult(blocked=False)

        if not text or len(text.strip()) == 0:
            return ModerationResult(blocked=False)

        # 1. 本地规则
        local: FilterResult = self.local.check(text)

        # 2. 高风险类别快速判定
        if local.is_blocked and local.dominant_category in HIGH_RISK_CATEGORIES:
            return self._build_result(
                local_result=local,
                cloud_suggestion="skipped",
                scene=scene,
            )

        # 3. 低风险或 SAFE —— 调阿里云二审
        cloud_suggestion = "pass"
        cloud_blocked = False
        if self.aliyun.usable:
            try:
                cloud = await self.aliyun.check_text(text)
                cloud_suggestion = cloud.suggestion
                cloud_blocked = cloud.is_blocked
            except Exception:
                # 云审故障不阻断主链路
                cloud_suggestion = "error"

        return self._build_result(
            local_result=local,
            cloud_suggestion=cloud_suggestion,
            cloud_blocked=cloud_blocked,
            scene=scene,
        )

    def _build_result(
        self,
        local_result: FilterResult,
        cloud_suggestion: str,
        cloud_blocked: bool = False,
        scene: str = "user_input",
    ) -> ModerationResult:
        category = local_result.dominant_category
        local_blocked = local_result.is_blocked

        # 最终 blocked 判定
        blocked = local_blocked or cloud_blocked
        # Dry-run 覆盖：永远不真 block，只上报
        if is_dry_run():
            blocked = False

        reason_parts = []
        if local_blocked:
            hit_cats = sorted({h.category.value for h in local_result.hits})
            reason_parts.append(f"local:{','.join(hit_cats)}")
        if cloud_blocked:
            reason_parts.append(f"cloud:{cloud_suggestion}")

        return ModerationResult(
            blocked=blocked,
            category=category,
            reason="|".join(reason_parts) or "safe",
            user_message=USER_MESSAGE_BY_CATEGORY.get(category, SAFE_FALLBACK_REPLY),
            hits=list(local_result.hits),
            local_blocked=local_blocked,
            cloud_blocked=cloud_blocked,
            cloud_suggestion=cloud_suggestion,
            score=local_result.score,
        )


_moderator: Optional[Moderator] = None


def get_moderator() -> Moderator:
    """获取全局单例"""
    global _moderator
    if _moderator is None:
        _moderator = Moderator()
    return _moderator
