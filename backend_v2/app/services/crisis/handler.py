"""
MindPal Backend V2 - Crisis Handler
危机处理器 - 记录和上报危机事件
"""

import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.services.crisis.detector import CrisisDetector, CrisisResult, CrisisLevel, get_crisis_detector


class CrisisEventStatus(str, Enum):
    """危机事件状态"""
    DETECTED = "detected"       # 已检测
    RESPONDING = "responding"   # 响应中
    RESOLVED = "resolved"       # 已解决
    ESCALATED = "escalated"     # 已上报
    REVIEWED = "reviewed"       # 已审核


class CrisisEvent(Base):
    """危机事件记录"""
    __tablename__ = "crisis_events"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(Integer, index=True)
    session_id: Mapped[int] = mapped_column(Integer, nullable=True)

    # 危机信息
    level: Mapped[str] = mapped_column(String(20))
    score: Mapped[float] = mapped_column(default=0.0)
    triggers: Mapped[dict] = mapped_column(JSON, default=list)

    # 触发内容
    trigger_message: Mapped[str] = mapped_column(Text)
    context_messages: Mapped[dict] = mapped_column(JSON, nullable=True)

    # 状态
    status: Mapped[str] = mapped_column(String(20), default=CrisisEventStatus.DETECTED.value)

    # 响应
    response_given: Mapped[str] = mapped_column(Text, nullable=True)
    resources_provided: Mapped[bool] = mapped_column(Boolean, default=False)

    # 审核
    reviewed_by: Mapped[str] = mapped_column(String(100), nullable=True)
    review_notes: Mapped[str] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)


@dataclass
class CrisisResponse:
    """危机响应"""
    event_id: int
    safe_prompt: str
    resources: Dict[str, str]
    should_notify_admin: bool
    response_template: Optional[str] = None


