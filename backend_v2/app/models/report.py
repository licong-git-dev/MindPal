"""
MindPal Backend V2 - User Report Model

用户投诉举报记录。对应 PIPL §44-47（用户权利）+
《生成式人工智能服务管理暂行办法》§15（投诉处理义务）。

设计:
- 所有字段允许为空（匿名举报）
- target_type + target_id 定位被举报对象
- status 生命周期: pending → reviewing → resolved | dismissed
- 响应 SLA: 24h 内首次回复，7 天内处理完毕
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReportCategory(str, enum.Enum):
    """举报类别"""
    INAPPROPRIATE_CONTENT = "inappropriate_content"  # 不当内容
    HARASSMENT = "harassment"                         # 骚扰 / 诱导
    PRIVACY_LEAK = "privacy_leak"                     # 隐私泄露
    IMPERSONATION = "impersonation"                   # 冒充他人
    CRISIS_FAILURE = "crisis_failure"                 # 危机干预失败（AI 没识别或回复不当）
    SYSTEM_BUG = "system_bug"                         # 系统故障
    OTHER = "other"


class ReportStatus(str, enum.Enum):
    PENDING = "pending"         # 新提交
    REVIEWING = "reviewing"     # 审核中
    RESOLVED = "resolved"       # 已处理
    DISMISSED = "dismissed"     # 无效举报


class ReportTargetType(str, enum.Enum):
    DIGITAL_HUMAN = "digital_human"  # 针对某个数字人
    MESSAGE = "message"              # 针对某条消息
    USER = "user"                    # 针对其他用户（社交场景，预留）
    SYSTEM = "system"                # 系统层面


class UserReport(Base):
    """用户举报记录"""
    __tablename__ = "user_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 举报人（允许匿名 - user_id 为 null 时通过 email 联系）
    reporter_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    reporter_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # 被举报目标
    target_type: Mapped[ReportTargetType] = mapped_column(
        SQLEnum(ReportTargetType), nullable=False
    )
    target_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # 上下文截图或消息片段（用户手动粘贴，限长 2000 字符）
    context_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 举报内容
    category: Mapped[ReportCategory] = mapped_column(
        SQLEnum(ReportCategory), nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # 处理状态
    status: Mapped[ReportStatus] = mapped_column(
        SQLEnum(ReportStatus), default=ReportStatus.PENDING, index=True
    )
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    first_response_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True, comment="首次响应时间（SLA 24h）"
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "reporter_user_id": self.reporter_user_id,
            "reporter_email": self.reporter_email,
            "target_type": self.target_type.value if self.target_type else None,
            "target_id": self.target_id,
            "context_snippet": self.context_snippet,
            "category": self.category.value if self.category else None,
            "description": self.description,
            "status": self.status.value if self.status else None,
            "resolution_note": self.resolution_note,
            "first_response_at": self.first_response_at.isoformat() if self.first_response_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
