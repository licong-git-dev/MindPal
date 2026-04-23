"""
MindPal Backend V2 - NPC Services Package
"""

from app.services.npc.manager import NPCManager, NPCConfig, get_npc_manager

__all__ = [
    "NPCManager",
    "NPCConfig",
    "get_npc_manager",
]
