"""
MindPal Backend V2 - Social Models
"""

from datetime import datetime
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class FriendshipStatus(str, enum.Enum):
    """好友关系状态"""
    PENDING = "pending"      # 待接受
    ACCEPTED = "accepted"    # 已接受
    BLOCKED = "blocked"      # 已屏蔽


class Friendship(Base):
    """好友关系表"""
    __tablename__ = "friendships"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 发起者和接收者
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    friend_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)

    # 状态
    status: Mapped[str] = mapped_column(String(20), default="pending")

    # 申请消息
    request_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 关系
    player = relationship("Player", foreign_keys=[player_id])
    friend = relationship("Player", foreign_keys=[friend_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "player_id": self.player_id,
            "friend_id": self.friend_id,
            "status": self.status,
            "request_message": self.request_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
        }


class BlockedPlayer(Base):
    """屏蔽列表"""
    __tablename__ = "blocked_players"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    blocked_player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)

    # 屏蔽原因
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    player = relationship("Player", foreign_keys=[player_id])
    blocked_player = relationship("Player", foreign_keys=[blocked_player_id])


class ChatMessage(Base):
    """聊天消息表"""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 发送者
    sender_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)

    # 频道类型: world, zone, party, private
    channel: Mapped[str] = mapped_column(String(20), index=True)

    # 私聊目标 (私聊时使用)
    receiver_id: Mapped[int | None] = mapped_column(ForeignKey("players.id"), nullable=True, index=True)

    # 区域/队伍ID (区域/队伍频道时使用)
    target_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 消息内容
    content: Mapped[str] = mapped_column(Text)

    # 消息类型: text, system, emote
    message_type: Mapped[str] = mapped_column(String(20), default="text")

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    sender = relationship("Player", foreign_keys=[sender_id])
    receiver = relationship("Player", foreign_keys=[receiver_id])

    def to_dict(self) -> dict:
        sender_data = {
            "player_id": self.sender.id,
            "nickname": self.sender.nickname,
            "level": self.sender.level,
        } if self.sender else None

        return {
            "id": self.id,
            "channel": self.channel,
            "sender": sender_data,
            "content": self.content,
            "message_type": self.message_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Party(Base):
    """队伍表"""
    __tablename__ = "parties"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 队长
    leader_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)

    # 队伍名称
    name: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 配置
    max_members: Mapped[int] = mapped_column(Integer, default=4)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    # 当前区域
    current_zone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    disbanded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 关系
    leader = relationship("Player", foreign_keys=[leader_id])
    members = relationship("PartyMember", back_populates="party")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "leader_id": self.leader_id,
            "name": self.name,
            "max_members": self.max_members,
            "is_public": self.is_public,
            "current_zone": self.current_zone,
            "member_count": len([m for m in self.members if m]) if self.members else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PartyMember(Base):
    """队伍成员表"""
    __tablename__ = "party_members"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    party_id: Mapped[int] = mapped_column(ForeignKey("parties.id"), index=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)

    # 角色: leader, member
    role: Mapped[str] = mapped_column(String(20), default="member")

    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # 关系
    party = relationship("Party", back_populates="members")
    player = relationship("Player")

    def to_dict(self) -> dict:
        player_data = {
            "player_id": self.player.id,
            "nickname": self.player.nickname,
            "level": self.player.level,
            "current_zone": self.player.current_zone,
        } if self.player else None

        return {
            "party_id": self.party_id,
            "role": self.role,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None,
            "player": player_data,
        }
