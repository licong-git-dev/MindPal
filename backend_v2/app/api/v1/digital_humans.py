"""
MindPal Backend V2 - Digital Human API Routes
数字人CRUD和对话API
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from datetime import datetime
from typing import Optional
import uuid
import json

from app.database import get_db
from app.models.user import User
from app.models.digital_human import DigitalHuman, DHConversation, DHMessage
from app.schemas.digital_human import (
    DigitalHumanCreate,
    DigitalHumanUpdate,
    DigitalHumanResponse,
    DHChatRequest,
)
from app.schemas import APIResponse
from app.core.security import get_current_user_id
from app.services.personality_engine import get_personality_engine
from app.services.llm import get_llm_router

router = APIRouter()


# ===================== 数字人 CRUD =====================

@router.post("", response_model=APIResponse)
async def create_digital_human(
    body: DigitalHumanCreate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    创建数字人

    - **name**: 数字人名字
    - **personality**: 性格类型 (gentle/energetic/wise/humorous/caring/creative)
    - **role_type**: 角色类型 (companion/teacher)
    - **voice_id**: 声音ID
    - **domains**: 擅长领域列表
    """
    # 检查用户是否存在
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # 检查数字人数量限制（免费用户最多3个）
    stmt = select(DigitalHuman).where(
        and_(
            DigitalHuman.user_id == user_id,
            DigitalHuman.is_active == True
        )
    )
    result = await db.execute(stmt)
    existing_count = len(result.scalars().all())

    if existing_count >= 10:  # 临时限制
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum number of digital humans reached"
        )

    # 生成System Prompt
    personality_engine = get_personality_engine()
    system_prompt = personality_engine.generate_system_prompt(
        name=body.name,
        personality=body.personality,
        personality_traits=body.personality_traits.model_dump() if body.personality_traits else None,
        custom_personality=body.custom_personality,
        role_type=body.role_type,
        domains=body.domains,
        user_name=user.username or "用户"
    )

    # 创建数字人
    dh = DigitalHuman(
        user_id=user_id,
        name=body.name,
        avatar_type=body.avatar_type,
        personality=body.personality,
        personality_traits=body.personality_traits.model_dump() if body.personality_traits else None,
        custom_personality=body.custom_personality,
        role_type=body.role_type,
        voice_id=body.voice_id,
        voice_speed=body.voice_speed,
        domains=body.domains,
        system_prompt=system_prompt,
        is_default=existing_count == 0  # 第一个数字人设为默认
    )

    db.add(dh)
    await db.commit()
    await db.refresh(dh)

    return APIResponse(
        code=0,
        message="Digital human created successfully",
        data={
            "id": dh.id,
            "name": dh.name,
            "personality": dh.personality,
            "personality_display": dh.get_personality_display(),
            "role_type": dh.role_type,
            "is_default": dh.is_default,
            "created_at": dh.created_at.isoformat()
        }
    )


@router.get("", response_model=APIResponse)
async def list_digital_humans(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取用户的数字人列表"""
    # 查询总数
    stmt = select(DigitalHuman).where(
        and_(
            DigitalHuman.user_id == user_id,
            DigitalHuman.is_active == True
        )
    )
    result = await db.execute(stmt)
    all_dhs = result.scalars().all()
    total = len(all_dhs)

    # 分页查询
    stmt = select(DigitalHuman).where(
        and_(
            DigitalHuman.user_id == user_id,
            DigitalHuman.is_active == True
        )
    ).order_by(desc(DigitalHuman.is_default), desc(DigitalHuman.last_conversation_at)).offset((page - 1) * size).limit(size)

    result = await db.execute(stmt)
    dhs = result.scalars().all()

    items = []
    for dh in dhs:
        item = dh.to_dict()
        item["personality_display"] = dh.get_personality_display()
        items.append(item)

    return APIResponse(
        code=0,
        message="success",
        data={
            "total": total,
            "page": page,
            "size": size,
            "items": items
        }
    )


@router.get("/{dh_id}", response_model=APIResponse)
async def get_digital_human(
    dh_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取数字人详情"""
    stmt = select(DigitalHuman).where(
        and_(
            DigitalHuman.id == dh_id,
            DigitalHuman.user_id == user_id
        )
    )
    result = await db.execute(stmt)
    dh = result.scalar_one_or_none()

    if not dh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital human not found"
        )

    data = dh.to_dict()
    data["personality_display"] = dh.get_personality_display()

    return APIResponse(
        code=0,
        message="success",
        data=data
    )


