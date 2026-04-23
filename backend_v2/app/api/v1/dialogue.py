"""
MindPal Backend V2 - Dialogue API Routes
集成Phase 3A增强功能：情感分析、危机干预、记忆检索
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import uuid
import json

from app.database import get_db
from app.models import Player, NPCAffinity, DialogueSession, DialogueMessage
from app.schemas import ChatRequest, APIResponse
from app.core.security import get_current_user_id
from app.services.llm import get_llm_router
from app.services.npc import get_npc_manager

# Phase 3A 增强服务
from app.services.dialogue import get_enhanced_processor
from app.services.emotion import get_emotion_analyzer
from app.services.crisis import get_crisis_detector
from app.services.ai import get_cost_tracker

router = APIRouter()


@router.post("/chat", response_model=APIResponse)
async def chat(
    request: ChatRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    与NPC对话 (非流式) - 集成情感分析、危机干预、记忆检索

    - **npc_id**: NPC ID (bei, aela, momo, chronos, sesame)
    - **message**: 用户消息
    - **session_id**: 会话ID (可选，用于保持会话)
    """
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 验证NPC ID
    valid_npcs = ["bei", "aela", "momo", "chronos", "sesame"]
    if request.npc_id not in valid_npcs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid NPC ID. Must be one of: {valid_npcs}"
        )

    # 检查配额
    cost_tracker = get_cost_tracker()
    quota_check = cost_tracker.check_quota(player.id, estimated_tokens=1000)
    if not quota_check["allowed"]:
        return APIResponse(
            code=429,
            message=f"Daily quota exceeded: {quota_check['reason']}",
            data={
                "remaining_tokens": quota_check["remaining_tokens"],
                "remaining_cost": quota_check["remaining_cost"]
            }
        )

    # 获取或创建会话
    session_id = request.session_id or str(uuid.uuid4())

    stmt = select(DialogueSession).where(DialogueSession.session_id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        session = DialogueSession(
            session_id=session_id,
            player_id=player.id,
            npc_id=request.npc_id,
        )
        db.add(session)
        await db.flush()

    # 保存用户消息
    user_message = DialogueMessage(
        session_id=session_id,
        role="user",
        content=request.message,
    )
    db.add(user_message)

    # 获取好感度
    stmt = select(NPCAffinity).where(
        NPCAffinity.player_id == player.id,
        NPCAffinity.npc_id == request.npc_id
    )
    result = await db.execute(stmt)
    affinity = result.scalar_one_or_none()

    # 获取历史消息（最近10轮）
    stmt = select(DialogueMessage).where(
        DialogueMessage.session_id == session_id
    ).order_by(DialogueMessage.created_at.desc()).limit(20)
    result = await db.execute(stmt)
    history_messages = result.scalars().all()
    history_messages = list(history_messages)
    history_messages.reverse()

    # 构建消息列表
    messages = []
    for msg in history_messages:
        messages.append({
            "role": msg.role,
            "content": msg.content
        })

    # 获取NPC人设和LLM服务
    npc_manager = get_npc_manager()
    llm_router = get_llm_router()

    # 构建基础System Prompt
    base_system_prompt = npc_manager.build_prompt_for_npc(
        npc_id=request.npc_id,
        affinity_value=affinity.value if affinity else 0,
        player_name=player.nickname,
    )

    # Phase 3A: 使用增强对话处理器
    enhanced_processor = get_enhanced_processor(db)
    dialogue_context = await enhanced_processor.process_message(
        player_id=player.id,
        npc_id=request.npc_id,
        session_id=session_id,
        message=request.message,
        player_name=player.nickname,
        affinity_value=affinity.value if affinity else 0,
        base_system_prompt=base_system_prompt,
        history_messages=messages
    )

    # 检查并处理危机情况
    crisis_response = None
    if dialogue_context.is_crisis_mode:
        crisis_response = await enhanced_processor.handle_crisis_if_needed(dialogue_context)

    # 准备LLM消息
    messages.append({
        "role": "user",
        "content": request.message
    })

    # 获取适合该NPC的LLM服务
    llm_service = llm_router.get_service_for_npc(request.npc_id)

    # 调用LLM生成回复（使用增强的系统提示）
    try:
        ai_response = await llm_service.chat(
            messages=messages,
            system_prompt=dialogue_context.enhanced_system_prompt,
            temperature=0.8 if not dialogue_context.is_crisis_mode else 0.5,
            max_tokens=500,
        )
    except Exception as e:
        ai_response = f"抱歉，我现在有点恍惚...能再说一遍吗？（系统提示：{str(e)[:50]}）"

    # 使用Phase 3A情感分析结果
    emotion = dialogue_context.emotion_result.dominant.value if dialogue_context.emotion_result else "neutral"

    # 保存AI回复
    ai_msg = DialogueMessage(
        session_id=session_id,
        role="assistant",
        content=ai_response,
        emotion=emotion,
        llm_model=dialogue_context.selected_model,
    )
    db.add(ai_msg)

    # 存储对话记忆
    await enhanced_processor.store_conversation_memory(dialogue_context, ai_response)

    # 记录使用量（估算token）
    input_tokens = len(request.message) * 2 + len(dialogue_context.enhanced_system_prompt)
    output_tokens = len(ai_response) * 2
    usage = enhanced_processor.record_usage(dialogue_context, input_tokens, output_tokens)

    # 更新会话统计
    session.message_count += 2
    session.last_message_at = datetime.utcnow()

    # 根据情感计算好感度变化
    affinity_change = 1
    if dialogue_context.emotion_result:
        if dialogue_context.emotion_result.is_positive:
            affinity_change = 2
        elif dialogue_context.emotion_result.needs_comfort:
            affinity_change = 1  # 情感支持也增加好感度

    if affinity:
        affinity.value = min(100, affinity.value + affinity_change)
        affinity.dialogue_count += 1
        affinity.last_interaction = datetime.utcnow()

    # 更新玩家统计
    player.dialogues_count += 1

    # 获取响应元数据
    metadata = enhanced_processor.get_response_metadata(dialogue_context)

    return APIResponse(
        code=0,
        message="success",
        data={
            "session_id": session_id,
            "npc_id": request.npc_id,
            "response": ai_response,
            "emotion": emotion,
            "is_complete": True,
            "affinity_change": affinity_change,
            "current_affinity": affinity.value if affinity else 0,
            # Phase 3A 增强数据
            "emotion_analysis": metadata["emotion"],
            "crisis_detected": metadata["crisis"]["detected"],
            "model_used": metadata["model"],
            "memories_referenced": metadata["memories_used"],
            "crisis_resources": crisis_response.get("resources") if crisis_response else None
        }
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    与NPC对话 (流式SSE) - 集成情感分析、危机干预、记忆检索

    返回Server-Sent Events流，实时输出AI回复
    """
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 验证NPC ID
    valid_npcs = ["bei", "aela", "momo", "chronos", "sesame"]
    if request.npc_id not in valid_npcs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid NPC ID. Must be one of: {valid_npcs}"
        )

    # 检查配额
    cost_tracker = get_cost_tracker()
    quota_check = cost_tracker.check_quota(player.id, estimated_tokens=1000)
    if not quota_check["allowed"]:
        # 返回配额超限的SSE事件
        async def quota_exceeded_generator():
            yield f"event: error\ndata: {json.dumps({'error': 'quota_exceeded', 'reason': quota_check['reason']})}\n\n"
        return StreamingResponse(
            quota_exceeded_generator(),
            media_type="text/event-stream"
        )

    session_id = request.session_id or str(uuid.uuid4())

    # 获取或创建会话
    stmt = select(DialogueSession).where(DialogueSession.session_id == session_id)
    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        session = DialogueSession(
            session_id=session_id,
            player_id=player.id,
            npc_id=request.npc_id,
        )
        db.add(session)
        await db.flush()

    # 保存用户消息
    user_message = DialogueMessage(
        session_id=session_id,
        role="user",
        content=request.message,
    )
    db.add(user_message)
    await db.flush()

    # 获取好感度
    stmt = select(NPCAffinity).where(
        NPCAffinity.player_id == player.id,
        NPCAffinity.npc_id == request.npc_id
    )
    result = await db.execute(stmt)
    affinity = result.scalar_one_or_none()

    # 获取历史消息（最近10轮）
    stmt = select(DialogueMessage).where(
        DialogueMessage.session_id == session_id
    ).order_by(DialogueMessage.created_at.desc()).limit(20)
    result = await db.execute(stmt)
    history_messages = result.scalars().all()
    history_messages = list(history_messages)
    history_messages.reverse()

    # 构建消息列表
    messages = []
    for msg in history_messages:
        messages.append({
            "role": msg.role,
            "content": msg.content
        })

    # 获取NPC人设和LLM服务
    npc_manager = get_npc_manager()
    llm_router = get_llm_router()

    # 构建基础System Prompt
    base_system_prompt = npc_manager.build_prompt_for_npc(
        npc_id=request.npc_id,
        affinity_value=affinity.value if affinity else 0,
        player_name=player.nickname,
    )

    # Phase 3A: 使用增强对话处理器
    enhanced_processor = get_enhanced_processor(db)
    dialogue_context = await enhanced_processor.process_message(
        player_id=player.id,
        npc_id=request.npc_id,
        session_id=session_id,
        message=request.message,
        player_name=player.nickname,
        affinity_value=affinity.value if affinity else 0,
        base_system_prompt=base_system_prompt,
        history_messages=messages
    )

    # 检查并处理危机情况
    crisis_response = None
    if dialogue_context.is_crisis_mode:
        crisis_response = await enhanced_processor.handle_crisis_if_needed(dialogue_context)

    # 获取适合该NPC的LLM服务
    llm_service = llm_router.get_service_for_npc(request.npc_id)

    # 保存上下文以便在生成器中使用
    context = {
        "session_id": session_id,
        "npc_id": request.npc_id,
        "player_id": player.id,
        "affinity": affinity,
        "session": session,
        "player": player,
        "dialogue_context": dialogue_context,
        "crisis_response": crisis_response,
        "enhanced_processor": enhanced_processor
    }

    # 获取响应元数据
    metadata = enhanced_processor.get_response_metadata(dialogue_context)

    async def generate():
        """SSE生成器 - 真正的流式LLM响应（集成Phase 3A）"""
        full_response = ""

        # 发送开始事件（包含情感和危机信息）
        start_data = {
            'session_id': context['session_id'],
            'npc_id': context['npc_id'],
            'emotion': metadata['emotion'],
            'crisis_detected': metadata['crisis']['detected'],
            'model': metadata['model']
        }
        yield f"event: start\ndata: {json.dumps(start_data)}\n\n"

        # 如果检测到危机，先发送危机信息
        if context['crisis_response']:
            yield f"event: crisis\ndata: {json.dumps({'resources': context['crisis_response'].get('resources', [])})}\n\n"

        try:
            # 调用LLM流式接口（使用增强的系统提示）
            async for chunk in llm_service.chat_stream(
                messages=messages + [{"role": "user", "content": request.message}],
                system_prompt=context['dialogue_context'].enhanced_system_prompt,
                temperature=0.8 if not context['dialogue_context'].is_crisis_mode else 0.5,
                max_tokens=500,
            ):
                full_response += chunk
                # 发送增量内容
                yield f"event: delta\ndata: {json.dumps({'content': chunk})}\n\n"

        except Exception as e:
            error_msg = f"抱歉，我现在有点恍惚...能再说一遍吗？"
            full_response = error_msg
            yield f"event: delta\ndata: {json.dumps({'content': error_msg})}\n\n"

        # 使用Phase 3A情感结果计算好感度变化
        affinity_change = 1
        if context['dialogue_context'].emotion_result:
            if context['dialogue_context'].emotion_result.is_positive:
                affinity_change = 2
            elif context['dialogue_context'].emotion_result.needs_comfort:
                affinity_change = 1

        current_affinity = context['affinity'].value if context['affinity'] else 0

        # 发送完成事件（包含完整的Phase 3A元数据）
        done_data = {
            'full_response': full_response,
            'affinity_change': affinity_change,
            'current_affinity': current_affinity,
            'emotion': metadata['emotion']['dominant'],
            'emotion_intensity': metadata['emotion']['intensity'],
            'crisis_detected': metadata['crisis']['detected'],
            'memories_used': metadata['memories_used'],
            'model_used': metadata['model']
        }
        yield f"event: done\ndata: {json.dumps(done_data)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/history", response_model=APIResponse)
async def get_history(
    npc_id: str,
    limit: int = 20,
    before: str = None,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取对话历史

    - **npc_id**: NPC ID
    - **limit**: 返回消息数量
    - **before**: 获取此消息ID之前的消息
    """
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 获取该NPC的所有会话
    stmt = select(DialogueSession.session_id).where(
        DialogueSession.player_id == player.id,
        DialogueSession.npc_id == npc_id
    )
    result = await db.execute(stmt)
    session_ids = [row[0] for row in result.fetchall()]

    if not session_ids:
        return APIResponse(
            code=0,
            message="success",
            data={
                "npc_id": npc_id,
                "messages": [],
                "has_more": False
            }
        )

    # 获取消息
    stmt = select(DialogueMessage).where(
        DialogueMessage.session_id.in_(session_ids)
    ).order_by(DialogueMessage.created_at.desc()).limit(limit + 1)

    result = await db.execute(stmt)
    messages = result.scalars().all()

    has_more = len(messages) > limit
    messages = messages[:limit]
    messages.reverse()  # 按时间正序

    return APIResponse(
        code=0,
        message="success",
        data={
            "npc_id": npc_id,
            "messages": [msg.to_dict() for msg in messages],
            "has_more": has_more
        }
    )


@router.get("/affinity", response_model=APIResponse)
async def get_affinity(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取所有NPC好感度"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 获取所有好感度
    stmt = select(NPCAffinity).where(NPCAffinity.player_id == player.id)
    result = await db.execute(stmt)
    affinities = result.scalars().all()

    affinity_data = {}
    for aff in affinities:
        affinity_data[aff.npc_id] = {
            "level": aff.get_level(),
            "value": aff.value,
            "title": aff.get_title(),
        }

    return APIResponse(
        code=0,
        message="success",
        data=affinity_data
    )
