"""
MindPal Backend V2 - Leaderboard API Routes
排行榜系统
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from datetime import datetime, timedelta
from typing import Optional

from app.database import get_db
from app.models import Player, PlayerAchievement
from app.models.social import Friendship
from app.schemas import APIResponse
from app.core.security import get_current_user_id

router = APIRouter()


# ===================== 等级排行榜 =====================

@router.get("/level", response_model=APIResponse)
async def get_level_leaderboard(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取等级排行榜"""
    # 获取当前玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    current_player = result.scalar_one_or_none()

    if not current_player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取排行榜
    stmt = select(Player).order_by(
        desc(Player.level),
        desc(Player.experience)
    ).offset((page - 1) * size).limit(size)

    result = await db.execute(stmt)
    players = result.scalars().all()

    # 获取总人数
    stmt = select(func.count(Player.id))
    result = await db.execute(stmt)
    total = result.scalar()

    # 获取当前玩家排名
    stmt = select(func.count(Player.id)).where(
        (Player.level > current_player.level) |
        ((Player.level == current_player.level) & (Player.experience > current_player.experience))
    )
    result = await db.execute(stmt)
    my_rank = result.scalar() + 1

    # 构建响应
    leaderboard = []
    for i, p in enumerate(players):
        rank = (page - 1) * size + i + 1
        leaderboard.append({
            "rank": rank,
            "player_id": p.id,
            "nickname": p.nickname,
            "level": p.level,
            "experience": p.experience,
            "is_me": p.id == current_player.id
        })

    return APIResponse(
        code=0,
        message="success",
        data={
            "leaderboard": leaderboard,
            "total": total,
            "my_rank": my_rank,
            "my_level": current_player.level,
            "page": page,
            "size": size
        }
    )


# ===================== 成就点数排行榜 =====================

