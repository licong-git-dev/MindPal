"""
MindPal Backend V2 - Three Keys Challenge API
三钥匙挑战API端点
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
import json

from app.database import get_db
from app.models import Player
from app.schemas import APIResponse
from app.core.security import get_current_user_id

from app.services.three_keys import (
    KeyType,
    ChallengeStatus,
    get_three_keys_manager
)

router = APIRouter()


# ==================== Schemas ====================

class ChallengeResponseRequest(BaseModel):
    """挑战回答请求"""
    key_type: str = Field(..., description="钥匙类型: courage/release/hope")
    stage: int = Field(..., ge=1, le=3, description="阶段 1-3")
    response: str = Field(..., min_length=10, max_length=2000, description="用户回答")


class ChallengeStartRequest(BaseModel):
    """开始挑战请求"""
    key_type: str = Field(..., description="钥匙类型: courage/release/hope")


# ==================== Helper ====================

async def get_player(user_id: int, db: AsyncSession) -> Player:
    """获取玩家"""
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    return player


def get_challenge_progress(player: Player, key_type: KeyType) -> dict:
    """从玩家extra_data获取挑战进度"""
    extra_data = player.extra_data or {}
    challenges = extra_data.get("three_keys", {})
    return challenges.get(key_type.value, {
        "status": ChallengeStatus.AVAILABLE.value,
        "current_stage": 0,
        "responses": []
    })


async def save_challenge_progress(
    player: Player,
    key_type: KeyType,
    progress: dict,
    db: AsyncSession
):
    """保存挑战进度到玩家extra_data"""
    if player.extra_data is None:
        player.extra_data = {}

    if "three_keys" not in player.extra_data:
        player.extra_data["three_keys"] = {}

    player.extra_data["three_keys"][key_type.value] = progress

    # SQLAlchemy需要检测到变化
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(player, "extra_data")


# ==================== Endpoints ====================

@router.get("/status", response_model=APIResponse)
async def get_challenge_status(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取三钥匙挑战状态

    返回玩家在三个挑战中的进度
    """
    player = await get_player(user_id, db)
    manager = get_three_keys_manager()

    status_data = {}
    completed_count = 0

    for key_type in KeyType:
        progress = get_challenge_progress(player, key_type)
        total_stages = manager.get_total_stages(key_type)

        status_data[key_type.value] = {
            "name": {
                KeyType.COURAGE: "勇气之钥 - 镜中对话",
                KeyType.RELEASE: "释然之钥 - 记忆迷宫",
                KeyType.HOPE: "希望之钥 - 未来建造"
            }[key_type],
            "status": progress.get("status", ChallengeStatus.AVAILABLE.value),
            "current_stage": progress.get("current_stage", 0),
            "total_stages": total_stages,
            "started_at": progress.get("started_at"),
            "completed_at": progress.get("completed_at")
        }

        if progress.get("status") == ChallengeStatus.COMPLETED.value:
            completed_count += 1

    return APIResponse(
        code=0,
        message="success",
        data={
            "challenges": status_data,
            "completed_count": completed_count,
            "all_completed": completed_count == 3,
            "can_enter_sanctuary": completed_count == 3
        }
    )


