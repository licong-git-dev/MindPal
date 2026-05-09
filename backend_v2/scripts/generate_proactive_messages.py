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
     - 每个 DH 失败重试 3 次（0.5s / 2s / 8s 指数退避）
     - 重试都失败 → 写死信日志，继续下一个 DH（**不让单点故障影响整体跑批**）
  4. 批量写库（每 50 条提交一次）

幂等安全：
  generator 会检查"已有未读未过期的主动消息"，不会重复生成。
  即使脚本一天跑两次也不会双倍发。

死信日志（F3）:
  - 重试都失败的 DH 会被记录到 PROACTIVE_DEADLETTER_LOG
    （默认 /var/log/mindpal/proactive_deadletter.log；
     env 覆盖：MINDPAL_DEADLETTER_LOG=/path/to.log）
  - 每行格式：ISO_TIMESTAMP | dh_id={id} user_id={uid} | error={class}: {msg}
    后跟缩进的 traceback 行
  - 运维通过 grep 这个文件就能拿到所有"漏发"的清单
"""

from __future__ import annotations

import asyncio
import os
import sys
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

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

# 单 DH 重试参数
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (0.5, 2.0, 8.0)  # 第 1/2/3 次重试前的等待

# 死信日志路径（env 可覆盖）
DEADLETTER_LOG = os.environ.get(
    "MINDPAL_DEADLETTER_LOG",
    "/var/log/mindpal/proactive_deadletter.log",
)


def _write_deadletter(dh: DigitalHuman, exc: BaseException) -> None:
    """把彻底失败的 DH 写到死信日志。"""
    line = (
        f"{datetime.utcnow().isoformat()}Z | "
        f"dh_id={getattr(dh, 'id', '?')} user_id={getattr(dh, 'user_id', '?')} | "
        f"error={type(exc).__name__}: {exc}\n"
    )
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    body = "".join("    " + ln for ln in tb)
    try:
        Path(DEADLETTER_LOG).parent.mkdir(parents=True, exist_ok=True)
        with open(DEADLETTER_LOG, "a", encoding="utf-8") as f:
            f.write(line)
            f.write(body)
            f.write("\n")
    except Exception as log_exc:  # noqa: BLE001
        # 死信都写不出去（磁盘满 / 权限问题）→ 退化到 stderr
        print(
            f"[DEADLETTER-WRITE-FAILED] {log_exc} (original: {line.strip()})",
            file=sys.stderr,
        )


async def _generate_with_retry(
    session: AsyncSession, dh: DigitalHuman
) -> Optional[object]:
    """
    带重试的单 DH 生成。返回值：
      - GeneratedProactive 对象 → 成功，调用方写库
      - None → generator 主动判断"无需生成"（idle 不足 / 已有未读 等），不算失败
      - 抛异常 → MAX_ATTEMPTS 次都失败，调用方负责吃掉并写死信
    """
    generator = get_proactive_generator()
    last_exc: Optional[BaseException] = None
    for attempt in range(MAX_ATTEMPTS):
        try:
            return await generator.generate(session, dh)
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            if attempt < MAX_ATTEMPTS - 1:
                wait = BACKOFF_SECONDS[attempt]
                print(
                    f"[RETRY] dh={dh.id} attempt {attempt + 1}/{MAX_ATTEMPTS} "
                    f"failed: {type(exc).__name__}: {exc} → 等 {wait}s 重试",
                    file=sys.stderr,
                )
                await asyncio.sleep(wait)
            # 不要回滚整 session — 让其它 DH 已添加的 add() 还能 commit
    # 走到这里 = MAX_ATTEMPTS 全失败
    assert last_exc is not None
    raise last_exc


async def _run(session: AsyncSession) -> dict:
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
    failed = 0
    failed_dh_ids: List[int] = []

    for dh in dhs:
        if per_user_count[dh.user_id] >= MAX_PER_USER_PER_DAY:
            skipped += 1
            continue

        try:
            proactive = await _generate_with_retry(session, dh)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            failed_dh_ids.append(dh.id)
            _write_deadletter(dh, exc)
            print(
                f"[FAIL] dh={dh.id}: {type(exc).__name__}: {exc} → 写死信，继续下一个",
                file=sys.stderr,
            )
            continue

        if proactive is None:
            skipped += 1
            continue

        session.add(proactive.to_model())
        per_user_count[dh.user_id] += 1
        generated += 1

        # 每 50 条落一次库，避免长事务
        if generated % 50 == 0:
            try:
                await session.commit()
            except Exception as exc:  # noqa: BLE001
                # 批量提交失败：回滚 + 把这一批整体记到死信，但脚本继续
                await session.rollback()
                print(
                    f"[BATCH-COMMIT-FAIL] {type(exc).__name__}: {exc} → rolled back, 继续",
                    file=sys.stderr,
                )

    try:
        await session.commit()
    except Exception as exc:  # noqa: BLE001
        await session.rollback()
        print(
            f"[FINAL-COMMIT-FAIL] {type(exc).__name__}: {exc} → 全量回滚",
            file=sys.stderr,
        )
        # 整批失败也算一次 fatal failure（不抛，让 wrapper 决定 exit code）
        failed += 1

    return {
        "total_dhs": len(dhs),
        "generated": generated,
        "skipped": skipped,
        "failed": failed,
        "failed_dh_ids": failed_dh_ids,
        "users_touched": len(per_user_count),
    }


async def main() -> int:
    """主入口。返回 exit code（0=全部 OK，1=有死信）。"""
    async with async_session_maker() as session:
        stats = await _run(session)
    print(
        f"[proactive] done: total_dhs={stats['total_dhs']} "
        f"generated={stats['generated']} skipped={stats['skipped']} "
        f"failed={stats['failed']} users_touched={stats['users_touched']}"
    )
    if stats.get("failed_dh_ids"):
        print(
            f"[proactive] failed dh ids (deadlettered): "
            f"{stats['failed_dh_ids']}; see {DEADLETTER_LOG}",
            file=sys.stderr,
        )
    return 0 if stats.get("failed", 0) == 0 else 1


# Celery 风格的入口（可选）
def run() -> dict:
    return asyncio.run(_run_with_session())


async def _run_with_session() -> dict:
    async with async_session_maker() as session:
        return await _run(session)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
