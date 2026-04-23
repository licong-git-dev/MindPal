"""
MindPal Backend V2 - Inventory & Item Models
"""

from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Float, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Item(Base):
    """物品定义表 (静态配置)"""
    __tablename__ = "items"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # 物品ID，如 potion_hp_small
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 分类
    category: Mapped[str] = mapped_column(String(50))  # consumable, equipment, material, key_item
    sub_category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rarity: Mapped[str] = mapped_column(String(20), default="common")  # common, rare, epic, legendary

    # 属性
    stackable: Mapped[bool] = mapped_column(Boolean, default=True)
    max_stack: Mapped[int] = mapped_column(Integer, default=99)
    sellable: Mapped[bool] = mapped_column(Boolean, default=True)
    sell_price: Mapped[int] = mapped_column(Integer, default=0)

    # 效果 (JSON)
    effects: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # 示例: {"type": "heal", "value": 50} 或 {"type": "buff", "stat": "speed", "value": 10, "duration": 300}

    # 资源
    icon: Mapped[str | None] = mapped_column(String(255), nullable=True)
    model_3d: Mapped[str | None] = mapped_column(String(255), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "sub_category": self.sub_category,
            "rarity": self.rarity,
            "stackable": self.stackable,
            "max_stack": self.max_stack,
            "sellable": self.sellable,
            "sell_price": self.sell_price,
            "effects": self.effects,
            "icon": self.icon,
        }


class InventoryItem(Base):
    """玩家背包物品表"""
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"))

    # 背包位置
    slot: Mapped[int] = mapped_column(Integer)

    # 数量
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    # 装备状态
    is_equipped: Mapped[bool] = mapped_column(Boolean, default=False)
    equipment_slot: Mapped[str | None] = mapped_column(String(50), nullable=True)  # head, body, weapon, etc.

    # 自定义属性 (强化等级、附魔等)
    custom_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 时间戳
    obtained_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    player = relationship("Player", back_populates="inventory_items")
    item = relationship("Item")

    def to_dict(self) -> dict:
        item_data = self.item.to_dict() if self.item else {}
        return {
            "slot": self.slot,
            "item_id": self.item_id,
            "quantity": self.quantity,
            "is_equipped": self.is_equipped,
            "equipment_slot": self.equipment_slot,
            "custom_data": self.custom_data,
            "obtained_at": self.obtained_at.isoformat() if self.obtained_at else None,
            **item_data
        }


class ShopItem(Base):
    """商店商品表"""
    __tablename__ = "shop_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    item_id: Mapped[str] = mapped_column(ForeignKey("items.id"))

    # 价格
    gold_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    diamond_price: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 限购
    daily_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 上架状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    start_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 折扣
    discount_percent: Mapped[int] = mapped_column(Integer, default=0)  # 0-100

    # 排序
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # 关系
    item = relationship("Item")

    def get_actual_price(self, currency: str = "gold") -> int:
        """获取实际价格（考虑折扣）"""
        if currency == "gold" and self.gold_price:
            return int(self.gold_price * (100 - self.discount_percent) / 100)
        elif currency == "diamond" and self.diamond_price:
            return int(self.diamond_price * (100 - self.discount_percent) / 100)
        return 0

    def to_dict(self) -> dict:
        item_data = self.item.to_dict() if self.item else {}
        return {
            "id": self.id,
            "item_id": self.item_id,
            "gold_price": self.gold_price,
            "diamond_price": self.diamond_price,
            "daily_limit": self.daily_limit,
            "discount_percent": self.discount_percent,
            "is_active": self.is_active,
            **item_data
        }
