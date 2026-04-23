"""
MindPal Backend V2 - Quest API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Player, Quest, QuestProgress, Item, InventoryItem
from app.schemas import APIResponse
from app.core.security import get_current_user_id

router = APIRouter()


class UpdateProgressRequest(BaseModel):
    """更新任务进度请求"""
    objective_id: str
    progress: int = 1


@router.get("", response_model=APIResponse)
async def get_quests(
    quest_type: Optional[str] = Query(None, description="任务类型: main/side/daily"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态过滤: in_progress/completed/available"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取任务列表

    - **quest_type**: 任务类型 (main/side/daily)
    - **status**: 状态过滤 (in_progress/completed/available)
    """
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 获取玩家的任务进度
    stmt = select(QuestProgress).options(
        joinedload(QuestProgress.quest)
    ).where(QuestProgress.player_id == player.id)

    if status_filter:
        stmt = stmt.where(QuestProgress.status == status_filter)

    result = await db.execute(stmt)
    quest_progress_list = result.scalars().all()

    # 按任务类型分组
    main_quests = []
    side_quests = []
    daily_quests = []

    for qp in quest_progress_list:
        quest_data = qp.to_dict()
        if quest_type and qp.quest.quest_type != quest_type:
            continue

        if qp.quest.quest_type == "main":
            main_quests.append(quest_data)
        elif qp.quest.quest_type == "side":
            side_quests.append(quest_data)
        elif qp.quest.quest_type == "daily":
            daily_quests.append(quest_data)

    return APIResponse(
        code=0,
        message="success",
        data={
            "main_quests": main_quests,
            "side_quests": side_quests,
            "daily_quests": daily_quests,
            "total": len(quest_progress_list)
        }
    )


@router.get("/available", response_model=APIResponse)
async def get_available_quests(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取可接受的任务列表"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 获取玩家已有的任务
    stmt = select(QuestProgress.quest_id).where(QuestProgress.player_id == player.id)
    result = await db.execute(stmt)
    existing_quest_ids = {row[0] for row in result.fetchall()}

    # 获取所有任务
    stmt = select(Quest)
    result = await db.execute(stmt)
    all_quests = result.scalars().all()

    # 过滤可接受的任务
    available_quests = []
    for quest in all_quests:
        # 已有任务跳过
        if quest.id in existing_quest_ids:
            continue

        # 检查等级要求
        if player.level < quest.required_level:
            continue

        # 检查前置任务
        if quest.prerequisite_quest_id:
            stmt = select(QuestProgress).where(
                and_(
                    QuestProgress.player_id == player.id,
                    QuestProgress.quest_id == quest.prerequisite_quest_id,
                    QuestProgress.status.in_(["completed", "claimed"])
                )
            )
            result = await db.execute(stmt)
            if not result.scalar_one_or_none():
                continue

        available_quests.append(quest.to_dict())

    return APIResponse(
        code=0,
        message="success",
        data={
            "quests": available_quests
        }
    )


@router.get("/{quest_id}", response_model=APIResponse)
async def get_quest_detail(
    quest_id: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取任务详情"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 获取任务进度
    stmt = select(QuestProgress).options(
        joinedload(QuestProgress.quest)
    ).where(
        and_(
            QuestProgress.player_id == player.id,
            QuestProgress.quest_id == quest_id
        )
    )
    result = await db.execute(stmt)
    quest_progress = result.scalar_one_or_none()

    if quest_progress:
        return APIResponse(
            code=0,
            message="success",
            data=quest_progress.to_dict()
        )

    # 如果没有进度，返回任务定义
    stmt = select(Quest).where(Quest.id == quest_id)
    result = await db.execute(stmt)
    quest = result.scalar_one_or_none()

    if not quest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quest not found"
        )

    return APIResponse(
        code=0,
        message="success",
        data={
            **quest.to_dict(),
            "status": "available",
            "objectives_progress": {}
        }
    )


@router.post("/{quest_id}/accept", response_model=APIResponse)
async def accept_quest(
    quest_id: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """接受任务"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 检查是否已接受
    stmt = select(QuestProgress).where(
        and_(
            QuestProgress.player_id == player.id,
            QuestProgress.quest_id == quest_id
        )
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quest already accepted"
        )

    # 获取任务定义
    stmt = select(Quest).where(Quest.id == quest_id)
    result = await db.execute(stmt)
    quest = result.scalar_one_or_none()

    if not quest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quest not found"
        )

    # 检查等级要求
    if player.level < quest.required_level:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Requires level {quest.required_level}"
        )

    # 检查前置任务
    if quest.prerequisite_quest_id:
        stmt = select(QuestProgress).where(
            and_(
                QuestProgress.player_id == player.id,
                QuestProgress.quest_id == quest.prerequisite_quest_id,
                QuestProgress.status.in_(["completed", "claimed"])
            )
        )
        result = await db.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Prerequisite quest not completed"
            )

    # 初始化目标进度
    objectives_progress = {}
    for obj in quest.objectives:
        obj_id = obj.get("id")
        target = obj.get("count", 1)
        objectives_progress[obj_id] = {
            "current": 0,
            "target": target,
            "completed": False
        }

    # 创建任务进度
    quest_progress = QuestProgress(
        player_id=player.id,
        quest_id=quest_id,
        status="in_progress",
        objectives_progress=objectives_progress
    )
    db.add(quest_progress)

    return APIResponse(
        code=0,
        message="success",
        data={
            "quest_id": quest_id,
            "status": "in_progress",
            "objectives_progress": objectives_progress
        }
    )


@router.post("/{quest_id}/progress", response_model=APIResponse)
async def update_quest_progress(
    quest_id: str,
    request: UpdateProgressRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    更新任务进度

    - **objective_id**: 目标ID
    - **progress**: 增加的进度值
    """
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 获取任务进度
    stmt = select(QuestProgress).options(
        joinedload(QuestProgress.quest)
    ).where(
        and_(
            QuestProgress.player_id == player.id,
            QuestProgress.quest_id == quest_id
        )
    )
    result = await db.execute(stmt)
    quest_progress = result.scalar_one_or_none()

    if not quest_progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quest not found or not accepted"
        )

    if quest_progress.status != "in_progress":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Quest is not in progress (status: {quest_progress.status})"
        )

    # 更新目标进度
    obj_progress = quest_progress.objectives_progress.get(request.objective_id)
    if not obj_progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Objective '{request.objective_id}' not found"
        )

    # 增加进度
    obj_progress["current"] = min(
        obj_progress["current"] + request.progress,
        obj_progress["target"]
    )
    obj_progress["completed"] = obj_progress["current"] >= obj_progress["target"]

    # 更新到数据库（需要重新赋值以触发更新）
    quest_progress.objectives_progress = {**quest_progress.objectives_progress}

    # 检查任务是否完成
    quest_completed = quest_progress.is_complete()
    if quest_completed and quest_progress.status == "in_progress":
        quest_progress.status = "completed"
        quest_progress.completed_at = datetime.utcnow()

    return APIResponse(
        code=0,
        message="success",
        data={
            "quest_id": quest_id,
            "objective_id": request.objective_id,
            "current": obj_progress["current"],
            "target": obj_progress["target"],
            "completed": obj_progress["completed"],
            "quest_completed": quest_completed
        }
    )


