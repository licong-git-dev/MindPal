"""
MindPal Backend V2 - Chat API Routes (WebSocket + REST)
实时聊天系统
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
import json

from app.database import get_db
from app.models import Player
from app.models.social import ChatMessage, Friendship, BlockedPlayer
from app.schemas import APIResponse
from app.core.security import get_current_user_id
from app.core.websocket import get_connection_manager, MessageType

router = APIRouter()


class SendMessageBody(BaseModel):
    """发送消息请求"""
    channel: str  # world, zone, party, private
    content: str
    receiver_id: Optional[int] = None  # 私聊目标
    target_id: Optional[str] = None    # 区域/队伍ID


# ===================== WebSocket 端点 =====================

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket连接端点

    连接格式: ws://host/api/v1/chat/ws?token=<jwt_token>

    消息格式 (JSON):
    {
        "type": "chat" | "ping" | "zone_change" | "party_join" | "party_leave",
        "data": { ... }
    }

    chat消息格式:
    {
        "type": "chat",
        "data": {
            "channel": "world" | "zone" | "party" | "private",
            "content": "消息内容",
            "receiver_id": 123,  // 私聊时使用
            "target_id": "zone_1"  // 区域/队伍频道时使用
        }
    }
    """
    manager = get_connection_manager()

    # 验证token
    try:
        from app.core.security import decode_token
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
        user_id = int(user_id)
    except Exception as e:
        await websocket.close(code=4001, reason=f"Token error: {str(e)}")
        return

    # 获取玩家信息
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        await websocket.close(code=4002, reason="Player not found")
        return

    # 建立连接
    connected = await manager.connect(
        websocket=websocket,
        player_id=player.id,
        user_id=user_id,
        nickname=player.nickname,
        current_zone=player.current_zone
    )

    if not connected:
        return

    # 获取好友列表用于通知上线
    stmt = select(Friendship).where(
        and_(
            or_(
                Friendship.player_id == player.id,
                Friendship.friend_id == player.id
            ),
            Friendship.status == "accepted"
        )
    )
    result = await db.execute(stmt)
    friendships = result.scalars().all()
    friend_ids = []
    for f in friendships:
        if f.player_id == player.id:
            friend_ids.append(f.friend_id)
        else:
            friend_ids.append(f.player_id)

    # 通知好友上线
    await manager.notify_friends_online(player.id, friend_ids)

    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            msg_type = data.get("type")
            msg_data = data.get("data", {})

            if msg_type == "ping":
                # 心跳响应
                manager.update_heartbeat(player.id)
                await manager.send_personal(
                    player.id,
                    MessageType.PONG,
                    {"timestamp": datetime.utcnow().isoformat()}
                )

            elif msg_type == "chat":
                # 处理聊天消息
                await handle_chat_message(
                    db=db,
                    manager=manager,
                    player=player,
                    channel=msg_data.get("channel", "world"),
                    content=msg_data.get("content", ""),
                    receiver_id=msg_data.get("receiver_id"),
                    target_id=msg_data.get("target_id")
                )

            elif msg_type == "zone_change":
                # 切换区域
                new_zone = msg_data.get("zone_id")
                if new_zone:
                    manager.update_zone(player.id, new_zone)
                    # 更新数据库中的区域
                    player.current_zone = new_zone

            elif msg_type == "party_join":
                # 加入队伍
                party_id = msg_data.get("party_id")
                if party_id:
                    manager.join_party(player.id, party_id)

            elif msg_type == "party_leave":
                # 离开队伍
                manager.leave_party(player.id)

    except WebSocketDisconnect:
        # 正常断开
        pass
    except Exception as e:
        print(f"WebSocket error for player {player.id}: {e}")
    finally:
        # 清理连接
        manager.disconnect(player.id)

        # 通知好友下线
        await manager.notify_friends_offline(player.id, player.nickname, friend_ids)


