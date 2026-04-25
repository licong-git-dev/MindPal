"""
MindPal Backend V2 - CP Relationship API

C2 双人共养 — 让两个用户共同绑定到一个数字人。

端点:
  POST   /cp/invitations           创建邀请码（仅 DH 主人能发）
  POST   /cp/invitations/accept    接受邀请码 → 建立 bond
  GET    /cp/bonds                 我参与的 bond 列表
  DELETE /cp/bonds/{bond_id}       退出 bond（任意一方都可以）
"""

from __future__ import annotations

import secrets
import string
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.database import get_db
from app.models.cp import CpBond, CpInvitation
from app.models.digital_human import DigitalHuman
from app.models.user import User
from app.schemas import APIResponse


router = APIRouter()


# ==================== Schemas ====================

class CreateInvitationBody(BaseModel):
    dh_id: int = Field(..., description="要分享给伙伴的数字人 ID")


class AcceptInvitationBody(BaseModel):
    code: str = Field(..., min_length=4, max_length=16)


# ==================== Helpers ====================

INVITATION_TTL = timedelta(days=7)
INVITATION_CODE_ALPHABET = string.ascii_uppercase + string.digits


async def _generate_unique_code(db: AsyncSession, length: int = 6) -> str:
    """生成 6 位唯一邀请码（大写字母 + 数字）"""
    for _ in range(8):
        code = ''.join(secrets.choice(INVITATION_CODE_ALPHABET) for _ in range(length))
        existing = await db.execute(select(CpInvitation).where(CpInvitation.code == code))
        if existing.scalar_one_or_none() is None:
            return code
    # 8 次都撞了概率几乎为 0；兜底加 1 位
    return await _generate_unique_code(db, length + 1)


async def _get_owned_dh(dh_id: int, user_id: int, db: AsyncSession) -> DigitalHuman:
    stmt = select(DigitalHuman).where(
        DigitalHuman.id == dh_id,
        DigitalHuman.user_id == user_id,
        DigitalHuman.is_active.is_(True),
    )
    res = await db.execute(stmt)
    dh = res.scalar_one_or_none()
    if not dh:
        raise HTTPException(404, "Digital human not found or you are not the owner")
    return dh


async def _get_bond(bond_id: int, user_id: int, db: AsyncSession) -> CpBond:
    stmt = select(CpBond).where(CpBond.id == bond_id)
    res = await db.execute(stmt)
    bond = res.scalar_one_or_none()
    if not bond:
        raise HTTPException(404, "bond not found")
    if not (bond.user_a == user_id or bond.user_b == user_id):
        raise HTTPException(403, "not your bond")
    return bond


# ==================== Endpoints ====================

@router.post("/invitations", response_model=APIResponse)
async def create_invitation(
    body: CreateInvitationBody,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """生成邀请码（仅 DH 主人能发）。"""
    dh = await _get_owned_dh(body.dh_id, user_id, db)

    # 检查是否已经有 active bond — 一个 DH 当前只允许一个 partner
    existing_bond = await db.execute(
        select(CpBond).where(
            CpBond.dh_id == dh.id,
            CpBond.status == "active",
        )
    )
    if existing_bond.scalar_one_or_none():
        raise HTTPException(409, "this digital human already has a CP partner")

    code = await _generate_unique_code(db)
    inv = CpInvitation(
        dh_id=dh.id,
        inviter_id=user_id,
        code=code,
        status="pending",
        expires_at=datetime.utcnow() + INVITATION_TTL,
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)

    return APIResponse(
        code=0,
        message="invitation created",
        data={
            "code": code,
            "dh_id": dh.id,
            "dh_name": dh.name,
            "expires_at": inv.expires_at.isoformat(),
            "ttl_days": INVITATION_TTL.days,
        },
    )


@router.post("/invitations/accept", response_model=APIResponse)
async def accept_invitation(
    body: AcceptInvitationBody,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """接受邀请码 → 建立 CpBond。"""
    code = body.code.strip().upper()
    res = await db.execute(select(CpInvitation).where(CpInvitation.code == code))
    inv: Optional[CpInvitation] = res.scalar_one_or_none()
    if not inv:
        raise HTTPException(404, "invitation code not found")
    if inv.status != "pending":
        raise HTTPException(409, f"invitation is {inv.status}")
    if inv.expires_at and inv.expires_at < datetime.utcnow():
        inv.status = "expired"
        await db.commit()
        raise HTTPException(410, "invitation expired")
    if inv.inviter_id == user_id:
        raise HTTPException(400, "cannot accept your own invitation")

    # 已经有这个 DH 的 bond → 直接告知
    existing = await db.execute(
        select(CpBond).where(
            CpBond.dh_id == inv.dh_id,
            CpBond.status == "active",
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, "this digital human already has an active partner")

    bond = CpBond(
        dh_id=inv.dh_id,
        user_a=inv.inviter_id,
        user_b=user_id,
        status="active",
        started_at=datetime.utcnow(),
    )
    inv.status = "accepted"
    inv.accepted_by = user_id
    inv.accepted_at = datetime.utcnow()
    db.add(bond)
    await db.commit()
    await db.refresh(bond)

    # 取 dh 名 / 邀请人名给前端做提示
    dh_q = await db.execute(select(DigitalHuman).where(DigitalHuman.id == inv.dh_id))
    dh = dh_q.scalar_one_or_none()
    inviter_q = await db.execute(select(User).where(User.id == inv.inviter_id))
    inviter = inviter_q.scalar_one_or_none()

    return APIResponse(
        code=0,
        message="invitation accepted",
        data={
            "bond_id": bond.id,
            "dh_id": bond.dh_id,
            "dh_name": dh.name if dh else None,
            "partner_id": bond.user_a,
            "partner_name": inviter.username if inviter else None,
            "started_at": bond.started_at.isoformat(),
        },
    )


@router.get("/bonds", response_model=APIResponse)
async def list_my_bonds(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """列出我参与的所有 active bond。"""
    stmt = (
        select(CpBond)
        .where(
            CpBond.status == "active",
            or_(CpBond.user_a == user_id, CpBond.user_b == user_id),
        )
        .order_by(desc(CpBond.started_at))
    )
    res = await db.execute(stmt)
    bonds: List[CpBond] = list(res.scalars().all())

    items = []
    for b in bonds:
        partner_id = b.user_b if b.user_a == user_id else b.user_a
        partner_q = await db.execute(select(User).where(User.id == partner_id))
        partner = partner_q.scalar_one_or_none()
        dh_q = await db.execute(select(DigitalHuman).where(DigitalHuman.id == b.dh_id))
        dh = dh_q.scalar_one_or_none()
        items.append({
            "bond_id": b.id,
            "dh_id": b.dh_id,
            "dh_name": dh.name if dh else None,
            "is_owner": (b.user_a == user_id),
            "partner_id": partner_id,
            "partner_name": partner.username if partner else None,
            "started_at": b.started_at.isoformat() if b.started_at else None,
        })

    return APIResponse(code=0, message="ok", data={"items": items})


@router.delete("/bonds/{bond_id}", response_model=APIResponse)
async def leave_bond(
    bond_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """退出 bond（任意一方都可以）。"""
    bond = await _get_bond(bond_id, user_id, db)
    if bond.status != "active":
        return APIResponse(code=0, message="already inactive", data={"id": bond_id})
    bond.status = "left"
    bond.ended_at = datetime.utcnow()
    await db.commit()
    return APIResponse(code=0, message="left", data={"id": bond_id})
