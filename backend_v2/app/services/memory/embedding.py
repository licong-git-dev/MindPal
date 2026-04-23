"""
MindPal Backend V2 - Embedding Service
文本向量化服务 - 支持多种Embedding提供商
"""

import os
import hashlib
import json
from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
import httpx
from functools import lru_cache


class EmbeddingServiceBase(ABC):
    """Embedding服务基类"""

    @abstractmethod
    async def encode(self, text: str) -> List[float]:
        """将单个文本编码为向量"""
        pass

    @abstractmethod
    async def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """批量编码文本"""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """向量维度"""
        pass


class QwenEmbeddingService(EmbeddingServiceBase):
    """阿里云通义千问Embedding服务"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
        self.model = "text-embedding-v2"
        self._dimension = 1536
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def dimension(self) -> int:
        return self._dimension

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def encode(self, text: str) -> List[float]:
        """编码单个文本"""
        results = await self.encode_batch([text])
        return results[0]

    async def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """批量编码文本"""
        client = await self._get_client()

        payload = {
            "model": self.model,
            "input": {
                "texts": texts
            },
            "parameters": {
                "text_type": "query"
            }
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = await client.post(
            self.base_url,
            json=payload,
            headers=headers
        )
        response.raise_for_status()

        data = response.json()
        embeddings = data.get("output", {}).get("embeddings", [])

        # 按index排序
        sorted_embeddings = sorted(embeddings, key=lambda x: x.get("text_index", 0))
        return [e["embedding"] for e in sorted_embeddings]

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


class OpenAIEmbeddingService(EmbeddingServiceBase):
    """OpenAI Embedding服务"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = "text-embedding-3-small"
        self._dimension = 1536
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def dimension(self) -> int:
        return self._dimension

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def encode(self, text: str) -> List[float]:
        """编码单个文本"""
        results = await self.encode_batch([text])
        return results[0]

    async def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """批量编码文本"""
        client = await self._get_client()

        payload = {
            "model": self.model,
            "input": texts
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        response = await client.post(
            f"{self.base_url}/embeddings",
            json=payload,
            headers=headers
        )
        response.raise_for_status()

        data = response.json()
        embeddings = data.get("data", [])

        # 按index排序
        sorted_embeddings = sorted(embeddings, key=lambda x: x.get("index", 0))
        return [e["embedding"] for e in sorted_embeddings]

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


class LocalEmbeddingService(EmbeddingServiceBase):
    """本地Embedding服务 - 使用sentence-transformers（备用方案）"""

    def __init__(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self._model = None
        self._dimension = 384  # MiniLM默认维度

    @property
    def dimension(self) -> int:
        return self._dimension

    def _load_model(self):
        """懒加载模型"""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
                self._dimension = self._model.get_sentence_embedding_dimension()
            except ImportError:
                raise ImportError("请安装 sentence-transformers: pip install sentence-transformers")
        return self._model

    async def encode(self, text: str) -> List[float]:
        """编码单个文本"""
        model = self._load_model()
        embedding = model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    async def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """批量编码文本"""
        model = self._load_model()
        embeddings = model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    async def close(self):
        pass


class SimpleHashEmbedding(EmbeddingServiceBase):
    """简单哈希Embedding - 用于测试和开发（无需API）"""

    def __init__(self, dimension: int = 384):
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    async def encode(self, text: str) -> List[float]:
        """使用哈希生成伪向量"""
        # 基于文本内容生成确定性的向量
        hash_bytes = hashlib.sha512(text.encode()).digest()

        # 扩展到所需维度
        vector = []
        for i in range(self._dimension):
            byte_idx = i % len(hash_bytes)
            # 归一化到 [-1, 1]
            value = (hash_bytes[byte_idx] / 127.5) - 1.0
            vector.append(value)

        # 归一化向量
        norm = sum(v ** 2 for v in vector) ** 0.5
        if norm > 0:
            vector = [v / norm for v in vector]

        return vector

    async def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """批量编码"""
        return [await self.encode(text) for text in texts]

    async def close(self):
        pass


class EmbeddingService:
    """Embedding服务工厂和管理器"""

    _instance: Optional["EmbeddingService"] = None
    _service: Optional[EmbeddingServiceBase] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._service is None:
            self._service = self._create_service()

    def _create_service(self) -> EmbeddingServiceBase:
        """根据配置创建Embedding服务"""
        provider = os.getenv("EMBEDDING_PROVIDER", "simple")

        if provider == "qwen":
            return QwenEmbeddingService()
        elif provider == "openai":
            return OpenAIEmbeddingService()
        elif provider == "local":
            return LocalEmbeddingService()
        else:
            # 默认使用简单哈希（开发/测试用）
            return SimpleHashEmbedding()

    @property
    def dimension(self) -> int:
        return self._service.dimension

    async def encode(self, text: str) -> List[float]:
        """编码文本"""
        return await self._service.encode(text)

    async def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """批量编码"""
        return await self._service.encode_batch(texts)

    async def close(self):
        """关闭服务"""
        if self._service:
            await self._service.close()


# 便捷函数
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """获取全局Embedding服务实例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
