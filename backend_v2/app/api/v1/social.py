"""
MindPal Backend V2 - Social API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import joinedload
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Player
from app.models.social import Friendship, BlockedPlayer, Party, PartyMember
from app.schemas import APIResponse
from app.core.security import get_current_user_id

router = APIRouter()


class FriendRequestBody(BaseModel):
    """好友申请请求"""
    target_player_id: int
    message: Optional[str] = None


class HandleRequestBody(BaseModel):
    """处理好友申请"""
    action: str  # accept | reject


class BlockPlayerBody(BaseModel):
    """屏蔽玩家"""
    player_id: int
    reason: Optional[str] = None


class CreatePartyBody(BaseModel):
    """创建队伍"""
    name: Optional[str] = None
    is_public: bool = False


# ===================== 搜索玩家 =====================

@router.get("/search", response_model=APIResponse)
async def search_players(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    搜索玩家

    - **keyword**: 搜索关键词 (昵称)
    """
    # 获取当前玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    current_player = result.scalar_one_or_none()

    if not current_player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 搜索玩家
    stmt = select(Player).where(
        and_(
            Player.nickname.ilike(f"%{keyword}%"),
            Player.id != current_player.id
        )
    ).offset((page - 1) * size).limit(size)

    result = await db.execute(stmt)
    players = result.scalars().all()

    # 获取好友关系
    friend_ids = set()
    stmt = select(Friendship).where(
        and_(
            or_(
                Friendship.player_id == current_player.id,
                Friendship.friend_id == current_player.id
            ),
            Friendship.status == "accepted"
        )
    )
    result = await db.execute(stmt)
    friendships = result.scalars().all()
    for f in friendships:
        if f.player_id == current_player.id:
            friend_ids.add(f.friend_id)
        else:
            friend_ids.add(f.player_id)

    # 构建响应
    players_data = []
    for p in players:
        players_data.append({
            "player_id": p.id,
            "nickname": p.nickname,
            "level": p.level,
            "current_zone": p.current_zone,
            "is_friend": p.id in friend_ids,
        })

    return APIResponse(
        code=0,
        message="success",
        data={
            "players": players_data,
            "total": len(players_data)
        }
    )


# ===================== 好友系统 =====================

