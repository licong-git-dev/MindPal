"""
MindPal Backend V2 - WebSocket Manager
实时通信管理器，支持聊天、通知、状态同步
"""

from fastapi import WebSocket
from typing import Dict, Set, Optional, List
from datetime import datetime
import json
import asyncio
from dataclasses import dataclass, field
from enum import Enum


class MessageType(str, Enum):
    """消息类型"""
    # 聊天消息
    CHAT_WORLD = "chat_world"       # 世界频道
    CHAT_ZONE = "chat_zone"         # 区域频道
    CHAT_PARTY = "chat_party"       # 队伍频道
    CHAT_PRIVATE = "chat_private"   # 私聊

    # 系统通知
    SYSTEM_NOTICE = "system_notice"     # 系统公告
    FRIEND_REQUEST = "friend_request"   # 好友申请
    FRIEND_ONLINE = "friend_online"     # 好友上线
    FRIEND_OFFLINE = "friend_offline"   # 好友下线

    # 队伍相关
    PARTY_INVITE = "party_invite"       # 队伍邀请
    PARTY_UPDATE = "party_update"       # 队伍更新
    PARTY_KICK = "party_kick"           # 被踢出队伍
    PARTY_DISBAND = "party_disband"     # 队伍解散

    # 游戏事件
    NPC_EVENT = "npc_event"             # NPC事件
    QUEST_UPDATE = "quest_update"       # 任务更新
    ACHIEVEMENT = "achievement"         # 成就达成
    LEVEL_UP = "level_up"               # 升级通知
    ITEM_DROP = "item_drop"             # 物品掉落

    # 连接管理
    PING = "ping"
    PONG = "pong"
    ERROR = "error"


