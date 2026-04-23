"""
MindPal Backend V2 - 数据库初始化脚本
运行: python -m scripts.init_db
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import engine, Base, async_session_maker
from app.models import (
    User, Player, Item, ShopItem, Quest, Achievement
)
from app.models.payment import RechargeProduct, ProductType
from app.services.achievement_loader import seed_achievements


async def create_tables():
    """创建所有数据库表"""
    print("📦 Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created successfully")


async def seed_items():
    """初始化物品数据"""
    print("🎁 Seeding items...")

    items_data = [
        # 钥匙物品
        {"id": "key_courage", "name": "勇气之钥", "type": "key", "rarity": "legendary",
         "description": "镜中对话挑战的奖励，象征着直面自我的勇气", "is_tradable": False},
        {"id": "key_release", "name": "释然之钥", "type": "key", "rarity": "legendary",
         "description": "记忆迷宫挑战的奖励，象征着放下过去的释然", "is_tradable": False},
        {"id": "key_hope", "name": "希望之钥", "type": "key", "rarity": "legendary",
         "description": "未来建造挑战的奖励，象征着对未来的希望", "is_tradable": False},

        # 消耗品
        {"id": "potion_energy", "name": "活力药水", "type": "consumable", "rarity": "common",
         "description": "恢复50点体力", "is_tradable": True, "price": 100},
        {"id": "potion_mood", "name": "心情甜点", "type": "consumable", "rarity": "common",
         "description": "提升心情值20点", "is_tradable": True, "price": 150},
        {"id": "scroll_affinity", "name": "好感卷轴", "type": "consumable", "rarity": "rare",
         "description": "与NPC对话时好感度提升翻倍，持续10分钟", "is_tradable": True, "price": 500},

        # 装饰品
        {"id": "deco_flower_crown", "name": "花环头饰", "type": "decoration", "rarity": "rare",
         "description": "春日气息的可爱花环", "is_tradable": True, "price": 800},
        {"id": "deco_star_pendant", "name": "星光吊坠", "type": "decoration", "rarity": "epic",
         "description": "闪烁着神秘光芒的吊坠", "is_tradable": True, "price": 2000},

        # 礼物
        {"id": "gift_bei_ribbon", "name": "蝴蝶结发带", "type": "gift", "rarity": "rare",
         "description": "小贝最喜欢的礼物", "is_tradable": True, "price": 300,
         "extra_data": {"affinity_bonus": {"bei": 15}}},
        {"id": "gift_momo_gem", "name": "神秘宝石", "type": "gift", "rarity": "epic",
         "description": "莫莫收藏的稀有宝石", "is_tradable": True, "price": 1000,
         "extra_data": {"affinity_bonus": {"momo": 20}}},
    ]

    async with async_session_maker() as db:
        for item_data in items_data:
            # 检查是否已存在
            stmt = select(Item).where(Item.id == item_data["id"])
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                item = Item(**item_data)
                db.add(item)
                print(f"  + {item_data['name']}")

        await db.commit()

    print(f"✅ Seeded {len(items_data)} items")


async def seed_shop_items():
    """初始化商店物品"""
    print("🏪 Seeding shop items...")

    shop_items = [
        {"item_id": "potion_energy", "price": 100, "currency": "gold", "stock": -1, "category": "consumables"},
        {"item_id": "potion_mood", "price": 150, "currency": "gold", "stock": -1, "category": "consumables"},
        {"item_id": "scroll_affinity", "price": 500, "currency": "gold", "stock": 10, "category": "consumables"},
        {"item_id": "deco_flower_crown", "price": 80, "currency": "diamonds", "stock": 5, "category": "decorations"},
        {"item_id": "deco_star_pendant", "price": 200, "currency": "diamonds", "stock": 3, "category": "decorations"},
        {"item_id": "gift_bei_ribbon", "price": 300, "currency": "gold", "stock": -1, "category": "gifts"},
        {"item_id": "gift_momo_gem", "price": 100, "currency": "diamonds", "stock": 5, "category": "gifts"},
    ]

    async with async_session_maker() as db:
        for shop_data in shop_items:
            # 检查是否已存在
            stmt = select(ShopItem).where(ShopItem.item_id == shop_data["item_id"])
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                shop_item = ShopItem(**shop_data)
                db.add(shop_item)
                print(f"  + {shop_data['item_id']} in shop")

        await db.commit()

    print(f"✅ Seeded {len(shop_items)} shop items")


async def seed_quests():
    """初始化任务数据"""
    print("📜 Seeding quests...")

    quests_data = [
        # 主线任务
        {
            "id": "main_001",
            "title": "初入心境",
            "description": "欢迎来到MindPal世界！和向导艾拉对话，了解这个奇妙的地方。",
            "type": "main",
            "status": "available",
            "objectives": [
                {"id": "obj_1", "description": "与艾拉对话", "type": "dialogue", "target": "aela", "required": 1}
            ],
            "rewards": {"exp": 100, "gold": 200},
            "order_index": 1
        },
        {
            "id": "main_002",
            "title": "寻找小贝",
            "description": "艾拉说附近有一个活泼的小精灵叫小贝，去认识一下吧！",
            "type": "main",
            "status": "locked",
            "prerequisites": ["main_001"],
            "objectives": [
                {"id": "obj_1", "description": "找到并与小贝对话", "type": "dialogue", "target": "bei", "required": 1}
            ],
            "rewards": {"exp": 150, "gold": 300},
            "order_index": 2
        },
        {
            "id": "main_003",
            "title": "莫莫的商店",
            "description": "小贝推荐你去莫莫的奇异商店看看，据说那里有很多有趣的物品。",
            "type": "main",
            "status": "locked",
            "prerequisites": ["main_002"],
            "objectives": [
                {"id": "obj_1", "description": "访问莫莫的商店", "type": "dialogue", "target": "momo", "required": 1},
                {"id": "obj_2", "description": "购买任意物品", "type": "shop", "target": "any", "required": 1}
            ],
            "rewards": {"exp": 200, "gold": 500},
            "order_index": 3
        },

        # 每日任务
        {
            "id": "daily_chat",
            "title": "每日对话",
            "description": "和任意NPC对话3次",
            "type": "daily",
            "status": "available",
            "objectives": [
                {"id": "obj_1", "description": "与NPC对话", "type": "dialogue", "target": "any", "required": 3}
            ],
            "rewards": {"exp": 50, "gold": 100},
            "cooldown": 86400
        },
        {
            "id": "daily_explore",
            "title": "探索时光",
            "description": "在世界中探索5分钟",
            "type": "daily",
            "status": "available",
            "objectives": [
                {"id": "obj_1", "description": "在线探索", "type": "time", "target": "online", "required": 300}
            ],
            "rewards": {"exp": 30, "gold": 50},
            "cooldown": 86400
        },
    ]

    async with async_session_maker() as db:
        for quest_data in quests_data:
            # 检查是否已存在
            stmt = select(Quest).where(Quest.id == quest_data["id"])
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                quest = Quest(**quest_data)
                db.add(quest)
                print(f"  + {quest_data['title']}")

        await db.commit()

    print(f"✅ Seeded {len(quests_data)} quests")


async def seed_achievements_data():
    """初始化成就数据"""
    print("🏆 Seeding achievements...")
    async with async_session_maker() as db:
        count = await seed_achievements(db)
        await db.commit()
    print(f"✅ Seeded {count} achievements")


async def seed_recharge_products():
    """初始化充值商品"""
    print("💎 Seeding recharge products...")

    products_data = [
        # 钻石充值
        {
            "product_id": "diamond_60",
            "name": "60钻石",
            "description": "基础钻石包",
            "product_type": ProductType.DIAMONDS,
            "price": 6.0,
            "diamonds": 60,
            "bonus_diamonds": 0,
            "first_purchase_bonus": 60,
            "sort_order": 1
        },
        {
            "product_id": "diamond_300",
            "name": "300钻石",
            "description": "超值钻石包",
            "product_type": ProductType.DIAMONDS,
            "price": 30.0,
            "original_price": 30.0,
            "diamonds": 300,
            "bonus_diamonds": 30,
            "first_purchase_bonus": 300,
            "sort_order": 2
        },
        {
            "product_id": "diamond_680",
            "name": "680钻石",
            "description": "豪华钻石包",
            "product_type": ProductType.DIAMONDS,
            "price": 68.0,
            "original_price": 68.0,
            "diamonds": 680,
            "bonus_diamonds": 80,
            "first_purchase_bonus": 680,
            "sort_order": 3
        },
        {
            "product_id": "diamond_1280",
            "name": "1280钻石",
            "description": "至尊钻石包",
            "product_type": ProductType.DIAMONDS,
            "price": 128.0,
            "diamonds": 1280,
            "bonus_diamonds": 200,
            "first_purchase_bonus": 1280,
            "sort_order": 4
        },

        # VIP会员
        {
            "product_id": "vip_month",
            "name": "月卡会员",
            "description": "30天VIP特权，每日领取50钻石",
            "product_type": ProductType.VIP,
            "price": 30.0,
            "diamonds": 300,
            "vip_days": 30,
            "sort_order": 10
        },
        {
            "product_id": "vip_season",
            "name": "季卡会员",
            "description": "90天VIP特权，每日领取50钻石",
            "product_type": ProductType.VIP,
            "price": 68.0,
            "original_price": 90.0,
            "diamonds": 900,
            "vip_days": 90,
            "sort_order": 11
        },
        {
            "product_id": "vip_year",
            "name": "年卡会员",
            "description": "365天VIP特权，每日领取50钻石",
            "product_type": ProductType.VIP,
            "price": 198.0,
            "original_price": 360.0,
            "diamonds": 3650,
            "vip_days": 365,
            "sort_order": 12
        },

        # 体力包
        {
            "product_id": "energy_small",
            "name": "小体力包",
            "description": "恢复50点体力",
            "product_type": ProductType.ENERGY,
            "price": 6.0,
            "items": '{"energy": 50}',
            "sort_order": 20
        },
        {
            "product_id": "energy_large",
            "name": "大体力包",
            "description": "恢复满体力",
            "product_type": ProductType.ENERGY,
            "price": 12.0,
            "items": '{"energy": 200}',
            "sort_order": 21
        },
    ]

    async with async_session_maker() as db:
        for product_data in products_data:
            # 检查是否已存在
            stmt = select(RechargeProduct).where(
                RechargeProduct.product_id == product_data["product_id"]
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if not existing:
                product = RechargeProduct(**product_data)
                db.add(product)
                print(f"  + {product_data['name']}")

        await db.commit()

    print(f"✅ Seeded {len(products_data)} recharge products")


async def create_test_user():
    """创建测试用户"""
    print("👤 Creating test user...")

    async with async_session_maker() as db:
        # 检查是否已存在
        stmt = select(User).where(User.phone == "13800000000")
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if not existing:
            from app.core.security import get_password_hash

            user = User(
                phone="13800000000",
                password_hash=get_password_hash("test123456"),
                nickname="测试玩家"
            )
            db.add(user)
            await db.flush()

            # 创建角色
            player = Player(
                user_id=user.id,
                name="心灵旅者",
                gender="neutral",
                avatar="default_avatar",
                level=1,
                exp=0,
                gold=1000,
                diamonds=100,
                energy=100
            )
            db.add(player)
            await db.commit()

            print(f"  + User: 13800000000 / test123456")
            print(f"  + Player: 心灵旅者")
        else:
            print("  - Test user already exists")

    print("✅ Test user ready")


async def main():
    """主函数"""
    print("=" * 50)
    print("MindPal Backend V2 - Database Initialization")
    print("=" * 50)

    try:
        await create_tables()
        await seed_items()
        await seed_shop_items()
        await seed_quests()
        await seed_achievements_data()
        await seed_recharge_products()
        await create_test_user()

        print("=" * 50)
        print("🎉 Database initialization completed!")
        print("=" * 50)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
