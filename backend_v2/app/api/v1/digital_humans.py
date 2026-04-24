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
from app.core.quota import QuotaGuard, DEFAULT_CHAT_TOKENS
from app.core.cache import (
    get_cache,
    llm_cache_key,
    should_skip_cache,
    fake_stream_from_cache,
)
from app.services.personality_engine import get_personality_engine
from app.services.llm import get_llm_router
from app.services.dialogue import get_enhanced_processor
from app.services.memory import get_memory_retriever
from app.services.moderation import get_moderator, SAFE_FALLBACK_REPLY

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
    guard = QuotaGuard(user_id, DEFAULT_CHAT_TOKENS)
    if not guard.check():
        raise guard.as_http_402()

    # === 内容审核：用户输入过滤（P3-2）===
    moderator = get_moderator()
    mod_input = await moderator.check(body.message, scene="user_input")
    if mod_input.blocked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CONTENT_BLOCKED",
                "category": mod_input.category.value,
                "reason": mod_input.reason,
                "user_message": mod_input.user_message,
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

    # 调用 LLM（P1-4: 加缓存层）
    llm_router = get_llm_router()
    llm_service = llm_router.get_service()

    # 构建完整 messages（历史 + 当前）
    messages = history_dicts + [{"role": "user", "content": body.message}]
    temperature = 0.5 if dialogue_context.is_crisis_mode else 0.8
    system_prompt = dialogue_context.enhanced_system_prompt or base_prompt

    cache = get_cache()
    skip_reason = should_skip_cache(
        is_crisis=dialogue_context.is_crisis_mode,
        temperature=temperature,
        message_text=body.message,
    )
    cache_key = None
    cached_text: Optional[str] = None
    if not skip_reason:
        cache_key = llm_cache_key(
            model=llm_service.get_model_name(),
            messages=messages,
            system_prompt=system_prompt,
            temperature=temperature,
        )
        try:
            cached_text = await cache.get(cache_key)
        except Exception:
            cached_text = None

    ai_response = cached_text
    cache_hit = bool(cached_text)
    if not cache_hit:
        try:
            ai_response = await llm_service.chat(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=500,
            )
        except Exception:
            ai_response = "抱歉，我现在有点恍惚...能再说一遍吗？"

        # 写入缓存（仅真实调用 + 无 skip 条件）
        if ai_response and cache_key and not skip_reason:
            try:
                await cache.set(cache_key, ai_response)
            except Exception:
                pass

    # === 内容审核：LLM 输出过滤（P3-2，非流式）===
    mod_output = await moderator.check(ai_response or "", scene="llm_output")
    output_blocked = mod_output.blocked
    if output_blocked:
        # 替换为安全兜底文案，不把违规内容写回前端或数据库
        ai_response = mod_output.user_message or SAFE_FALLBACK_REPLY

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

    # 配额检查 —— 流式场景用 SSE error 帧告知前端（而非 HTTP 402，因流已准备开启）
    guard = QuotaGuard(user_id, DEFAULT_CHAT_TOKENS)
    if not guard.check():
        err_payload = guard.as_sse_error_payload()
        async def quota_error_stream():
            yield f"event: error\ndata: {json.dumps(err_payload, ensure_ascii=False)}\n\n"
        return StreamingResponse(quota_error_stream(), media_type="text/event-stream")

    # === 内容审核：用户输入过滤（P3-2，流式）===
    moderator = get_moderator()
    mod_input = await moderator.check(body.message, scene="user_input")
    if mod_input.blocked:
        err_payload = {
            "error": "content_blocked",
            "code": "CONTENT_BLOCKED",
            "category": mod_input.category.value,
            "reason": mod_input.reason,
            "user_message": mod_input.user_message,
        }
        async def blocked_stream():
            yield f"event: error\ndata: {json.dumps(err_payload, ensure_ascii=False)}\n\n"
        return StreamingResponse(blocked_stream(), media_type="text/event-stream")

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

    # 响应缓存（P1-4）: 危机模式/高温/过短过长 skip
    cache = get_cache()
    skip_reason = should_skip_cache(
        is_crisis=dialogue_context.is_crisis_mode,
        temperature=temperature,
        message_text=body.message,
    )
    cache_key = None
    cached_text: Optional[str] = None
    if not skip_reason:
        cache_key = llm_cache_key(
            model=llm_service.get_model_name(),
            messages=chat_messages,
            system_prompt=system_prompt,
            temperature=temperature,
        )
        try:
            cached_text = await cache.get(cache_key)
        except Exception:
            cached_text = None  # 缓存故障降级为未命中

    # commit 当前用户消息+情感，避免流式过程中事务悬挂
    await db.commit()

    async def generate():
        full_response = ""
        cache_hit = bool(cached_text)

        # start 帧（带情感和危机状态 + 命中缓存标记）
        start_data = {
            "session_id": session_id,
            "dh_id": dh_id,
            "emotion": metadata["emotion"]["dominant"],
            "emotion_intensity": metadata["emotion"]["intensity"],
            "needs_comfort": metadata["emotion"]["needs_comfort"],
            "crisis_detected": metadata["crisis"]["detected"],
            "crisis_level": metadata["crisis"]["level"],
            "model": metadata["model"],
            "cache_hit": cache_hit,
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

        # delta 帧：缓存命中走 fake-stream，否则真实 LLM 流式
        try:
            if cache_hit and cached_text:
                # 从缓存回放（省一次真实 LLM 调用）
                full_response = cached_text
                async for chunk in fake_stream_from_cache(cached_text):
                    yield f"event: delta\ndata: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
            else:
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

        # === 内容审核：LLM 输出过滤（流式，在 done 帧前终审）===
        output_mod = await moderator.check(full_response or "", scene="llm_output")
        output_blocked = output_mod.blocked
        persisted_response = full_response
        if output_blocked:
            # 替换为安全文案，通过 SSE moderation 事件告知前端本次回复被替换
            persisted_response = output_mod.user_message or SAFE_FALLBACK_REPLY
            mod_payload = json.dumps({
                "category": output_mod.category.value,
                "replaced": True,
                "reason": output_mod.reason,
            }, ensure_ascii=False)
            yield f"event: moderation\ndata: {mod_payload}\n\n"
            # 告诉前端"上面显示的内容请作废，以这条安全文案为准"
            delta_payload = json.dumps({
                "content": "\n\n[系统提示] " + persisted_response,
                "replace_full_response": True,
            }, ensure_ascii=False)
            yield f"event: delta\ndata: {delta_payload}\n\n"
            full_response = persisted_response

        # 写入缓存（只在真实生成 + 无 skip + 未被 moderation 替换时写）
        if (not cache_hit and cache_key and full_response
                and not skip_reason and not output_blocked):
            try:
                await cache.set(cache_key, full_response)
            except Exception:
                pass  # 缓存写入失败不影响主链路

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


@router.get("/options/personalities/grouped", response_model=APIResponse)
async def get_personalities_grouped():
    """按大类分组的性格选项 (companion / romantic / ...)

    前端 create-dh-step2.html 按 tab 切换使用。
    返回格式:
      {
        "companion": [{key,name,description,avatar,sample_line,base_traits}, ...],
        "romantic":  [...]
      }
    """
    personality_engine = get_personality_engine()
    return APIResponse(
        code=0,
        message="success",
        data={"categories": personality_engine.get_personalities_by_category()}
    )


# ===================== 长期记忆可视化 API =====================
#
# 设计原则：
#  - 路径: /digital-humans/{dh_id}/memories/*
#  - 不依赖 Player 模型（与游戏 NPC 的 memory.py 解耦）
#  - 底层用 user_id + npc_key="dh_{dh_id}" 作为 vector_store 的过滤键
#  - 用户只能操作自己的数字人记忆（通过 DigitalHuman.user_id 验证）

async def _verify_dh_ownership(
    dh_id: int,
    user_id: int,
    db: AsyncSession
) -> DigitalHuman:
    """验证数字人属于当前用户，否则 404。"""
    stmt = select(DigitalHuman).where(
        and_(
            DigitalHuman.id == dh_id,
            DigitalHuman.user_id == user_id,
            DigitalHuman.is_active == True,
        )
    )
    result = await db.execute(stmt)
    dh = result.scalar_one_or_none()
    if not dh:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital human not found"
        )
    return dh