@router.post("/start", response_model=APIResponse)
async def start_challenge(
    request: ChallengeStartRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    开始一个挑战

    返回第一阶段的提示
    """
    player = await get_player(user_id, db)
    manager = get_three_keys_manager()

    # 验证钥匙类型
    try:
        key_type = KeyType(request.key_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid key type. Must be: courage, release, or hope"
        )

    # 检查当前状态
    progress = get_challenge_progress(player, key_type)
    current_status = progress.get("status", ChallengeStatus.AVAILABLE.value)

    if current_status == ChallengeStatus.COMPLETED.value:
        return APIResponse(
            code=0,
            message="Challenge already completed",
            data={
                "key_type": key_type.value,
                "status": "completed",
                "completed_at": progress.get("completed_at")
            }
        )

    # 开始挑战
    stage_data = manager.get_stage_prompt(key_type, 1)

    progress = {
        "status": ChallengeStatus.IN_PROGRESS.value,
        "current_stage": 1,
        "started_at": datetime.utcnow().isoformat(),
        "responses": []
    }

    await save_challenge_progress(player, key_type, progress, db)
    await db.commit()

    return APIResponse(
        code=0,
        message="Challenge started",
        data={
            "key_type": key_type.value,
            "stage": 1,
            "total_stages": manager.get_total_stages(key_type),
            "title": stage_data["title"],
            "prompt": stage_data["prompt"]
        }
    )


@router.post("/respond", response_model=APIResponse)
async def submit_response(
    request: ChallengeResponseRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    提交挑战回答

    评估回答并返回下一阶段或完成结果
    """
    player = await get_player(user_id, db)
    manager = get_three_keys_manager()

    # 验证钥匙类型
    try:
        key_type = KeyType(request.key_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid key type"
        )

    # 检查当前状态
    progress = get_challenge_progress(player, key_type)
    current_status = progress.get("status", ChallengeStatus.AVAILABLE.value)

    if current_status != ChallengeStatus.IN_PROGRESS.value:
        raise HTTPException(
            status_code=400,
            detail="Challenge not in progress. Start the challenge first."
        )

    current_stage = progress.get("current_stage", 0)
    if request.stage != current_stage:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stage. Current stage is {current_stage}"
        )

    # 保存回答
    responses = progress.get("responses", [])
    responses.append({
        "stage": request.stage,
        "response": request.response,
        "submitted_at": datetime.utcnow().isoformat()
    })

    total_stages = manager.get_total_stages(key_type)

    # 检查是否完成所有阶段
    if request.stage >= total_stages:
        # 挑战完成
        progress["status"] = ChallengeStatus.COMPLETED.value
        progress["current_stage"] = total_stages
        progress["completed_at"] = datetime.utcnow().isoformat()
        progress["responses"] = responses

        await save_challenge_progress(player, key_type, progress, db)

        # 触发成就
        achievement_id = {
            KeyType.COURAGE: "story_courage_key",
            KeyType.RELEASE: "story_release_key",
            KeyType.HOPE: "story_hope_key"
        }[key_type]

        # TODO: 调用成就系统解锁成就

        await db.commit()

        return APIResponse(
            code=0,
            message="Challenge completed!",
            data={
                "key_type": key_type.value,
                "completed": True,
                "completion_message": manager.get_completion_message(key_type),
                "achievement_unlocked": achievement_id
            }
        )
    else:
        # 进入下一阶段
        next_stage = request.stage + 1
        next_stage_data = manager.get_stage_prompt(key_type, next_stage)

        progress["current_stage"] = next_stage
        progress["responses"] = responses

        await save_challenge_progress(player, key_type, progress, db)
        await db.commit()

        return APIResponse(
            code=0,
            message="Response recorded",
            data={
                "key_type": key_type.value,
                "stage": next_stage,
                "total_stages": total_stages,
                "title": next_stage_data["title"],
                "prompt": next_stage_data["prompt"]
            }
        )


@router.get("/prompt/{key_type}/{stage}", response_model=APIResponse)
async def get_stage_prompt(
    key_type: str,
    stage: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取指定阶段的提示

    用于重新获取当前阶段的问题
    """
    player = await get_player(user_id, db)
    manager = get_three_keys_manager()

    # 验证钥匙类型
    try:
        kt = KeyType(key_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid key type"
        )

    # 检查进度
    progress = get_challenge_progress(player, kt)
    current_status = progress.get("status", ChallengeStatus.AVAILABLE.value)
    current_stage = progress.get("current_stage", 0)

    if current_status != ChallengeStatus.IN_PROGRESS.value:
        raise HTTPException(
            status_code=400,
            detail="Challenge not in progress"
        )

    if stage != current_stage:
        raise HTTPException(
            status_code=400,
            detail=f"Can only get prompt for current stage ({current_stage})"
        )

    stage_data = manager.get_stage_prompt(kt, stage)
    if not stage_data:
        raise HTTPException(
            status_code=404,
            detail="Stage not found"
        )

    return APIResponse(
        code=0,
        message="success",
        data={
            "key_type": key_type,
            "stage": stage,
            "total_stages": manager.get_total_stages(kt),
            "title": stage_data["title"],
            "prompt": stage_data["prompt"]
        }
    )


@router.get("/history/{key_type}", response_model=APIResponse)
async def get_challenge_history(
    key_type: str,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取挑战历史记录

    返回玩家在该挑战中的所有回答
    """
    player = await get_player(user_id, db)

    # 验证钥匙类型
    try:
        kt = KeyType(key_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid key type"
        )

    progress = get_challenge_progress(player, kt)

    if progress.get("status") == ChallengeStatus.AVAILABLE.value:
        return APIResponse(
            code=0,
            message="Challenge not started",
            data={
                "key_type": key_type,
                "status": "not_started",
                "responses": []
            }
        )

    return APIResponse(
        code=0,
        message="success",
        data={
            "key_type": key_type,
            "status": progress.get("status"),
            "started_at": progress.get("started_at"),
            "completed_at": progress.get("completed_at"),
            "responses": progress.get("responses", [])
        }
    )
