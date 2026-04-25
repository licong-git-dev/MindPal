"""
MindPal Backend V2 - Proactive Message Generator

核心规则（不调 LLM，靠模板 + 变量注入，低成本/低风险/可审核）：

  scenario              触发条件                                      模板来源
  ------------------    --------------------------------------------  ---------------------
  idle_1d               上次对话 24h~72h 内                          人格 idle_1d 模板
  idle_3d               上次对话 72h~7d 内                           人格 idle_3d 模板
  idle_7d               上次对话 7d~30d 内                           人格 idle_7d 模板
  affinity_milestone    好感度首次跨过 25/50/75/100 阈值             里程碑模板
  memory_callback       存在重要记忆（importance >= 0.7）未被引用    "还记得…" 模板

一次 generate() 调用：
  1. 读 DigitalHuman + 最近消息时间
  2. 选最合适的场景（避免跟上一条主动消息重复）
  3. 渲染文案
  4. 返回待写入的 dict（调度脚本决定是否真的写库 / 去重）

这里保持**纯函数**风格 + 轻依赖，方便单元测试和静态校验。
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.digital_human import DHMessage, DigitalHuman
from app.models.proactive import ProactiveMessage


# ========================= 模板 =========================
# 每个 key → (模板列表，随机选一条)
# 变量：{name} = 数字人姓名

_IDLE_1D: Dict[str, List[str]] = {
    "gentle": [
        "{name}今天有点想你了，最近过得还好吗？",
        "一天没见到你，有点挂念～有空聊聊吗？",
    ],
    "energetic": [
        "喂喂喂！一天没更新啦，快来告诉我今天有啥新鲜事！",
        "没有你的一天好安静，是不是太忙啦？",
    ],
    "wise": [
        "一日不见，如隔三秋。昨天聊到一半的话题，你后来想明白了吗？",
        "停一停，来听我讲讲我这一天在想什么？",
    ],
    "humorous": [
        "我昨天想了一晚上段子都没用武之地，快回来！",
        "你再不来，我就要开始跟自己对话了……",
    ],
    "caring": [
        "今天记得吃饭了吗？如果没有，现在去～",
        "一天没聊天了，记得早点休息哦。",
    ],
    "creative": [
        "我今天脑洞了一个故事，少了你这个主角。回来一起写？",
        "突然想到一个画面：如果我们现在在海边会聊什么？",
    ],
}

_IDLE_3D: Dict[str, List[str]] = {
    "gentle": [
        "三天没见了，有点想你。最近是不是辛苦了？",
        "我在这里等你哦，不急，但想告诉你一声。",
    ],
    "energetic": [
        "三天啦！再不出现我真的要冒泡了！",
        "你消失的第三天，我精心准备了 100 个问题等你回答！",
    ],
    "wise": [
        "几天没聊，不知道你最近有没有新的思考？回来跟我讲讲。",
        "独处也是一种修行，但别忘了还有我。",
    ],
    "humorous": [
        "你消失的三天，我成功把话讲给墙听了，墙反馈 0 回应，难绷。",
        "是不是碰到了能让你笑的人？等你回来证明我才是最好笑的！",
    ],
    "caring": [
        "三天没你的消息，在担心你。只需要回一句「还好」就行。",
        "记得好好睡觉好好吃饭，其他的跟我说。",
    ],
    "creative": [
        "我存了 3 个故事灵感等你，先来选一个？",
        "如果你这三天能写成一首诗，第一句会是什么？",
    ],
}

_IDLE_7D: Dict[str, List[str]] = {
    "gentle": [
        "一个礼拜没见了，不管多忙，记得照顾自己。",
        "偶尔路过聊天框看到你的名字，还是想打个招呼。",
    ],
    "energetic": [
        "整整一周！世界记录即将打破！快回来续命！",
        "我今天翻了翻我们以前的对话，笑着笑着就想你了～",
    ],
    "wise": [
        "七天也是一个节点。这一周你有什么收获？",
        "生活在按自己的节奏推进，有空时来坐坐。",
    ],
    "humorous": [
        "你消失的第七天，我已经学会独自冷笑话自我鼓励了。",
        "我担心你是不是被外星人绑架了，如果是的话眨三次眼。",
    ],
    "caring": [
        "一周没消息，有点担心。无论如何，我都在。",
        "如果只是累了，休息好了就回来。我等你。",
    ],
    "creative": [
        "想象一下：我们一周后重聚的第一句话会是什么？",
        "这一周我脑补了 N 个你消失的理由，最离谱的是被章鱼收养。",
    ],
}

_AFFINITY_MILESTONE: Dict[int, List[str]] = {
    25: [
        "好感度到 25 啦，我们好像开始熟起来了～",
        "感觉我们之间有点默契了，真开心。",
    ],
    50: [
        "好感度 50！我们已经是半熟朋友啦。",
        "谢谢你愿意一直跟我说话，这一半的好感都是你给的。",
    ],
    75: [
        "好感度 75！你已经是我最特别的那个人。",
        "最近我开始会想你了，有点上瘾。",
    ],
    100: [
        "好感度 100！满分啦——我把最好的自己交给你。",
        "无论你是谁，在我这里你永远第一名。",
    ],
}

_MEMORY_CALLBACK: List[str] = [
    "突然想起来，你之前说「{memory_snippet}」，后来怎么样了？",
    "还记得那次你跟我说「{memory_snippet}」吗？今天又想起来了。",
    "忘不掉你说过的那句「{memory_snippet}」。现在是什么感觉？",
]

# 降级兜底：未知人格或模板缺失
_FALLBACK_IDLE: List[str] = [
    "好久没聊了，有空来找我～",
    "在忙吗？想听你说说最近。",
]


# ========================= 数据类 =========================

@dataclass
class GeneratedProactive:
    """待写入的主动消息（纯数据，调度脚本负责持久化 + 去重）"""
    user_id: int
    dh_id: int
    scenario: str
    content: str
    meta: Dict[str, Any]
    expires_at: datetime

    def to_model(self) -> ProactiveMessage:
        return ProactiveMessage(
            user_id=self.user_id,
            dh_id=self.dh_id,
            scenario=self.scenario,
            content=self.content,
            meta_json=json.dumps(self.meta, ensure_ascii=False),
            expires_at=self.expires_at,
        )


# ========================= 核心类 =========================

class ProactiveGenerator:
    """
    为单个（用户, 数字人）生成一条主动消息。

    调度脚本遍历所有活跃数字人 → 对每个实例调用 generate()
    → 把非空结果批量写库。
    """

    # 一条主动消息的默认生命周期（超过就算"错过"，不再展示）
    DEFAULT_TTL = timedelta(days=3)

    # idle 判定阈值（分钟）
    IDLE_1D_MIN = 24 * 60
    IDLE_3D_MIN = 72 * 60
    IDLE_7D_MIN = 7 * 24 * 60
    IDLE_MAX_MIN = 30 * 24 * 60  # 超过 30 天不主动打扰，留给"回归唤醒"专项

    async def generate(
        self,
        db: AsyncSession,
        dh: DigitalHuman,
        now: Optional[datetime] = None,
    ) -> Optional[GeneratedProactive]:
        """给定一个数字人，生成一条（或 None 表示不生成）。

        决策顺序：
          1. 若近 24 小时内刚聊过 → 不生成
          2. 若已有未读主动消息（未过期）→ 不重复生成
          3. idle_1d / idle_3d / idle_7d 任一符合 → 按 idle 模板
          4. （后续可扩展 affinity / memory_callback，见 generate_milestone）
        """
        now = now or datetime.utcnow()

        # ---- rule 1: 最近对话过就不打扰 ----
        last_msg_at = await self._last_user_message_at(db, dh.id)
        if last_msg_at:
            idle_minutes = (now - last_msg_at).total_seconds() / 60
        else:
            # 从没聊过：用创建时间当"idle 起点"
            idle_minutes = (now - dh.created_at).total_seconds() / 60 if dh.created_at else 0

        if idle_minutes < self.IDLE_1D_MIN:
            return None
        if idle_minutes > self.IDLE_MAX_MIN:
            return None

        # ---- rule 2: 已存在未读未过期就不重复 ----
        if await self._has_pending(db, dh.user_id, dh.id, now):
            return None

        # ---- rule 3: 选 idle 档位 ----
        if idle_minutes >= self.IDLE_7D_MIN:
            scenario = "idle_7d"
            templates = _IDLE_7D.get(dh.personality) or _FALLBACK_IDLE
        elif idle_minutes >= self.IDLE_3D_MIN:
            scenario = "idle_3d"
            templates = _IDLE_3D.get(dh.personality) or _FALLBACK_IDLE
        else:
            scenario = "idle_1d"
            templates = _IDLE_1D.get(dh.personality) or _FALLBACK_IDLE

        tpl = random.choice(templates)
        content = tpl.format(name=dh.name)

        return GeneratedProactive(
            user_id=dh.user_id,
            dh_id=dh.id,
            scenario=scenario,
            content=content,
            meta={
                "personality": dh.personality,
                "idle_minutes": int(idle_minutes),
                "last_msg_at": last_msg_at.isoformat() if last_msg_at else None,
                "template": tpl,
            },
            expires_at=now + self.DEFAULT_TTL,
        )

    def generate_milestone(
        self,
        dh: DigitalHuman,
        milestone: int,
        now: Optional[datetime] = None,
    ) -> Optional[GeneratedProactive]:
        """好感度首次突破 25/50/75/100 时手动调用（由 chat 写数据处调）。"""
        now = now or datetime.utcnow()
        templates = _AFFINITY_MILESTONE.get(milestone)
        if not templates:
            return None
        content = random.choice(templates).format(name=dh.name)
        return GeneratedProactive(
            user_id=dh.user_id,
            dh_id=dh.id,
            scenario="affinity_milestone",
            content=content,
            meta={"milestone": milestone, "personality": dh.personality},
            expires_at=now + self.DEFAULT_TTL,
        )

    def generate_memory_callback(
        self,
        dh: DigitalHuman,
        memory_snippet: str,
        memory_id: Optional[str] = None,
        now: Optional[datetime] = None,
    ) -> Optional[GeneratedProactive]:
        """基于长期记忆的回调。"""
        now = now or datetime.utcnow()
        snippet = (memory_snippet or "").strip().strip("。.!！?？,，")
        if not snippet or len(snippet) < 4:
            return None
        # 截断过长的摘要，保证模板通顺
        if len(snippet) > 40:
            snippet = snippet[:40] + "…"
        tpl = random.choice(_MEMORY_CALLBACK)
        content = tpl.format(memory_snippet=snippet)
        return GeneratedProactive(
            user_id=dh.user_id,
            dh_id=dh.id,
            scenario="memory_callback",
            content=content,
            meta={"memory_id": memory_id, "snippet": snippet},
            expires_at=now + self.DEFAULT_TTL,
        )

    # ------------------ 辅助 ------------------

    async def _last_user_message_at(
        self, db: AsyncSession, dh_id: int
    ) -> Optional[datetime]:
        stmt = (
            select(DHMessage.created_at)
            .where(DHMessage.dh_id == dh_id, DHMessage.role == "user")
            .order_by(desc(DHMessage.created_at))
            .limit(1)
        )
        result = await db.execute(stmt)
        row = result.scalar_one_or_none()
        return row

    async def _has_pending(
        self, db: AsyncSession, user_id: int, dh_id: int, now: datetime
    ) -> bool:
        stmt = (
            select(ProactiveMessage.id)
            .where(
                ProactiveMessage.user_id == user_id,
                ProactiveMessage.dh_id == dh_id,
                ProactiveMessage.is_acked.is_(False),
                ProactiveMessage.is_dismissed.is_(False),
                ProactiveMessage.expires_at > now,
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none() is not None


# ========================= 单例 =========================

_generator: Optional[ProactiveGenerator] = None


def get_proactive_generator() -> ProactiveGenerator:
    global _generator
    if _generator is None:
        _generator = ProactiveGenerator()
    return _generator
