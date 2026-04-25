"""
为 ROI-7（主动消息）+ C2（CP 双人共养）创建数据库表。

运行（**生产/staging 环境，第一次部署 ROI-7 + CP 时**）:

    cd backend_v2
    python -m scripts.create_proactive_cp_tables

幂等：使用 SQLAlchemy create_all，已存在的表不会被重建/破坏数据。
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# 确保能 import app.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import engine, Base
from app.models.proactive import ProactiveMessage
from app.models.cp import CpInvitation, CpBond


TABLES = [
    ("proactive_messages", ProactiveMessage),
    ("cp_invitations",     CpInvitation),
    ("cp_bonds",           CpBond),
]


async def main() -> None:
    print("[migrate] starting create_proactive_cp_tables")
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[m.__table__ for _, m in TABLES],
        )
    for name, _ in TABLES:
        print(f"  ✓ {name}")
    print("[migrate] done")


if __name__ == "__main__":
    asyncio.run(main())
