"""
MindPal Backend V2 - Digital Human Model
用户自定义数字人模型
"""

from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Float, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class DigitalHuman(Base):
    """数字人表 - 用户创建的个性化AI伙伴"""
    __tablename__ = "digital_humans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # 基础信息
    name: Mapped[str] = mapped_column(String(50))  # 数字人名字
    avatar_type: Mapped[str] = mapped_column(String(50), default="default")  # 形象类型
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # 头像URL

    # 性格设定
    personality: Mapped[str] = mapped_column(String(50), default="gentle")  # 性格类型
    personality_traits: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # 特质滑块值
    custom_personality: Mapped[str | None] = mapped_column(Text, nullable=True)  # 自定义性格描述

    # 角色类型
    role_type: Mapped[str] = mapped_column(String(50), default="companion")  # companion/teacher

    # 声音设定
    voice_id: Mapped[str] = mapped_column(String(50), default="xiaoya")  # 声音ID
    voice_speed: Mapped[float] = mapped_column(Float, default=1.0)  # 语速

    # 擅长领域
    domains: Mapped[list | None] = mapped_column(JSON, nullable=True)  # ["学习", "情感", "娱乐"]

    # 生成的系统提示词
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 统计信息
    total_conversations: Mapped[int] = mapped_column(Integer, default=0)
    total_messages: Mapped[int] = mapped_column(Integer, default=0)
    last_conversation_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)  # 是否为默认数字人

    # 3D场景相关 (Phase 3 HunyuanWorld集成)
    home_scene_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    home_scene_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "avatar_type": self.avatar_type,
            "avatar_url": self.avatar_url,
            "personality": self.personality,
            "personality_traits": self.personality_traits,
            "custom_personality": self.custom_personality,
            "role_type": self.role_type,
            "voice_id": self.voice_id,
            "domains": self.domains,
            "total_conversations": self.total_conversations,
            "total_messages": self.total_messages,
            "is_active": self.is_active,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_conversation_at": self.last_conversation_at.isoformat() if self.last_conversation_at else None,
        }

    def get_personality_display(self) -> str:
        """获取性格显示名称"""
        personality_map = {
            "gentle": "温柔体贴",
            "energetic": "活泼开朗",
            "wise": "睿智沉稳",
            "humorous": "幽默风趣",
            "caring": "关怀备至",
            "creative": "创意无限",
        }
        return personality_map.get(self.personality, self.personality)


class DHConversation(Base):
    """数字人对话会话表"""
    __tablename__ = "dh_conversations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(36), unique=True, index=True)  # UUID
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    dh_id: Mapped[int] = mapped_column(ForeignKey("digital_humans.id"), index=True)

    # 会话状态
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    # 情感状态
    dominant_emotion: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 时间戳
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DHMessage(Base):
    """数字人对话消息表"""
    __tablename__ = "dh_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("dh_conversations.session_id"), index=True)
    dh_id: Mapped[int] = mapped_column(ForeignKey("digital_humans.id"), index=True)

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
