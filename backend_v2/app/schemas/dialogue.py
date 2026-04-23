"""
MindPal Backend V2 - Pydantic Schemas for Dialogue
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== 请求模式 ====================

class EmotionData(BaseModel):
    """情感数据"""
    joy: float = Field(default=0.0, ge=0, le=1)
    sadness: float = Field(default=0.0, ge=0, le=1)
    anger: float = Field(default=0.0, ge=0, le=1)
    fear: float = Field(default=0.0, ge=0, le=1)
    surprise: float = Field(default=0.0, ge=0, le=1)
    neutral: float = Field(default=0.0, ge=0, le=1)


class ChatRequest(BaseModel):
    """对话请求"""
    npc_id: str = Field(..., description="NPC ID (bei, aela, momo, chronos, sesame)")
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    emotion_data: Optional[EmotionData] = None


class StreamChatRequest(BaseModel):
    """流式对话请求"""
    npc_id: str
    message: str
    session_id: Optional[str] = None


# ==================== 响应模式 ====================

class MessageResponse(BaseModel):
    """消息响应"""
    id: int
    role: str  # user / assistant
    content: str
    emotion: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True


class ChatResponse(BaseModel):
    """对话响应"""
    session_id: str
    npc_id: str
    response: str
    emotion: Optional[str] = None
    is_complete: bool
    affinity_change: Optional[int] = None
    current_affinity: Optional[int] = None


class ChatHistoryResponse(BaseModel):
    """对话历史响应"""
    npc_id: str
    messages: List[MessageResponse]
    has_more: bool


class AffinityItem(BaseModel):
    """单个NPC好感度"""
    level: int
    value: int
    title: str


class AllAffinityResponse(BaseModel):
    """所有NPC好感度响应"""
    aela: Optional[AffinityItem] = None
    momo: Optional[AffinityItem] = None
    chronos: Optional[AffinityItem] = None
    bei: Optional[AffinityItem] = None
    sesame: Optional[AffinityItem] = None


# ==================== SSE事件 ====================

class SSEStartEvent(BaseModel):
    """SSE开始事件"""
    session_id: str
    npc_id: str


class SSEDeltaEvent(BaseModel):
    """SSE增量内容事件"""
    content: str


class SSEDoneEvent(BaseModel):
    """SSE完成事件"""
    full_response: str
    affinity_change: Optional[int] = None
    emotion: Optional[str] = None


class SSEErrorEvent(BaseModel):
    """SSE错误事件"""
    error: str
