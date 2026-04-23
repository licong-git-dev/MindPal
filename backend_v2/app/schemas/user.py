"""
MindPal Backend V2 - Pydantic Schemas for User & Auth
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Union, List, Any
from datetime import datetime


# ==================== 请求模式 ====================

class UserRegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    verification_code: Optional[str] = None  # 邮箱验证码


class UserLoginRequest(BaseModel):
    """用户登录请求"""
    account: str = Field(..., description="邮箱或用户名")
    password: str


class TokenRefreshRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str


class OAuthLoginRequest(BaseModel):
    """OAuth登录请求"""
    code: str
    state: Optional[str] = None


# ==================== 响应模式 ====================

class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: str
    phone: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """登录响应"""
    user_id: int
    username: str
    player_id: Optional[int] = None
    has_character: bool
    access_token: str
    expires_in: int


class RegisterResponse(BaseModel):
    """注册响应"""
    user_id: int
    username: str
    access_token: str
    expires_in: int


# ==================== 通用响应 ====================

class APIResponse(BaseModel):
    """通用API响应"""
    code: int = 0
    message: str = "success"
    data: Optional[Union[dict, list, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ErrorResponse(BaseModel):
    """错误响应"""
    code: int
    message: str
    error_detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
