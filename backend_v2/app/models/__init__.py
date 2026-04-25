"""
MindPal Backend V2 - Models Package
"""

from app.database import Base
from app.models.user import User
from app.models.player import Player, NPCAffinity
from app.models.dialogue import DialogueSession, DialogueMessage, DialogueMemory
from app.models.inventory import Item, InventoryItem, ShopItem
from app.models.quest import Quest, QuestProgress, Achievement, PlayerAchievement
from app.models.social import Friendship, BlockedPlayer, ChatMessage, Party, PartyMember
from app.models.payment import Order, PaymentLog, VIPSubscription, RechargeProduct
from app.models.digital_human import DigitalHuman, DHConversation, DHMessage
from app.models.proactive import ProactiveMessage
from app.models.cp import CpInvitation, CpBond
from app.models.report import UserReport, ReportCategory, ReportStatus, ReportTargetType

__all__ = [
    "Base",
    "User",
    "Player",
    "NPCAffinity",
    "DialogueSession",
    "DialogueMessage",
    "DialogueMemory",
    "Item",
    "InventoryItem",
    "ShopItem",
    "Quest",
    "QuestProgress",
    "Achievement",
    "PlayerAchievement",
    "Friendship",
    "BlockedPlayer",
    "ChatMessage",
    "Party",
    "PartyMember",
    "Order",
    "PaymentLog",
    "VIPSubscription",
    "RechargeProduct",
    "DigitalHuman",
    "DHConversation",
    "DHMessage",
    "ProactiveMessage",
    "CpInvitation",
    "CpBond",
    "UserReport",
    "ReportCategory",
    "ReportStatus",
    "ReportTargetType",
]
