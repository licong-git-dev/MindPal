"""
MindPal Backend V2 - Schemas Package
"""

from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenRefreshRequest,
    OAuthLoginRequest,
    TokenResponse,
    UserResponse,
    LoginResponse,
    RegisterResponse,
    APIResponse,
    ErrorResponse,
)

from app.schemas.player import (
    AvatarConfig,
    CreateCharacterRequest,
    UpdatePositionRequest,
    PositionResponse,
    StatsResponse,
    PlayerResponse,
    CreateCharacterResponse,
    PositionSyncResponse,
    AffinityInfo,
    AffinityResponse,
)

from app.schemas.dialogue import (
    EmotionData,
    ChatRequest,
    StreamChatRequest,
    MessageResponse,
    ChatResponse,
    ChatHistoryResponse,
    AllAffinityResponse,
)

__all__ = [
    # User schemas
    "UserRegisterRequest",
    "UserLoginRequest",
    "TokenRefreshRequest",
    "OAuthLoginRequest",
    "TokenResponse",
    "UserResponse",
    "LoginResponse",
    "RegisterResponse",
    "APIResponse",
    "ErrorResponse",
    # Player schemas
    "AvatarConfig",
    "CreateCharacterRequest",
    "UpdatePositionRequest",
    "PositionResponse",
    "StatsResponse",
    "PlayerResponse",
    "CreateCharacterResponse",
    "PositionSyncResponse",
    "AffinityInfo",
    "AffinityResponse",
    # Dialogue schemas
    "EmotionData",
    "ChatRequest",
    "StreamChatRequest",
    "MessageResponse",
    "ChatResponse",
    "ChatHistoryResponse",
    "AllAffinityResponse",
]
