"""
MindPal Backend V2 - Conversation Memory Manager
对话记忆管理器 - 整合短期记忆(Redis)、长期记忆(DB)和语义记忆(向量库)
"""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.models.dialogue import DialogueSession, DialogueMessage
from app.models.player import Player
from app.services.memory.retriever import MemoryRetriever, RetrievedMemory, get_memory_retriever


@dataclass
class PlayerProfile:
    """玩家档案"""
    player_id: int
    nickname: str
    communication_style: str = "友好"
    interests: List[str] = None
    recent_topics: List[str] = None
    emotion_history: List[Dict[str, Any]] = None
    preferences: Dict[str, Any] = None

    def __post_init__(self):
        if self.interests is None:
            self.interests = []
        if self.recent_topics is None:
            self.recent_topics = []
        if self.emotion_history is None:
            self.emotion_history = []
        if self.preferences is None:
            self.preferences = {}


class ConversationMemory:
    """对话记忆管理系统"""

    def __init__(
        self,
        db: AsyncSession,
        retriever: Optional[MemoryRetriever] = None
    ):
        self.db = db
        self.retriever = retriever or get_memory_retriever()
        self._profile_cache: Dict[int, PlayerProfile] = {}

    async def get_recent_messages(
        self,
        player_id: int,
        npc_id: str,
        session_id: Optional[int] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取最近的对话消息（短期记忆）"""
        query = select(DialogueMessage).where(
            DialogueMessage.player_id == player_id,
            DialogueMessage.npc_id == npc_id
        )

        if session_id:
            query = query.where(DialogueMessage.session_id == session_id)

        query = query.order_by(desc(DialogueMessage.created_at)).limit(limit)

        result = await self.db.execute(query)
        messages = result.scalars().all()

        # 转换为字典列表，按时间正序
        return [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "emotion": msg.emotion,
                "created_at": msg.created_at.isoformat()
            }
            for msg in reversed(messages)
        ]

    async def get_relevant_memories(
        self,
        player_id: int,
        npc_id: str,
        query: str,
        limit: int = 5
    ) -> List[RetrievedMemory]:
        """获取语义相关的记忆（长期记忆）"""
        return await self.retriever.retrieve_relevant(
            player_id=player_id,
            npc_id=npc_id,
            query=query,
            limit=limit
        )

    async def save_dialogue(
        self,
        player_id: int,
        npc_id: str,
        user_message: str,
        npc_response: str,
        session_id: int,
        user_emotion: Optional[str] = None,
        npc_emotion: Optional[str] = None,
        importance: float = 0.5
    ):
        """保存对话并存入向量库"""
        # 1. 保存用户消息到数据库
        user_msg = DialogueMessage(
            session_id=session_id,
            player_id=player_id,
            npc_id=npc_id,
            role="user",
            content=user_message,
            emotion=user_emotion
        )
        self.db.add(user_msg)

        # 2. 保存NPC回复到数据库
        npc_msg = DialogueMessage(
            session_id=session_id,
            player_id=player_id,
            npc_id=npc_id,
            role="assistant",
            content=npc_response,
            emotion=npc_emotion
        )
        self.db.add(npc_msg)

        await self.db.commit()

        # 3. 存入向量库（仅存储重要或有情感的对话）
        if importance > 0.3 or user_emotion or len(user_message) > 50:
            await self.retriever.store_memory(
                player_id=player_id,
                npc_id=npc_id,
                user_message=user_message,
                npc_response=npc_response,
                emotion=user_emotion,
                importance=importance,
                session_id=session_id
            )

    async def get_player_profile(self, player_id: int) -> PlayerProfile:
        """获取玩家档案"""
        # 检查缓存
        if player_id in self._profile_cache:
            return self._profile_cache[player_id]

        # 从数据库获取玩家信息
        result = await self.db.execute(
            select(Player).where(Player.id == player_id)
        )
        player = result.scalar_one_or_none()

        if not player:
            return PlayerProfile(player_id=player_id, nickname="旅行者")

        # 分析对话历史获取兴趣和话题
        interests, topics = await self._analyze_player_interests(player_id)

        # 获取情感历史
        emotion_history = await self._get_emotion_history(player_id)

        profile = PlayerProfile(
            player_id=player_id,
            nickname=player.nickname,
            interests=interests,
            recent_topics=topics,
            emotion_history=emotion_history
        )

        # 缓存
        self._profile_cache[player_id] = profile
        return profile

    async def update_player_profile(
        self,
        player_id: int,
        recent_emotion: Optional[str] = None,
        recent_topic: Optional[str] = None
    ):
        """更新玩家档案"""
        profile = await self.get_player_profile(player_id)

        if recent_emotion:
            profile.emotion_history.append({
                "emotion": recent_emotion,
                "timestamp": datetime.utcnow().isoformat()
            })
            # 保留最近50条
            profile.emotion_history = profile.emotion_history[-50:]

        if recent_topic and recent_topic not in profile.recent_topics:
            profile.recent_topics.append(recent_topic)
            # 保留最近10个话题
            profile.recent_topics = profile.recent_topics[-10:]

        # 更新缓存
        self._profile_cache[player_id] = profile

    async def build_full_context(
        self,
        player_id: int,
        npc_id: str,
        current_message: str,
        session_id: Optional[int] = None,
        recent_limit: int = 10,
        memory_limit: int = 5
    ) -> Dict[str, Any]:
        """构建完整的对话上下文"""
        # 1. 获取最近消息
        recent_messages = await self.get_recent_messages(
            player_id=player_id,
            npc_id=npc_id,
            session_id=session_id,
            limit=recent_limit
        )

        # 2. 获取相关记忆
        relevant_memories = await self.get_relevant_memories(
            player_id=player_id,
            npc_id=npc_id,
            query=current_message,
            limit=memory_limit
        )

        # 3. 获取玩家档案
        player_profile = await self.get_player_profile(player_id)

        # 4. 构建上下文
        context = {
            "recent_messages": recent_messages,
            "relevant_memories": [
                {
                    "summary": mem.summary,
                    "emotion": mem.emotion,
                    "relevance": mem.relevance_score
                }
                for mem in relevant_memories
            ],
            "player_profile": {
                "nickname": player_profile.nickname,
                "interests": player_profile.interests,
                "recent_topics": player_profile.recent_topics,
                "recent_emotions": [
                    e["emotion"] for e in player_profile.emotion_history[-5:]
                ]
            }
        }

        return context

    async def build_context_prompt(
        self,
        player_id: int,
        npc_id: str,
        current_message: str,
        session_id: Optional[int] = None
    ) -> str:
        """构建注入到system prompt的上下文文本"""
        context = await self.build_full_context(
            player_id=player_id,
            npc_id=npc_id,
            current_message=current_message,
            session_id=session_id
        )

        parts = []

        # 玩家信息
        profile = context["player_profile"]
        parts.append(f"""## 玩家信息
- 昵称: {profile['nickname']}
- 兴趣: {', '.join(profile['interests']) or '未知'}
- 近期话题: {', '.join(profile['recent_topics']) or '无'}
- 近期情绪: {', '.join(profile['recent_emotions']) or '平静'}""")

        # 相关记忆
        if context["relevant_memories"]:
            memory_lines = []
            for mem in context["relevant_memories"]:
                emotion_tag = f"[{mem['emotion']}]" if mem.get('emotion') else ""
                memory_lines.append(f"- {emotion_tag} {mem['summary']}")
            parts.append(f"""## 相关历史记忆
{chr(10).join(memory_lines)}""")

        return "\n\n".join(parts)

    async def _analyze_player_interests(self, player_id: int) -> tuple:
        """分析玩家兴趣和话题"""
        # 简化实现：返回空列表
        # 实际可以分析历史对话提取关键词
        return [], []

    async def _get_emotion_history(self, player_id: int) -> List[Dict]:
        """获取情感历史"""
        # 查询最近的对话情感
        result = await self.db.execute(
            select(DialogueMessage.emotion, DialogueMessage.created_at)
            .where(
                DialogueMessage.player_id == player_id,
                DialogueMessage.role == "user",
                DialogueMessage.emotion.isnot(None)
            )
            .order_by(desc(DialogueMessage.created_at))
            .limit(50)
        )

        rows = result.all()
        return [
            {"emotion": row.emotion, "timestamp": row.created_at.isoformat()}
            for row in rows
        ]

    async def get_session_summary(
        self,
        session_id: int
    ) -> Dict[str, Any]:
        """获取会话摘要"""
        result = await self.db.execute(
            select(DialogueMessage)
            .where(DialogueMessage.session_id == session_id)
            .order_by(DialogueMessage.created_at)
        )
        messages = result.scalars().all()

        if not messages:
            return {"message_count": 0, "duration": 0, "emotions": []}

        emotions = [m.emotion for m in messages if m.emotion]
        duration = (messages[-1].created_at - messages[0].created_at).total_seconds()

        return {
            "message_count": len(messages),
            "duration_seconds": duration,
            "emotions": list(set(emotions)),
            "dominant_emotion": max(set(emotions), key=emotions.count) if emotions else None,
            "start_time": messages[0].created_at.isoformat(),
            "end_time": messages[-1].created_at.isoformat()
        }

    def clear_cache(self, player_id: Optional[int] = None):
        """清除缓存"""
        if player_id:
            self._profile_cache.pop(player_id, None)
        else:
            self._profile_cache.clear()
