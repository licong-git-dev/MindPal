"""
MindPal Backend V2 - Player API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.database import get_db
from app.models import Player, NPCAffinity
from app.schemas import (
    CreateCharacterRequest,
    UpdatePositionRequest,
    CreateCharacterResponse,
    PositionResponse,
    PositionSyncResponse,
    APIResponse,
)
from app.core.security import get_current_user_id
from app.config import settings

router = APIRouter()


@router.post("/character", response_model=APIResponse)
async def create_character(
    request: CreateCharacterRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    创建游戏角色

    - **nickname**: 角色昵称 (2-50字符)
    - **avatar_config**: 头像配置 (可选)
    """
    # 检查是否已有角色
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    existing_player = result.scalar_one_or_none()

    if existing_player:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Character already exists"
        )

    # 创建角色
    player = Player(
        user_id=user_id,
        nickname=request.nickname,
        level=1,
        experience=0,
        gold=settings.DEFAULT_GOLD,
        diamonds=settings.DEFAULT_DIAMONDS,
        current_zone="central_plaza",
        position_x=0.0,
        position_y=0.0,
        position_z=0.0,
        avatar_config=request.avatar_config.model_dump() if request.avatar_config else None,
        keys_collected=[],
    )
    db.add(player)
    await db.flush()

    # 初始化NPC好感度
    npc_ids = ["bei", "aela", "momo", "chronos", "sesame"]
    for npc_id in npc_ids:
        affinity = NPCAffinity(
            player_id=player.id,
            npc_id=npc_id,
            value=0,
        )
        db.add(affinity)

    return APIResponse(
        code=0,
        message="success",
        data=CreateCharacterResponse(
            player_id=player.id,
            nickname=player.nickname,
            level=player.level,
            gold=player.gold,
            diamonds=player.diamonds,
            current_zone=player.current_zone,
            position=PositionResponse(
                x=player.position_x,
                y=player.position_y,
                z=player.position_z
            )
        ).model_dump()
    )


@router.get("/character", response_model=APIResponse)
async def get_character(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取角色信息"""
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found. Please create one first."
        )

    return APIResponse(
        code=0,
        message="success",
        data={
            "player_id": player.id,
            "nickname": player.nickname,
            "level": player.level,
            "experience": player.experience,
            "exp_to_next_level": player.exp_to_next_level(),
            "gold": player.gold,
            "diamonds": player.diamonds,
            "current_zone": player.current_zone,
            "position": {
                "x": player.position_x,
                "y": player.position_y,
                "z": player.position_z
            },
            "avatar_config": player.avatar_config,
            "stats": {
                "total_playtime": player.total_playtime,
                "dialogues_count": player.dialogues_count,
                "keys_collected": player.keys_collected or [],
                "achievements_count": player.achievements_count,
            }
        }
    )


@router.put("/position", response_model=APIResponse)
async def update_position(
    request: UpdatePositionRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    更新角色位置

    - **zone**: 当前区域
    - **x, y, z**: 坐标
    - **rotation_y**: Y轴旋转角度
    """
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 更新位置
    player.current_zone = request.zone
    player.position_x = request.x
    player.position_y = request.y
    player.position_z = request.z
    player.rotation_y = request.rotation_y or 0.0
    player.last_online = datetime.utcnow()

    return APIResponse(
        code=0,
        message="success",
        data=PositionSyncResponse(synced=True).model_dump()
    )


@router.get("/inventory", response_model=APIResponse)
async def get_inventory(
    category: str = "all",
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取背包物品

    - **category**: 物品分类 (all, consumable, equipment, material, key_item)
    """
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 获取背包物品
    from app.models import InventoryItem, Item
    from sqlalchemy.orm import selectinload

    stmt = select(InventoryItem).where(
        InventoryItem.player_id == player.id
    ).options(selectinload(InventoryItem.item))

    if category != "all":
        stmt = stmt.join(Item).where(Item.category == category)

    stmt = stmt.order_by(InventoryItem.slot)
    result = await db.execute(stmt)
    inventory_items = result.scalars().all()

    return APIResponse(
        code=0,
        message="success",
        data={
            "capacity": settings.MAX_INVENTORY_SLOTS,
            "used": len(inventory_items),
            "items": [item.to_dict() for item in inventory_items]
        }
    )


@router.post("/inventory/use", response_model=APIResponse)
async def use_item(
    slot: int,
    quantity: int = 1,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    使用物品

    - **slot**: 背包槽位
    - **quantity**: 使用数量
    """
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 获取背包物品
    from app.models import InventoryItem
    from sqlalchemy.orm import selectinload

    stmt = select(InventoryItem).where(
        InventoryItem.player_id == player.id,
        InventoryItem.slot == slot
    ).options(selectinload(InventoryItem.item))

    result = await db.execute(stmt)
    inventory_item = result.scalar_one_or_none()

    if not inventory_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in slot"
        )

    if inventory_item.quantity < quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient quantity"
        )

    # 应用物品效果
    item = inventory_item.item
    effect = None

    if item.effects:
        effect = item.effects
        # TODO: 实际应用效果 (如回血、增益等)

    # 减少数量
    inventory_item.quantity -= quantity
    if inventory_item.quantity <= 0:
        await db.delete(inventory_item)

    return APIResponse(
        code=0,
        message="success",
        data={
            "item_id": item.id,
            "quantity_remaining": max(0, inventory_item.quantity),
            "effect": effect
        }
    )
