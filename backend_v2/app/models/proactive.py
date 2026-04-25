"""
MindPal Backend V2 - Proactive Message Model

ROI-7 主动消息：数字人主动给用户推一句问候/回忆/关心，拉动次日留存。

一条记录 = 一个"准备好要推给用户"的消息。
调度脚本（scripts/generate_proactive_messages.py）每天跑一次，
按场景给每个活跃用户的每个数字人最多生成一条；
前端在 dh-list 页/chat 页拉 GET /proactive/mine 展示未读红点，
打开后调 POST /proactive/{id}/ack 标记已读。
"""

from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProactiveMessage(Base):
    """数字人主动消息表"""
    __tablename__ = "proactive_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    dh_id: Mapped[int] = mapped_column(ForeignKey("digital_humans.id"), index=True)

    # 生成场景：idle_1d / idle_3d / idle_7d / affinity_milestone / memory_callback / birthday
    scenario: Mapped[str] = mapped_column(String(40), index=True)

    # 消息正文（由 generator 基于场景 + 人格 + top 记忆渲染）
    content: Mapped[str] = mapped_column(Text)

    # 生成元数据（JSON 字符串，记录触发依据：好感度、引用的记忆 id、最后聊天时间等）
    meta_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 状态机：pending → delivered（已被前端拉到）→ acked（用户打开对话/点击）
    # 或者 dismissed（用户手动关闭/过期）
    is_delivered: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_acked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    acked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)

    __table_args__ = (
        # 查询"某用户的某数字人的未读主动消息"的主路径
        Index("ix_proactive_user_dh_unacked", "user_id", "dh_id", "is_acked"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "dh_id": self.dh_id,
            "scenario": self.scenario,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "delivered_at": self.delivered_at.isoformat() if self.delivered_at else None,
            "acked_at": self.acked_at.isoformat() if self.acked_at else None,
            "is_acked": self.is_acked,
            "is_dismissed": self.is_dismissed,
        }
