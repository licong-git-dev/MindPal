"""
MindPal Backend V2 - Achievement API Routes
成就系统
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Player, Achievement, PlayerAchievement
from app.schemas import APIResponse
from app.core.security import get_current_user_id
from app.core.websocket import get_connection_manager, MessageType

router = APIRouter()


# ===================== 成就查询 =====================

@router.get("", response_model=APIResponse)
async def get_achievements(
    category: Optional[str] = Query(None, description="成就分类"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态过滤: unlocked/locked"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取成就列表

    - **category**: 成就分类 (exploration/social/combat/collection/story)
    - **status**: 状态过滤 (unlocked/locked)
    """
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取所有成就
    stmt = select(Achievement)
    if category:
        stmt = stmt.where(Achievement.category == category)
    result = await db.execute(stmt)
    all_achievements = result.scalars().all()

    # 获取玩家已解锁的成就
    stmt = select(PlayerAchievement).where(
        PlayerAchievement.player_id == player.id
    )
    result = await db.execute(stmt)
    player_achievements = {pa.achievement_id: pa for pa in result.scalars().all()}

    # 构建响应
    achievements_data = []
    for ach in all_achievements:
        is_unlocked = ach.id in player_achievements

        if status_filter == "unlocked" and not is_unlocked:
            continue
        if status_filter == "locked" and is_unlocked:
            continue

        pa = player_achievements.get(ach.id)
        achievements_data.append({
            "id": ach.id,
            "name": ach.name,
            "description": ach.description,
            "category": ach.category,
            "points": ach.points,
            "icon": ach.icon,
            "is_hidden": ach.is_hidden and not is_unlocked,  # 隐藏成就未解锁时不显示详情
            "is_unlocked": is_unlocked,
            "unlocked_at": pa.unlocked_at.isoformat() if pa and pa.unlocked_at else None,
            "progress": pa.progress if pa else 0,
            "target": ach.target_value or 1
        })

    # 统计
    total_points = sum(a.points for a in all_achievements)
    unlocked_points = sum(
        player_achievements[ach.id].achievement.points
        for ach in all_achievements
        if ach.id in player_achievements
    ) if player_achievements else 0

    return APIResponse(
        code=0,
        message="success",
        data={
            "achievements": achievements_data,
            "stats": {
                "total": len(all_achievements),
                "unlocked": len(player_achievements),
                "total_points": total_points,
                "unlocked_points": unlocked_points
            }
        }
    )


