"""
MindPal Backend V2 - Response Cache Layer

提供 LLM 响应缓存以降低 30%+ 调用成本（DEEP_AUDIT_V3 P1-4）。

设计原则:
- 可选增强（fallback safe）: Redis 不可用自动降级到无缓存，不阻塞主链路
- 双后端: Redis（生产）/ In-Memory（开发、低流量 fallback）
- 智能 skip: 危机模式 / 高温 / 极短/极长文本 不缓存
- 流式兼容: 缓存命中时把完整响应分段 yield，保持打字机效果

缓存 key = sha256(model + system_prompt + messages_json + temperature)
内容 = LLM 返回的完整文本字符串
TTL = 默认 24 小时，可在 .env 调整
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import time
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple


# ==================== 配置 ====================

DEFAULT_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "86400"))  # 24h
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "true").lower() != "false"
REDIS_URL = os.getenv("REDIS_URL", "")

# 不缓存的温度阈值（>=0.9 通常是希望随机性强的场景）
NO_CACHE_TEMP_THRESHOLD = 0.9

# 文本长度保护（极短/极长都不缓存）
MIN_CACHEABLE_CHARS = 10
MAX_CACHEABLE_CHARS = 4000


# ==================== 后端抽象 ====================

class CacheBackend:
    async def get(self, key: str) -> Optional[str]:
        raise NotImplementedError

    async def set(self, key: str, value: str, ttl: int = DEFAULT_TTL_SECONDS) -> None:
        raise NotImplementedError

    async def delete(self, key: str) -> None:
        raise NotImplementedError

    async def ping(self) -> bool:
        return True


class NullCache(CacheBackend):
    """永远不命中的缓存 — 用于 Redis 不可用时的 fallback。"""
    async def get(self, key: str) -> Optional[str]:
        return None

    async def set(self, key: str, value: str, ttl: int = DEFAULT_TTL_SECONDS) -> None:
        return None

    async def delete(self, key: str) -> None:
        return None

    async def ping(self) -> bool:
        return False


class InMemoryCache(CacheBackend):
    """简单内存缓存 — 单进程、开发用。"""

    def __init__(self, max_items: int = 1000):
        self._store: Dict[str, Tuple[str, float]] = {}  # key → (value, expires_at)
        self._max = max_items

    async def get(self, key: str) -> Optional[str]:
        item = self._store.get(key)
        if not item:
            return None
        value, expires = item
        if time.time() > expires:
            self._store.pop(key, None)
            return None
        return value

    async def set(self, key: str, value: str, ttl: int = DEFAULT_TTL_SECONDS) -> None:
        if len(self._store) >= self._max:
            # 简单 LRU 替代：随机淘汰一个
            self._store.pop(next(iter(self._store)), None)
        self._store[key] = (value, time.time() + ttl)

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def ping(self) -> bool:
        return True


class RedisCache(CacheBackend):
    """基于 redis.asyncio 的后端。"""

    def __init__(self, url: str):
        self.url = url
        self._client = None
        self._available = True

    def _get_client(self):
        if self._client is None and self._available:
            try:
                from redis import asyncio as aioredis  # redis>=4.2
                self._client = aioredis.from_url(
                    self.url, encoding="utf-8", decode_responses=True
                )
            except ImportError:
                self._available = False
                self._client = None
        return self._client

    async def get(self, key: str) -> Optional[str]:
        client = self._get_client()
        if not client:
            return None
        try:
            return await client.get(key)
        except Exception:
            return None

    async def set(self, key: str, value: str, ttl: int = DEFAULT_TTL_SECONDS) -> None:
        client = self._get_client()
        if not client:
            return
        try:
            await client.set(key, value, ex=ttl)
        except Exception:
            pass

    async def delete(self, key: str) -> None:
        client = self._get_client()
        if not client:
            return
        try:
            await client.delete(key)
        except Exception:
            pass

    async def ping(self) -> bool:
        client = self._get_client()
        if not client:
            return False
        try:
            await client.ping()
            return True
        except Exception:
            return False


# ==================== 工厂 ====================

_cache_instance: Optional[CacheBackend] = None


def get_cache() -> CacheBackend:
    """获取全局缓存实例（单例）。

    优先级: CACHE_ENABLED=false 禁用 → REDIS_URL 走 Redis → 默认 InMemory
    """
    global _cache_instance
    if _cache_instance is not None:
        return _cache_instance

    if not CACHE_ENABLED:
        _cache_instance = NullCache()
    elif REDIS_URL:
        _cache_instance = RedisCache(REDIS_URL)
    else:
        _cache_instance = InMemoryCache()

    return _cache_instance


# ==================== Key 生成 ====================

def llm_cache_key(
    model: str,
    messages: List[Dict[str, str]],
    system_prompt: str,
    temperature: float,
) -> str:
    """生成稳定的 LLM 响应缓存 key。

    相同输入 → 相同 key；轻微浮点差异（0.8 vs 0.80000001）规范化到 3 位小数。
    """
    payload = {
        "m": model,
        "sp": system_prompt or "",
        "msgs": messages or [],
        "t": round(float(temperature), 3),
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"mp:llm:{h}"


# ==================== 跳过策略 ====================

def should_skip_cache(
    *,
    is_crisis: bool = False,
    temperature: float = 0.7,
    message_text: str = "",
    force_skip: bool = False,
) -> Optional[str]:
    """返回跳过原因字符串（或 None 代表可以缓存）。

    命中任意条件都会跳过缓存：
    - 强制 skip
    - 危机模式（LLM 必须每次重新评估）
    - temperature 过高（要求随机性）
    - 消息过短/过长
    """
    if force_skip:
        return "force_skip"
    if is_crisis:
        return "crisis_mode"
    if temperature >= NO_CACHE_TEMP_THRESHOLD:
        return "high_temperature"
    if not message_text or len(message_text) < MIN_CACHEABLE_CHARS:
        return "msg_too_short"
    if len(message_text) > MAX_CACHEABLE_CHARS:
        return "msg_too_long"
    return None


# ==================== 流式兼容的分段 ====================

def chunk_for_stream(text: str, chunk_chars: int = 16) -> List[str]:
    """把完整文本切成适合流式播放的小片。

    默认 16 字符一段，约等于 10-12 个汉字；这个粒度接近真实 LLM 流式的节奏，
    从缓存回放时用户感知不到差异。
    """
    if not text:
        return []
    return [text[i:i + chunk_chars] for i in range(0, len(text), chunk_chars)]


async def fake_stream_from_cache(
    text: str,
    chunk_chars: int = 16,
    chunk_delay_ms: int = 20,
) -> AsyncGenerator[str, None]:
    """把缓存文本按 chunk 回放成异步生成器（模拟流式）。"""
    for chunk in chunk_for_stream(text, chunk_chars):
        yield chunk
        if chunk_delay_ms > 0:
            await asyncio.sleep(chunk_delay_ms / 1000.0)


__all__ = [
    "CacheBackend",
    "NullCache",
    "InMemoryCache",
    "RedisCache",
    "get_cache",
    "llm_cache_key",
    "should_skip_cache",
    "chunk_for_stream",
    "fake_stream_from_cache",
    "DEFAULT_TTL_SECONDS",
    "CACHE_ENABLED",
]
