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
from app.services.dialogue import get_enhanced_processor

router = APIRouter()


def _dh_context_key(dh_id: int) -> str:
    """将 DigitalHuman ID 映射成 enhanced_processor 所需的 npc_id 形式。

    enhanced_processor 的 memory / crisis / emotion 链路对 npc_id 只做 key 用途，
    不查 NPC 表。用 "dh_{id}" 前缀避免与游戏 NPC 撞 key。
    """
    return f"dh_{dh_id}"


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

    集成完整 pipeline:
      1. 配额检查（cost_tracker）
      2. 情感分析 + 危机检测（emotion_analyzer + crisis_detector）
      3. 长期记忆检索（memory_retriever）
      4. 危机模式降温 + 安全 system prompt
      5. LLM 调用
      6. 记忆写入 + 情感保存到 DHMessage.emotion
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

    # 获取用户昵称
    user_stmt = select(User).where(User.id == user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    player_name = (user.username if user else None) or "朋友"

    # 初始化 pipeline 处理器
    processor = get_enhanced_processor(db)
    npc_key = _dh_context_key(dh_id)

    # 配额检查（超限直接 402）
    quota = processor.check_quota(user_id, estimated_tokens=1000)
    if not quota["allowed"]:
        raise HTTPException(
            status_code=402,
            detail={
                "code": "QUOTA_EXCEEDED",
                "reason": quota.get("reason", "daily quota exceeded"),
                "remaining_tokens": quota.get("remaining_tokens"),
                "remaining_cost": quota.get("remaining_cost"),
                "upgrade_url": "/pricing.html"
            }
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

    # 保存用户消息（先占位，情感稍后回填）
    user_msg = DHMessage(
        session_id=session_id,
        dh_id=dh_id,
        role="user",
        content=body.message,
    )
    db.add(user_msg)
    await db.flush()

    # 获取历史消息（最近10轮）
    stmt = select(DHMessage).where(
        DHMessage.session_id == session_id
    ).order_by(DHMessage.created_at.desc()).limit(20)
    result = await db.execute(stmt)
    history_messages = list(result.scalars().all())
    history_messages.reverse()

    # 构建 history dicts 供 processor 用
    history_dicts = [
        {"role": msg.role, "content": msg.content}
        for msg in history_messages
        if msg.id != user_msg.id  # 不把当前消息重复加入历史
    ]

    # process_message: 情感分析 + 危机检测 + 记忆检索 + 构建增强 prompt
    base_prompt = dh.system_prompt or f"你是{dh.name}，一个友善的 AI 伙伴。"
    dialogue_context = await processor.process_message(
        player_id=user_id,
        npc_id=npc_key,
        session_id=session_id,
        message=body.message,
        player_name=player_name,
        affinity_value=0,
        base_system_prompt=base_prompt,
        history_messages=history_dicts,
    )

    # 危机处理
    crisis_response = None
    if dialogue_context.is_crisis_mode:
        crisis_response = await processor.handle_crisis_if_needed(dialogue_context)

    # 回填用户消息的情感
    if dialogue_context.emotion_result:
        user_msg.emotion = dialogue_context.emotion_result.dominant.value
        user_msg.emotion_scores = {
            "intensity": round(dialogue_context.emotion_result.intensity, 3),
            "is_positive": dialogue_context.emotion_result.is_positive,
            "needs_comfort": dialogue_context.emotion_result.needs_comfort,
        }

    # 调用 LLM
    llm_router = get_llm_router()
    llm_service = llm_router.get_service()

    # 构建完整 messages（历史 + 当前）
    messages = history_dicts + [{"role": "user", "content": body.message}]

    try:
        ai_response = await llm_service.chat(
            messages=messages,
            system_prompt=dialogue_context.enhanced_system_prompt or base_prompt,
            temperature=0.5 if dialogue_context.is_crisis_mode else 0.8,
            max_tokens=500,
        )
    except Exception:
        ai_response = "抱歉，我现在有点恍惚...能再说一遍吗？"

    # 保存 AI 回复（含情感标记）
    ai_msg = DHMessage(
        session_id=session_id,
        dh_id=dh_id,
        role="assistant",
        content=ai_response,
        emotion=dialogue_context.emotion_result.dominant.value if dialogue_context.emotion_result else None,
        llm_model=llm_service.get_model_name(),
    )
    db.add(ai_msg)

    # 存入长期记忆（跨 session）
    await processor.store_conversation_memory(dialogue_context, ai_response)

    # 更新统计
    session.message_count += 2
    session.last_message_at = datetime.utcnow()
    dh.total_messages += 2
    dh.total_conversations = dh.total_conversations or 0
    if not body.session_id:
        dh.total_conversations += 1
    dh.last_conversation_at = datetime.utcnow()

    # 记录成本（估算）
    processor.record_usage(
        dialogue_context,
        input_tokens=sum(len(m["content"]) for m in messages) // 3,
        output_tokens=len(ai_response) // 3,
    )

    await db.commit()

    # 返回结构化元数据
    metadata = processor.get_response_metadata(dialogue_context)
    return APIResponse(
        code=0,
        message="success",
        data={
            "session_id": session_id,
            "dh_id": dh_id,
            "response": ai_response,
            "is_complete": True,
            "emotion": metadata["emotion"],
            "crisis": metadata["crisis"],
            "crisis_resources": crisis_response.get("resources") if crisis_response else None,
            "memories_used": metadata["memories_used"],
            "model_used": metadata["model"],
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
    与数字人对话（流式 SSE）—— 接入完整 pipeline

    SSE 事件序列:
      event: start    data: {session_id, dh_id, emotion, crisis_detected, model}
      event: crisis   data: {resources, level}    [仅危机模式]
      event: delta    data: {content}             [多次，每个 chunk 一帧]
      event: done     data: {full_response, emotion, emotion_intensity,
                             crisis_detected, memories_used, model_used}
      event: error    data: {error, reason}       [quota 超限等]

    返回 Server-Sent Events 流。
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

    # 获取用户昵称
    user_stmt = select(User).where(User.id == user_id)
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    player_name = (user.username if user else None) or "朋友"

    # 初始化处理器
    processor = get_enhanced_processor(db)
    npc_key = _dh_context_key(dh_id)

    # 配额检查 —— 返回 SSE error 帧而不是 HTTP 402，因为前端已连上流
    quota = processor.check_quota(user_id, estimated_tokens=1000)
    if not quota["allowed"]:
        async def quota_error_stream():
            err = {
                "error": "quota_exceeded",
                "reason": quota.get("reason", "daily quota exceeded"),
                "remaining_tokens": quota.get("remaining_tokens"),
                "remaining_cost": quota.get("remaining_cost"),
                "upgrade_url": "/pricing.html",
            }
            yield f"event: error\ndata: {json.dumps(err, ensure_ascii=False)}\n\n"
        return StreamingResponse(quota_error_stream(), media_type="text/event-stream")

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
    history_rows = list(result.scalars().all())
    history_rows.reverse()
    history_dicts = [
        {"role": r.role, "content": r.content}
        for r in history_rows
        if r.id != user_msg.id
    ]

    # 预处理：情感/危机/记忆
    base_prompt = dh.system_prompt or f"你是{dh.name}，一个友善的 AI 伙伴。"
    dialogue_context = await processor.process_message(
        player_id=user_id,
        npc_id=npc_key,
        session_id=session_id,
        message=body.message,
        player_name=player_name,
        affinity_value=0,
        base_system_prompt=base_prompt,
        history_messages=history_dicts,
    )

    crisis_response = None
    if dialogue_context.is_crisis_mode:
        crisis_response = await processor.handle_crisis_if_needed(dialogue_context)

    # 回填用户消息情感到 DHMessage
    if dialogue_context.emotion_result:
        user_msg.emotion = dialogue_context.emotion_result.dominant.value
        user_msg.emotion_scores = {
            "intensity": round(dialogue_context.emotion_result.intensity, 3),
            "is_positive": dialogue_context.emotion_result.is_positive,
            "needs_comfort": dialogue_context.emotion_result.needs_comfort,
        }

    metadata = processor.get_response_metadata(dialogue_context)

    # 准备 LLM 调用参数（跳出生成器前全部准备好，避免闭包中 db session 的复杂性）
    llm_router = get_llm_router()
    llm_service = llm_router.get_service()
    chat_messages = history_dicts + [{"role": "user", "content": body.message}]
    system_prompt = dialogue_context.enhanced_system_prompt or base_prompt
    temperature = 0.5 if dialogue_context.is_crisis_mode else 0.8

    # commit 当前用户消息+情感，避免流式过程中事务悬挂
    await db.commit()

    async def generate():
        full_response = ""

        # start 帧（带情感和危机状态）
        start_data = {
            "session_id": session_id,
            "dh_id": dh_id,
            "emotion": metadata["emotion"]["dominant"],
            "emotion_intensity": metadata["emotion"]["intensity"],
            "needs_comfort": metadata["emotion"]["needs_comfort"],
            "crisis_detected": metadata["crisis"]["detected"],
            "crisis_level": metadata["crisis"]["level"],
            "model": metadata["model"],
        }
        yield f"event: start\ndata: {json.dumps(start_data, ensure_ascii=False)}\n\n"

        # crisis 帧（仅危机模式，在 delta 之前）
        if crisis_response:
            crisis_data = {
                "level": metadata["crisis"]["level"],
                "resources": crisis_response.get("resources", []),
                "intervention_needed": metadata["crisis"]["intervention_needed"],
            }
            yield f"event: crisis\ndata: {json.dumps(crisis_data, ensure_ascii=False)}\n\n"

        # delta 帧（LLM 流式输出）
        try:
            async for chunk in llm_service.chat_stream(
                messages=chat_messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=500,
            ):
                full_response += chunk
                yield f"event: delta\ndata: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        except Exception:
            fallback = "抱歉，我现在有点恍惚...能再说一遍吗？"
            full_response = fallback
            yield f"event: delta\ndata: {json.dumps({'content': fallback}, ensure_ascii=False)}\n\n"

        # done 帧前：保存 AI 消息 + 记忆 + 统计 + 用量
        try:
            ai_msg = DHMessage(
                session_id=session_id,
                dh_id=dh_id,
                role="assistant",
                content=full_response,
                emotion=metadata["emotion"]["dominant"] if metadata["emotion"]["dominant"] != "neutral" else None,
                llm_model=llm_service.get_model_name(),
            )
            db.add(ai_msg)

            session.message_count += 2
            session.last_message_at = datetime.utcnow()
            dh.total_messages += 2
            dh.total_conversations = dh.total_conversations or 0
            if not body.session_id:
                dh.total_conversations += 1
            dh.last_conversation_at = datetime.utcnow()

            await processor.store_conversation_memory(dialogue_context, full_response)

            processor.record_usage(
                dialogue_context,
                input_tokens=sum(len(m["content"]) for m in chat_messages) // 3,
                output_tokens=len(full_response) // 3,
            )

            await db.commit()
        except Exception:
            # 持久化失败不影响已发给用户的回复
            pass

        # done 帧
        done_data = {
            "full_response": full_response,
            "session_id": session_id,
            "emotion": metadata["emotion"]["dominant"],
            "emotion_intensity": metadata["emotion"]["intensity"],
            "crisis_detected": metadata["crisis"]["detected"],
            "crisis_level": metadata["crisis"]["level"],
            "memories_used": metadata["memories_used"],
            "model_used": metadata["model"],
        }
        yield f"event: done\ndata: {json.dumps(done_data, ensure_ascii=False)}\n\n"

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
