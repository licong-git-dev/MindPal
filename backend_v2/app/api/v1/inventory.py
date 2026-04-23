"""
MindPal Backend V2 - Inventory API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Player, Item, InventoryItem
from app.schemas import APIResponse
from app.core.security import get_current_user_id

router = APIRouter()


class UseItemRequest(BaseModel):
    """使用物品请求"""
    slot: int
    quantity: int = 1


class MoveItemRequest(BaseModel):
    """移动物品请求"""
    from_slot: int
    to_slot: int


class DiscardItemRequest(BaseModel):
    """丢弃物品请求"""
    action: str = "discard"  # discard | decompose
    quantity: int = 1


@router.get("", response_model=APIResponse)
async def get_inventory(
    category: Optional[str] = Query(None, description="物品分类过滤"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取背包物品列表

    - **category**: 可选，按分类过滤 (consumable, equipment, material, key_item)
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

    # 查询背包物品
    stmt = select(InventoryItem).options(
        joinedload(InventoryItem.item)
    ).where(InventoryItem.player_id == player.id)

    # 按分类过滤
    if category:
        stmt = stmt.join(Item).where(Item.category == category)

    stmt = stmt.order_by(InventoryItem.slot)
    result = await db.execute(stmt)
    items = result.scalars().all()

    return APIResponse(
        code=0,
        message="success",
        data={
            "capacity": 48,  # 背包容量
            "used": len(items),
            "items": [item.to_dict() for item in items]
        }
    )


@router.get("/{slot}", response_model=APIResponse)
async def get_inventory_item(
    slot: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取指定格子的物品详情"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 查询物品
    stmt = select(InventoryItem).options(
        joinedload(InventoryItem.item)
    ).where(
        and_(
            InventoryItem.player_id == player.id,
            InventoryItem.slot == slot
        )
    )
    result = await db.execute(stmt)
    inv_item = result.scalar_one_or_none()

    if not inv_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in this slot"
        )

    return APIResponse(
        code=0,
        message="success",
        data=inv_item.to_dict()
    )


@router.post("/use", response_model=APIResponse)
async def use_item(
    request: UseItemRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    使用物品

    - **slot**: 背包格子位置
    - **quantity**: 使用数量
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

    # 查询物品
    stmt = select(InventoryItem).options(
        joinedload(InventoryItem.item)
    ).where(
        and_(
            InventoryItem.player_id == player.id,
            InventoryItem.slot == request.slot
        )
    )
    result = await db.execute(stmt)
    inv_item = result.scalar_one_or_none()

    if not inv_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in this slot"
        )

    if inv_item.quantity < request.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough items"
        )

    item = inv_item.item

    # 检查物品是否可使用
    if item.category != "consumable":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item cannot be used"
        )

    # 处理物品效果
    effect_result = {}
    if item.effects:
        effect_type = item.effects.get("type")
        effect_value = item.effects.get("value", 0)

        if effect_type == "heal":
            # 恢复生命值 (简化处理)
            effect_result = {
                "type": "heal",
                "value": effect_value * request.quantity
            }
        elif effect_type == "gold":
            player.gold += effect_value * request.quantity
            effect_result = {
                "type": "gold",
                "value": effect_value * request.quantity
            }
        elif effect_type == "exp":
            player.experience += effect_value * request.quantity
            effect_result = {
                "type": "exp",
                "value": effect_value * request.quantity
            }

    # 减少物品数量
    inv_item.quantity -= request.quantity

    # 如果数量为0，删除物品
    if inv_item.quantity <= 0:
        await db.delete(inv_item)

    return APIResponse(
        code=0,
        message="success",
        data={
            "item_id": item.id,
            "item_name": item.name,
            "quantity_used": request.quantity,
            "quantity_remaining": max(0, inv_item.quantity),
            "effect": effect_result
        }
    )


@router.put("/move", response_model=APIResponse)
async def move_item(
    request: MoveItemRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    移动物品到其他格子

    - **from_slot**: 原格子
    - **to_slot**: 目标格子
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

    # 验证格子范围
    if not (0 <= request.from_slot < 48 and 0 <= request.to_slot < 48):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid slot number (must be 0-47)"
        )

    # 查询源物品
    stmt = select(InventoryItem).where(
        and_(
            InventoryItem.player_id == player.id,
            InventoryItem.slot == request.from_slot
        )
    )
    result = await db.execute(stmt)
    from_item = result.scalar_one_or_none()

    if not from_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No item in source slot"
        )

    # 查询目标格子
    stmt = select(InventoryItem).where(
        and_(
            InventoryItem.player_id == player.id,
            InventoryItem.slot == request.to_slot
        )
    )
    result = await db.execute(stmt)
    to_item = result.scalar_one_or_none()

    if to_item:
        # 交换位置
        to_item.slot = request.from_slot

    from_item.slot = request.to_slot

    return APIResponse(
        code=0,
        message="success",
        data={
            "from_slot": request.from_slot,
            "to_slot": request.to_slot,
            "swapped": to_item is not None
        }
    )


@router.delete("/{slot}", response_model=APIResponse)
async def discard_item(
    slot: int,
    request: DiscardItemRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    丢弃或分解物品

    - **slot**: 背包格子位置
    - **action**: discard(丢弃) 或 decompose(分解)
    - **quantity**: 丢弃数量
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

    # 查询物品
    stmt = select(InventoryItem).options(
        joinedload(InventoryItem.item)
    ).where(
        and_(
            InventoryItem.player_id == player.id,
            InventoryItem.slot == slot
        )
    )
    result = await db.execute(stmt)
    inv_item = result.scalar_one_or_none()

    if not inv_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found in this slot"
        )

    if inv_item.quantity < request.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough items"
        )

    item = inv_item.item
    rewards = []

    if request.action == "decompose":
        # 分解获得材料（简化处理：按售价的10%返还金币）
        gold_reward = int(item.sell_price * request.quantity * 0.1)
        if gold_reward > 0:
            player.gold += gold_reward
            rewards.append({"type": "gold", "amount": gold_reward})
    elif request.action == "discard":
        # 直接丢弃
        pass
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Must be 'discard' or 'decompose'"
        )

    # 减少数量
    inv_item.quantity -= request.quantity
    if inv_item.quantity <= 0:
        await db.delete(inv_item)

    return APIResponse(
        code=0,
        message="success",
        data={
            "action": request.action,
            "item_id": item.id,
            "quantity_removed": request.quantity,
            "rewards": rewards
        }
    )


@router.post("/add", response_model=APIResponse)
async def add_item_to_inventory(
    item_id: str,
    quantity: int = 1,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    添加物品到背包 (内部/测试用)

    - **item_id**: 物品ID
    - **quantity**: 数量
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

    # 验证物品存在
    stmt = select(Item).where(Item.id == item_id)
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    # 查找是否已有该物品（可堆叠）
    if item.stackable:
        stmt = select(InventoryItem).where(
            and_(
                InventoryItem.player_id == player.id,
                InventoryItem.item_id == item_id
            )
        )
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            # 增加数量
            existing.quantity = min(existing.quantity + quantity, item.max_stack)
            return APIResponse(
                code=0,
                message="success",
                data={
                    "item_id": item_id,
                    "slot": existing.slot,
                    "quantity": existing.quantity,
                    "stacked": True
                }
            )

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

    if free_slot is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inventory is full"
        )

    # 创建新物品
    new_item = InventoryItem(
        player_id=player.id,
        item_id=item_id,
        slot=free_slot,
        quantity=quantity
    )
    db.add(new_item)

    return APIResponse(
        code=0,
        message="success",
        data={
            "item_id": item_id,
            "slot": free_slot,
            "quantity": quantity,
            "stacked": False
        }
    )
