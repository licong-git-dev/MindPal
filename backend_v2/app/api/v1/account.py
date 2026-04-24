"""
MindPal Backend V2 - Account Data Rights API

提供用户数据权利（User Data Rights）端点，对应《个人信息保护法》(PIPL)
第 44、45、47 条要求：
  - 第 44 条 知情权：用户可查看自己的个人信息范围
  - 第 45 条 查阅复制权：用户可下载自己的数据副本
  - 第 47 条 删除权：用户可删除自己的个人信息

端点汇总（全部挂在 /api/v1/account/*）:
  GET    /data-summary   数据摘要概览
  GET    /data-export    完整数据 JSON 导出
  DELETE /memories       清空所有长期记忆（跨所有数字人）
  DELETE /             注销账户（级联删除全部关联数据）

所有端点都要求 JWT 认证。注销操作需显式传 confirm=true 兜底。
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user_id
from app.database import get_db
from app.models.digital_human import DHConversation, DHMessage, DigitalHuman
from app.models.payment import Order
from app.models.user import User
from app.schemas import APIResponse
from app.services.memory import get_memory_retriever


router = APIRouter()


# ==================== Schemas ====================

class PasswordVerifyBody(BaseModel):
    """注销前密码验证"""
    password: str = Field(..., min_length=1, description="当前账号密码")


# ==================== 辅助函数 ====================

async def _get_user(user_id: int, db: AsyncSession) -> User:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


async def _count_user_digital_humans(user_id: int, db: AsyncSession) -> int:
    stmt = select(DigitalHuman).where(
        DigitalHuman.user_id == user_id,
        DigitalHuman.is_active == True,
    )
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def _count_user_conversations(user_id: int, db: AsyncSession) -> int:
    stmt = select(DHConversation).where(DHConversation.user_id == user_id)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def _count_user_messages(user_id: int, db: AsyncSession) -> int:
    """统计用户所有对话消息数（通过 DHConversation 关联）"""
    # 先取用户的所有 session_id
    stmt = select(DHConversation.session_id).where(DHConversation.user_id == user_id)
    result = await db.execute(stmt)
    session_ids = [row[0] for row in result.fetchall()]
    if not session_ids:
        return 0
    stmt = select(DHMessage).where(DHMessage.session_id.in_(session_ids))
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def _count_user_orders(user_id: int, db: AsyncSession) -> int:
    stmt = select(Order).where(Order.user_id == user_id)
    result = await db.execute(stmt)
    return len(result.scalars().all())


async def _count_user_memories(user_id: int) -> int:
    """统计用户所有长期记忆（跨所有数字人）"""
    retriever = get_memory_retriever()
    try:
        return await retriever.store.count({"player_id": user_id})
    except Exception:
        return 0


# ==================== 端点 1：数据摘要 ====================

@router.get("/data-summary", response_model=APIResponse)
async def get_data_summary(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    数据摘要概览 — PIPL §44 知情权

    返回用户在系统中存在的各类数据的数量统计，让用户知道"系统记录了我什么"。
    """
    user = await _get_user(user_id, db)

    dh_count = await _count_user_digital_humans(user_id, db)
    conv_count = await _count_user_conversations(user_id, db)
    msg_count = await _count_user_messages(user_id, db)
    order_count = await _count_user_orders(user_id, db)
    memory_count = await _count_user_memories(user_id)

    return APIResponse(
        code=0,
        message="success",
        data={
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "counts": {
                "digital_humans": dh_count,
                "conversations": conv_count,
                "messages": msg_count,
                "long_term_memories": memory_count,
                "orders": order_count,
            },
            "categories": [
                {"name": "账号基本信息", "description": "用户名、邮箱、手机号、创建时间"},
                {"name": "数字人档案", "description": "名字、头像、性格设定、人格 prompt"},
                {"name": "对话记录", "description": "与数字人的完整对话历史（含情感标记）"},
                {"name": "长期记忆", "description": "跨会话记住的事（可视化见 /memory.html）"},
                {"name": "订单记录", "description": "会员订阅和支付流水"},
            ],
        }
    )


# ==================== 端点 2：数据导出 ====================

