"""
MindPal Backend V2 - Shop API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import joinedload
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Player, Item, InventoryItem, ShopItem
from app.schemas import APIResponse
from app.core.security import get_current_user_id

router = APIRouter()


class PurchaseRequest(BaseModel):
    """购买请求"""
    item_id: int  # ShopItem ID
    quantity: int = 1
    currency: str = "gold"  # gold | diamond


# 购买记录表（简化存储在内存，生产环境应该存数据库）
# 格式: {player_id: {date: {shop_item_id: count}}}
_purchase_records: dict = {}


def get_today_purchases(player_id: int, shop_item_id: int) -> int:
    """获取今日购买次数"""
    today = date.today().isoformat()
    return _purchase_records.get(player_id, {}).get(today, {}).get(shop_item_id, 0)


def record_purchase(player_id: int, shop_item_id: int, quantity: int):
    """记录购买"""
    today = date.today().isoformat()
    if player_id not in _purchase_records:
        _purchase_records[player_id] = {}
    if today not in _purchase_records[player_id]:
        _purchase_records[player_id][today] = {}
    if shop_item_id not in _purchase_records[player_id][today]:
        _purchase_records[player_id][today][shop_item_id] = 0
    _purchase_records[player_id][today][shop_item_id] += quantity


@router.get("/items", response_model=APIResponse)
async def get_shop_items(
    category: Optional[str] = Query(None, description="物品分类"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取商城商品列表

    - **category**: 可选，按分类过滤
    - **page**: 页码
    - **size**: 每页数量
    """
    # 获取玩家（用于计算购买次数）
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 查询商品
    now = datetime.utcnow()
    stmt = select(ShopItem).options(
        joinedload(ShopItem.item)
    ).where(
        ShopItem.is_active == True
    )

    # 过滤时间限制
    stmt = stmt.where(
        and_(
            (ShopItem.start_time == None) | (ShopItem.start_time <= now),
            (ShopItem.end_time == None) | (ShopItem.end_time >= now)
        )
    )

    # 按分类过滤
    if category:
        stmt = stmt.join(Item).where(Item.category == category)

    # 排序和分页
    stmt = stmt.order_by(ShopItem.sort_order, ShopItem.id)
    total_stmt = select(ShopItem).where(ShopItem.is_active == True)
    total_result = await db.execute(total_stmt)
    total = len(total_result.scalars().all())

    stmt = stmt.offset((page - 1) * size).limit(size)
    result = await db.execute(stmt)
    items = result.scalars().all()

    # 构建响应数据
    items_data = []
    for shop_item in items:
        item_dict = shop_item.to_dict()
        # 添加今日购买次数
        item_dict["purchased_today"] = get_today_purchases(player.id, shop_item.id)
        items_data.append(item_dict)

    return APIResponse(
        code=0,
        message="success",
        data={
            "items": items_data,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    )


@router.get("/items/{item_id}", response_model=APIResponse)
async def get_shop_item_detail(
    item_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取商品详情"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    # 查询商品
    stmt = select(ShopItem).options(
        joinedload(ShopItem.item)
    ).where(ShopItem.id == item_id)
    result = await db.execute(stmt)
    shop_item = result.scalar_one_or_none()

    if not shop_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop item not found"
        )

    item_dict = shop_item.to_dict()
    item_dict["purchased_today"] = get_today_purchases(player.id, shop_item.id)
    item_dict["actual_gold_price"] = shop_item.get_actual_price("gold")
    item_dict["actual_diamond_price"] = shop_item.get_actual_price("diamond")

    return APIResponse(
        code=0,
        message="success",
        data=item_dict
    )


@router.post("/purchase", response_model=APIResponse)
async def purchase_item(
    request: PurchaseRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    购买商品

    - **item_id**: 商城商品ID
    - **quantity**: 购买数量
    - **currency**: 支付货币 (gold / diamond)
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

    # 查询商品
    stmt = select(ShopItem).options(
        joinedload(ShopItem.item)
    ).where(ShopItem.id == request.item_id)
    result = await db.execute(stmt)
    shop_item = result.scalar_one_or_none()

    if not shop_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shop item not found"
        )

    if not shop_item.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item is not available"
        )

    # 检查时间限制
    now = datetime.utcnow()
    if shop_item.start_time and now < shop_item.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item is not yet available"
        )
    if shop_item.end_time and now > shop_item.end_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item is no longer available"
        )

    # 检查每日限购
    if shop_item.daily_limit:
        today_purchased = get_today_purchases(player.id, shop_item.id)
        if today_purchased + request.quantity > shop_item.daily_limit:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Daily limit exceeded. You can only buy {shop_item.daily_limit - today_purchased} more today."
            )

    # 计算价格
    if request.currency == "gold":
        unit_price = shop_item.get_actual_price("gold")
        if not unit_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This item cannot be purchased with gold"
            )
        total_price = unit_price * request.quantity
        if player.gold < total_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough gold. Need {total_price}, have {player.gold}"
            )
        player.gold -= total_price
    elif request.currency == "diamond":
        unit_price = shop_item.get_actual_price("diamond")
        if not unit_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This item cannot be purchased with diamonds"
            )
        total_price = unit_price * request.quantity
        if player.diamonds < total_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Not enough diamonds. Need {total_price}, have {player.diamonds}"
            )
        player.diamonds -= total_price
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid currency. Must be 'gold' or 'diamond'"
        )

    # 添加物品到背包
    item = shop_item.item

    # 查找是否已有该物品（可堆叠）
    existing_item = None
    if item.stackable:
        stmt = select(InventoryItem).where(
            and_(
                InventoryItem.player_id == player.id,
                InventoryItem.item_id == item.id
            )
        )
        result = await db.execute(stmt)
        existing_item = result.scalar_one_or_none()

    if existing_item:
        # 增加数量
        existing_item.quantity = min(existing_item.quantity + request.quantity, item.max_stack)
        slot = existing_item.slot
    else:
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
            # 退还货币
            if request.currency == "gold":
                player.gold += total_price
            else:
                player.diamonds += total_price
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inventory is full"
            )

        # 创建新物品
        new_inv_item = InventoryItem(
            player_id=player.id,
            item_id=item.id,
            slot=free_slot,
            quantity=request.quantity
        )
        db.add(new_inv_item)
        slot = free_slot

    # 记录购买
    record_purchase(player.id, shop_item.id, request.quantity)

    return APIResponse(
        code=0,
        message="success",
        data={
            "item_id": item.id,
            "item_name": item.name,
            "quantity": request.quantity,
            "total_cost": total_price,
            "currency": request.currency,
            "slot": slot,
            "balance": {
                "gold": player.gold,
                "diamonds": player.diamonds
            }
        }
    )


@router.get("/balance", response_model=APIResponse)
async def get_balance(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取玩家货币余额"""
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )

    return APIResponse(
        code=0,
        message="success",
        data={
            "gold": player.gold,
            "diamonds": player.diamonds
        }
    )
