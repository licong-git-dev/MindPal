"""
MindPal Backend V2 - Player Model
"""

from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Player(Base):
    """游戏角色表"""
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    nickname: Mapped[str] = mapped_column(String(50))

    # 角色属性
    level: Mapped[int] = mapped_column(Integer, default=1)
    experience: Mapped[int] = mapped_column(Integer, default=0)

    # 货币
    gold: Mapped[int] = mapped_column(Integer, default=1000)
    diamonds: Mapped[int] = mapped_column(Integer, default=0)

    # 位置信息
    current_zone: Mapped[str] = mapped_column(String(50), default="central_plaza")
    position_x: Mapped[float] = mapped_column(Float, default=0.0)
    position_y: Mapped[float] = mapped_column(Float, default=0.0)
    position_z: Mapped[float] = mapped_column(Float, default=0.0)
    rotation_y: Mapped[float] = mapped_column(Float, default=0.0)

    # 外观配置 (JSON)
    avatar_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # 统计数据
    total_playtime: Mapped[int] = mapped_column(Integer, default=0)  # 秒
    dialogues_count: Mapped[int] = mapped_column(Integer, default=0)
    achievements_count: Mapped[int] = mapped_column(Integer, default=0)

    # 钥匙收集状态
    keys_collected: Mapped[list | None] = mapped_column(JSON, default=list)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_online: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 关系
    user = relationship("User", back_populates="player")
    affinities = relationship("NPCAffinity", back_populates="player")
    inventory_items = relationship("InventoryItem", back_populates="player")
    quest_progress = relationship("QuestProgress", back_populates="player")

    def to_dict(self) -> dict:
        return {
            "player_id": self.id,
            "nickname": self.nickname,
            "level": self.level,
            "experience": self.experience,
            "gold": self.gold,
            "diamonds": self.diamonds,
            "current_zone": self.current_zone,
            "position": {
                "x": self.position_x,
                "y": self.position_y,
                "z": self.position_z
            },
            "rotation_y": self.rotation_y,
            "avatar_config": self.avatar_config,
            "keys_collected": self.keys_collected or [],
            "stats": {
                "total_playtime": self.total_playtime,
                "dialogues_count": self.dialogues_count,
                "achievements_count": self.achievements_count,
            },
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def exp_to_next_level(self) -> int:
        """计算升级所需经验"""
        return self.level * 1000


class NPCAffinity(Base):
    """NPC好感度表"""
    __tablename__ = "npc_affinities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"))
    npc_id: Mapped[str] = mapped_column(String(50), index=True)  # bei, aela, momo, etc.

    # 好感度 (0-100)
    value: Mapped[int] = mapped_column(Integer, default=0)

    # 统计
    dialogue_count: Mapped[int] = mapped_column(Integer, default=0)
    gifts_given: Mapped[int] = mapped_column(Integer, default=0)

    # 时间戳
    first_met: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_interaction: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 关系
    player = relationship("Player", back_populates="affinities")

    def get_level(self) -> int:
        """获取好感度等级 (1-5)"""
        if self.value < 20:
            return 1
        elif self.value < 40:
            return 2
        elif self.value < 60:
            return 3
        elif self.value < 80:
            return 4
        else:
            return 5

    def get_title(self) -> str:
        """获取关系称号"""
        titles = {
            1: "初识",
            2: "友好",
            3: "熟悉",
            4: "亲密",
            5: "挚友"
        }
        return titles.get(self.get_level(), "初识")

    def to_dict(self) -> dict:
        return {
            "npc_id": self.npc_id,
            "level": self.get_level(),
            "value": self.value,
            "title": self.get_title(),
            "dialogue_count": self.dialogue_count,
            "first_met": self.first_met.isoformat() if self.first_met else None,
        }