@router.get("/friends", response_model=APIResponse)
async def get_friends(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取好友列表"""
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    current_player = result.scalar_one_or_none()

    if not current_player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取已接受的好友关系
    stmt = select(Friendship).where(
        and_(
            or_(
                Friendship.player_id == current_player.id,
                Friendship.friend_id == current_player.id
            ),
            Friendship.status == "accepted"
        )
    )
    result = await db.execute(stmt)
    friendships = result.scalars().all()

    # 获取好友玩家信息
    friend_ids = []
    for f in friendships:
        if f.player_id == current_player.id:
            friend_ids.append(f.friend_id)
        else:
            friend_ids.append(f.player_id)

    if not friend_ids:
        return APIResponse(
            code=0,
            message="success",
            data={"friends": [], "total": 0}
        )

    stmt = select(Player).where(Player.id.in_(friend_ids))
    result = await db.execute(stmt)
    friends = result.scalars().all()

    friends_data = []
    for f in friends:
        friends_data.append({
            "player_id": f.id,
            "nickname": f.nickname,
            "level": f.level,
            "current_zone": f.current_zone,
            "is_online": True,  # 简化处理，实际需要Redis跟踪
            "last_online": f.last_online.isoformat() if f.last_online else None,
        })

    return APIResponse(
        code=0,
        message="success",
        data={
            "friends": friends_data,
            "total": len(friends_data)
        }
    )


@router.post("/friends/request", response_model=APIResponse)
async def send_friend_request(
    request: FriendRequestBody,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """发送好友申请"""
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    current_player = result.scalar_one_or_none()

    if not current_player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 检查目标玩家是否存在
    stmt = select(Player).where(Player.id == request.target_player_id)
    result = await db.execute(stmt)
    target_player = result.scalar_one_or_none()

    if not target_player:
        raise HTTPException(status_code=404, detail="Target player not found")

    if target_player.id == current_player.id:
        raise HTTPException(status_code=400, detail="Cannot add yourself as friend")

    # 检查是否已有关系
    stmt = select(Friendship).where(
        or_(
            and_(
                Friendship.player_id == current_player.id,
                Friendship.friend_id == target_player.id
            ),
            and_(
                Friendship.player_id == target_player.id,
                Friendship.friend_id == current_player.id
            )
        )
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing:
        if existing.status == "accepted":
            raise HTTPException(status_code=400, detail="Already friends")
        elif existing.status == "pending":
            raise HTTPException(status_code=400, detail="Friend request already sent")
        elif existing.status == "blocked":
            raise HTTPException(status_code=400, detail="Cannot send friend request")

    # 检查是否被屏蔽
    stmt = select(BlockedPlayer).where(
        and_(
            BlockedPlayer.player_id == target_player.id,
            BlockedPlayer.blocked_player_id == current_player.id
        )
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Cannot send friend request to this player")

    # 创建好友申请
    friendship = Friendship(
        player_id=current_player.id,
        friend_id=target_player.id,
        status="pending",
        request_message=request.message
    )
    db.add(friendship)

    return APIResponse(
        code=0,
        message="success",
        data={
            "request_id": friendship.id,
            "status": "pending"
        }
    )


@router.get("/friends/requests", response_model=APIResponse)
async def get_friend_requests(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取收到的好友申请"""
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    current_player = result.scalar_one_or_none()

    if not current_player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取待处理的申请
    stmt = select(Friendship).where(
        and_(
            Friendship.friend_id == current_player.id,
            Friendship.status == "pending"
        )
    )
    result = await db.execute(stmt)
    requests = result.scalars().all()

    # 获取申请者信息
    requester_ids = [r.player_id for r in requests]
    if not requester_ids:
        return APIResponse(
            code=0,
            message="success",
            data={"requests": [], "total": 0}
        )

    stmt = select(Player).where(Player.id.in_(requester_ids))
    result = await db.execute(stmt)
    requesters = {p.id: p for p in result.scalars().all()}

    requests_data = []
    for r in requests:
        requester = requesters.get(r.player_id)
        if requester:
            requests_data.append({
                "request_id": r.id,
                "player": {
                    "player_id": requester.id,
                    "nickname": requester.nickname,
                    "level": requester.level,
                },
                "message": r.request_message,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            })

    return APIResponse(
        code=0,
        message="success",
        data={
            "requests": requests_data,
            "total": len(requests_data)
        }
    )


@router.put("/friends/request/{request_id}", response_model=APIResponse)
async def handle_friend_request(
    request_id: int,
    body: HandleRequestBody,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    处理好友申请

    - **action**: accept(接受) 或 reject(拒绝)
    """
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    current_player = result.scalar_one_or_none()

    if not current_player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取申请
    stmt = select(Friendship).where(
        and_(
            Friendship.id == request_id,
            Friendship.friend_id == current_player.id,
            Friendship.status == "pending"
        )
    )
    result = await db.execute(stmt)
    friendship = result.scalar_one_or_none()

    if not friendship:
        raise HTTPException(status_code=404, detail="Friend request not found")

    if body.action == "accept":
        friendship.status = "accepted"
        friendship.accepted_at = datetime.utcnow()

        # 获取好友信息
        stmt = select(Player).where(Player.id == friendship.player_id)
        result = await db.execute(stmt)
        friend = result.scalar_one_or_none()

        return APIResponse(
            code=0,
            message="success",
            data={
                "action": "accept",
                "friend": {
                    "player_id": friend.id,
                    "nickname": friend.nickname,
                    "level": friend.level,
                } if friend else None
            }
        )
    elif body.action == "reject":
        await db.delete(friendship)
        return APIResponse(
            code=0,
            message="success",
            data={"action": "reject"}
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid action")


@router.delete("/friends/{friend_id}", response_model=APIResponse)
async def remove_friend(
    friend_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """删除好友"""
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    current_player = result.scalar_one_or_none()

    if not current_player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 查找好友关系
    stmt = select(Friendship).where(
        and_(
            or_(
                and_(
                    Friendship.player_id == current_player.id,
                    Friendship.friend_id == friend_id
                ),
                and_(
                    Friendship.player_id == friend_id,
                    Friendship.friend_id == current_player.id
                )
            ),
            Friendship.status == "accepted"
        )
    )
    result = await db.execute(stmt)
    friendship = result.scalar_one_or_none()

    if not friendship:
        raise HTTPException(status_code=404, detail="Friendship not found")

    await db.delete(friendship)

    return APIResponse(
        code=0,
        message="success",
        data={"removed": True}
    )


# ===================== 屏蔽系统 =====================

@router.post("/block", response_model=APIResponse)
async def block_player(
    body: BlockPlayerBody,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """屏蔽玩家"""
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    current_player = result.scalar_one_or_none()

    if not current_player:
        raise HTTPException(status_code=404, detail="Character not found")

    if body.player_id == current_player.id:
        raise HTTPException(status_code=400, detail="Cannot block yourself")

    # 检查是否已屏蔽
    stmt = select(BlockedPlayer).where(
        and_(
            BlockedPlayer.player_id == current_player.id,
            BlockedPlayer.blocked_player_id == body.player_id
        )
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Player already blocked")

    # 创建屏蔽记录
    blocked = BlockedPlayer(
        player_id=current_player.id,
        blocked_player_id=body.player_id,
        reason=body.reason
    )
    db.add(blocked)

    # 删除好友关系
    stmt = select(Friendship).where(
        or_(
            and_(
                Friendship.player_id == current_player.id,
                Friendship.friend_id == body.player_id
            ),
            and_(
                Friendship.player_id == body.player_id,
                Friendship.friend_id == current_player.id
            )
        )
    )
    result = await db.execute(stmt)
    friendship = result.scalar_one_or_none()
    if friendship:
        await db.delete(friendship)

    return APIResponse(
        code=0,
        message="success",
        data={"blocked": True}
    )


@router.delete("/block/{player_id}", response_model=APIResponse)
async def unblock_player(
    player_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """取消屏蔽"""
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    current_player = result.scalar_one_or_none()

    if not current_player:
        raise HTTPException(status_code=404, detail="Character not found")

    stmt = select(BlockedPlayer).where(
        and_(
            BlockedPlayer.player_id == current_player.id,
            BlockedPlayer.blocked_player_id == player_id
        )
    )
    result = await db.execute(stmt)
    blocked = result.scalar_one_or_none()

    if not blocked:
        raise HTTPException(status_code=404, detail="Block record not found")

    await db.delete(blocked)

    return APIResponse(
        code=0,
        message="success",
        data={"unblocked": True}
    )


@router.get("/blocked", response_model=APIResponse)
async def get_blocked_list(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取屏蔽列表"""
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    current_player = result.scalar_one_or_none()

    if not current_player:
        raise HTTPException(status_code=404, detail="Character not found")

    stmt = select(BlockedPlayer).where(
        BlockedPlayer.player_id == current_player.id
    )
    result = await db.execute(stmt)
    blocked_list = result.scalars().all()

    blocked_ids = [b.blocked_player_id for b in blocked_list]
    if not blocked_ids:
        return APIResponse(
            code=0,
            message="success",
            data={"blocked": [], "total": 0}
        )

    stmt = select(Player).where(Player.id.in_(blocked_ids))
    result = await db.execute(stmt)
    players = {p.id: p for p in result.scalars().all()}

    blocked_data = []
    for b in blocked_list:
        player = players.get(b.blocked_player_id)
        if player:
            blocked_data.append({
                "player_id": player.id,
                "nickname": player.nickname,
                "blocked_at": b.created_at.isoformat() if b.created_at else None,
                "reason": b.reason,
            })

    return APIResponse(
        code=0,
        message="success",
        data={
            "blocked": blocked_data,
            "total": len(blocked_data)
        }
    )