@router.post("/{quest_id}/claim", response_model=APIResponse)
async def claim_quest_rewards(
    quest_id: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """领取任务奖励"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 获取任务进度
    stmt = select(QuestProgress).options(
        joinedload(QuestProgress.quest)
    ).where(
        and_(
            QuestProgress.player_id == player.id,
            QuestProgress.quest_id == quest_id
        )
    )
    result = await db.execute(stmt)
    quest_progress = result.scalar_one_or_none()

    if not quest_progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quest not found"
        )

    if quest_progress.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quest not completed yet"
        )

    # 发放奖励
    rewards = quest_progress.quest.rewards
    rewards_claimed = {}

    # 经验奖励
    if "exp" in rewards:
        exp_reward = rewards["exp"]
        player.experience += exp_reward
        rewards_claimed["exp"] = exp_reward

        # 检查升级
        level_up = False
        while player.experience >= player.exp_to_next_level():
            player.experience -= player.exp_to_next_level()
            player.level += 1
            level_up = True
        rewards_claimed["level_up"] = level_up
        rewards_claimed["new_level"] = player.level

    # 金币奖励
    if "gold" in rewards:
        gold_reward = rewards["gold"]
        player.gold += gold_reward
        rewards_claimed["gold"] = gold_reward

    # 钻石奖励
    if "diamonds" in rewards:
        diamond_reward = rewards["diamonds"]
        player.diamonds += diamond_reward
        rewards_claimed["diamonds"] = diamond_reward

    # 物品奖励
    items_claimed = []
    if "items" in rewards:
        for item_data in rewards["items"]:
            item_id = item_data.get("id")
            quantity = item_data.get("quantity", 1)

            # 查找物品是否存在
            stmt = select(Item).where(Item.id == item_id)
            result = await db.execute(stmt)
            item = result.scalar_one_or_none()

            if item:
                # 添加到背包（简化处理）
                # 查找空闲格子
                stmt = select(InventoryItem.slot).where(
                    InventoryItem.player_id == player.id
                )
                result = await db.execute(stmt)
                used_slots = {row[0] for row in result.fetchall()}

                free_slot = None
                for i in range(48):
                    if i not in used_slots:
                        free_slot = i
                        break

                if free_slot is not None:
                    new_item = InventoryItem(
                        player_id=player.id,
                        item_id=item_id,
                        slot=free_slot,
                        quantity=quantity
                    )
                    db.add(new_item)
                    items_claimed.append({
                        "id": item_id,
                        "name": item.name,
                        "quantity": quantity
                    })

    rewards_claimed["items"] = items_claimed

    # 更新任务状态
    quest_progress.status = "claimed"
    quest_progress.claimed_at = datetime.utcnow()

    # 检查是否有后续任务
    next_quest = None
    if quest_progress.quest.next_quest_id:
        stmt = select(Quest).where(Quest.id == quest_progress.quest.next_quest_id)
        result = await db.execute(stmt)
        next_quest_obj = result.scalar_one_or_none()
        if next_quest_obj:
            next_quest = {
                "id": next_quest_obj.id,
                "title": next_quest_obj.title
            }

    return APIResponse(
        code=0,
        message="success",
        data={
            "quest_id": quest_id,
            "rewards_claimed": rewards_claimed,
            "next_quest": next_quest
        }
    )


@router.post("/{quest_id}/abandon", response_model=APIResponse)
async def abandon_quest(
    quest_id: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """放弃任务"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 获取任务进度
    stmt = select(QuestProgress).options(
        joinedload(QuestProgress.quest)
    ).where(
        and_(
            QuestProgress.player_id == player.id,
            QuestProgress.quest_id == quest_id
        )
    )
    result = await db.execute(stmt)
    quest_progress = result.scalar_one_or_none()

    if not quest_progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Quest not found"
        )

    # 主线任务不能放弃
    if quest_progress.quest.quest_type == "main":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot abandon main quests"
        )

    if quest_progress.status in ["claimed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot abandon claimed quests"
        )

    # 删除任务进度
    await db.delete(quest_progress)

    return APIResponse(
        code=0,
        message="success",
        data={
            "quest_id": quest_id,
            "abandoned": True
        }
    )
