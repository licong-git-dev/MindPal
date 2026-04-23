"""
MindPal Backend V2 - LLM Router Service
根据场景选择最佳LLM服务
"""

from typing import Dict, Optional
from enum import Enum

from app.services.llm.base import BaseLLMService
from app.services.llm.qwen import QwenService
from app.services.llm.claude import ClaudeService
from app.config import settings


class LLMScene(Enum):
    """LLM使用场景"""
    GENERAL = "general"          # 通用对话
    EMOTIONAL = "emotional"      # 情感对话（需要共情）
    CRISIS = "crisis"            # 危机干预（需要专业处理）
    GUIDE = "guide"              # 引导对话（任务/教程）
    MERCHANT = "merchant"        # 商人对话（交易相关）


class LLMRouter:
    """
    LLM路由器

    根据对话场景和NPC类型选择最合适的LLM服务：
    - 情感对话/危机干预 → Claude（更强的共情能力）
    - 通用对话/引导 → Qwen（成本更低，响应更快）
    """

    def __init__(self):
        self._qwen: Optional[QwenService] = None
        self._claude: Optional[ClaudeService] = None

        # NPC到场景的默认映射
        self.npc_scene_map: Dict[str, LLMScene] = {
            "bei": LLMScene.EMOTIONAL,      # 小北 - 情感陪伴
            "aela": LLMScene.GUIDE,         # 艾拉 - 引导者
            "momo": LLMScene.MERCHANT,      # 莫莫 - 商人
            "chronos": LLMScene.GUIDE,      # 克洛诺斯 - 任务引导
            "sesame": LLMScene.GENERAL,     # 芝麻 - 宠物伙伴
        }

    @property
    def qwen(self) -> QwenService:
        """懒加载Qwen服务"""
        if self._qwen is None:
            self._qwen = QwenService()
        return self._qwen

    @property
    def claude(self) -> ClaudeService:
        """懒加载Claude服务"""
        if self._claude is None:
            self._claude = ClaudeService()
        return self._claude

    def get_service(
        self,
        scene: Optional[LLMScene] = None,
        npc_id: Optional[str] = None,
        force_provider: Optional[str] = None,
    ) -> BaseLLMService:
        """
        获取LLM服务

        Args:
            scene: 对话场景
            npc_id: NPC ID（用于推断场景）
            force_provider: 强制使用指定服务商 ("qwen" | "claude")

        Returns:
            LLM服务实例
        """
        # 强制使用指定服务商
        if force_provider:
            if force_provider == "claude":
                return self.claude
            return self.qwen

        # 根据NPC推断场景
        if scene is None and npc_id:
            scene = self.npc_scene_map.get(npc_id, LLMScene.GENERAL)

        # 根据场景选择服务
        if scene in [LLMScene.EMOTIONAL, LLMScene.CRISIS]:
            # 情感对话和危机干预使用Claude
            if settings.ANTHROPIC_API_KEY:
                return self.claude
            # Claude不可用时降级到Qwen
            return self.qwen

        # 其他场景使用Qwen（成本更低）
        if settings.DASHSCOPE_API_KEY:
            return self.qwen

        # Qwen不可用时尝试Claude
        if settings.ANTHROPIC_API_KEY:
            return self.claude

        # 都不可用，返回Qwen（会返回错误提示）
        return self.qwen

    def get_service_for_npc(self, npc_id: str) -> BaseLLMService:
        """根据NPC获取推荐的LLM服务"""
        return self.get_service(npc_id=npc_id)


# 全局单例
_llm_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    """获取LLM路由器单例"""
    global _llm_router
    if _llm_router is None:
        _llm_router = LLMRouter()
    return _llm_router