@router.get("/{achievement_id}", response_model=APIResponse)
async def get_achievement_detail(
    achievement_id: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取成就详情"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取成就
    stmt = select(Achievement).where(Achievement.id == achievement_id)
    result = await db.execute(stmt)
    achievement = result.scalar_one_or_none()

    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    # 获取玩家进度
    stmt = select(PlayerAchievement).where(
        and_(
            PlayerAchievement.player_id == player.id,
            PlayerAchievement.achievement_id == achievement_id
        )
    )
    result = await db.execute(stmt)
    player_achievement = result.scalar_one_or_none()

    is_unlocked = player_achievement is not None

    # 隐藏成就未解锁时不显示详情
    if achievement.is_hidden and not is_unlocked:
        return APIResponse(
            code=0,
            message="success",
            data={
                "id": achievement.id,
                "name": "???",
                "description": "隐藏成就",
                "is_hidden": True,
                "is_unlocked": False
            }
        )

    return APIResponse(
        code=0,
        message="success",
        data={
            "id": achievement.id,
            "name": achievement.name,
            "description": achievement.description,
            "category": achievement.category,
            "points": achievement.points,
            "icon": achievement.icon,
            "is_hidden": achievement.is_hidden,
            "is_unlocked": is_unlocked,
            "unlocked_at": player_achievement.unlocked_at.isoformat() if player_achievement and player_achievement.unlocked_at else None,
            "progress": player_achievement.progress if player_achievement else 0,
            "target": achievement.target_value or 1,
            "rewards": achievement.rewards
        }
    )


@router.post("/{achievement_id}/progress", response_model=APIResponse)
async def update_achievement_progress(
    achievement_id: str,
    progress: int = Query(..., ge=0, description="增加的进度值"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    更新成就进度（内部调用或测试用）

    - **progress**: 增加的进度值
    """
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取成就
    stmt = select(Achievement).where(Achievement.id == achievement_id)
    result = await db.execute(stmt)
    achievement = result.scalar_one_or_none()

    if not achievement:
        raise HTTPException(status_code=404, detail="Achievement not found")

    # 获取或创建玩家成就记录
    stmt = select(PlayerAchievement).where(
        and_(
            PlayerAchievement.player_id == player.id,
            PlayerAchievement.achievement_id == achievement_id
        )
    )
    result = await db.execute(stmt)
    player_achievement = result.scalar_one_or_none()

    if not player_achievement:
        player_achievement = PlayerAchievement(
            player_id=player.id,
            achievement_id=achievement_id,
            progress=0
        )
        db.add(player_achievement)

    # 如果已解锁，不再更新
    if player_achievement.unlocked_at:
        return APIResponse(
            code=0,
            message="success",
            data={
                "achievement_id": achievement_id,
                "already_unlocked": True
            }
        )

    # 更新进度
    player_achievement.progress += progress
    target = achievement.target_value or 1

    # 检查是否解锁
    just_unlocked = False
    if player_achievement.progress >= target:
        player_achievement.progress = target
        player_achievement.unlocked_at = datetime.utcnow()
        just_unlocked = True

        # 更新玩家成就计数
        player.achievements_count += 1

        # 发放奖励
        rewards_claimed = {}
        if achievement.rewards:
            if "exp" in achievement.rewards:
                player.experience += achievement.rewards["exp"]
                rewards_claimed["exp"] = achievement.rewards["exp"]
            if "gold" in achievement.rewards:
                player.gold += achievement.rewards["gold"]
                rewards_claimed["gold"] = achievement.rewards["gold"]
            if "diamonds" in achievement.rewards:
                player.diamonds += achievement.rewards["diamonds"]
                rewards_claimed["diamonds"] = achievement.rewards["diamonds"]

        # 发送通知
        manager = get_connection_manager()
        await manager.send_personal(
            player.id,
            MessageType.ACHIEVEMENT,
            {
                "achievement_id": achievement.id,
                "name": achievement.name,
                "description": achievement.description,
                "points": achievement.points,
                "icon": achievement.icon,
                "rewards": rewards_claimed
            }
        )

    await db.commit()

    return APIResponse(
        code=0,
        message="success",
        data={
            "achievement_id": achievement_id,
            "current_progress": player_achievement.progress,
            "target": target,
            "just_unlocked": just_unlocked
        }
    )


@router.get("/categories/list", response_model=APIResponse)
async def get_achievement_categories(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取成就分类列表及统计"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取所有成就按分类统计
    stmt = select(
        Achievement.category,
        func.count(Achievement.id).label("total"),
        func.sum(Achievement.points).label("total_points")
    ).group_by(Achievement.category)
    result = await db.execute(stmt)
    category_stats = {row[0]: {"total": row[1], "total_points": row[2] or 0} for row in result.fetchall()}

    # 获取玩家已解锁的成就按分类统计
    stmt = select(
        Achievement.category,
        func.count(PlayerAchievement.id).label("unlocked"),
        func.sum(Achievement.points).label("unlocked_points")
    ).join(
        PlayerAchievement, PlayerAchievement.achievement_id == Achievement.id
    ).where(
        PlayerAchievement.player_id == player.id
    ).group_by(Achievement.category)
    result = await db.execute(stmt)
    unlocked_stats = {row[0]: {"unlocked": row[1], "unlocked_points": row[2] or 0} for row in result.fetchall()}

    # 合并统计
    categories = []
    category_names = {
        "exploration": "探索",
        "social": "社交",
        "combat": "战斗",
        "collection": "收集",
        "story": "剧情",
        "npc": "NPC亲密度"
    }

    for cat, stats in category_stats.items():
        unlocked = unlocked_stats.get(cat, {"unlocked": 0, "unlocked_points": 0})
        categories.append({
            "id": cat,
            "name": category_names.get(cat, cat),
            "total": stats["total"],
            "unlocked": unlocked["unlocked"],
            "total_points": stats["total_points"],
            "unlocked_points": unlocked["unlocked_points"],
            "completion_rate": round(unlocked["unlocked"] / stats["total"] * 100, 1) if stats["total"] > 0 else 0
        })

    return APIResponse(
        code=0,
        message="success",
        data={"categories": categories}
    )
