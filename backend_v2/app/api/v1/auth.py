"""
MindPal Backend V2 - Auth API Routes
"""

from datetime import datetime
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenRefreshRequest,
    LoginResponse,
    RegisterResponse,
    APIResponse,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
    get_password_hash,
    verify_password,
    get_current_user_id,
)
from app.config import settings

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def get_db_dependency():
    from app.database import get_db

    async for db in get_db():
        yield db

router = APIRouter()


def set_refresh_cookie(response: Response, refresh_token: str):
    """设置HttpOnly refresh token cookie"""
    response.set_cookie(
        key="mindpal_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/auth",
    )


@router.post("/register", response_model=APIResponse)
async def register(
    request: UserRegisterRequest,
    response: Response,
    db: "AsyncSession" = Depends(get_db_dependency)
):
    """
    用户注册

    - **username**: 用户名 (3-50字符)
    - **email**: 邮箱地址
    - **password**: 密码 (8-100字符)
    """
    from sqlalchemy import or_, select

    from app.models import User

    # 检查用户名是否已存在
    stmt = select(User).where(
        or_(User.username == request.username, User.email == request.email)
    )
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        if existing_user.username == request.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

    # 创建新用户
    user = User(
        username=request.username,
        email=request.email,
        password_hash=get_password_hash(request.password),
    )
    db.add(user)
    await db.flush()

    # 生成Token
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    set_refresh_cookie(response, refresh_token)

    return APIResponse(
        code=0,
        message="success",
        data=RegisterResponse(
            user_id=user.id,
            username=user.username,
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ).model_dump()
    )


@router.post("/login", response_model=APIResponse)
async def login(
    request: UserLoginRequest,
    response: Response,
    db: "AsyncSession" = Depends(get_db_dependency)
):
    """
    用户登录

    - **account**: 邮箱或用户名
    - **password**: 密码
    """
    from sqlalchemy import or_, select

    from app.models import Player, User

    # 查找用户
    stmt = select(User).where(
        or_(User.username == request.account, User.email == request.account)
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # 更新最后登录时间
    user.last_login = datetime.utcnow()

    # 查找玩家角色
    stmt = select(Player).where(Player.user_id == user.id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    # 生成Token
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    set_refresh_cookie(response, refresh_token)

    return APIResponse(
        code=0,
        message="success",
        data=LoginResponse(
            user_id=user.id,
            username=user.username,
            player_id=player.id if player else None,
            has_character=player is not None,
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        ).model_dump()
    )


@router.post("/refresh", response_model=APIResponse)
async def refresh_token(
    request: Request,
    token_request: TokenRefreshRequest | None = None,
    db: "AsyncSession" = Depends(get_db_dependency)
):
    """
    刷新访问令牌

    - **refresh_token**: 刷新令牌
    """
    refresh_token_value = None

    if token_request and token_request.refresh_token:
        refresh_token_value = token_request.refresh_token
    else:
        refresh_token_value = request.cookies.get("mindpal_refresh_token")

    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is required"
        )

    user_id = verify_refresh_token(refresh_token_value)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    from sqlalchemy import select

    from app.models import User

    # 验证用户是否存在且活跃
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled"
        )

    # 生成新的访问令牌
    access_token = create_access_token(data={"sub": str(user_id)})

    return APIResponse(
        code=0,
        message="success",
        data={
            "access_token": access_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }
    )


@router.get("/me", response_model=APIResponse)
async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: "AsyncSession" = Depends(get_db_dependency)
):
    """获取当前用户信息"""
    from sqlalchemy import select

    from app.models import User

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return APIResponse(
        code=0,
        message="success",
        data=user.to_dict()
    )