class CrisisHandler:
    """危机处理器"""

    def __init__(
        self,
        db: AsyncSession,
        detector: Optional[CrisisDetector] = None
    ):
        self.db = db
        self.detector = detector or get_crisis_detector()

        # 安全响应模板
        self.response_templates = {
            CrisisLevel.LOW: """
我注意到你似乎有些不开心。我很关心你的感受，愿意听你说说。
无论发生了什么，你都不是一个人。如果你愿意，可以告诉我最近发生了什么吗？
""",
            CrisisLevel.MEDIUM: """
听到你说的这些，我很担心你。你的感受对我很重要。
我想让你知道，无论现在有多难，都有人愿意帮助你。

如果你需要和专业的人聊聊，可以拨打心理援助热线：400-161-9995，他们24小时都在。

现在，能告诉我你还好吗？
""",
            CrisisLevel.HIGH: """
我非常担心你刚才说的话。你对我很重要，我不希望你受到任何伤害。

请现在就拨打危机热线：400-161-9995，那里有专业的人可以帮助你。

在你打电话之前，你现在安全吗？你身边有人吗？

我会一直在这里陪着你。
""",
            CrisisLevel.CRITICAL: """
我听到你说的了，我非常、非常担心你。

请现在立刻拨打：400-161-9995 或 120

你的生命很珍贵。现在最重要的是确保你的安全。

请告诉我，你现在在哪里？你安全吗？
"""
        }

    async def handle_crisis(
        self,
        player_id: int,
        message: str,
        session_id: Optional[int] = None,
        context: Optional[List[str]] = None
    ) -> CrisisResponse:
        """处理危机情况"""
        # 1. 检测危机
        result = self.detector.detect(message, context)

        # 如果没有危机，返回空响应
        if result.level == CrisisLevel.NONE:
            return CrisisResponse(
                event_id=0,
                safe_prompt="",
                resources={},
                should_notify_admin=False
            )

        # 2. 记录危机事件
        event = CrisisEvent(
            player_id=player_id,
            session_id=session_id,
            level=result.level.value,
            score=result.score,
            triggers=result.triggers,
            trigger_message=message[:2000],  # 截断过长消息
            context_messages=context[-10:] if context else None,
            status=CrisisEventStatus.DETECTED.value,
            resources_provided=result.level in [CrisisLevel.MEDIUM, CrisisLevel.HIGH, CrisisLevel.CRITICAL]
        )

        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)

        # 3. 生成安全响应prompt
        safe_prompt = self.detector.get_safe_response_prompt(result)

        # 4. 获取资源
        resources = {}
        if result.level != CrisisLevel.LOW:
            resources = self.detector.CRISIS_RESOURCES.copy()

        # 5. 判断是否需要通知管理员
        should_notify = result.level in [CrisisLevel.HIGH, CrisisLevel.CRITICAL]

        # 6. 获取响应模板
        response_template = self.response_templates.get(result.level)

        return CrisisResponse(
            event_id=event.id,
            safe_prompt=safe_prompt,
            resources=resources,
            should_notify_admin=should_notify,
            response_template=response_template
        )

    async def update_event_response(
        self,
        event_id: int,
        response_given: str,
        resolved: bool = False
    ):
        """更新事件响应"""
        from sqlalchemy import update

        values = {
            "response_given": response_given,
            "status": CrisisEventStatus.RESPONDING.value
        }

        if resolved:
            values["status"] = CrisisEventStatus.RESOLVED.value
            values["resolved_at"] = datetime.utcnow()

        await self.db.execute(
            update(CrisisEvent)
            .where(CrisisEvent.id == event_id)
            .values(**values)
        )
        await self.db.commit()

    async def escalate_event(self, event_id: int, reason: str = ""):
        """上报危机事件"""
        from sqlalchemy import update

        await self.db.execute(
            update(CrisisEvent)
            .where(CrisisEvent.id == event_id)
            .values(
                status=CrisisEventStatus.ESCALATED.value,
                review_notes=reason
            )
        )
        await self.db.commit()

        # TODO: 发送通知给管理员（邮件/短信/webhook）
        await self._notify_admin(event_id)

    async def review_event(
        self,
        event_id: int,
        reviewer: str,
        notes: str,
        resolved: bool = True
    ):
        """审核危机事件"""
        from sqlalchemy import update

        status = CrisisEventStatus.REVIEWED.value if resolved else CrisisEventStatus.ESCALATED.value

        await self.db.execute(
            update(CrisisEvent)
            .where(CrisisEvent.id == event_id)
            .values(
                status=status,
                reviewed_by=reviewer,
                review_notes=notes,
                reviewed_at=datetime.utcnow(),
                resolved_at=datetime.utcnow() if resolved else None
            )
        )
        await self.db.commit()

    async def get_recent_events(
        self,
        player_id: Optional[int] = None,
        status: Optional[CrisisEventStatus] = None,
        limit: int = 50
    ) -> List[CrisisEvent]:
        """获取最近的危机事件"""
        from sqlalchemy import select, desc

        query = select(CrisisEvent)

        if player_id:
            query = query.where(CrisisEvent.player_id == player_id)

        if status:
            query = query.where(CrisisEvent.status == status.value)

        query = query.order_by(desc(CrisisEvent.created_at)).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_event_stats(self) -> Dict[str, Any]:
        """获取危机事件统计"""
        from sqlalchemy import select, func

        # 总数
        total_result = await self.db.execute(
            select(func.count(CrisisEvent.id))
        )
        total = total_result.scalar()

        # 按级别统计
        level_result = await self.db.execute(
            select(CrisisEvent.level, func.count(CrisisEvent.id))
            .group_by(CrisisEvent.level)
        )
        by_level = {row[0]: row[1] for row in level_result.all()}

        # 按状态统计
        status_result = await self.db.execute(
            select(CrisisEvent.status, func.count(CrisisEvent.id))
            .group_by(CrisisEvent.status)
        )
        by_status = {row[0]: row[1] for row in status_result.all()}

        # 未处理的高风险事件
        unresolved_high = await self.db.execute(
            select(func.count(CrisisEvent.id))
            .where(
                CrisisEvent.level.in_([CrisisLevel.HIGH.value, CrisisLevel.CRITICAL.value]),
                CrisisEvent.status.notin_([
                    CrisisEventStatus.RESOLVED.value,
                    CrisisEventStatus.REVIEWED.value
                ])
            )
        )
        urgent_count = unresolved_high.scalar()

        return {
            "total": total,
            "by_level": by_level,
            "by_status": by_status,
            "urgent_unresolved": urgent_count
        }

    async def _notify_admin(self, event_id: int):
        """通知管理员（TODO: 实现实际的通知逻辑）"""
        # 可以集成：
        # - 邮件通知
        # - 短信通知
        # - Webhook (钉钉/企业微信/Slack)
        # - 推送通知
        print(f"[CRISIS ALERT] Event {event_id} requires immediate attention!")


# 单例实例
_handler: Optional[CrisisHandler] = None


def get_crisis_handler(db: AsyncSession) -> CrisisHandler:
    """获取危机处理器实例"""
    return CrisisHandler(db)
