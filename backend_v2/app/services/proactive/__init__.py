"""
MindPal Backend V2 - Proactive Message Services

负责为每个（用户 × 数字人）生成主动问候消息。
"""

from app.services.proactive.generator import ProactiveGenerator, get_proactive_generator

__all__ = ["ProactiveGenerator", "get_proactive_generator"]