@router.put("/{dh_id}", response_model=APIResponse)
async def update_digital_human(
    dh_id: int,
    body: DigitalHumanUpdate,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """更新数字人"""
    stmt = select(DigitalHuman).where(
        and_(
            DigitalHuman.id == dh_id,
            DigitalHuman.user_id == user_id
        )
    )
    result = await db.execute(stmt)
    dh = result.scalar_one_or_none()

    if not dh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital human not found"
        )

    # 更新字段
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "personality_traits" and value:
            setattr(dh, field, value.model_dump() if hasattr(value, 'model_dump') else value)
        else:
            setattr(dh, field, value)

    # 如果性格相关字段有变化，重新生成System Prompt
    if any(field in update_data for field in ["personality", "personality_traits", "custom_personality", "role_type", "domains", "name"]):
        personality_engine = get_personality_engine()

        # 获取用户名
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        dh.system_prompt = personality_engine.generate_system_prompt(
            name=dh.name,
            personality=dh.personality,
            personality_traits=dh.personality_traits,
            custom_personality=dh.custom_personality,
            role_type=dh.role_type,
            domains=dh.domains,
            user_name=user.username if user else "用户"
        )

    # 处理设为默认
    if body.is_default:
        # 取消其他默认
        stmt = select(DigitalHuman).where(
            and_(
                DigitalHuman.user_id == user_id,
                DigitalHuman.is_default == True,
                DigitalHuman.id != dh_id
            )
        )
        result = await db.execute(stmt)
        for other_dh in result.scalars().all():
            other_dh.is_default = False

    dh.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(dh)

    data = dh.to_dict()
    data["personality_display"] = dh.get_personality_display()

    return APIResponse(
        code=0,
        message="Digital human updated successfully",
        data=data
    )


@router.delete("/{dh_id}", response_model=APIResponse)
async def delete_digital_human(
    dh_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """删除数字人（软删除）"""
    stmt = select(DigitalHuman).where(
        and_(
            DigitalHuman.id == dh_id,
            DigitalHuman.user_id == user_id
        )
    )
    result = await db.execute(stmt)
    dh = result.scalar_one_or_none()

    if not dh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital human not found"
        )

    # 软删除
    dh.is_active = False
    dh.updated_at = datetime.utcnow()

    # 如果是默认数字人，设置另一个为默认
    if dh.is_default:
        stmt = select(DigitalHuman).where(
            and_(
                DigitalHuman.user_id == user_id,
                DigitalHuman.is_active == True,
                DigitalHuman.id != dh_id
            )
        ).limit(1)
        result = await db.execute(stmt)
        another_dh = result.scalar_one_or_none()
        if another_dh:
            another_dh.is_default = True

    await db.commit()

    return APIResponse(
        code=0,
        message="Digital human deleted successfully",
        data={"id": dh_id}
    )


# ===================== 对话 API =====================

@router.post("/{dh_id}/chat", response_model=APIResponse)
async def chat_with_dh(
    dh_id: int,
    body: DHChatRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    与数字人对话（非流式）

    - **dh_id**: 数字人ID
    - **message**: 用户消息
    - **session_id**: 会话ID（可选）
    """
    # 获取数字人
    stmt = select(DigitalHuman).where(
        and_(
            DigitalHuman.id == dh_id,
            DigitalHuman.user_id == user_id,
            DigitalHuman.is_active == True
        )
    )
    result = await db.execute(stmt)
    dh = result.scalar_one_or_none()

    if not dh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital human not found"
        )

    # 获取或创建会话
    session_id = body.session_id or str(uuid.uuid4())

    stmt = select(DHConversation).where(DHConversation.session_id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        session = DHConversation(
            session_id=session_id,
            user_id=user_id,
            dh_id=dh_id,
        )
        db.add(session)
        await db.flush()

    # 保存用户消息
    user_msg = DHMessage(
        session_id=session_id,
        dh_id=dh_id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)

    # 获取历史消息（最近10轮）
    stmt = select(DHMessage).where(
        DHMessage.session_id == session_id
    ).order_by(DHMessage.created_at.desc()).limit(20)
    result = await db.execute(stmt)
    history_messages = list(result.scalars().all())
    history_messages.reverse()

    # 构建消息列表
    messages = [{"role": msg.role, "content": msg.content} for msg in history_messages]
    messages.append({"role": "user", "content": body.message})

    # 调用LLM
    llm_router = get_llm_router()
    llm_service = llm_router.get_service()

    try:
        ai_response = await llm_service.chat(
            messages=messages,
            system_prompt=dh.system_prompt or f"你是{dh.name}，一个友善的AI伙伴。",
            temperature=0.8,
            max_tokens=500,
        )
    except Exception as e:
        ai_response = f"抱歉，我现在有点恍惚...能再说一遍吗？"

    # 保存AI回复
    ai_msg = DHMessage(
        session_id=session_id,
        dh_id=dh_id,
        role="assistant",
        content=ai_response,
        llm_model=llm_service.get_model_name(),
    )
    db.add(ai_msg)

    # 更新统计
    session.message_count += 2
    session.last_message_at = datetime.utcnow()
    dh.total_messages += 2
    dh.total_conversations = dh.total_conversations or 0
    if not body.session_id:  # 新会话
        dh.total_conversations += 1
    dh.last_conversation_at = datetime.utcnow()

    await db.commit()

    return APIResponse(
        code=0,
        message="success",
        data={
            "session_id": session_id,
            "dh_id": dh_id,
            "response": ai_response,
            "is_complete": True,
        }
    )


@router.post("/{dh_id}/chat/stream")
async def chat_stream_with_dh(
    dh_id: int,
    body: DHChatRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    与数字人对话（流式SSE）

    返回Server-Sent Events流
    """
    # 获取数字人
    stmt = select(DigitalHuman).where(
        and_(
            DigitalHuman.id == dh_id,
            DigitalHuman.user_id == user_id,
            DigitalHuman.is_active == True
        )
    )
    result = await db.execute(stmt)
    dh = result.scalar_one_or_none()

    if not dh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital human not found"
        )

    # 获取或创建会话
    session_id = body.session_id or str(uuid.uuid4())

    stmt = select(DHConversation).where(DHConversation.session_id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        session = DHConversation(
            session_id=session_id,
            user_id=user_id,
            dh_id=dh_id,
        )
        db.add(session)
        await db.flush()

    # 保存用户消息
    user_msg = DHMessage(
        session_id=session_id,
        dh_id=dh_id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)
    await db.flush()

    # 获取历史消息
    stmt = select(DHMessage).where(
        DHMessage.session_id == session_id
    ).order_by(DHMessage.created_at.desc()).limit(20)
    result = await db.execute(stmt)
    history_messages = list(result.scalars().all())
    history_messages.reverse()

    messages = [{"role": msg.role, "content": msg.content} for msg in history_messages]
    messages.append({"role": "user", "content": body.message})

    # 获取LLM服务
    llm_router = get_llm_router()
    llm_service = llm_router.get_service()

    async def generate():
        """SSE生成器"""
        full_response = ""

        # 发送开始事件
        yield f"event: start\ndata: {json.dumps({'session_id': session_id, 'dh_id': dh_id})}\n\n"

        try:
            async for chunk in llm_service.chat_stream(
                messages=messages,
                system_prompt=dh.system_prompt or f"你是{dh.name}，一个友善的AI伙伴。",
                temperature=0.8,
                max_tokens=500,
            ):
                full_response += chunk
                yield f"event: delta\ndata: {json.dumps({'content': chunk})}\n\n"
        except Exception as e:
            error_msg = "抱歉，我现在有点恍惚...能再说一遍吗？"
            full_response = error_msg
            yield f"event: delta\ndata: {json.dumps({'content': error_msg})}\n\n"

        # 发送完成事件
        yield f"event: done\ndata: {json.dumps({'full_response': full_response})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/{dh_id}/history", response_model=APIResponse)
