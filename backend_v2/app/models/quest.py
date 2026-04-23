"""
MindPal Backend V2 - Quest Model
"""

from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Quest(Base):
    """任务定义表 (静态配置)"""
    __tablename__ = "quests"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # 如 main_chapter1_quest1
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 分类
    quest_type: Mapped[str] = mapped_column(String(50))  # main, side, daily
    chapter: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 主线章节

    # 关联NPC
    npc_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 前置任务
    prerequisite_quest_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    required_level: Mapped[int] = mapped_column(Integer, default=1)
    required_affinity: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {"bei": 30}

    # 任务目标 (JSON列表)
    objectives: Mapped[list] = mapped_column(JSON, default=list)
    # 示例: [{"id": "obj1", "type": "talk_to_npc", "npc_id": "bei", "count": 1}]

    # 奖励 (JSON)
    rewards: Mapped[dict] = mapped_column(JSON, default=dict)
    # 示例: {"exp": 500, "gold": 1000, "items": [{"id": "potion_hp", "quantity": 5}]}

    # 任务链
    next_quest_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 配置
    is_repeatable: Mapped[bool] = mapped_column(Boolean, default=False)
    time_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)  # 秒，为空表示无限制

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "quest_type": self.quest_type,
            "chapter": self.chapter,
            "npc_id": self.npc_id,
            "required_level": self.required_level,
            "objectives": self.objectives,
            "rewards": self.rewards,
        }


class QuestProgress(Base):
    """玩家任务进度表"""
    __tablename__ = "quest_progress"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    quest_id: Mapped[str] = mapped_column(ForeignKey("quests.id"), index=True)

    # 状态
    status: Mapped[str] = mapped_column(String(20), default="in_progress")
    # available, in_progress, completed, failed, claimed

    # 目标进度 (JSON)
    objectives_progress: Mapped[dict] = mapped_column(JSON, default=dict)
    # 示例: {"obj1": {"current": 1, "target": 1, "completed": true}}

    # 时间戳
    accepted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 关系
    player = relationship("Player", back_populates="quest_progress")
    quest = relationship("Quest")

    def is_complete(self) -> bool:
        """检查任务是否完成"""
        for obj_id, progress in self.objectives_progress.items():
            if not progress.get("completed", False):
                return False
        return True

    def to_dict(self) -> dict:
        quest_data = self.quest.to_dict() if self.quest else {}
        return {
            "quest_id": self.quest_id,
            "status": self.status,
            "objectives_progress": self.objectives_progress,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            **quest_data
        }


class Achievement(Base):
    """成就定义表"""
    __tablename__ = "achievements"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 分类
    category: Mapped[str] = mapped_column(String(50))  # exploration, dialogue, collection, etc.

    # 成就点数
    points: Mapped[int] = mapped_column(Integer, default=10)

    # 解锁条件 (JSON)
    conditions: Mapped[dict] = mapped_column(JSON, default=dict)
    # 示例: {"type": "dialogue_count", "npc_id": "bei", "count": 100}

    # 目标值（用于进度追踪）
    target_value: Mapped[int | None] = mapped_column(Integer, nullable=True, default=1)

    # 奖励
    rewards: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 图标
    icon: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # 隐藏成就
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)


class PlayerAchievement(Base):
    """玩家已解锁成就表"""
    __tablename__ = "player_achievements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    achievement_id: Mapped[str] = mapped_column(ForeignKey("achievements.id"))

    # 进度（用于追踪型成就）
    progress: Mapped[int] = mapped_column(Integer, default=0)

    # 时间戳
    unlocked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 关系
    achievement = relationship("Achievement")
