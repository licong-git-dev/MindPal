"""
MindPal Backend V2 - 会员产品种子脚本

运行方式（不启服务，仅对数据库插入记录）:

    cd backend_v2
    python -m scripts.seed_products

这会在 recharge_products 表中插入/更新以下会员套餐:

  - member_monthly: 会员月付（¥19.9/月）
  - member_yearly:  会员年付（¥199/年，原价 ¥239）
  - svip_monthly:   SVIP 月付（¥39.9/月，预留，暂不上线）

前端 pricing.html 的 subscribePlan() 会按 product_id 创建订单。

本脚本是**幂等**的：重复运行会更新价格/描述但不产生重复记录。
"""

import asyncio
import sys
from pathlib import Path

# 确保能导入 app.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import engine, async_session_maker, Base
from app.models.payment import RechargeProduct, ProductType


# ProductType 当前只有 DIAMONDS / VIP / ITEM_PACK / ENERGY。
# 所有会员套餐都用 ProductType.VIP，通过 product_id 区分月/年。
PRODUCTS = [
    {
        "product_id": "member_monthly",
        "name": "会员月付",
        "description": "无限对话 + 长期记忆 + 202 种方言 + 3D 形象，按月续订",
        "product_type": ProductType.VIP,
        "price": 19.9,
        "original_price": 29.9,
        "is_active": 1,
        "sort_order": 10,
    },
    {
        "product_id": "member_yearly",
        "name": "会员年付",
        "description": "年付立省 ¥40，包含月付全部权益",
        "product_type": ProductType.VIP,
        "price": 199.0,
        "original_price": 239.0,
        "is_active": 1,
        "sort_order": 20,
    },
    {
        "product_id": "svip_monthly",
        "name": "SVIP 月付（预留）",
        "description": "在会员基础上解锁角色剧情、卡池抽卡、纪念日主动联系",
        "product_type": ProductType.VIP,
        "price": 39.9,
        "original_price": 49.9,
        "is_active": 0,  # 暂时下线，等 F 方向落地
        "sort_order": 30,
    },
]


async def upsert_product(session: AsyncSession, spec: dict) -> str:
    """幂等插入/更新单个产品。返回 created/updated 标签。"""
    stmt = select(RechargeProduct).where(
        RechargeProduct.product_id == spec["product_id"]
    )
    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing is None:
        product = RechargeProduct(**spec)
        session.add(product)
        return "created"
    else:
        for key, value in spec.items():
            setattr(existing, key, value)
        return "updated"


async def main():
    # 确保表已创建
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_maker() as session:
        for spec in PRODUCTS:
            action = await upsert_product(session, spec)
            print(f"  [{action}] {spec['product_id']} — {spec['name']} (¥{spec['price']})")
        await session.commit()

    print("\n✓ seed complete. 产品数量:", len(PRODUCTS))


if __name__ == "__main__":
    asyncio.run(main())