async def get_chat_history(
    dh_id: int,
    limit: int = Query(20, ge=1, le=100),
    session_id: Optional[str] = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取与数字人的对话历史"""
    # 验证数字人属于用户
    stmt = select(DigitalHuman).where(
        and_(
            DigitalHuman.id == dh_id,
            DigitalHuman.user_id == user_id
        )
    )
    result = await db.execute(stmt)
    dh = result.scalar_one_or_none()

    if not dh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital human not found"
        )

    # 查询消息
    if session_id:
        stmt = select(DHMessage).where(
            and_(
                DHMessage.dh_id == dh_id,
                DHMessage.session_id == session_id
            )
        ).order_by(DHMessage.created_at.desc()).limit(limit + 1)
    else:
        stmt = select(DHMessage).where(
            DHMessage.dh_id == dh_id
        ).order_by(DHMessage.created_at.desc()).limit(limit + 1)

    result = await db.execute(stmt)
    messages = list(result.scalars().all())

    has_more = len(messages) > limit
    messages = messages[:limit]
    messages.reverse()

    return APIResponse(
        code=0,
        message="success",
        data={
            "dh_id": dh_id,
            "messages": [msg.to_dict() for msg in messages],
            "has_more": has_more
        }
    )


@router.delete("/{dh_id}/history", response_model=APIResponse)
async def clear_chat_history(
    dh_id: int,
    session_id: Optional[str] = Query(None),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """清空与数字人的对话历史"""
    # 验证数字人属于用户
    stmt = select(DigitalHuman).where(
        and_(
            DigitalHuman.id == dh_id,
            DigitalHuman.user_id == user_id
        )
    )
    result = await db.execute(stmt)
    dh = result.scalar_one_or_none()

    if not dh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital human not found"
        )

    # 删除消息
    if session_id:
        stmt = select(DHMessage).where(
            and_(
                DHMessage.dh_id == dh_id,
                DHMessage.session_id == session_id
            )
        )
    else:
        stmt = select(DHMessage).where(DHMessage.dh_id == dh_id)

    result = await db.execute(stmt)
    messages = result.scalars().all()

    for msg in messages:
        await db.delete(msg)

    await db.commit()

    return APIResponse(
        code=0,
        message="Chat history cleared",
        data={"dh_id": dh_id, "deleted_count": len(list(messages))}
    )


# ===================== 辅助 API =====================

@router.get("/options/personalities", response_model=APIResponse)
async def get_personality_options():
    """获取所有可选性格"""
    personality_engine = get_personality_engine()
    return APIResponse(
        code=0,
        message="success",
        data={"items": personality_engine.get_all_personalities()}
    )


@router.get("/options/domains", response_model=APIResponse)
async def get_domain_options():
    """获取所有可选领域"""
    personality_engine = get_personality_engine()
    return APIResponse(
        code=0,
        message="success",
        data={"items": personality_engine.get_all_domains()}
    )
