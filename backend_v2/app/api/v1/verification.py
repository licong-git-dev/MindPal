"""
MindPal Backend V2 - Identity Verification API

合规点:
- 《生成式人工智能服务管理暂行办法》§9（要求真实身份信息）
- 《未成年人保护法》（禁止 18 岁以下）

端点:
  POST /verification/submit   提交实名认证
  GET  /verification/status   查询当前认证状态
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.database import get_db
from app.models.user import User
from app.schemas import APIResponse
from app.services.verification import (
    VerificationStatus,
    get_identity_verifier,
)


router = APIRouter()


# ==================== Schemas ====================

class VerifyBody(BaseModel):
    name: str = Field(..., min_length=2, max_length=50, description="真实姓名")
    id_card: str = Field(..., min_length=18, max_length=18, description="18 位身份证号")
    phone: str = Field(..., min_length=11, max_length=11, description="11 位手机号")


# ==================== 端点 ====================

@router.post("/submit", response_model=APIResponse)
async def submit_verification(
    body: VerifyBody,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    提交实名认证。

    - 身份证指向未成年 → 400 拒绝（不能注册）
    - 三方 API 未配置 → 返回 503 告知管理员
    - 认证成功 → User.is_verified = True，更新认证元数据

    注意: 不保存 id_card 明文，只存 hash 和出生年月（最小必要）。
    """
    verifier = get_identity_verifier()
    result = await verifier.verify(body.name, body.id_card, body.phone)

    if result.status == VerificationStatus.INVALID_ID_FORMAT:
        raise HTTPException(status_code=400, detail="身份证格式错误")

    if result.status == VerificationStatus.MINOR_DETECTED:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "MINOR_DETECTED",
                "message": result.error_message,
                "birth_year": result.birth_year,
            }
        )

    if result.status == VerificationStatus.NOT_CONFIGURED:
        # 真实 API 未接通时的降级：告知前端不可用
        # 生产环境应由运维监控 / 告警
        raise HTTPException(
            status_code=503,
            detail={
                "code": "VERIFICATION_NOT_CONFIGURED",
                "message": "实名认证服务暂未开启，请联系管理员。"
            }
        )

    if result.status != VerificationStatus.SUCCESS or not result.is_verified:
        raise HTTPException(
            status_code=400,
            detail={
                "code": result.status.value,
                "message": result.error_message or "实名认证失败，请核对信息"
            }
        )

    # 更新 User.is_verified
    stmt = select(User).where(User.id == user_id)
    user_result = await db.execute(stmt)
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    await db.commit()

    return APIResponse(
        code=0,
        message="success",
        data={
            "is_verified": True,
            "verified_at": datetime.utcnow().isoformat(),
            "birth_year": result.birth_year,
        }
    )


@router.get("/status", response_model=APIResponse)
async def get_verification_status(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """查询当前用户认证状态"""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return APIResponse(
        code=0,
        message="success",
        data={
            "is_verified": user.is_verified,
        }
    )
