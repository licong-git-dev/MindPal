"""
MindPal Backend V2 - User Report API

合规点:
- 《生成式人工智能服务管理暂行办法》§15: 提供投诉举报接口
- SLA: 首次响应 24h，处理完毕 7 天

端点:
  POST   /reports          创建举报（已登录或匿名）
  GET    /reports/mine     我的举报列表
  GET    /reports/{id}     举报详情（自己的 or 管理员）
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.database import get_db
from app.models.report import (
    ReportCategory,
    ReportStatus,
    ReportTargetType,
    UserReport,
)
from app.schemas import APIResponse


router = APIRouter()


# ==================== Schemas ====================

class CreateReportBody(BaseModel):
    category: ReportCategory
    description: str = Field(..., min_length=10, max_length=2000)
    target_type: ReportTargetType = ReportTargetType.SYSTEM
    target_id: Optional[str] = Field(None, max_length=100)
    context_snippet: Optional[str] = Field(None, max_length=2000)
    # 匿名举报时必传 email 以便回复
    reporter_email: Optional[EmailStr] = None


# ==================== 辅助 ====================

async def _get_optional_user_id(request: Request) -> Optional[int]:
    """尽力获取当前用户 id，失败则返回 None（支持匿名举报）"""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    token = auth[7:]
    if token.startswith("temp_") or not token:
        return None
    try:
        from app.core.security import decode_token
        payload = decode_token(token)
        sub = payload.get("sub") if payload else None
        return int(sub) if sub else None
    except Exception:
        return None


# ==================== 端点 ====================

@router.post("", response_model=APIResponse)
async def create_report(
    body: CreateReportBody,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    创建举报。登录用户可匿名选项；未登录用户必须提供 email。
    """
    user_id = await _get_optional_user_id(request)

    if not user_id and not body.reporter_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="匿名举报必须提供 reporter_email 以便回复"
        )

    report = UserReport(
        reporter_user_id=user_id,
        reporter_email=body.reporter_email,
        category=body.category,
        description=body.description,
        target_type=body.target_type,
        target_id=body.target_id,
        context_snippet=body.context_snippet,
        status=ReportStatus.PENDING,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    return APIResponse(
        code=0,
        message="success",
        data={
            "id": report.id,
            "status": report.status.value,
            "created_at": report.created_at.isoformat(),
            "sla_message": "我们将在 24 小时内首次响应，7 天内处理完毕。紧急情况请拨打 400-161-9995（全国心理援助热线）。",
        }
    )


@router.get("/mine", response_model=APIResponse)
async def list_my_reports(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """我的举报列表（仅登录用户）"""
    stmt = select(UserReport).where(
        UserReport.reporter_user_id == user_id
    ).order_by(desc(UserReport.created_at)).offset(offset).limit(limit)

    result = await db.execute(stmt)
    reports = result.scalars().all()

    return APIResponse(
        code=0,
        message="success",
        data={
            "items": [r.to_dict() for r in reports],
            "total": len(reports),
        }
    )


@router.get("/{report_id}", response_model=APIResponse)
async def get_report(
    report_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """查看举报详情（仅本人）"""
    stmt = select(UserReport).where(UserReport.id == report_id)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if report.reporter_user_id and report.reporter_user_id != user_id:
        # 这里未来可以加管理员判定，允许审核员查看全部
        raise HTTPException(status_code=403, detail="Not your report")

    return APIResponse(
        code=0,
        message="success",
        data=report.to_dict()
    )
