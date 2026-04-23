"""
MindPal Backend V2 - Party API Routes
队伍系统
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import joinedload
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.models import Player
from app.models.social import Party, PartyMember, Friendship
from app.schemas import APIResponse
from app.core.security import get_current_user_id
from app.core.websocket import get_connection_manager, MessageType

router = APIRouter()


class CreatePartyBody(BaseModel):
    """创建队伍"""
    name: Optional[str] = None
    is_public: bool = False
    max_members: int = 4


class InvitePlayerBody(BaseModel):
    """邀请玩家"""
    player_id: int


class TransferLeaderBody(BaseModel):
    """转让队长"""
    player_id: int


# ===================== 队伍管理 =====================

@router.post("", response_model=APIResponse)
async def create_party(
    body: CreatePartyBody,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """创建队伍"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 检查是否已在队伍中
    stmt = select(PartyMember).where(PartyMember.player_id == player.id)
    result = await db.execute(stmt)
    existing_membership = result.scalar_one_or_none()

    if existing_membership:
        raise HTTPException(status_code=400, detail="Already in a party")

    # 创建队伍
    party = Party(
        leader_id=player.id,
        name=body.name or f"{player.nickname}的队伍",
        max_members=min(body.max_members, 8),  # 最多8人
        is_public=body.is_public,
        current_zone=player.current_zone
    )
    db.add(party)
    await db.flush()

    # 添加队长为成员
    member = PartyMember(
        party_id=party.id,
        player_id=player.id,
        role="leader"
    )
    db.add(member)

    await db.commit()
    await db.refresh(party)

    # 更新WebSocket订阅
    manager = get_connection_manager()
    manager.join_party(player.id, party.id)

    return APIResponse(
        code=0,
        message="success",
        data={
            "party_id": party.id,
            "name": party.name,
            "leader_id": party.leader_id,
            "max_members": party.max_members,
            "is_public": party.is_public
        }
    )


