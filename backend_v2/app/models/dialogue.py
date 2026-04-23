"""
MindPal Backend V2 - Dialogue Model
"""

from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class DialogueSession(Base):
    """对话会话表"""
    __tablename__ = "dialogue_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)  # UUID
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    npc_id: Mapped[str] = mapped_column(String(50), index=True)

    # 会话状态
    is_active: Mapped[bool] = mapped_column(default=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    # 情感状态
    dominant_emotion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    affinity_change: Mapped[int] = mapped_column(Integer, default=0)

    # 时间戳
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DialogueMessage(Base):
    """对话消息表"""
    __tablename__ = "dialogue_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("dialogue_sessions.session_id"), index=True)

    # 消息内容
    role: Mapped[str] = mapped_column(String(20))  # user / assistant
    content: Mapped[str] = mapped_column(Text)

    # 情感数据
    emotion: Mapped[str | None] = mapped_column(String(50), nullable=True)
    emotion_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 元数据
    tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    llm_model: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "emotion": self.emotion,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
        }


class DialogueMemory(Base):
    """对话记忆表 (长期记忆)"""
    __tablename__ = "dialogue_memories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    npc_id: Mapped[str] = mapped_column(String(50), index=True)

    # 记忆内容
    memory_type: Mapped[str] = mapped_column(String(50))  # fact, emotion, event, preference
    content: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 重要性评分 (1-10)
    importance: Mapped[int] = mapped_column(Integer, default=5)

    # 向量ID (用于Qdrant检索)
    vector_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # 来源会话
    source_session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_accessed: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    access_count: Mapped[int] = mapped_column(Integer, default=0)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "memory_type": self.memory_type,
            "content": self.content,
            "summary": self.summary,
            "importance": self.importance,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
