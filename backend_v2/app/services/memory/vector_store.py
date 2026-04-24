"""
MindPal Backend V2 - Vector Store
向量存储服务 - 支持ChromaDB和内存存储
"""

import os
import json
import math
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import asyncio


@dataclass
class VectorDocument:
    """向量文档"""
    id: str
    text: str
    vector: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SearchResult:
    """搜索结果"""
    id: str
    text: str
    score: float
    metadata: Dict[str, Any]


class VectorStoreBase:
    """向量存储基类"""

    async def add(self, doc: VectorDocument) -> str:
        """添加文档"""
        raise NotImplementedError

    async def add_batch(self, docs: List[VectorDocument]) -> List[str]:
        """批量添加文档"""
        raise NotImplementedError

    async def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[SearchResult]:
        """搜索相似向量"""
        raise NotImplementedError

    async def delete(self, doc_id: str) -> bool:
        """删除文档"""
        raise NotImplementedError

    async def get(self, doc_id: str) -> Optional[VectorDocument]:
        """获取文档"""
        raise NotImplementedError

    async def count(self, filter_metadata: Optional[Dict[str, Any]] = None) -> int:
        """文档数量（可按元数据过滤）"""
        raise NotImplementedError

    async def list_by_metadata(
        self,
        filter_metadata: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
        order_desc: bool = True,
    ) -> List[VectorDocument]:
        """按元数据过滤列出文档（按 created_at 排序，默认最新在前）

        用途：可视化记忆浏览（非语义搜索，纯时间线/列表）。
        """
        raise NotImplementedError

    async def delete_by_metadata(
        self,
        filter_metadata: Dict[str, Any],
    ) -> int:
        """按元数据过滤批量删除，返回删除数量。"""
        raise NotImplementedError


class InMemoryVectorStore(VectorStoreBase):
    """内存向量存储 - 开发测试用"""

    def __init__(self, persist_path: Optional[str] = None):
        self._documents: Dict[str, VectorDocument] = {}
        self._persist_path = persist_path
        self._load_from_disk()

    def _load_from_disk(self):
        """从磁盘加载"""
        if self._persist_path and os.path.exists(self._persist_path):
            try:
                with open(self._persist_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for doc_data in data:
                        doc = VectorDocument(
                            id=doc_data["id"],
                            text=doc_data["text"],
                            vector=doc_data["vector"],
                            metadata=doc_data.get("metadata", {}),
                            created_at=datetime.fromisoformat(doc_data.get("created_at", datetime.utcnow().isoformat()))
                        )
                        self._documents[doc.id] = doc
            except Exception as e:
                print(f"Warning: Failed to load vector store from disk: {e}")

    def _save_to_disk(self):
        """保存到磁盘"""
        if self._persist_path:
            try:
                data = [
                    {
                        "id": doc.id,
                        "text": doc.text,
                        "vector": doc.vector,
                        "metadata": doc.metadata,
                        "created_at": doc.created_at.isoformat()
                    }
                    for doc in self._documents.values()
                ]
                os.makedirs(os.path.dirname(self._persist_path), exist_ok=True)
                with open(self._persist_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False)
            except Exception as e:
                print(f"Warning: Failed to save vector store to disk: {e}")

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if len(vec1) != len(vec2):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)

    async def add(self, doc: VectorDocument) -> str:
        """添加文档"""
        self._documents[doc.id] = doc
        self._save_to_disk()
        return doc.id

    async def add_batch(self, docs: List[VectorDocument]) -> List[str]:
        """批量添加文档"""
        ids = []
        for doc in docs:
            self._documents[doc.id] = doc
            ids.append(doc.id)
        self._save_to_disk()
        return ids

    async def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[SearchResult]:
        """搜索相似向量"""
        results = []

        for doc in self._documents.values():
            # 元数据过滤
            if filter_metadata:
                match = all(
                    doc.metadata.get(k) == v
                    for k, v in filter_metadata.items()
                )
                if not match:
                    continue

            # 计算相似度
            score = self._cosine_similarity(query_vector, doc.vector)

            if score >= score_threshold:
                results.append(SearchResult(
                    id=doc.id,
                    text=doc.text,
                    score=score,
                    metadata=doc.metadata
                ))

        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

    async def delete(self, doc_id: str) -> bool:
        """删除文档"""
        if doc_id in self._documents:
            del self._documents[doc_id]
            self._save_to_disk()
            return True
        return False

    async def get(self, doc_id: str) -> Optional[VectorDocument]:
        """获取文档"""
        return self._documents.get(doc_id)

    @staticmethod
    def _match_filter(doc: VectorDocument, filter_metadata: Optional[Dict[str, Any]]) -> bool:
        if not filter_metadata:
            return True
        return all(doc.metadata.get(k) == v for k, v in filter_metadata.items())

    async def count(self, filter_metadata: Optional[Dict[str, Any]] = None) -> int:
        """文档数量（可按元数据过滤）"""
        if not filter_metadata:
            return len(self._documents)
        return sum(1 for doc in self._documents.values() if self._match_filter(doc, filter_metadata))

    async def list_by_metadata(
        self,
        filter_metadata: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
        order_desc: bool = True,
    ) -> List[VectorDocument]:
        """按元数据过滤列出文档（按 created_at 排序）"""
        filtered = [
            doc for doc in self._documents.values()
            if self._match_filter(doc, filter_metadata)
        ]
        filtered.sort(key=lambda d: d.created_at, reverse=order_desc)
        return filtered[offset:offset + limit]

    async def delete_by_metadata(
        self,
        filter_metadata: Dict[str, Any],
    ) -> int:
        """按元数据批量删除。"""
        if not filter_metadata:
            return 0
        to_delete = [
            doc_id for doc_id, doc in self._documents.items()
            if self._match_filter(doc, filter_metadata)
        ]
        for doc_id in to_delete:
            del self._documents[doc_id]
        if to_delete:
            self._save_to_disk()
        return len(to_delete)