@router.get("", response_model=APIResponse)
async def get_my_party(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取当前队伍信息"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取队伍成员关系
    stmt = select(PartyMember).options(
        joinedload(PartyMember.party)
    ).where(PartyMember.player_id == player.id)
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()

    if not membership:
        return APIResponse(
            code=0,
            message="success",
            data={"party": None}
        )

    party = membership.party

    # 获取所有成员
    stmt = select(PartyMember).options(
        joinedload(PartyMember.player)
    ).where(PartyMember.party_id == party.id)
    result = await db.execute(stmt)
    members = result.scalars().all()

    members_data = []
    manager = get_connection_manager()
    for m in members:
        if m.player:
            members_data.append({
                "player_id": m.player.id,
                "nickname": m.player.nickname,
                "level": m.player.level,
                "current_zone": m.player.current_zone,
                "role": m.role,
                "is_online": manager.is_online(m.player.id),
                "joined_at": m.joined_at.isoformat() if m.joined_at else None
            })

    return APIResponse(
        code=0,
        message="success",
        data={
            "party": {
                "id": party.id,
                "name": party.name,
                "leader_id": party.leader_id,
                "max_members": party.max_members,
                "is_public": party.is_public,
                "current_zone": party.current_zone,
                "created_at": party.created_at.isoformat() if party.created_at else None,
                "members": members_data,
                "member_count": len(members_data)
            }
        }
    )


@router.get("/public", response_model=APIResponse)
async def get_public_parties(
    zone: Optional[str] = Query(None, description="过滤区域"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """获取公开队伍列表"""
    stmt = select(Party).where(
        and_(
            Party.is_public == True,
            Party.disbanded_at == None
        )
    )

    if zone:
        stmt = stmt.where(Party.current_zone == zone)

    stmt = stmt.offset((page - 1) * size).limit(size)

    result = await db.execute(stmt)
    parties = result.scalars().all()

    parties_data = []
    for p in parties:
        # 获取成员数量
        stmt = select(PartyMember).where(PartyMember.party_id == p.id)
        result = await db.execute(stmt)
        member_count = len(result.scalars().all())

        # 获取队长信息
        stmt = select(Player).where(Player.id == p.leader_id)
        result = await db.execute(stmt)
        leader = result.scalar_one_or_none()

        parties_data.append({
            "id": p.id,
            "name": p.name,
            "leader": {
                "player_id": leader.id,
                "nickname": leader.nickname,
                "level": leader.level
            } if leader else None,
            "member_count": member_count,
            "max_members": p.max_members,
            "current_zone": p.current_zone
        })

    return APIResponse(
        code=0,
        message="success",
        data={
            "parties": parties_data,
            "total": len(parties_data)
        }
    )


@router.post("/join/{party_id}", response_model=APIResponse)
async def join_party(
    party_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """加入公开队伍"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 检查是否已在队伍中
    stmt = select(PartyMember).where(PartyMember.player_id == player.id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already in a party")

    # 获取队伍
    stmt = select(Party).where(
        and_(
            Party.id == party_id,
            Party.disbanded_at == None
        )
    )
    result = await db.execute(stmt)
    party = result.scalar_one_or_none()

    if not party:
        raise HTTPException(status_code=404, detail="Party not found")

    if not party.is_public:
        raise HTTPException(status_code=400, detail="Party is not public")

    # 检查人数
    stmt = select(PartyMember).where(PartyMember.party_id == party_id)
    result = await db.execute(stmt)
    current_members = len(result.scalars().all())

    if current_members >= party.max_members:
        raise HTTPException(status_code=400, detail="Party is full")

    # 加入队伍
    member = PartyMember(
        party_id=party_id,
        player_id=player.id,
        role="member"
    )
    db.add(member)
    await db.commit()

    # 更新WebSocket订阅
    manager = get_connection_manager()
    manager.join_party(player.id, party_id)

    # 通知队伍成员
    await manager.broadcast_party(
        party_id,
        MessageType.PARTY_UPDATE,
        {
            "action": "join",
            "player": {
                "player_id": player.id,
                "nickname": player.nickname,
                "level": player.level
            }
        },
        exclude_player=player.id
    )

    return APIResponse(
        code=0,
        message="success",
        data={
            "party_id": party_id,
            "joined": True
        }
    )


@router.post("/invite", response_model=APIResponse)
async def invite_player(
    body: InvitePlayerBody,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """邀请玩家加入队伍"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取当前队伍
    stmt = select(PartyMember).options(
        joinedload(PartyMember.party)
    ).where(PartyMember.player_id == player.id)
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(status_code=400, detail="Not in a party")

    party = membership.party

    # 检查人数
    stmt = select(PartyMember).where(PartyMember.party_id == party.id)
    result = await db.execute(stmt)
    current_members = len(result.scalars().all())

    if current_members >= party.max_members:
        raise HTTPException(status_code=400, detail="Party is full")

    # 检查目标玩家
    stmt = select(Player).where(Player.id == body.player_id)
    result = await db.execute(stmt)
    target_player = result.scalar_one_or_none()

    if not target_player:
        raise HTTPException(status_code=404, detail="Target player not found")

    # 检查目标是否已在队伍中
    stmt = select(PartyMember).where(PartyMember.player_id == body.player_id)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Target player already in a party")

    # 发送邀请通知
    manager = get_connection_manager()
    await manager.send_personal(
        body.player_id,
        MessageType.PARTY_INVITE,
        {
            "party_id": party.id,
            "party_name": party.name,
            "inviter": {
                "player_id": player.id,
                "nickname": player.nickname,
                "level": player.level
            }
        }
    )

    return APIResponse(
        code=0,
        message="success",
        data={
            "invited": True,
            "target_player_id": body.player_id
        }
    )


@router.post("/leave", response_model=APIResponse)
async def leave_party(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """离开队伍"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取队伍成员关系
    stmt = select(PartyMember).options(
        joinedload(PartyMember.party)
    ).where(PartyMember.player_id == player.id)
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(status_code=400, detail="Not in a party")

    party = membership.party
    party_id = party.id
    is_leader = membership.role == "leader"

    # 删除成员关系
    await db.delete(membership)

    # 如果是队长，需要转让或解散
    if is_leader:
        # 获取其他成员
        stmt = select(PartyMember).where(
            and_(
                PartyMember.party_id == party_id,
                PartyMember.player_id != player.id
            )
        ).order_by(PartyMember.joined_at)
        result = await db.execute(stmt)
        other_members = result.scalars().all()

        if other_members:
            # 转让给最早加入的成员
            new_leader = other_members[0]
            new_leader.role = "leader"
            party.leader_id = new_leader.player_id

            # 通知新队长
            manager = get_connection_manager()
            await manager.send_personal(
                new_leader.player_id,
                MessageType.PARTY_UPDATE,
                {
                    "action": "promoted",
                    "message": "You are now the party leader"
                }
            )
        else:
            # 解散队伍
            party.disbanded_at = datetime.utcnow()

    await db.commit()

    # 更新WebSocket订阅
    manager = get_connection_manager()
    manager.leave_party(player.id)

    # 通知队伍成员
    await manager.broadcast_party(
        party_id,
        MessageType.PARTY_UPDATE,
        {
            "action": "leave",
            "player": {
                "player_id": player.id,
                "nickname": player.nickname
            }
        }
    )

    return APIResponse(
        code=0,
        message="success",
        data={"left": True}
    )


@router.post("/kick/{player_id}", response_model=APIResponse)
async def kick_player(
    player_id: int,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """踢出队员（仅队长）"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取队伍成员关系
    stmt = select(PartyMember).options(
        joinedload(PartyMember.party)
    ).where(PartyMember.player_id == player.id)
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(status_code=400, detail="Not in a party")

    if membership.role != "leader":
        raise HTTPException(status_code=403, detail="Only leader can kick members")

    party = membership.party

    # 获取目标成员
    stmt = select(PartyMember).where(
        and_(
            PartyMember.party_id == party.id,
            PartyMember.player_id == player_id
        )
    )
    result = await db.execute(stmt)
    target_membership = result.scalar_one_or_none()

    if not target_membership:
        raise HTTPException(status_code=404, detail="Target player not in party")

    if target_membership.player_id == player.id:
        raise HTTPException(status_code=400, detail="Cannot kick yourself")

    # 获取被踢玩家信息
    stmt = select(Player).where(Player.id == player_id)
    result = await db.execute(stmt)
    kicked_player = result.scalar_one_or_none()

    # 删除成员关系
    await db.delete(target_membership)
    await db.commit()

    # 更新WebSocket订阅
    manager = get_connection_manager()
    manager.leave_party(player_id)

    # 通知被踢玩家
    await manager.send_personal(
        player_id,
        MessageType.PARTY_KICK,
        {
            "party_id": party.id,
            "message": "You have been kicked from the party"
        }
    )

    # 通知队伍其他成员
    await manager.broadcast_party(
        party.id,
        MessageType.PARTY_UPDATE,
        {
            "action": "kick",
            "player": {
                "player_id": player_id,
                "nickname": kicked_player.nickname if kicked_player else "Unknown"
            }
        }
    )

    return APIResponse(
        code=0,
        message="success",
        data={"kicked": True}
    )


@router.post("/transfer", response_model=APIResponse)
async def transfer_leadership(
    body: TransferLeaderBody,
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """转让队长"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取队伍成员关系
    stmt = select(PartyMember).options(
        joinedload(PartyMember.party)
    ).where(PartyMember.player_id == player.id)
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(status_code=400, detail="Not in a party")

    if membership.role != "leader":
        raise HTTPException(status_code=403, detail="Only leader can transfer leadership")

    party = membership.party

    # 获取目标成员
    stmt = select(PartyMember).where(
        and_(
            PartyMember.party_id == party.id,
            PartyMember.player_id == body.player_id
        )
    )
    result = await db.execute(stmt)
    target_membership = result.scalar_one_or_none()

    if not target_membership:
        raise HTTPException(status_code=404, detail="Target player not in party")

    if target_membership.player_id == player.id:
        raise HTTPException(status_code=400, detail="Already the leader")

    # 转让队长
    membership.role = "member"
    target_membership.role = "leader"
    party.leader_id = body.player_id

    await db.commit()

    # 通知队伍成员
    manager = get_connection_manager()
    await manager.broadcast_party(
        party.id,
        MessageType.PARTY_UPDATE,
        {
            "action": "transfer",
            "new_leader_id": body.player_id
        }
    )

    return APIResponse(
        code=0,
        message="success",
        data={
            "transferred": True,
            "new_leader_id": body.player_id
        }
    )


@router.delete("", response_model=APIResponse)
async def disband_party(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """解散队伍（仅队长）"""
    # 获取玩家
    stmt = select(Player).where(Player.user_id == user_id)
    result = await db.execute(stmt)
    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Character not found")

    # 获取队伍成员关系
    stmt = select(PartyMember).options(
        joinedload(PartyMember.party)
    ).where(PartyMember.player_id == player.id)
    result = await db.execute(stmt)
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(status_code=400, detail="Not in a party")

    if membership.role != "leader":
        raise HTTPException(status_code=403, detail="Only leader can disband party")

    party = membership.party
    party_id = party.id

    # 获取所有成员
    stmt = select(PartyMember).where(PartyMember.party_id == party_id)
    result = await db.execute(stmt)
    members = result.scalars().all()

    member_ids = [m.player_id for m in members]

    # 删除所有成员关系
    for m in members:
        await db.delete(m)

    # 标记队伍解散
    party.disbanded_at = datetime.utcnow()

    await db.commit()

    # 更新WebSocket订阅并通知
    manager = get_connection_manager()
    for mid in member_ids:
        manager.leave_party(mid)
        await manager.send_personal(
            mid,
            MessageType.PARTY_DISBAND,
            {
                "party_id": party_id,
                "message": "Party has been disbanded"
            }
        )

    return APIResponse(
        code=0,
        message="success",
        data={"disbanded": True}
    )
