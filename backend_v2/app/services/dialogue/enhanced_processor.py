"""
MindPal Backend V2 - Enhanced Dialogue Processor
集成情感分析、危机干预、记忆检索的增强对话处理器
"""

from typing import Optional, Dict, Any, List, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime

from app.services.emotion import get_emotion_analyzer, EmotionResult
from app.services.crisis import get_crisis_detector, get_crisis_handler, CrisisResult
from app.services.memory import get_memory_retriever, ConversationMemory
from app.services.ai import get_llm_router, get_cost_tracker


@dataclass
class DialogueContext:
    """对话上下文"""
    player_id: int
    npc_id: str
    session_id: str
    player_name: str
    affinity_value: int = 0
    message: str = ""

    # 分析结果
    emotion_result: Optional[EmotionResult] = None
    crisis_result: Optional[CrisisResult] = None

    # 记忆上下文
    relevant_memories: List[Dict] = None
    recent_messages: List[Dict] = None
    player_profile: Dict = None

    # 系统提示
    base_system_prompt: str = ""
    enhanced_system_prompt: str = ""

    # 模型选择
    selected_model: str = ""
    is_crisis_mode: bool = False


class EnhancedDialogueProcessor:
    """增强型对话处理器"""

    def __init__(self, db_session=None):
        self.db = db_session
        self.emotion_analyzer = get_emotion_analyzer()
        self.crisis_detector = get_crisis_detector()
        self.memory_retriever = get_memory_retriever()
        self.llm_router = get_llm_router()
        self.cost_tracker = get_cost_tracker()

        if db_session:
            self.crisis_handler = get_crisis_handler(db_session)
            self.memory_manager = ConversationMemory(db_session)
        else:
            self.crisis_handler = None
            self.memory_manager = None

    async def process_message(
        self,
        player_id: int,
        npc_id: str,
        session_id: str,
        message: str,
        player_name: str = "玩家",
        affinity_value: int = 0,
        base_system_prompt: str = "",
        history_messages: List[Dict] = None
    ) -> DialogueContext:
        """
        处理用户消息，执行完整的预处理流程

        Returns:
            DialogueContext: 包含所有分析结果的上下文对象
        """
        context = DialogueContext(
            player_id=player_id,
            npc_id=npc_id,
            session_id=session_id,
            player_name=player_name,
            affinity_value=affinity_value,
            message=message,
            base_system_prompt=base_system_prompt,
            recent_messages=history_messages or []
        )

        # 1. 情感分析
        context.emotion_result = self.emotion_analyzer.analyze(message)

        # 2. 危机检测
        context.crisis_result = self.crisis_detector.detect(
            message,
            context=[msg.get("content", "") for msg in (history_messages or [])[-5:]]
        )

        # 3. 判断是否进入危机模式
        context.is_crisis_mode = (
            context.crisis_result.needs_intervention or
            context.emotion_result.crisis_risk
        )

        # 4. 检索相关记忆
        try:
            memories = await self.memory_retriever.retrieve_relevant(
                player_id=player_id,
                npc_id=npc_id,
                query=message,
                limit=5
            )
            context.relevant_memories = [
                {
                    "summary": mem.summary,
                    "emotion": mem.emotion,
                    "relevance": mem.relevance_score
                }
                for mem in memories
            ]
        except Exception:
            context.relevant_memories = []

        # 5. 获取玩家档案
        if self.memory_manager:
            try:
                profile = await self.memory_manager.get_player_profile(player_id)
                context.player_profile = {
                    "nickname": profile.nickname,
                    "interests": profile.interests,
                    "communication_style": profile.communication_style,
                    "recent_topics": profile.recent_topics
                }
            except Exception:
                context.player_profile = {}

        # 6. 选择最佳模型
        model_name, model_config = self.llm_router.select_model(
            npc_id=npc_id,
            is_crisis=context.is_crisis_mode
        )
        context.selected_model = model_name

        # 7. 构建增强的系统提示
        context.enhanced_system_prompt = self._build_enhanced_prompt(context)

        return context

    def _build_enhanced_prompt(self, context: DialogueContext) -> str:
        """构建增强的系统提示词"""
        parts = [context.base_system_prompt]

        # 添加情感响应指导
        if context.emotion_result:
            emotion_instruction = self.emotion_analyzer.get_response_instruction(
                context.emotion_result
            )
            parts.append(f"\n\n【当前用户情感状态】\n{emotion_instruction}")

        # 添加危机处理指导
        if context.is_crisis_mode and context.crisis_result:
            parts.append(f"\n\n【重要安全提示】\n{context.crisis_result.recommended_action}")
            if context.crisis_result.safe_response_required:
                parts.append("\n请确保回复温暖、支持性，并在适当时提供专业帮助资源。")

        # 添加记忆上下文
        if context.relevant_memories:
            memory_text = "\n".join([
                f"- {mem['summary']}"
                for mem in context.relevant_memories[:3]
            ])
            parts.append(f"\n\n【相关历史记忆】\n{memory_text}")

        # 添加玩家偏好
        if context.player_profile:
            profile = context.player_profile
            if profile.get("interests"):
                parts.append(f"\n\n【玩家兴趣】{', '.join(profile['interests'][:5])}")
            if profile.get("communication_style"):
                parts.append(f"【沟通风格】{profile['communication_style']}")

        return "\n".join(parts)

    async def handle_crisis_if_needed(
        self,
        context: DialogueContext
    ) -> Optional[Dict[str, Any]]:
        """
        如果检测到危机，进行处理

        Returns:
            如果是危机情况返回处理结果，否则返回None
        """
        if not context.is_crisis_mode or not self.crisis_handler:
            return None

        response = await self.crisis_handler.handle_crisis(
            player_id=context.player_id,
            message=context.message,
            context=[msg.get("content", "") for msg in context.recent_messages[-5:]]
        )

        return {
            "event_id": response.event_id,
            "safe_prompt": response.safe_prompt,
            "resources": response.resources,
            "should_notify_admin": response.should_notify_admin,
            "response_template": response.response_template
        }

    async def store_conversation_memory(
        self,
        context: DialogueContext,
        npc_response: str
    ) -> Optional[str]:
        """
        存储对话记忆

        Returns:
            memory_id 或 None
        """
        try:
            importance = 0.5

            # 根据情感强度调整重要性
            if context.emotion_result:
                importance += context.emotion_result.intensity * 0.3

            # 危机对话更重要
            if context.is_crisis_mode:
                importance = min(1.0, importance + 0.3)

            memory_id = await self.memory_retriever.store_memory(
                player_id=context.player_id,
                npc_id=context.npc_id,
                user_message=context.message,
                npc_response=npc_response,
                emotion=context.emotion_result.dominant.value if context.emotion_result else None,
                importance=importance
            )

            return memory_id
        except Exception:
            return None

    def record_usage(
        self,
        context: DialogueContext,
        input_tokens: int,
        output_tokens: int
    ) -> Dict[str, Any]:
        """记录使用量"""
        return self.cost_tracker.record_usage(
            player_id=context.player_id,
            service=context.selected_model,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )

    def check_quota(
        self,
        player_id: int,
        estimated_tokens: int = 0
    ) -> Dict[str, Any]:
        """检查配额"""
        return self.cost_tracker.check_quota(player_id, estimated_tokens)

    async def generate_response(
        self,
        context: DialogueContext,
        messages: List[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """
        生成AI回复（流式）

        Yields:
            回复文本片段
        """
        # 使用LLM路由器生成回复
        async for chunk in self.llm_router.route_request(
            npc_id=context.npc_id,
            messages=messages,
            system_prompt=context.enhanced_system_prompt,
            is_crisis=context.is_crisis_mode,
            max_retries=3
        ):
            yield chunk

    def get_response_metadata(
        self,
        context: DialogueContext
    ) -> Dict[str, Any]:
        """获取响应元数据"""
        return {
            "emotion": {
                "dominant": context.emotion_result.dominant.value if context.emotion_result else "neutral",
                "intensity": round(context.emotion_result.intensity, 2) if context.emotion_result else 0,
                "needs_comfort": context.emotion_result.needs_comfort if context.emotion_result else False
            },
            "crisis": {
                "detected": context.is_crisis_mode,
                "level": context.crisis_result.level.value if context.crisis_result else "none",
                "intervention_needed": context.crisis_result.needs_intervention if context.crisis_result else False
            },
            "model": context.selected_model,
            "memories_used": len(context.relevant_memories) if context.relevant_memories else 0
        }


# 工厂函数
def get_enhanced_processor(db_session=None) -> EnhancedDialogueProcessor:
    """获取增强对话处理器实例"""
    return EnhancedDialogueProcessor(db_session)
