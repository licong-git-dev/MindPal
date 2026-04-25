"""
MindPal Backend V2 - CP Relationship Models

C2 双人共养：两个用户共同绑定到同一个数字人，对话历史 / 记忆 / 好感度
都可以共同看到。最小可用版本：
  - CpInvitation: 邀请码（pending → accepted/expired）
  - CpBond: 已建立的关系（dh_id × user_a × user_b，单向去重）

权限模型（在 digital_humans GET 等端点扩展）：
  - DigitalHuman.user_id 仍然是"主人"
  - 若当前用户是 CpBond.user_a 或 user_b 之一，则视为有访问权
"""

from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class CpInvitation(Base):
    """CP 邀请码（一次性，TTL 7 天）"""
    __tablename__ = "cp_invitations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dh_id: Mapped[int] = mapped_column(ForeignKey("digital_humans.id"), index=True)
    inviter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # 6 位邀请码，case-insensitive，全表唯一（在应用层保证）
    code: Mapped[str] = mapped_column(String(16), unique=True, index=True)

    # pending / accepted / expired / cancelled
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)

    accepted_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "dh_id": self.dh_id,
            "inviter_id": self.inviter_id,
            "code": self.code,
            "status": self.status,
            "accepted_by": self.accepted_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
        }


class CpBond(Base):
    """已建立的 CP 绑定。一个 (dh_id, user_a, user_b) 元组只能有一条 active。"""
    __tablename__ = "cp_bonds"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    dh_id: Mapped[int] = mapped_column(ForeignKey("digital_humans.id"), index=True)

    # user_a 永远是 DH 的"主人"（DigitalHuman.user_id），user_b 是被邀请方
    user_a: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    user_b: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # active / left
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)

    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_cpbond_dh_users", "dh_id", "user_a", "user_b"),
        Index("ix_cpbond_user_b_active", "user_b", "status"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "dh_id": self.dh_id,
            "user_a": self.user_a,
            "user_b": self.user_b,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
        }

    @staticmethod
    def involves(bond: "CpBond", user_id: int) -> bool:
        return bond.user_a == user_id or bond.user_b == user_id
