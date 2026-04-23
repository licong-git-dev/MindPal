"""
MindPal Backend V2 - API V1 Package
"""

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.player import router as player_router
from app.api.v1.dialogue import router as dialogue_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.shop import router as shop_router
from app.api.v1.quest import router as quest_router
from app.api.v1.social import router as social_router
from app.api.v1.chat import router as chat_router
from app.api.v1.party import router as party_router
from app.api.v1.achievement import router as achievement_router
from app.api.v1.leaderboard import router as leaderboard_router
from app.api.v1.memory import router as memory_router
from app.api.v1.ai_service import router as ai_service_router
from app.api.v1.three_keys import router as three_keys_router
from app.api.v1.voice import router as voice_router
from app.api.v1.payment import router as payment_router
from app.api.v1.ws import router as ws_router
from app.api.v1.digital_humans import router as digital_humans_router
from app.api.v1.analytics import router as analytics_router

# 创建根路由
api_router = APIRouter()

# 注册子路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(player_router, prefix="/player", tags=["角色"])
api_router.include_router(dialogue_router, prefix="/dialogue", tags=["对话"])
api_router.include_router(inventory_router, prefix="/inventory", tags=["背包"])
api_router.include_router(shop_router, prefix="/shop", tags=["商城"])
api_router.include_router(quest_router, prefix="/quests", tags=["任务"])
api_router.include_router(social_router, prefix="/social", tags=["社交"])
api_router.include_router(chat_router, prefix="/chat", tags=["聊天"])
api_router.include_router(party_router, prefix="/party", tags=["队伍"])
api_router.include_router(achievement_router, prefix="/achievements", tags=["成就"])
api_router.include_router(leaderboard_router, prefix="/leaderboard", tags=["排行榜"])
api_router.include_router(memory_router, prefix="/memory", tags=["记忆"])
api_router.include_router(ai_service_router, prefix="/ai", tags=["AI服务"])
api_router.include_router(three_keys_router, prefix="/three-keys", tags=["三钥匙挑战"])
api_router.include_router(voice_router, prefix="/voice", tags=["语音"])
api_router.include_router(payment_router, prefix="/payment", tags=["支付"])
api_router.include_router(ws_router, tags=["WebSocket"])
api_router.include_router(digital_humans_router, prefix="/digital-humans", tags=["数字人"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["埋点分析"])


__all__ = ["api_router"]
