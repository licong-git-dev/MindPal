"""
MindPal Backend V2 - AI Service API
AI服务管理API端点
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.database import get_db
from app.models.player import Player
from app.core.security import get_current_user_id
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.emotion import EmotionAnalyzer, get_emotion_analyzer
from app.services.crisis import CrisisDetector, CrisisHandler, get_crisis_detector, get_crisis_handler
from app.services.ai import LLMRouter, get_llm_router, get_health_checker, get_cost_tracker


router = APIRouter()


# ==================== Helper ====================

async def get_player_from_user_id(user_id: int, db: AsyncSession) -> Player:
    """从user_id获取Player"""
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Character not found"
        )
    return player


# ==================== Schemas ====================

class EmotionAnalyzeRequest(BaseModel):
    """情感分析请求"""
    text: str = Field(..., min_length=1, max_length=2000)


class EmotionAnalyzeResponse(BaseModel):
    """情感分析响应"""
    dominant: str
    scores: dict
    intensity: float
    needs_comfort: bool
    is_positive: bool
    crisis_risk: bool


class CrisisCheckRequest(BaseModel):
    """危机检查请求"""
    text: str = Field(..., min_length=1, max_length=2000)
    context: Optional[list] = None


class QuotaCheckRequest(BaseModel):
    """配额检查请求"""
    estimated_tokens: int = Field(0, ge=0)


# ==================== Emotion Endpoints ====================

@router.post("/emotion/analyze")
async def analyze_emotion(
    request: EmotionAnalyzeRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    分析文本情感

    使用关键词检测和规则分析文本的情感倾向
    """
    _ = await get_player_from_user_id(user_id, db)  # 验证用户身份
    analyzer = get_emotion_analyzer()
    result = analyzer.analyze(request.text)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "dominant": result.dominant.value,
            "scores": result.scores,
            "intensity": round(result.intensity, 2),
            "needs_comfort": result.needs_comfort,
            "is_positive": result.is_positive,
            "crisis_risk": result.crisis_risk,
            "keywords_matched": result.keywords_matched[:10]  # 限制返回数量
        }
    }


@router.post("/emotion/instruction")
async def get_emotion_instruction(
    request: EmotionAnalyzeRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取情感回应指导

    根据情感分析结果生成NPC回应的指导prompt
    """
    _ = await get_player_from_user_id(user_id, db)  # 验证用户身份
    analyzer = get_emotion_analyzer()
    result = analyzer.analyze(request.text)
    instruction = analyzer.get_response_instruction(result)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "emotion": result.dominant.value,
            "intensity": round(result.intensity, 2),
            "instruction": instruction
        }
    }


# ==================== Crisis Endpoints ====================

@router.post("/crisis/check")
async def check_crisis(
    request: CrisisCheckRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    检查危机信号

    分析文本中的心理危机信号并返回风险评估
    """
    _ = await get_player_from_user_id(user_id, db)  # 验证用户身份
    detector = get_crisis_detector()
    result = detector.detect(request.text, request.context)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "level": result.level.value,
            "score": round(result.score, 2),
            "triggers": result.triggers[:5],  # 限制返回数量
            "needs_intervention": result.needs_intervention,
            "needs_escalation": result.needs_escalation,
            "recommended_action": result.recommended_action,
            "safe_response_required": result.safe_response_required
        }
    }


@router.post("/crisis/handle")
async def handle_crisis(
    request: CrisisCheckRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    处理危机情况

    记录危机事件并返回安全响应指导
    """
    player = await get_player_from_user_id(user_id, db)
    handler = get_crisis_handler(db)
    response = await handler.handle_crisis(
        player_id=player.id,
        message=request.text,
        context=request.context
    )

    return {
        "code": 0,
        "message": "success",
        "data": {
            "event_id": response.event_id,
            "safe_prompt": response.safe_prompt[:2000] if response.safe_prompt else "",
            "resources": response.resources,
            "should_notify_admin": response.should_notify_admin,
            "response_template": response.response_template
        }
    }


# ==================== LLM Router Endpoints ====================

@router.get("/llm/status")
async def get_llm_status(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取LLM服务状态

    返回所有LLM服务的健康状态和路由配置
    """
    _ = await get_player_from_user_id(user_id, db)  # 验证用户身份
    llm_router = get_llm_router()
    status = llm_router.get_routing_status()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "models": status["models"],
            "health": status["health"]
        }
    }


@router.get("/llm/health")
async def get_health_status(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取服务健康状态

    返回各LLM服务的详细健康指标
    """
    _ = await get_player_from_user_id(user_id, db)  # 验证用户身份
    checker = get_health_checker()
    status = checker.get_all_status()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "services": status
        }
    }


@router.post("/llm/select")
async def select_model(
    npc_id: str,
    is_crisis: bool = False,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    选择最佳模型

    根据NPC和场景选择最佳的LLM模型
    """
    _ = await get_player_from_user_id(user_id, db)  # 验证用户身份
    llm_router = get_llm_router()
    model_name, config = llm_router.select_model(npc_id, is_crisis)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "selected_model": model_name,
            "provider": config.provider,
            "tier": config.tier.value,
            "max_tokens": config.max_tokens,
            "temperature": config.default_temperature
        }
    }


# ==================== Cost Endpoints ====================

@router.get("/cost/usage")
async def get_usage(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取使用统计

    返回当前玩家的AI服务使用情况
    """
    player = await get_player_from_user_id(user_id, db)
    tracker = get_cost_tracker()
    usage = tracker.get_player_usage(player.id)

    return {
        "code": 0,
        "message": "success",
        "data": usage
    }


@router.post("/cost/check-quota")
async def check_quota(
    request: QuotaCheckRequest,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    检查配额

    检查玩家是否有足够的配额进行AI对话
    """
    player = await get_player_from_user_id(user_id, db)
    tracker = get_cost_tracker()
    quota = tracker.check_quota(player.id, request.estimated_tokens)

    return {
        "code": 0,
        "message": "success",
        "data": quota
    }


@router.get("/cost/daily-report")
async def get_daily_report(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取每日报告

    返回今日的AI服务使用报告
    """
    _ = await get_player_from_user_id(user_id, db)  # 验证用户身份
    tracker = get_cost_tracker()
    report = tracker.get_daily_report()

    return {
        "code": 0,
        "message": "success",
        "data": report
    }


@router.get("/cost/service-stats")
async def get_service_stats(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取服务统计

    返回各AI服务的使用统计
    """
    _ = await get_player_from_user_id(user_id, db)  # 验证用户身份
    tracker = get_cost_tracker()
    stats = tracker.get_service_stats()

    return {
        "code": 0,
        "message": "success",
        "data": stats
    }