@router.get("/data-export")
async def export_all_data(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    完整数据导出 — PIPL §45 查阅复制权

    返回一个完整的 JSON 附件，包含用户所有可识别数据。
    用户可保存此文件作为自己数据的完整副本。
    """
    user = await _get_user(user_id, db)

    # 1. 账号基本信息（不含密码 hash）
    user_data = {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "phone": user.phone,
        "wechat_openid": user.wechat_openid,
        "qq_openid": user.qq_openid,
        "google_id": user.google_id,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None,
    }

    # 2. 所有数字人
    dh_stmt = select(DigitalHuman).where(DigitalHuman.user_id == user_id)
    dh_result = await db.execute(dh_stmt)
    dhs: List[Dict[str, Any]] = []
    dh_list = dh_result.scalars().all()
    dh_ids: List[int] = []
    for dh in dh_list:
        dh_ids.append(dh.id)
        dhs.append({
            "id": dh.id,
            "name": dh.name,
            "avatar_type": dh.avatar_type,
            "avatar_url": dh.avatar_url,
            "personality": dh.personality,
            "personality_traits": dh.personality_traits,
            "custom_personality": dh.custom_personality,
            "role_type": dh.role_type,
            "system_prompt": getattr(dh, "system_prompt", None),
            "total_messages": dh.total_messages,
            "total_conversations": dh.total_conversations,
            "is_active": dh.is_active,
            "created_at": dh.created_at.isoformat() if getattr(dh, "created_at", None) else None,
        })

    # 3. 所有会话
    conv_stmt = select(DHConversation).where(DHConversation.user_id == user_id)
    conv_result = await db.execute(conv_stmt)
    conversations: List[Dict[str, Any]] = []
    session_ids: List[str] = []
    for c in conv_result.scalars().all():
        session_ids.append(c.session_id)
        conversations.append({
            "session_id": c.session_id,
            "dh_id": c.dh_id,
            "is_active": c.is_active,
            "message_count": c.message_count,
            "dominant_emotion": c.dominant_emotion,
            "started_at": c.started_at.isoformat() if c.started_at else None,
            "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
            "ended_at": c.ended_at.isoformat() if c.ended_at else None,
        })

    # 4. 所有消息
    messages: List[Dict[str, Any]] = []
    if session_ids:
        msg_stmt = select(DHMessage).where(DHMessage.session_id.in_(session_ids))
        msg_result = await db.execute(msg_stmt)
        for m in msg_result.scalars().all():
            messages.append({
                "id": m.id,
                "session_id": m.session_id,
                "dh_id": m.dh_id,
                "role": m.role,
                "content": m.content,
                "emotion": m.emotion,
                "emotion_scores": m.emotion_scores,
                "llm_model": m.llm_model,
                "created_at": m.created_at.isoformat() if getattr(m, "created_at", None) else None,
            })

    # 5. 长期记忆（向量库）
    retriever = get_memory_retriever()
    memories: List[Dict[str, Any]] = []
    try:
        docs = await retriever.store.list_by_metadata(
            filter_metadata={"player_id": user_id},
            limit=10000,
            offset=0,
        )
        for doc in docs:
            memories.append({
                "id": doc.id,
                "text": doc.text,
                "metadata": doc.metadata,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
            })
    except Exception:
        memories = []  # 向量库故障不阻塞导出

    # 6. 订单记录
    order_stmt = select(Order).where(Order.user_id == user_id)
    order_result = await db.execute(order_stmt)
    orders: List[Dict[str, Any]] = []
    for o in order_result.scalars().all():
        orders.append({
            "order_no": o.order_no,
            "product_type": o.product_type.value if hasattr(o.product_type, "value") else str(o.product_type),
            "product_id": o.product_id,
            "product_name": o.product_name,
            "quantity": o.quantity,
            "amount": o.amount,
            "currency": o.currency,
            "payment_method": o.payment_method.value if o.payment_method and hasattr(o.payment_method, "value") else None,
            "payment_no": o.payment_no,
            "status": o.status.value if hasattr(o.status, "value") else str(o.status),
            "paid_at": o.paid_at.isoformat() if o.paid_at else None,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        })

    export = {
        "export_format_version": "1.0",
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "legal_basis": "PIPL Article 45 - Right to access and copy personal information",
        "user": user_data,
        "digital_humans": dhs,
        "conversations": conversations,
        "messages": messages,
        "long_term_memories": memories,
        "orders": orders,
    }

    body = json.dumps(export, ensure_ascii=False, indent=2)
    filename = f"mindpal_data_user_{user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"

    return Response(
        content=body,
        media_type="application/json; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


# ==================== 端点 3：清空所有记忆 ====================

@router.delete("/memories", response_model=APIResponse)
async def clear_all_memories(
    confirm: bool = Query(False, description="必须显式传 true"),
    user_id: int = Depends(get_current_user_id),
):
    """
    清空该用户的所有长期记忆（跨所有数字人）— PIPL §47 删除权

    不影响对话消息本身（仍保留在数据库）；仅删除向量库中的长期记忆摘要。
    如需删除对话本身，请调 DELETE /account 注销账户。
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please pass ?confirm=true to actually delete all memories"
        )

    retriever = get_memory_retriever()
    try:
        deleted = await retriever.store.delete_by_metadata({"player_id": user_id})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear memories: {e}"
        )

    return APIResponse(
        code=0,
        message="success",
        data={"deleted": deleted}
    )


