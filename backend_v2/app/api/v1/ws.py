"""
MindPal Backend V2 - WebSocket API
实时通信 WebSocket 端点
"""

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import async_session_maker
from app.core.security import decode_token
from app.core.websocket import (
    get_connection_manager,
    ConnectionManager,
    MessageType
)
from app.models import Player, User
from app.models.social import Friendship


router = APIRouter()


async def get_player_from_token(token: str) -> Optional[dict]:
    """从 Token 获取玩家信息"""
    try:
        payload = decode_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        async with async_session_maker() as db:
            # 获取用户和角色
            stmt = select(Player).where(Player.user_id == int(user_id))
            result = await db.execute(stmt)
            player = result.scalar_one_or_none()

            if not player:
                return None

            return {
                "user_id": int(user_id),
                "player_id": player.id,
                "nickname": player.name,
            }
    except Exception as e:
        print(f"Token decode error: {e}")
        return None


async def get_friend_ids(player_id: int) -> list:
    """获取好友ID列表"""
    async with async_session_maker() as db:
        stmt = select(Friendship).where(
            Friendship.player_id == player_id,
            Friendship.status == "accepted"
        )
        result = await db.execute(stmt)
        friendships = result.scalars().all()
        return [f.friend_id for f in friendships]


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT Token"),
    zone: Optional[str] = Query(None, description="当前区域"),
):
    """
    WebSocket 主连接

    连接示例：
    ws://localhost:8000/api/v1/ws?token=xxx&zone=village

    消息格式：
    发送: {"type": "chat", "data": {"channel": "world", "content": "Hello!"}}
    接收: {"type": "chat_world", "data": {...}, "timestamp": "..."}
    """
    manager = get_connection_manager()

    # 验证 Token
    player_info = await get_player_from_token(token)
    if not player_info:
        await websocket.close(code=4001, reason="Invalid token")
        return

    player_id = player_info["player_id"]
    user_id = player_info["user_id"]
    nickname = player_info["nickname"]

    # 建立连接
    connected = await manager.connect(
        websocket=websocket,
        player_id=player_id,
        user_id=user_id,
        nickname=nickname,
        current_zone=zone
    )

    if not connected:
        return

    # 通知好友上线
    friend_ids = await get_friend_ids(player_id)
    await manager.notify_friends_online(player_id, friend_ids)

    # 发送连接成功消息
    await manager.send_personal(player_id, MessageType.SYSTEM_NOTICE, {
        "message": "连接成功",
        "player_id": player_id,
        "nickname": nickname,
        "zone": zone,
    })

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                msg_type = message.get("type")
                msg_data = message.get("data", {})

                # 处理心跳
                if msg_type == "ping":
                    manager.update_heartbeat(player_id)
                    await manager.send_personal(player_id, MessageType.PONG, {})
                    continue

                # 处理聊天消息
                if msg_type == "chat":
                    channel = msg_data.get("channel", "world")
                    content = msg_data.get("content", "")
                    target_id = msg_data.get("target_id")
                    receiver_id = msg_data.get("receiver_id")

                    if content:
                        await manager.send_chat_message(
                            channel=channel,
                            sender_id=player_id,
                            sender_name=nickname,
                            content=content,
                            target_id=target_id,
                            receiver_id=receiver_id
                        )

                # 处理区域切换
                elif msg_type == "change_zone":
                    new_zone = msg_data.get("zone")
                    if new_zone:
                        manager.update_zone(player_id, new_zone)
                        await manager.send_personal(player_id, MessageType.SYSTEM_NOTICE, {
                            "message": f"已切换到区域: {new_zone}",
                            "zone": new_zone
                        })

                # 处理加入队伍
                elif msg_type == "join_party":
                    party_id = msg_data.get("party_id")
                    if party_id:
                        manager.join_party(player_id, party_id)

                # 处理离开队伍
                elif msg_type == "leave_party":
                    manager.leave_party(player_id)

            except json.JSONDecodeError:
                await manager.send_personal(player_id, MessageType.ERROR, {
                    "message": "Invalid JSON format"
                })

    except WebSocketDisconnect:
        pass
    finally:
        # 通知好友下线
        friend_ids = await get_friend_ids(player_id)
        await manager.notify_friends_offline(player_id, nickname, friend_ids)

        # 断开连接
        manager.disconnect(player_id)


@router.get("/ws/stats")
async def get_ws_stats():
    """获取 WebSocket 统计信息"""
    manager = get_connection_manager()
    return manager.get_stats()


@router.get("/ws/online")
async def get_online_players():
    """获取在线玩家列表"""
    manager = get_connection_manager()
    player_ids = manager.get_online_players()

    # 获取玩家信息
    players = []
    for pid in player_ids:
        info = manager.get_connection_info(pid)
        if info:
            players.append({
                "player_id": info["player_id"],
                "nickname": info["nickname"],
                "zone": info["current_zone"],
                "connected_at": info["connected_at"]
            })

    return {
        "total": len(players),
        "players": players
    }