class ChromaVectorStore(VectorStoreBase):
    """ChromaDB向量存储"""

    def __init__(
        self,
        collection_name: str = "mindpal_memory",
        persist_directory: Optional[str] = None
    ):
        self.collection_name = collection_name
        self.persist_directory = persist_directory or "./data/chroma"
        self._client = None
        self._collection = None

    def _get_client(self):
        """懒加载ChromaDB客户端"""
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings

                self._client = chromadb.Client(Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=self.persist_directory,
                    anonymized_telemetry=False
                ))
            except ImportError:
                raise ImportError("请安装 chromadb: pip install chromadb")
        return self._client

    def _get_collection(self):
        """获取集合"""
        if self._collection is None:
            client = self._get_client()
            self._collection = client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
        return self._collection

    async def add(self, doc: VectorDocument) -> str:
        """添加文档"""
        collection = self._get_collection()
        collection.add(
            ids=[doc.id],
            embeddings=[doc.vector],
            documents=[doc.text],
            metadatas=[{**doc.metadata, "created_at": doc.created_at.isoformat()}]
        )
        return doc.id

    async def add_batch(self, docs: List[VectorDocument]) -> List[str]:
        """批量添加文档"""
        if not docs:
            return []

        collection = self._get_collection()
        collection.add(
            ids=[doc.id for doc in docs],
            embeddings=[doc.vector for doc in docs],
            documents=[doc.text for doc in docs],
            metadatas=[{**doc.metadata, "created_at": doc.created_at.isoformat()} for doc in docs]
        )
        return [doc.id for doc in docs]

    async def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[SearchResult]:
        """搜索相似向量"""
        collection = self._get_collection()

        where = filter_metadata if filter_metadata else None

        results = collection.query(
            query_embeddings=[query_vector],
            n_results=limit,
            where=where
        )

        search_results = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                # ChromaDB返回的是距离，需要转换为相似度
                distance = results["distances"][0][i] if results.get("distances") else 0
                score = 1 - distance  # 余弦距离转相似度

                if score >= score_threshold:
                    search_results.append(SearchResult(
                        id=doc_id,
                        text=results["documents"][0][i] if results.get("documents") else "",
                        score=score,
                        metadata=results["metadatas"][0][i] if results.get("metadatas") else {}
                    ))

        return search_results

    async def delete(self, doc_id: str) -> bool:
        """删除文档"""
        try:
            collection = self._get_collection()
            collection.delete(ids=[doc_id])
            return True
        except Exception:
            return False

    async def get(self, doc_id: str) -> Optional[VectorDocument]:
        """获取文档"""
        collection = self._get_collection()
        result = collection.get(ids=[doc_id], include=["embeddings", "documents", "metadatas"])

        if result["ids"]:
            return VectorDocument(
                id=result["ids"][0],
                text=result["documents"][0] if result.get("documents") else "",
                vector=result["embeddings"][0] if result.get("embeddings") else [],
                metadata=result["metadatas"][0] if result.get("metadatas") else {}
            )
        return None

    async def count(self, filter_metadata: Optional[Dict[str, Any]] = None) -> int:
        """文档数量（ChromaDB 通过 get(where=) 过滤）"""
        collection = self._get_collection()
        if not filter_metadata:
            return collection.count()
        # Chroma 没有直接的条件 count，用 get() 后取长度
        result = collection.get(where=filter_metadata, include=[])
        return len(result.get("ids", []))

    async def list_by_metadata(
        self,
        filter_metadata: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
        order_desc: bool = True,
    ) -> List[VectorDocument]:
        """按元数据列出文档（Chroma 本身无排序支持，取回后本地排序）"""
        collection = self._get_collection()
        result = collection.get(
            where=filter_metadata or {},
            include=["embeddings", "documents", "metadatas"]
        )
        ids = result.get("ids", [])
        docs: List[VectorDocument] = []
        for i, doc_id in enumerate(ids):
            metadata = result["metadatas"][i] if result.get("metadatas") else {}
            created_at_str = metadata.get("created_at")
            created_at = (
                datetime.fromisoformat(created_at_str)
                if created_at_str else datetime.utcnow()
            )
            docs.append(VectorDocument(
                id=doc_id,
                text=result["documents"][i] if result.get("documents") else "",
                vector=result["embeddings"][i] if result.get("embeddings") else [],
                metadata=metadata,
                created_at=created_at,
            ))
        docs.sort(key=lambda d: d.created_at, reverse=order_desc)
        return docs[offset:offset + limit]

    async def delete_by_metadata(
        self,
        filter_metadata: Dict[str, Any],
    ) -> int:
        """按元数据批量删除"""
        if not filter_metadata:
            return 0
        collection = self._get_collection()
        result = collection.get(where=filter_metadata, include=[])
        ids = result.get("ids", [])
        if ids:
            collection.delete(ids=ids)
        return len(ids)