# ==================== 端点 4：注销账户 ====================

@router.delete("", response_model=APIResponse)
async def delete_account(
    body: PasswordVerifyBody,
    confirm: bool = Query(False, description="必须显式传 true"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """
    注销账户（级联删除所有关联数据）— PIPL §47 删除权

    删除顺序（先子表后主表以满足外键）:
      1. 长期记忆（向量库）
      2. DHMessage（所有对话消息）
      3. DHConversation（所有会话）
      4. DigitalHuman（所有数字人）
      5. Order（订单记录）- 注：保留订单号供财务审计，仅抹除 user_id
         但当前实现直接删除，合规需要时可改为"假名化"（参考 PIPL §51）
      6. User 表本身

    **保护性检查**:
    - 必须传 `?confirm=true`
    - 必须传正确的当前密码（防会话劫持后被恶意注销）
    - 订单删除可能被外键约束阻止（Payment 表有 order_id），将来改为
      设置 Order.user_id 为 NULL 更合规，但需要迁移脚本。
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please pass ?confirm=true to actually delete account"
        )

    user = await _get_user(user_id, db)

    # 密码验证
    if not user.check_password(body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password incorrect"
        )

    deleted_summary: Dict[str, int] = {}

    # 1. 长期记忆
    retriever = get_memory_retriever()
    try:
        deleted_summary["memories"] = await retriever.store.delete_by_metadata(
            {"player_id": user_id}
        )
    except Exception:
        deleted_summary["memories"] = 0

    # 2. 所有 session_id
    conv_stmt = select(DHConversation.session_id).where(DHConversation.user_id == user_id)
    conv_result = await db.execute(conv_stmt)
    session_ids = [row[0] for row in conv_result.fetchall()]

    # 3. 删除所有 DHMessage（先子后父）
    if session_ids:
        msg_count_stmt = select(DHMessage).where(DHMessage.session_id.in_(session_ids))
        msg_result = await db.execute(msg_count_stmt)
        deleted_summary["messages"] = len(msg_result.scalars().all())
        await db.execute(
            delete(DHMessage).where(DHMessage.session_id.in_(session_ids))
        )
    else:
        deleted_summary["messages"] = 0

    # 4. DHConversation
    conv_count_stmt = select(DHConversation).where(DHConversation.user_id == user_id)
    conv_count_result = await db.execute(conv_count_stmt)
    deleted_summary["conversations"] = len(conv_count_result.scalars().all())
    await db.execute(delete(DHConversation).where(DHConversation.user_id == user_id))

    # 5. DigitalHuman
    dh_count_stmt = select(DigitalHuman).where(DigitalHuman.user_id == user_id)
    dh_count_result = await db.execute(dh_count_stmt)
    deleted_summary["digital_humans"] = len(dh_count_result.scalars().all())
    await db.execute(delete(DigitalHuman).where(DigitalHuman.user_id == user_id))

    # 6. Order —— 注：Payment 表可能通过 order_id 外键依赖，删除可能失败
    # 当前实现尝试删除；如被外键阻止用户会看到 500，此时可先联系客服走手动流程
    order_count_stmt = select(Order).where(Order.user_id == user_id)
    order_count_result = await db.execute(order_count_stmt)
    deleted_summary["orders"] = len(order_count_result.scalars().all())
    try:
        await db.execute(delete(Order).where(Order.user_id == user_id))
    except Exception:
        # 订单删除失败不阻塞整体注销（可能有 Payment 外键引用）
        # 降级策略：保留订单但至少抹掉关键 PII —— 但目前 Order 表无冗余 PII 字段
        deleted_summary["orders_deletion_failed"] = True

    # 7. User 本身
    try:
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {e}"
        )

    return APIResponse(
        code=0,
        message="Account deleted. Farewell.",
        data={
            "deleted_summary": deleted_summary,
            "legal_basis": "PIPL Article 47 - Right to deletion",
        }
    )
