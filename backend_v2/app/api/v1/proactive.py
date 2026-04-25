"""
MindPal Backend V2 - Proactive Message API

ROI-7 主动消息端点：

  GET    /proactive/mine            未读 + 未过期主动消息列表（按 dh_id 聚合）
  POST   /proactive/{id}/ack        标记某条主动消息为已读
  POST   /proactive/{id}/dismiss    用户手动关闭（不打开 chat）

调度脚本（scripts/generate_proactive_messages.py）写入数据，
本路由只负责"读 + 状态翻转"，**不做 LLM 调用**，上下行都很轻量。
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.database import get_db
from app.models.proactive import ProactiveMessage
from app.schemas import APIResponse


router = APIRouter()


# ==================== Schemas ====================

class ProactiveItem(BaseModel):
    id: int
    dh_id: int
    scenario: str
    content: str
    created_at: Optional[str]
    delivered_at: Optional[str]
    is_acked: bool


class MineResponse(BaseModel):
    total: int
    items: List[ProactiveItem]
    by_dh: dict  # {dh_id: count}  方便前端给 dh-list 上红点


# ==================== 端点 ====================

@router.get("/mine", response_model=APIResponse)
async def list_my_proactive(
    dh_id: Optional[int] = Query(None, description="只看某个数字人"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    拉当前用户的"未读+未过期"主动消息。

    被拉到的消息自动标记 is_delivered=True（首次拉时填 delivered_at）。
    is_acked 仍保持 False，等用户真的打开 chat 才翻。
    """
    now = datetime.utcnow()
    stmt = (
        select(ProactiveMessage)
        .where(
            ProactiveMessage.user_id == user_id,
            ProactiveMessage.is_acked.is_(False),
            ProactiveMessage.is_dismissed.is_(False),
            ProactiveMessage.expires_at > now,
        )
        .order_by(desc(ProactiveMessage.created_at))
    )
    if dh_id is not None:
        stmt = stmt.where(ProactiveMessage.dh_id == dh_id)

    result = await db.execute(stmt)
    rows: List[ProactiveMessage] = list(result.scalars().all())

    # 标记 delivered（首次拉到时填时间戳）
    pending_ids = [r.id for r in rows if not r.is_delivered]
    if pending_ids:
        await db.execute(
            update(ProactiveMessage)
            .where(ProactiveMessage.id.in_(pending_ids))
            .values(is_delivered=True, delivered_at=now)
        )
        await db.commit()
        for r in rows:
            if r.id in pending_ids:
                r.is_delivered = True
                r.delivered_at = now

    by_dh: dict = {}
    items = []
    for r in rows:
        by_dh[r.dh_id] = by_dh.get(r.dh_id, 0) + 1
        items.append(r.to_dict())

    return APIResponse(
        code=0,
        message="ok",
        data={
            "total": len(items),
            "items": items,
            "by_dh": by_dh,
        },
    )


@router.post("/{message_id}/ack", response_model=APIResponse)
async def ack_proactive(
    message_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """用户打开了对应的对话，标记 is_acked=True。"""
    msg = await _load_owned(db, message_id, user_id)
    if msg.is_acked:
        return APIResponse(code=0, message="already acked", data={"id": message_id})

    msg.is_acked = True
    msg.acked_at = datetime.utcnow()
    await db.commit()
    return APIResponse(code=0, message="ok", data={"id": message_id})


@router.post("/{message_id}/dismiss", response_model=APIResponse)
async def dismiss_proactive(
    message_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """用户主动关闭（不打开对话）。"""
    msg = await _load_owned(db, message_id, user_id)
    msg.is_dismissed = True
    await db.commit()
    return APIResponse(code=0, message="ok", data={"id": message_id})


# ==================== 辅助 ====================

async def _load_owned(
    db: AsyncSession, message_id: int, user_id: int
) -> ProactiveMessage:
    stmt = select(ProactiveMessage).where(
        ProactiveMessage.id == message_id,
        ProactiveMessage.user_id == user_id,
    )
    result = await db.execute(stmt)
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="proactive message not found",
        )
    return msg
