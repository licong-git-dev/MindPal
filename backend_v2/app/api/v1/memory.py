"""
MindPal Backend V2 - Memory API
记忆管理API端点
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from datetime import datetime

from app.database import get_db
from app.models.player import Player
from app.core.security import get_current_user_id
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.memory import MemoryRetriever, get_memory_retriever
from app.services.memory.manager import ConversationMemory


router = APIRouter()


# ==================== Helper ====================

async def get_player_from_user_id(user_id: int, db: AsyncSession) -> Player:
    """从user_id获取Player"""
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    return player


# ==================== Schemas ====================

class MemorySearchRequest(BaseModel):
    """记忆搜索请求"""
    npc_id: str = Field(..., description="NPC ID")
    query: str = Field(..., min_length=1, max_length=500, description="搜索查询")
    limit: int = Field(5, ge=1, le=20, description="返回数量限制")


class MemoryItem(BaseModel):
    """记忆项"""
    id: str
    summary: str
    relevance_score: float
    emotion: Optional[str]
    created_at: datetime


class MemorySearchResponse(BaseModel):
    """记忆搜索响应"""
    memories: List[MemoryItem]
    total: int
    query: str


class ContextBuildRequest(BaseModel):
    """构建上下文请求"""
    npc_id: str
    current_message: str = Field(..., min_length=1, max_length=2000)
    max_memories: int = Field(5, ge=1, le=10)


class ContextResponse(BaseModel):
    """上下文响应"""
    context_prompt: str
    recent_messages_count: int
    relevant_memories_count: int
    player_profile: dict


class StoreMemoryRequest(BaseModel):
    """存储记忆请求"""
    npc_id: str
    user_message: str = Field(..., min_length=1, max_length=2000)
    npc_response: str = Field(..., min_length=1, max_length=4000)
    emotion: Optional[str] = None
    importance: float = Field(0.5, ge=0, le=1)


class StoreMemoryResponse(BaseModel):
    """存储记忆响应"""
    memory_id: str
    stored: bool


# ==================== Endpoints ====================

@router.post("/search", response_model=MemorySearchResponse)
async def search_memories(
    request: MemorySearchRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    搜索相关记忆

    根据查询文本语义搜索与特定NPC的历史对话记忆
    """
    player = await get_player_from_user_id(user_id, db)
    retriever = get_memory_retriever()

    memories = await retriever.retrieve_relevant(
        player_id=player.id,
        npc_id=request.npc_id,
        query=request.query,
        limit=request.limit
    )

    return MemorySearchResponse(
        memories=[
            MemoryItem(
                id=mem.id,
                summary=mem.summary,
                relevance_score=mem.relevance_score,
                emotion=mem.emotion,
                created_at=mem.created_at
            )
            for mem in memories
        ],
        total=len(memories),
        query=request.query
    )


@router.get("/recent/{npc_id}")
async def get_recent_memories(
    npc_id: str,
    limit: int = Query(10, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取最近的记忆

    返回与特定NPC的最近对话记忆
    """
    player = await get_player_from_user_id(user_id, db)
    retriever = get_memory_retriever()

    memories = await retriever.retrieve_recent(
        player_id=player.id,
        npc_id=npc_id,
        limit=limit
    )

    return {
        "code": 0,
        "message": "success",
        "data": {
            "memories": [
                {
                    "id": mem.id,
                    "summary": mem.summary,
                    "emotion": mem.emotion,
                    "created_at": mem.created_at.isoformat()
                }
                for mem in memories
            ],
            "total": len(memories)
        }
    }


@router.post("/context")
async def build_context(
    request: ContextBuildRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    构建对话上下文

    为当前对话构建完整的上下文，包括最近消息、相关记忆和玩家档案
    """
    player = await get_player_from_user_id(user_id, db)
    memory_manager = ConversationMemory(db)

    # 构建完整上下文
    context = await memory_manager.build_full_context(
        player_id=player.id,
        npc_id=request.npc_id,
        current_message=request.current_message
    )

    # 构建prompt文本
    context_prompt = await memory_manager.build_context_prompt(
        player_id=player.id,
        npc_id=request.npc_id,
        current_message=request.current_message
    )

    return {
        "code": 0,
        "message": "success",
        "data": {
            "context_prompt": context_prompt,
            "recent_messages_count": len(context.get("recent_messages", [])),
            "relevant_memories_count": len(context.get("relevant_memories", [])),
            "player_profile": context.get("player_profile", {})
        }
    }


@router.post("/store")
async def store_memory(
    request: StoreMemoryRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    存储新记忆

    将对话存储到向量数据库中
    """
    player = await get_player_from_user_id(user_id, db)
    retriever = get_memory_retriever()

    memory_id = await retriever.store_memory(
        player_id=player.id,
        npc_id=request.npc_id,
        user_message=request.user_message,
        npc_response=request.npc_response,
        emotion=request.emotion,
        importance=request.importance
    )

    return {
        "code": 0,
        "message": "success",
        "data": {
            "memory_id": memory_id,
            "stored": True
        }
    }


@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    删除记忆

    从向量数据库中删除特定记忆
    """
    player = await get_player_from_user_id(user_id, db)
    retriever = get_memory_retriever()

    # 验证记忆属于当前玩家（通过ID前缀）
    if not memory_id.startswith(f"mem_{player.id}_"):
        raise HTTPException(status_code=403, detail="Cannot delete other player's memory")

    success = await retriever.delete_memory(memory_id)

    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")

    return {
        "code": 0,
        "message": "success",
        "data": {
            "deleted": True
        }
    }


@router.get("/stats/{npc_id}")
async def get_memory_stats(
    npc_id: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取记忆统计

    返回与特定NPC的记忆统计信息
    """
    player = await get_player_from_user_id(user_id, db)
    retriever = get_memory_retriever()
    memory_manager = ConversationMemory(db)

    # 获取记忆数量
    memory_count = await retriever.get_memory_count(player.id, npc_id)

    # 获取玩家档案
    profile = await memory_manager.get_player_profile(player.id)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "npc_id": npc_id,
            "total_memories": memory_count,
            "player_interests": profile.interests,
            "recent_topics": profile.recent_topics,
            "recent_emotions": [e["emotion"] for e in profile.emotion_history[-5:]]
        }
    }


@router.get("/profile")
async def get_player_profile(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取玩家档案

    返回系统分析的玩家档案信息
    """
    player = await get_player_from_user_id(user_id, db)
    memory_manager = ConversationMemory(db)
    profile = await memory_manager.get_player_profile(player.id)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "player_id": profile.player_id,
            "nickname": profile.nickname,
            "communication_style": profile.communication_style,
            "interests": profile.interests,
            "recent_topics": profile.recent_topics,
            "emotion_history": profile.emotion_history[-20:],
            "preferences": profile.preferences
        }
    }