@router.get("/achievement", response_model=APIResponse)
async def get_achievement_leaderboard(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取成就点数排行榜"""
    # 获取当前玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    current_player = result.scalar_one_or_none()

    if not current_player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取排行榜
    stmt = select(Player).order_by(
        desc(Player.achievements_count)
    ).offset((page - 1) * size).limit(size)

    result = await db.execute(stmt)
    players = result.scalars().all()

    # 获取当前玩家排名
    stmt = select(func.count(Player.id)).where(
        Player.achievements_count > current_player.achievements_count
    )
    result = await db.execute(stmt)
    my_rank = result.scalar() + 1

    # 构建响应
    leaderboard = []
    for i, p in enumerate(players):
        rank = (page - 1) * size + i + 1
        leaderboard.append({
            "rank": rank,
            "player_id": p.id,
            "nickname": p.nickname,
            "achievements_count": p.achievements_count,
            "level": p.level,
            "is_me": p.id == current_player.id
        })

    return APIResponse(
        code=0,
        message="success",
        data={
            "leaderboard": leaderboard,
            "my_rank": my_rank,
            "my_achievements": current_player.achievements_count,
            "page": page,
            "size": size
        }
    )


# ===================== 财富排行榜 =====================

@router.get("/wealth", response_model=APIResponse)
async def get_wealth_leaderboard(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取财富排行榜（金币）"""
    # 获取当前玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    current_player = result.scalar_one_or_none()

    if not current_player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取排行榜
    stmt = select(Player).order_by(
        desc(Player.gold)
    ).offset((page - 1) * size).limit(size)

    result = await db.execute(stmt)
    players = result.scalars().all()

    # 获取当前玩家排名
    stmt = select(func.count(Player.id)).where(
        Player.gold > current_player.gold
    )
    result = await db.execute(stmt)
    my_rank = result.scalar() + 1

    # 构建响应
    leaderboard = []
    for i, p in enumerate(players):
        rank = (page - 1) * size + i + 1
        leaderboard.append({
            "rank": rank,
            "player_id": p.id,
            "nickname": p.nickname,
            "gold": p.gold,
            "level": p.level,
            "is_me": p.id == current_player.id
        })

    return APIResponse(
        code=0,
        message="success",
        data={
            "leaderboard": leaderboard,
            "my_rank": my_rank,
            "my_gold": current_player.gold,
            "page": page,
            "size": size
        }
    )


# ===================== 对话次数排行榜 =====================

@router.get("/dialogue", response_model=APIResponse)
async def get_dialogue_leaderboard(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取对话次数排行榜"""
    # 获取当前玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    current_player = result.scalar_one_or_none()

    if not current_player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取排行榜
    stmt = select(Player).order_by(
        desc(Player.dialogues_count)
    ).offset((page - 1) * size).limit(size)

    result = await db.execute(stmt)
    players = result.scalars().all()

    # 获取当前玩家排名
    stmt = select(func.count(Player.id)).where(
        Player.dialogues_count > current_player.dialogues_count
    )
    result = await db.execute(stmt)
    my_rank = result.scalar() + 1

    # 构建响应
    leaderboard = []
    for i, p in enumerate(players):
        rank = (page - 1) * size + i + 1
        leaderboard.append({
            "rank": rank,
            "player_id": p.id,
            "nickname": p.nickname,
            "dialogues_count": p.dialogues_count,
            "level": p.level,
            "is_me": p.id == current_player.id
        })

    return APIResponse(
        code=0,
        message="success",
        data={
            "leaderboard": leaderboard,
            "my_rank": my_rank,
            "my_dialogues": current_player.dialogues_count,
            "page": page,
            "size": size
        }
    )


# ===================== 游戏时长排行榜 =====================

@router.get("/playtime", response_model=APIResponse)
async def get_playtime_leaderboard(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取游戏时长排行榜"""
    # 获取当前玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    current_player = result.scalar_one_or_none()

    if not current_player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取排行榜
    stmt = select(Player).order_by(
        desc(Player.total_playtime)
    ).offset((page - 1) * size).limit(size)

    result = await db.execute(stmt)
    players = result.scalars().all()

    # 获取当前玩家排名
    stmt = select(func.count(Player.id)).where(
        Player.total_playtime > current_player.total_playtime
    )
    result = await db.execute(stmt)
    my_rank = result.scalar() + 1

    # 构建响应
    leaderboard = []
    for i, p in enumerate(players):
        rank = (page - 1) * size + i + 1
        # 转换为小时
        hours = p.total_playtime // 3600
        minutes = (p.total_playtime % 3600) // 60
        leaderboard.append({
            "rank": rank,
            "player_id": p.id,
            "nickname": p.nickname,
            "total_playtime": p.total_playtime,
            "playtime_display": f"{hours}小时{minutes}分钟",
            "level": p.level,
            "is_me": p.id == current_player.id
        })

    my_hours = current_player.total_playtime // 3600
    my_minutes = (current_player.total_playtime % 3600) // 60

    return APIResponse(
        code=0,
        message="success",
        data={
            "leaderboard": leaderboard,
            "my_rank": my_rank,
            "my_playtime": current_player.total_playtime,
            "my_playtime_display": f"{my_hours}小时{my_minutes}分钟",
            "page": page,
            "size": size
        }
    )


# ===================== 好友排行榜 =====================

@router.get("/friends", response_model=APIResponse)
async def get_friends_leaderboard(
    type: str = Query("level", description="排行类型: level/achievement/wealth/dialogue"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取好友排行榜"""
    # 获取当前玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    current_player = result.scalar_one_or_none()

    if not current_player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取好友ID列表
    stmt = select(Friendship).where(
        (
            (Friendship.player_id == current_player.id) |
            (Friendship.friend_id == current_player.id)
        ) &
        (Friendship.status == "accepted")
    )
    result = await db.execute(stmt)
    friendships = result.scalars().all()

    friend_ids = set()
    for f in friendships:
        if f.player_id == current_player.id:
            friend_ids.add(f.friend_id)
        else:
            friend_ids.add(f.player_id)

    # 加入自己
    friend_ids.add(current_player.id)

    if not friend_ids:
        return APIResponse(
            code=0,
            message="success",
            data={
                "leaderboard": [],
                "my_rank": 1
            }
        )

    # 根据类型排序
    order_field = {
        "level": (desc(Player.level), desc(Player.experience)),
        "achievement": (desc(Player.achievements_count),),
        "wealth": (desc(Player.gold),),
        "dialogue": (desc(Player.dialogues_count),)
    }.get(type, (desc(Player.level), desc(Player.experience)))

    stmt = select(Player).where(
        Player.id.in_(friend_ids)
    ).order_by(*order_field)

    result = await db.execute(stmt)
    friends = result.scalars().all()

    # 构建响应
    leaderboard = []
    my_rank = 1
    for i, p in enumerate(friends):
        rank = i + 1
        if p.id == current_player.id:
            my_rank = rank

        entry = {
            "rank": rank,
            "player_id": p.id,
            "nickname": p.nickname,
            "level": p.level,
            "is_me": p.id == current_player.id
        }

        if type == "level":
            entry["experience"] = p.experience
        elif type == "achievement":
            entry["achievements_count"] = p.achievements_count
        elif type == "wealth":
            entry["gold"] = p.gold
        elif type == "dialogue":
            entry["dialogues_count"] = p.dialogues_count

        leaderboard.append(entry)

    return APIResponse(
        code=0,
        message="success",
        data={
            "leaderboard": leaderboard,
            "my_rank": my_rank,
            "type": type
        }
    )


# ===================== 综合排行榜类型列表 =====================

@router.get("/types", response_model=APIResponse)
async def get_leaderboard_types(
    user_id: int = Depends(get_current_user_id)
):
    """获取排行榜类型列表"""
    return APIResponse(
        code=0,
        message="success",
        data={
            "types": [
                {
                    "id": "level",
                    "name": "等级排行",
                    "description": "按玩家等级和经验值排名",
                    "icon": "level"
                },
                {
                    "id": "achievement",
                    "name": "成就排行",
                    "description": "按解锁成就数量排名",
                    "icon": "achievement"
                },
                {
                    "id": "wealth",
                    "name": "财富排行",
                    "description": "按金币数量排名",
                    "icon": "gold"
                },
                {
                    "id": "dialogue",
                    "name": "对话排行",
                    "description": "按与NPC对话次数排名",
                    "icon": "dialogue"
                },
                {
                    "id": "playtime",
                    "name": "时长排行",
                    "description": "按游戏总时长排名",
                    "icon": "time"
                },
                {
                    "id": "friends",
                    "name": "好友排行",
                    "description": "仅显示好友之间的排名",
                    "icon": "friends"
                }
            ]
        }
    )
