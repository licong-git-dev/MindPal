"""
MindPal Backend V2 - Memory Retriever
记忆检索器 - 语义搜索和上下文构建
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass

from app.services.memory.embedding import EmbeddingService, get_embedding_service
from app.services.memory.vector_store import VectorStore, VectorDocument, SearchResult, get_vector_store


@dataclass
class MemoryItem:
    """记忆项"""
    id: str
    player_id: int
    npc_id: str
    content: str
    summary: str
    emotion: Optional[str] = None
    importance: float = 0.5
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class RetrievedMemory:
    """检索到的记忆"""
    id: str
    content: str
    summary: str
    relevance_score: float
    emotion: Optional[str]
    created_at: datetime
    metadata: Dict[str, Any]


class MemoryRetriever:
    """记忆检索器"""

    def __init__(
        self,
        embedding_service: Optional[EmbeddingService] = None,
        vector_store: Optional[VectorStore] = None
    ):
        self.embedding = embedding_service or get_embedding_service()
        self.store = vector_store or get_vector_store()

    async def store_memory(
        self,
        player_id: int,
        npc_id: str,
        user_message: str,
        npc_response: str,
        emotion: Optional[str] = None,
        importance: float = 0.5,
        session_id: Optional[int] = None
    ) -> str:
        """存储对话记忆"""
        # 生成记忆摘要
        summary = await self._generate_summary(user_message, npc_response)

        # 组合用于embedding的文本
        combined_text = f"用户: {user_message}\nNPC: {npc_response}"

        # 生成向量
        vector = await self.embedding.encode(summary)

        # 创建文档
        doc_id = f"mem_{player_id}_{npc_id}_{uuid.uuid4().hex[:8]}"
        doc = VectorDocument(
            id=doc_id,
            text=combined_text,
            vector=vector,
            metadata={
                "player_id": player_id,
                "npc_id": npc_id,
                "summary": summary,
                "emotion": emotion,
                "importance": importance,
                "session_id": session_id,
                "user_message": user_message[:500],  # 截断防止过长
                "npc_response": npc_response[:500]
            }
        )

        # 存储
        await self.store.add(doc)
        return doc_id

    async def retrieve_relevant(
        self,
        player_id: int,
        npc_id: str,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.3
    ) -> List[RetrievedMemory]:
        """检索相关记忆"""
        # 生成查询向量
        query_vector = await self.embedding.encode(query)

        # 搜索
        results = await self.store.search(
            query_vector=query_vector,
            limit=limit,
            filter_metadata={"player_id": player_id, "npc_id": npc_id},
            score_threshold=score_threshold
        )

        # 转换结果
        memories = []
        for result in results:
            memories.append(RetrievedMemory(
                id=result.id,
                content=result.text,
                summary=result.metadata.get("summary", ""),
                relevance_score=result.score,
                emotion=result.metadata.get("emotion"),
                created_at=datetime.fromisoformat(result.metadata.get("created_at", datetime.utcnow().isoformat())),
                metadata=result.metadata
            ))

        return memories

    async def retrieve_by_emotion(
        self,
        player_id: int,
        npc_id: str,
        emotion: str,
        limit: int = 3
    ) -> List[RetrievedMemory]:
        """按情感检索记忆"""
        # 使用情感作为查询
        emotion_queries = {
            "sadness": "悲伤、难过、失落、伤心的对话",
            "joy": "开心、快乐、高兴、欣喜的对话",
            "anger": "生气、愤怒、烦躁的对话",
            "fear": "害怕、担心、焦虑、恐惧的对话",
            "surprise": "惊讶、意外、震惊的对话"
        }

        query = emotion_queries.get(emotion, f"{emotion}情绪的对话")
        query_vector = await self.embedding.encode(query)

        results = await self.store.search(
            query_vector=query_vector,
            limit=limit * 2,  # 多搜索一些以便过滤
            filter_metadata={"player_id": player_id, "npc_id": npc_id},
            score_threshold=0.2
        )

        # 优先返回相同情感的记忆
        same_emotion = [r for r in results if r.metadata.get("emotion") == emotion]
        other_emotion = [r for r in results if r.metadata.get("emotion") != emotion]

        selected = same_emotion[:limit]
        if len(selected) < limit:
            selected.extend(other_emotion[:limit - len(selected)])

        memories = []
        for result in selected:
            memories.append(RetrievedMemory(
                id=result.id,
                content=result.text,
                summary=result.metadata.get("summary", ""),
                relevance_score=result.score,
                emotion=result.metadata.get("emotion"),
                created_at=datetime.fromisoformat(result.metadata.get("created_at", datetime.utcnow().isoformat())),
                metadata=result.metadata
            ))

        return memories

    async def retrieve_recent(
        self,
        player_id: int,
        npc_id: str,
        limit: int = 10
    ) -> List[RetrievedMemory]:
        """检索最近的记忆"""
        # 使用通用查询获取记忆
        query_vector = await self.embedding.encode("最近的对话记忆")

        results = await self.store.search(
            query_vector=query_vector,
            limit=limit * 2,
            filter_metadata={"player_id": player_id, "npc_id": npc_id},
            score_threshold=0.0
        )

        # 按创建时间排序
        results.sort(
            key=lambda r: r.metadata.get("created_at", ""),
            reverse=True
        )

        memories = []
        for result in results[:limit]:
            memories.append(RetrievedMemory(
                id=result.id,
                content=result.text,
                summary=result.metadata.get("summary", ""),
                relevance_score=result.score,
                emotion=result.metadata.get("emotion"),
                created_at=datetime.fromisoformat(result.metadata.get("created_at", datetime.utcnow().isoformat())),
                metadata=result.metadata
            ))

        return memories

    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        return await self.store.delete(memory_id)

    async def get_memory_count(self, player_id: int, npc_id: str) -> int:
        """获取记忆数量"""
        # 简化实现：返回总数
        return await self.store.count()

    async def build_context(
        self,
        player_id: int,
        npc_id: str,
        current_query: str,
        max_memories: int = 5
    ) -> str:
        """构建记忆上下文（用于注入到prompt中）"""
        memories = await self.retrieve_relevant(
            player_id=player_id,
            npc_id=npc_id,
            query=current_query,
            limit=max_memories,
            score_threshold=0.3
        )

        if not memories:
            return ""

        context_parts = ["## 相关历史记忆"]
        for i, mem in enumerate(memories, 1):
            context_parts.append(
                f"{i}. [{mem.emotion or '中性'}] {mem.summary} (相关度: {mem.relevance_score:.1%})"
            )

        return "\n".join(context_parts)

    async def _generate_summary(self, user_message: str, npc_response: str) -> str:
        """生成对话摘要"""
        # 简单实现：截取关键内容
        # 实际生产可以调用LLM生成更好的摘要

        # 提取用户消息的关键部分
        user_part = user_message[:100].replace("\n", " ").strip()
        if len(user_message) > 100:
            user_part += "..."

        # 提取NPC回复的关键部分
        npc_part = npc_response[:100].replace("\n", " ").strip()
        if len(npc_response) > 100:
            npc_part += "..."

        return f"用户说「{user_part}」，NPC回应「{npc_part}」"


# 便捷函数
_retriever: Optional[MemoryRetriever] = None


def get_memory_retriever() -> MemoryRetriever:
    """获取全局记忆检索器实例"""
    global _retriever
    if _retriever is None:
        _retriever = MemoryRetriever()
    return _retriever
