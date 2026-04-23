"""
MindPal Backend V2 - Digital Human Schemas
数字人相关的Pydantic数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


class PersonalityTraits(BaseModel):
    """性格特质"""
    liveliness: int = Field(default=50, ge=0, le=100, description="活泼度")
    humor: int = Field(default=50, ge=0, le=100, description="幽默感")
    empathy: int = Field(default=50, ge=0, le=100, description="同理心")
    initiative: int = Field(default=50, ge=0, le=100, description="主动性")
    creativity: int = Field(default=50, ge=0, le=100, description="创造力")


class DigitalHumanCreate(BaseModel):
    """创建数字人请求"""
    name: str = Field(..., min_length=1, max_length=50, description="数字人名字")
    avatar_type: str = Field(default="default", description="形象类型")
    personality: str = Field(default="gentle", description="性格类型")
    personality_traits: Optional[PersonalityTraits] = Field(default=None, description="性格特质")
    custom_personality: Optional[str] = Field(default=None, max_length=500, description="自定义性格描述")
    role_type: str = Field(default="companion", description="角色类型: companion/teacher")
    voice_id: str = Field(default="xiaoya", description="声音ID")
    voice_speed: float = Field(default=1.0, ge=0.5, le=2.0, description="语速")
    domains: Optional[List[str]] = Field(default=None, description="擅长领域")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "小雅",
                "avatar_type": "female_young",
                "personality": "gentle",
                "personality_traits": {
                    "liveliness": 40,
                    "humor": 30,
                    "empathy": 90,
                    "initiative": 50,
                    "creativity": 40
                },
                "role_type": "companion",
                "voice_id": "xiaoya",
                "domains": ["情感陪伴", "生活建议"]
            }
        }


class DigitalHumanUpdate(BaseModel):
    """更新数字人请求"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    avatar_type: Optional[str] = None
    personality: Optional[str] = None
    personality_traits: Optional[PersonalityTraits] = None
    custom_personality: Optional[str] = Field(default=None, max_length=500)
    role_type: Optional[str] = None
    voice_id: Optional[str] = None
    voice_speed: Optional[float] = Field(default=None, ge=0.5, le=2.0)
    domains: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class DigitalHumanResponse(BaseModel):
    """数字人响应"""
    id: int
    name: str
    avatar_type: str
    avatar_url: Optional[str]
    personality: str
    personality_display: str
    personality_traits: Optional[Dict]
    custom_personality: Optional[str]
    role_type: str
    voice_id: str
    domains: Optional[List[str]]
    total_conversations: int
    total_messages: int
    is_active: bool
    is_default: bool
    created_at: datetime
    last_conversation_at: Optional[datetime]


class DigitalHumanListResponse(BaseModel):
    """数字人列表响应"""
    total: int
    items: List[DigitalHumanResponse]


# 对话相关Schema
class DHChatRequest(BaseModel):
    """数字人对话请求"""
    dh_id: int = Field(..., description="数字人ID")
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")
    session_id: Optional[str] = Field(default=None, description="会话ID，可选")

    class Config:
        json_schema_extra = {
            "example": {
                "dh_id": 1,
                "message": "你好，今天过得怎么样？"
            }
        }


class DHChatResponse(BaseModel):
    """数字人对话响应"""
    session_id: str
    dh_id: int
    response: str
    emotion: Optional[str]
    is_complete: bool
    tokens_used: Optional[int]


class DHHistoryResponse(BaseModel):
    """对话历史响应"""
    dh_id: int
    messages: List[Dict]
    has_more: bool
