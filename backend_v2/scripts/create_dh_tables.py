"""
创建数字人相关的数据库表
"""

import asyncio
import sys
sys.path.insert(0, '.')

from app.database import engine, Base
from app.models.digital_human import DigitalHuman, DHConversation, DHMessage


async def create_digital_human_tables():
    """创建数字人相关表"""
    async with engine.begin() as conn:
        # 只创建数字人相关的表
        await conn.run_sync(Base.metadata.create_all, tables=[
            DigitalHuman.__table__,
            DHConversation.__table__,
            DHMessage.__table__,
        ])
        print("[OK] Digital human tables created successfully!")
        print("   - digital_humans")
        print("   - dh_conversations")
        print("   - dh_messages")


if __name__ == "__main__":
    asyncio.run(create_digital_human_tables())