class VectorStore:
    """向量存储工厂"""

    _instance: Optional["VectorStore"] = None
    _store: Optional[VectorStoreBase] = None

    def __new__(cls, store_type: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_store(store_type)
        return cls._instance

    def _init_store(self, store_type: Optional[str] = None):
        """初始化存储"""
        store_type = store_type or os.getenv("VECTOR_STORE_TYPE", "memory")
        persist_path = os.getenv("VECTOR_STORE_PATH", "./data/vector_store")

        if store_type == "chroma":
            self._store = ChromaVectorStore(persist_directory=persist_path)
        else:
            self._store = InMemoryVectorStore(
                persist_path=os.path.join(persist_path, "memory_store.json")
            )

    async def add(self, doc: VectorDocument) -> str:
        return await self._store.add(doc)

    async def add_batch(self, docs: List[VectorDocument]) -> List[str]:
        return await self._store.add_batch(docs)

    async def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        score_threshold: float = 0.0
    ) -> List[SearchResult]:
        return await self._store.search(query_vector, limit, filter_metadata, score_threshold)

    async def delete(self, doc_id: str) -> bool:
        return await self._store.delete(doc_id)

    async def get(self, doc_id: str) -> Optional[VectorDocument]:
        return await self._store.get(doc_id)

    async def count(self, filter_metadata: Optional[Dict[str, Any]] = None) -> int:
        return await self._store.count(filter_metadata)

    async def list_by_metadata(
        self,
        filter_metadata: Optional[Dict[str, Any]] = None,
        limit: int = 50,
        offset: int = 0,
        order_desc: bool = True,
    ) -> List[VectorDocument]:
        return await self._store.list_by_metadata(filter_metadata, limit, offset, order_desc)

    async def delete_by_metadata(
        self,
        filter_metadata: Dict[str, Any],
    ) -> int:
        return await self._store.delete_by_metadata(filter_metadata)


# 便捷函数
_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """获取全局向量存储实例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore()
    return _vector_store