@dataclass
class Connection:
    """WebSocket连接信息"""
    websocket: WebSocket
    player_id: int
    user_id: int
    nickname: str
    current_zone: Optional[str] = None
    party_id: Optional[int] = None
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # player_id -> Connection
        self._connections: Dict[int, Connection] = {}

        # 频道订阅
        self._zone_subscribers: Dict[str, Set[int]] = {}  # zone_id -> Set[player_id]
        self._party_subscribers: Dict[int, Set[int]] = {}  # party_id -> Set[player_id]

        # 心跳检测
        self._heartbeat_interval = 30  # 秒
        self._heartbeat_timeout = 90   # 秒

    async def connect(
        self,
        websocket: WebSocket,
        player_id: int,
        user_id: int,
        nickname: str,
        current_zone: Optional[str] = None
    ) -> bool:
        """建立连接"""
        try:
            await websocket.accept()

            # 如果已有连接，先断开旧连接
            if player_id in self._connections:
                old_conn = self._connections[player_id]
                try:
                    await old_conn.websocket.close(code=4000, reason="New connection established")
                except:
                    pass
                self._cleanup_connection(player_id)

            # 创建新连接
            connection = Connection(
                websocket=websocket,
                player_id=player_id,
                user_id=user_id,
                nickname=nickname,
                current_zone=current_zone
            )
            self._connections[player_id] = connection

            # 订阅区域频道
            if current_zone:
                self._subscribe_zone(player_id, current_zone)

            # 通知好友上线 (需要外部调用)
            return True
        except Exception as e:
            print(f"WebSocket connect error: {e}")
            return False

    def disconnect(self, player_id: int):
        """断开连接"""
        self._cleanup_connection(player_id)

    def _cleanup_connection(self, player_id: int):
        """清理连接"""
        if player_id not in self._connections:
            return

        conn = self._connections[player_id]

        # 取消区域订阅
        if conn.current_zone:
            self._unsubscribe_zone(player_id, conn.current_zone)

        # 取消队伍订阅
        if conn.party_id:
            self._unsubscribe_party(player_id, conn.party_id)

        # 删除连接
        del self._connections[player_id]

    def _subscribe_zone(self, player_id: int, zone_id: str):
        """订阅区域频道"""
        if zone_id not in self._zone_subscribers:
            self._zone_subscribers[zone_id] = set()
        self._zone_subscribers[zone_id].add(player_id)

    def _unsubscribe_zone(self, player_id: int, zone_id: str):
        """取消区域订阅"""
        if zone_id in self._zone_subscribers:
            self._zone_subscribers[zone_id].discard(player_id)
            if not self._zone_subscribers[zone_id]:
                del self._zone_subscribers[zone_id]

    def _subscribe_party(self, player_id: int, party_id: int):
        """订阅队伍频道"""
        if party_id not in self._party_subscribers:
            self._party_subscribers[party_id] = set()
        self._party_subscribers[party_id].add(player_id)

    def _unsubscribe_party(self, player_id: int, party_id: int):
        """取消队伍订阅"""
        if party_id in self._party_subscribers:
            self._party_subscribers[party_id].discard(player_id)
            if not self._party_subscribers[party_id]:
                del self._party_subscribers[party_id]

    def update_zone(self, player_id: int, new_zone: str):
        """更新玩家区域"""
        if player_id not in self._connections:
            return

        conn = self._connections[player_id]

        # 取消旧区域订阅
        if conn.current_zone:
            self._unsubscribe_zone(player_id, conn.current_zone)

        # 订阅新区域
        conn.current_zone = new_zone
        self._subscribe_zone(player_id, new_zone)

    def join_party(self, player_id: int, party_id: int):
        """加入队伍"""
        if player_id not in self._connections:
            return

        conn = self._connections[player_id]

        # 离开旧队伍
        if conn.party_id:
            self._unsubscribe_party(player_id, conn.party_id)

        # 加入新队伍
        conn.party_id = party_id
        self._subscribe_party(player_id, party_id)

    def leave_party(self, player_id: int):
        """离开队伍"""
        if player_id not in self._connections:
            return

        conn = self._connections[player_id]
        if conn.party_id:
            self._unsubscribe_party(player_id, conn.party_id)
            conn.party_id = None

    def is_online(self, player_id: int) -> bool:
        """检查玩家是否在线"""
        return player_id in self._connections

    def get_online_players(self) -> List[int]:
        """获取所有在线玩家ID"""
        return list(self._connections.keys())

    def get_zone_players(self, zone_id: str) -> List[int]:
        """获取区域内的玩家ID"""
        return list(self._zone_subscribers.get(zone_id, set()))

    def get_party_players(self, party_id: int) -> List[int]:
        """获取队伍内的玩家ID"""
        return list(self._party_subscribers.get(party_id, set()))

    async def send_personal(
        self,
        player_id: int,
        message_type: MessageType,
        data: dict
    ) -> bool:
        """发送私人消息"""
        if player_id not in self._connections:
            return False

        conn = self._connections[player_id]
        message = {
            "type": message_type.value,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            await conn.websocket.send_json(message)
            return True
        except Exception as e:
            print(f"Send to {player_id} failed: {e}")
            self.disconnect(player_id)
            return False

    async def send_to_players(
        self,
        player_ids: List[int],
        message_type: MessageType,
        data: dict
    ):
        """发送消息给多个玩家"""
        tasks = [
            self.send_personal(pid, message_type, data)
            for pid in player_ids
            if pid in self._connections
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def broadcast_world(self, message_type: MessageType, data: dict):
        """世界广播"""
        await self.send_to_players(
            list(self._connections.keys()),
            message_type,
            data
        )

    async def broadcast_zone(
        self,
        zone_id: str,
        message_type: MessageType,
        data: dict,
        exclude_player: Optional[int] = None
    ):
        """区域广播"""
        player_ids = self._zone_subscribers.get(zone_id, set())
        if exclude_player:
            player_ids = player_ids - {exclude_player}
        await self.send_to_players(list(player_ids), message_type, data)

    async def broadcast_party(
        self,
        party_id: int,
        message_type: MessageType,
        data: dict,
        exclude_player: Optional[int] = None
    ):
        """队伍广播"""
        player_ids = self._party_subscribers.get(party_id, set())
        if exclude_player:
            player_ids = player_ids - {exclude_player}
        await self.send_to_players(list(player_ids), message_type, data)

    async def send_chat_message(
        self,
        channel: str,
        sender_id: int,
        sender_name: str,
        content: str,
        target_id: Optional[str] = None,
        receiver_id: Optional[int] = None
    ):
        """发送聊天消息"""
        data = {
            "channel": channel,
            "sender": {
                "player_id": sender_id,
                "nickname": sender_name
            },
            "content": content,
            "target_id": target_id
        }

        if channel == "world":
            await self.broadcast_world(MessageType.CHAT_WORLD, data)
        elif channel == "zone" and target_id:
            await self.broadcast_zone(target_id, MessageType.CHAT_ZONE, data)
        elif channel == "party" and target_id:
            try:
                party_id = int(target_id)
                await self.broadcast_party(party_id, MessageType.CHAT_PARTY, data)
            except ValueError:
                pass
        elif channel == "private" and receiver_id:
            # 发送给接收者
            await self.send_personal(receiver_id, MessageType.CHAT_PRIVATE, data)
            # 也发送给发送者（确认）
            await self.send_personal(sender_id, MessageType.CHAT_PRIVATE, data)

    async def notify_friends_online(self, player_id: int, friend_ids: List[int]):
        """通知好友上线"""
        if player_id not in self._connections:
            return

        conn = self._connections[player_id]
        data = {
            "player_id": player_id,
            "nickname": conn.nickname
        }

        await self.send_to_players(friend_ids, MessageType.FRIEND_ONLINE, data)

    async def notify_friends_offline(self, player_id: int, nickname: str, friend_ids: List[int]):
        """通知好友下线"""
        data = {
            "player_id": player_id,
            "nickname": nickname
        }
        await self.send_to_players(friend_ids, MessageType.FRIEND_OFFLINE, data)

    def update_heartbeat(self, player_id: int):
        """更新心跳时间"""
        if player_id in self._connections:
            self._connections[player_id].last_heartbeat = datetime.utcnow()

    async def check_heartbeats(self):
        """检查心跳超时的连接"""
        now = datetime.utcnow()
        timeout_players = []

        for player_id, conn in self._connections.items():
            elapsed = (now - conn.last_heartbeat).total_seconds()
            if elapsed > self._heartbeat_timeout:
                timeout_players.append(player_id)

        for player_id in timeout_players:
            print(f"Player {player_id} heartbeat timeout, disconnecting...")
            self.disconnect(player_id)

    def get_connection_info(self, player_id: int) -> Optional[dict]:
        """获取连接信息"""
        if player_id not in self._connections:
            return None

        conn = self._connections[player_id]
        return {
            "player_id": conn.player_id,
            "user_id": conn.user_id,
            "nickname": conn.nickname,
            "current_zone": conn.current_zone,
            "party_id": conn.party_id,
            "connected_at": conn.connected_at.isoformat(),
            "last_heartbeat": conn.last_heartbeat.isoformat()
        }

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "total_connections": len(self._connections),
            "zones": {
                zone: len(players)
                for zone, players in self._zone_subscribers.items()
            },
            "parties": {
                party_id: len(players)
                for party_id, players in self._party_subscribers.items()
            }
        }


# 全局连接管理器实例
manager = ConnectionManager()


def get_connection_manager() -> ConnectionManager:
    """获取连接管理器实例"""
    return manager
