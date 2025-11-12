"""
向量数据库服务
使用 FAISS 存储和检索文本向量
"""

import os
import json
import pickle
import numpy as np
import faiss
from typing import List, Dict, Optional
from datetime import datetime
import dashscope
from dashscope import TextEmbedding


class VectorStore:
    """FAISS向量存储"""

    def __init__(self, dh_id: int, dimension: int = 1536):
        """
        初始化向量存储

        Args:
            dh_id: 数字人ID
            dimension: 向量维度 (Alibaba Cloud text-embedding-v2 = 1536)
        """
        self.dh_id = dh_id
        self.dimension = dimension
        self.index = None
        self.metadata = []  # 存储每个向量对应的元数据

        # 存储路径
        self.storage_dir = os.path.join('backend', 'data', 'vectors', str(dh_id))
        self.index_file = os.path.join(self.storage_dir, 'faiss.index')
        self.metadata_file = os.path.join(self.storage_dir, 'metadata.pkl')

        # 创建存储目录
        os.makedirs(self.storage_dir, exist_ok=True)

        # 加载或创建索引
        self._load_or_create_index()

    def _load_or_create_index(self):
        """加载或创建FAISS索引"""
        if os.path.exists(self.index_file) and os.path.exists(self.metadata_file):
            # 加载已有索引
            try:
                self.index = faiss.read_index(self.index_file)
                with open(self.metadata_file, 'rb') as f:
                    self.metadata = pickle.load(f)
                print(f"[VectorStore] 加载已有索引: {self.index.ntotal} 个向量")
            except Exception as e:
                print(f"[VectorStore] 加载索引失败: {e}, 创建新索引")
                self._create_new_index()
        else:
            # 创建新索引
            self._create_new_index()

    def _create_new_index(self):
        """创建新的FAISS索引"""
        # 使用 L2 距离的 IndexFlatL2 (精确搜索)
        self.index = faiss.IndexFlatL2(self.dimension)
        self.metadata = []
        print(f"[VectorStore] 创建新索引 (dimension={self.dimension})")

    def add_texts(self, texts: List[str], metadata_list: List[Dict] = None) -> bool:
        """
        添加文本到向量库

        Args:
            texts: 文本列表
            metadata_list: 每个文本对应的元数据

        Returns:
            是否成功
        """
        if not texts:
            return False

        try:
            # 生成向量
            embeddings = self._generate_embeddings(texts)
            if embeddings is None:
                return False

            # 添加到索引
            embeddings_array = np.array(embeddings).astype('float32')
            self.index.add(embeddings_array)

            # 保存元数据
            if metadata_list is None:
                metadata_list = [{} for _ in texts]

            for i, text in enumerate(texts):
                self.metadata.append({
                    'text': text,
                    'index': len(self.metadata),
                    'added_at': datetime.utcnow().isoformat(),
                    **metadata_list[i]
                })

            # 持久化
            self._save()

            print(f"[VectorStore] 添加 {len(texts)} 个文本, 总数: {self.index.ntotal}")
            return True

        except Exception as e:
            print(f"[VectorStore] 添加文本失败: {e}")
            return False

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        搜索相似文本

        Args:
            query: 查询文本
            top_k: 返回前k个最相似的结果

        Returns:
            [
                {
                    'text': str,
                    'score': float,  # 相似度分数(距离越小越相似)
                    'metadata': dict
                },
                ...
            ]
        """
        if self.index.ntotal == 0:
            return []

        try:
            # 生成查询向量
            query_embedding = self._generate_embeddings([query])
            if query_embedding is None:
                return []

            # 搜索
            query_vector = np.array(query_embedding).astype('float32')
            distances, indices = self.index.search(query_vector, min(top_k, self.index.ntotal))

            # 构造结果
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.metadata):
                    meta = self.metadata[idx]
                    results.append({
                        'text': meta.get('text', ''),
                        'score': float(distance),
                        'metadata': {k: v for k, v in meta.items() if k != 'text'}
                    })

            return results

        except Exception as e:
            print(f"[VectorStore] 搜索失败: {e}")
            return []

    def delete_by_doc_id(self, doc_id: int) -> bool:
        """
        删除指定文档的所有向量

        注意: FAISS IndexFlatL2 不支持直接删除,需要重建索引

        Args:
            doc_id: 文档ID

        Returns:
            是否成功
        """
        try:
            # 过滤掉要删除的元数据
            new_metadata = [m for m in self.metadata if m.get('doc_id') != doc_id]

            if len(new_metadata) == len(self.metadata):
                print(f"[VectorStore] 未找到doc_id={doc_id}的向量")
                return False

            # 提取剩余文本
            remaining_texts = [m['text'] for m in new_metadata]

            # 重建索引
            self._create_new_index()

            if remaining_texts:
                # 重新生成向量
                embeddings = self._generate_embeddings(remaining_texts)
                if embeddings:
                    embeddings_array = np.array(embeddings).astype('float32')
                    self.index.add(embeddings_array)

            self.metadata = new_metadata

            # 持久化
            self._save()

            print(f"[VectorStore] 删除doc_id={doc_id}, 剩余: {self.index.ntotal}")
            return True

        except Exception as e:
            print(f"[VectorStore] 删除失败: {e}")
            return False

    def _generate_embeddings(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        使用阿里云API生成文本向量

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        try:
            # 调用阿里云Embedding API
            response = TextEmbedding.call(
                model=TextEmbedding.Models.text_embedding_v2,
                input=texts
            )

            if response.status_code == 200:
                embeddings = [item['embedding'] for item in response.output['embeddings']]
                return embeddings
            else:
                print(f"[VectorStore] Embedding API错误: {response.code} - {response.message}")
                return None

        except Exception as e:
            print(f"[VectorStore] 生成向量失败: {e}")
            return None

    def _save(self):
        """保存索引和元数据"""
        try:
            faiss.write_index(self.index, self.index_file)
            with open(self.metadata_file, 'wb') as f:
                pickle.dump(self.metadata, f)
            print(f"[VectorStore] 索引已保存: {self.index_file}")
        except Exception as e:
            print(f"[VectorStore] 保存索引失败: {e}")

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'storage_path': self.storage_dir
        }

    def clear(self):
        """清空索引"""
        self._create_new_index()
        self._save()
        print(f"[VectorStore] 索引已清空")