@router.get("/{dh_id}/memories", response_model=APIResponse)
async def list_dh_memories(
    dh_id: int,
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    emotion: Optional[str] = Query(None, description="按情感筛选 (joy/sadness/anger/fear/surprise/disgust/love/neutral)"),
    q: Optional[str] = Query(None, description="语义搜索关键词，若提供则走向量搜索而非时间线"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """列出数字人的长期记忆（时间线 / 按情感 / 语义搜索）

    优先级: q > emotion > 时间线全部
    """
    await _verify_dh_ownership(dh_id, user_id, db)
    retriever = get_memory_retriever()
    npc_key = _dh_context_key(dh_id)

    if q:
        # 语义搜索分支
        memories = await retriever.retrieve_relevant(
            player_id=user_id,
            npc_id=npc_key,
            query=q,
            limit=limit,
            score_threshold=0.0,
        )
        mode = "semantic"
    else:
        # 时间线列表（可按 emotion 过滤）
        memories = await retriever.list_memories(
            player_id=user_id,
            npc_id=npc_key,
            limit=limit,
            offset=offset,
            emotion=emotion,
            order_desc=True,
        )
        mode = "timeline"

    total = await retriever.get_memory_count(user_id, npc_key)

    items = []
    for mem in memories:
        md = mem.metadata or {}
        items.append({
            "id": mem.id,
            "summary": mem.summary,
            "emotion": mem.emotion,
            "importance": md.get("importance", 0.5),
            "relevance_score": round(mem.relevance_score, 3) if mode == "semantic" else None,
            "user_message": md.get("user_message"),
            "npc_response": md.get("npc_response"),
            "created_at": mem.created_at.isoformat() if mem.created_at else None,
            "session_id": md.get("session_id"),
        })

    return APIResponse(
        code=0,
        message="success",
        data={
            "dh_id": dh_id,
            "mode": mode,
            "total": total,
            "limit": limit,
            "offset": offset,
            "emotion_filter": emotion,
            "query": q,
            "items": items,
        }
    )


@router.get("/{dh_id}/memories/stats", response_model=APIResponse)
async def get_dh_memory_stats(
    dh_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """数字人记忆统计：总数 + 按情感分组"""
    await _verify_dh_ownership(dh_id, user_id, db)
    retriever = get_memory_retriever()
    npc_key = _dh_context_key(dh_id)

    total = await retriever.get_memory_count(user_id, npc_key)
    by_emotion = await retriever.count_memories_by_emotion(user_id, npc_key)

    return APIResponse(
        code=0,
        message="success",
        data={
            "dh_id": dh_id,
            "total": total,
            "by_emotion": by_emotion,
        }
    )


@router.delete("/{dh_id}/memories/{memory_id}", response_model=APIResponse)
async def delete_dh_memory(
    dh_id: int,
    memory_id: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """删除单条数字人记忆"""
    await _verify_dh_ownership(dh_id, user_id, db)
    retriever = get_memory_retriever()

    # 记忆 id 格式: mem_{player_id}_{npc_id}_{hex8}，验证归属
    expected_prefix = f"mem_{user_id}_{_dh_context_key(dh_id)}_"
    if not memory_id.startswith(expected_prefix):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete memory that does not belong to this digital human"
        )

    success = await retriever.delete_memory(memory_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Memory not found"
        )

    return APIResponse(
        code=0,
        message="success",
        data={"deleted": True, "memory_id": memory_id}
    )


@router.delete("/{dh_id}/memories", response_model=APIResponse)
async def clear_dh_memories(
    dh_id: int,
    confirm: bool = Query(False, description="必须传 true 才实际删除"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    """清空数字人的所有长期记忆（不可恢复，需二次确认）"""
    await _verify_dh_ownership(dh_id, user_id, db)

    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please pass ?confirm=true to actually delete all memories"
        )

    retriever = get_memory_retriever()
    npc_key = _dh_context_key(dh_id)
    deleted = await retriever.delete_all_memories(user_id, npc_key)

    return APIResponse(
        code=0,
        message="success",
        data={"deleted": deleted, "dh_id": dh_id}
    )
