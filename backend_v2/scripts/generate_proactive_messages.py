"""
MindPal Backend V2 - 主动消息批量生成脚本（cron / Celery beat 可直接调）

运行方式（建议每天一次，例：每天 10:00）:

    cd backend_v2
    python -m scripts.generate_proactive_messages

系统 cron 示例（每天 10 点）：
    0 10 * * * cd /opt/mindpal/backend_v2 && /opt/mindpal/venv/bin/python -m scripts.generate_proactive_messages >> /var/log/mindpal/proactive.log 2>&1

Celery beat 示例（使用 celery 的场景）：
    from celery.schedules import crontab
    app.conf.beat_schedule = {
        "generate-proactive-messages": {
            "task": "scripts.generate_proactive_messages.run",
            "schedule": crontab(hour=10, minute=0),
        },
    }

逻辑：
  1. 拉所有 is_active=True 的数字人
  2. 按 user_id 维度分组，每个用户**最多只生成 3 条**（避免打扰）
  3. 调 generator.generate()（遵循 idle 规则 + 去重）
  4. 批量写库

幂等安全：
  generator 会检查"已有未读未过期的主动消息"，不会重复生成。
  即使脚本一天跑两次也不会双倍发。
"""

from __future__ import annotations

import asyncio
import sys
from collections import defaultdict
from pathlib import Path
from typing import List

# 确保能导入 app.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models.digital_human import DigitalHuman
from app.models.proactive import ProactiveMessage  # noqa: F401  - 确保模型被注册
from app.services.proactive import get_proactive_generator


# 每个用户每天最多生成的主动消息数（避免打扰）
MAX_PER_USER_PER_DAY = 3


async def _run(session: AsyncSession) -> dict:
    generator = get_proactive_generator()

    stmt = (
        select(DigitalHuman)
        .where(DigitalHuman.is_active.is_(True))
        .order_by(DigitalHuman.user_id, DigitalHuman.id)
    )
    result = await session.execute(stmt)
    dhs: List[DigitalHuman] = list(result.scalars().all())

    per_user_count: dict = defaultdict(int)
    generated = 0
    skipped = 0

    for dh in dhs:
        if per_user_count[dh.user_id] >= MAX_PER_USER_PER_DAY:
            skipped += 1
            continue

        try:
            proactive = await generator.generate(session, dh)
        except Exception as exc:  # noqa: BLE001
            print(f"[WARN] generate failed for dh={dh.id}: {exc}")
            continue

        if proactive is None:
            skipped += 1
            continue

        session.add(proactive.to_model())
        per_user_count[dh.user_id] += 1
        generated += 1

        # 每 50 条落一次库，避免长事务
        if generated % 50 == 0:
            await session.commit()

    await session.commit()

    return {
        "total_dhs": len(dhs),
        "generated": generated,
        "skipped": skipped,
        "users_touched": len(per_user_count),
    }


async def main() -> None:
    async with async_session_maker() as session:
        stats = await _run(session)
    print(
        f"[proactive] done: total_dhs={stats['total_dhs']} "
        f"generated={stats['generated']} skipped={stats['skipped']} "
        f"users_touched={stats['users_touched']}"
    )


# Celery 风格的入口（可选）
def run() -> dict:
    return asyncio.run(_run_with_session())


async def _run_with_session() -> dict:
    async with async_session_maker() as session:
        return await _run(session)


if __name__ == "__main__":
    asyncio.run(main())
