"""
MindPal Backend V2 - API V1 Package

当前激活的路由仅为 AI 数字人陪伴主链路。游戏化模块（player/quest/
inventory/shop/party/achievement/leaderboard/three_keys/ws/社交聊天）
是历史方向摇摆的遗留，不再对外暴露。

相关决策背景见:
  docs/roadmap/DEEP_AUDIT_V3.md  §"架构重债"
  docs/roadmap/PRODUCT_STRATEGY_V3.md  §"不做清单"
"""

from fastapi import APIRouter

# ==================== 激活的核心路由（AI 陪伴主链路） ====================
from app.api.v1.auth import router as auth_router
from app.api.v1.voice import router as voice_router
from app.api.v1.payment import router as payment_router
from app.api.v1.digital_humans import router as digital_humans_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.account import router as account_router
from app.api.v1.report import router as report_router
from app.api.v1.verification import router as verification_router
from app.api.v1.proactive import router as proactive_router

# ==================== 已禁用的游戏化路由（代码文件保留在 api/v1/ 供将来参考） ====================
# player_router        / prefix="/player"        角色 CRUD
# dialogue_router      / prefix="/dialogue"      NPC 对话（已被 digital_humans 替代）
# inventory_router     / prefix="/inventory"     背包
# shop_router          / prefix="/shop"          商城
# quest_router         / prefix="/quests"        任务
# social_router        / prefix="/social"        游戏社交
# chat_router          / prefix="/chat"          玩家多人聊天 WebSocket
# party_router         / prefix="/party"         队伍
# achievement_router   / prefix="/achievements"  成就
# leaderboard_router   / prefix="/leaderboard"   排行榜
# memory_router        / prefix="/memory"        老版 Player-based 记忆
#                                                （已被 /digital-humans/{id}/memories 替代）
# ai_service_router    / prefix="/ai"            AI 服务管理（与 LLM 路由耦合）
# three_keys_router    / prefix="/three-keys"    三钥匙挑战
# ws_router            /                         WebSocket（游戏 chat 依赖）

# 创建根路由
api_router = APIRouter()

# 注册核心子路由（仅 AI 陪伴链路）
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(digital_humans_router, prefix="/digital-humans", tags=["数字人"])
api_router.include_router(voice_router, prefix="/voice", tags=["语音"])
api_router.include_router(payment_router, prefix="/payment", tags=["支付"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["埋点分析"])
api_router.include_router(account_router, prefix="/account", tags=["账户数据权利"])
api_router.include_router(report_router, prefix="/reports", tags=["投诉举报"])
api_router.include_router(verification_router, prefix="/verification", tags=["实名认证"])
api_router.include_router(proactive_router, prefix="/proactive", tags=["主动消息"])


__all__ = ["api_router"]
