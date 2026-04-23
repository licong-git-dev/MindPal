"""
MindPal Backend V2 - Pydantic Schemas for Player
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ==================== 请求模式 ====================

class AvatarConfig(BaseModel):
    """头像配置"""
    gender: str = Field(..., pattern="^(male|female)$")
    face_shape: int = Field(default=1, ge=1, le=5)
    skin_color: str = Field(default="#FFE4C4")
    hair_style: int = Field(default=1, ge=1, le=10)
    hair_color: str = Field(default="#4A4A4A")
    eye_style: int = Field(default=1, ge=1, le=5)
    eye_color: str = Field(default="#8B4513")


class CreateCharacterRequest(BaseModel):
    """创建角色请求"""
    nickname: str = Field(..., min_length=2, max_length=50)
    avatar_config: Optional[AvatarConfig] = None


class UpdatePositionRequest(BaseModel):
    """更新位置请求"""
    zone: str
    x: float
    y: float
    z: float
    rotation_y: Optional[float] = 0.0


# ==================== 响应模式 ====================

class PositionResponse(BaseModel):
    """位置信息"""
    x: float
    y: float
    z: float


class StatsResponse(BaseModel):
    """统计信息"""
    total_playtime: int
    dialogues_count: int
    keys_collected: List[int]
    achievements_count: int


class PlayerResponse(BaseModel):
    """角色信息响应"""
    player_id: int
    nickname: str
    level: int
    experience: int
    exp_to_next_level: int
    gold: int
    diamonds: int
    current_zone: str
    position: PositionResponse
    avatar_config: Optional[Dict[str, Any]] = None
    equipment: Optional[Dict[str, Any]] = None
    stats: StatsResponse

    class Config:
        from_attributes = True


class CreateCharacterResponse(BaseModel):
    """创建角色响应"""
    player_id: int
    nickname: str
    level: int
    gold: int
    diamonds: int
    current_zone: str
    position: PositionResponse


class PositionSyncResponse(BaseModel):
    """位置同步响应"""
    synced: bool


# ==================== 好感度相关 ====================

class AffinityInfo(BaseModel):
    """好感度信息"""
    level: int
    value: int
    title: str


class AffinityResponse(BaseModel):
    """好感度响应"""
    aela: Optional[AffinityInfo] = None
    momo: Optional[AffinityInfo] = None
    chronos: Optional[AffinityInfo] = None
    bei: Optional[AffinityInfo] = None
    sesame: Optional[AffinityInfo] = None