async def handle_chat_message(
    db: AsyncSession,
    manager,
    player: Player,
    channel: str,
    content: str,
    receiver_id: Optional[int] = None,
    target_id: Optional[str] = None
):
    """处理聊天消息"""
    # 内容检查
    if not content or len(content) > 500:
        await manager.send_personal(
            player.id,
            MessageType.ERROR,
            {"error": "Message too long or empty"}
        )
        return

    # 私聊检查
    if channel == "private":
        if not receiver_id:
            await manager.send_personal(
                player.id,
                MessageType.ERROR,
                {"error": "Receiver not specified"}
            )
            return

        # 检查是否被屏蔽
        stmt = select(BlockedPlayer).where(
            and_(
                BlockedPlayer.player_id == receiver_id,
                BlockedPlayer.blocked_player_id == player.id
            )
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            await manager.send_personal(
                player.id,
                MessageType.ERROR,
                {"error": "Cannot send message to this player"}
            )
            return

    # 保存消息到数据库
    chat_message = ChatMessage(
        sender_id=player.id,
        channel=channel,
        receiver_id=receiver_id if channel == "private" else None,
        target_id=target_id if channel in ["zone", "party"] else None,
        content=content,
        message_type="text"
    )
    db.add(chat_message)
    await db.commit()

    # 广播消息
    await manager.send_chat_message(
        channel=channel,
        sender_id=player.id,
        sender_name=player.nickname,
        content=content,
        target_id=target_id,
        receiver_id=receiver_id
    )


# ===================== REST API =====================

@router.post("/send", response_model=APIResponse)
async def send_message(
    body: SendMessageBody,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    发送聊天消息 (REST API，用于不使用WebSocket的场景)

    - **channel**: 频道类型 (world/zone/party/private)
    - **content**: 消息内容
    - **receiver_id**: 私聊目标ID
    - **target_id**: 区域/队伍ID
    """
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 内容检查
    if not body.content or len(body.content) > 500:
        raise HTTPException(status_code=400, detail="Message too long or empty")

    # 私聊检查
    if body.channel == "private":
        if not body.receiver_id:
            raise HTTPException(status_code=400, detail="Receiver not specified")

        # 检查是否被屏蔽
        stmt = select(BlockedPlayer).where(
            and_(
                BlockedPlayer.player_id == body.receiver_id,
                BlockedPlayer.blocked_player_id == player.id
            )
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Cannot send message to this player")

    # 保存消息
    chat_message = ChatMessage(
        sender_id=player.id,
        channel=body.channel,
        receiver_id=body.receiver_id if body.channel == "private" else None,
        target_id=body.target_id if body.channel in ["zone", "party"] else None,
        content=body.content,
        message_type="text"
    )
    db.add(chat_message)
    await db.commit()
    await db.refresh(chat_message)

    # 广播消息
    manager = get_connection_manager()
    await manager.send_chat_message(
        channel=body.channel,
        sender_id=player.id,
        sender_name=player.nickname,
        content=body.content,
        target_id=body.target_id,
        receiver_id=body.receiver_id
    )

    return APIResponse(
        code=0,
        message="success",
        data={
            "message_id": chat_message.id,
            "channel": body.channel,
            "sent_at": chat_message.created_at.isoformat()
        }
    )


@router.get("/history", response_model=APIResponse)
async def get_chat_history(
    channel: str = Query(..., description="频道类型"),
    target_id: Optional[str] = Query(None, description="区域/队伍ID"),
    receiver_id: Optional[int] = Query(None, description="私聊对象ID"),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    获取聊天历史

    - **channel**: 频道类型 (world/zone/party/private)
    - **target_id**: 区域/队伍ID
    - **receiver_id**: 私聊对象ID
    """
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 构建查询
    stmt = select(ChatMessage).where(ChatMessage.channel == channel)

    if channel == "world":
        pass  # 世界频道获取全部
    elif channel == "zone":
        if not target_id:
            raise HTTPException(status_code=400, detail="Zone ID required")
        stmt = stmt.where(ChatMessage.target_id == target_id)
    elif channel == "party":
        if not target_id:
            raise HTTPException(status_code=400, detail="Party ID required")
        stmt = stmt.where(ChatMessage.target_id == target_id)
    elif channel == "private":
        if not receiver_id:
            raise HTTPException(status_code=400, detail="Receiver ID required")
        # 获取双方的私聊记录
        stmt = stmt.where(
            or_(
                and_(
                    ChatMessage.sender_id == player.id,
                    ChatMessage.receiver_id == receiver_id
                ),
                and_(
                    ChatMessage.sender_id == receiver_id,
                    ChatMessage.receiver_id == player.id
                )
            )
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid channel")

    # 排序和分页
    stmt = stmt.order_by(desc(ChatMessage.created_at))
    stmt = stmt.offset((page - 1) * size).limit(size)

    result = await db.execute(stmt)
    messages = result.scalars().all()

    # 获取发送者信息
    sender_ids = list(set(m.sender_id for m in messages))
    if sender_ids:
        stmt = select(Player).where(Player.id.in_(sender_ids))
        result = await db.execute(stmt)
        senders = {p.id: p for p in result.scalars().all()}
    else:
        senders = {}

    # 构建响应
    messages_data = []
    for m in reversed(messages):  # 反转以时间正序
        sender = senders.get(m.sender_id)
        messages_data.append({
            "id": m.id,
            "channel": m.channel,
            "sender": {
                "player_id": sender.id,
                "nickname": sender.nickname,
                "level": sender.level
            } if sender else None,
            "content": m.content,
            "message_type": m.message_type,
            "created_at": m.created_at.isoformat() if m.created_at else None
        })

    return APIResponse(
        code=0,
        message="success",
        data={
            "messages": messages_data,
            "total": len(messages_data),
            "page": page,
            "size": size
        }
    )


@router.get("/online", response_model=APIResponse)
async def get_online_players(
    zone_id: Optional[str] = Query(None, description="区域ID，不传则返回全服在线"),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取在线玩家列表"""
    manager = get_connection_manager()

    if zone_id:
        player_ids = manager.get_zone_players(zone_id)
    else:
        player_ids = manager.get_online_players()

    if not player_ids:
        return APIResponse(
            code=0,
            message="success",
            data={"players": [], "total": 0}
        )

    # 获取玩家信息
    stmt = select(Player).where(Player.id.in_(player_ids))
    result = await db.execute(stmt)
    players = result.scalars().all()

    players_data = []
    for p in players:
        conn_info = manager.get_connection_info(p.id)
        players_data.append({
            "player_id": p.id,
            "nickname": p.nickname,
            "level": p.level,
            "current_zone": conn_info.get("current_zone") if conn_info else p.current_zone,
            "party_id": conn_info.get("party_id") if conn_info else None
        })

    return APIResponse(
        code=0,
        message="success",
        data={
            "players": players_data,
            "total": len(players_data)
        }
    )


@router.get("/stats", response_model=APIResponse)
async def get_chat_stats(
    user_id: int = Depends(get_current_user_id)
):
    """获取聊天系统统计信息"""
    manager = get_connection_manager()
    stats = manager.get_stats()

    return APIResponse(
        code=0,
        message="success",
        data=stats
    )
