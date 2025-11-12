"""
RAG (Retrieval-Augmented Generation) 服务
结合向量检索和LLM生成,提供知识增强的对话
"""

from typing import List, Dict, Optional
from app.services.vector_store import VectorStore
from app.services.chunking_service import ChunkingService
from app.services.file_parser import FileParser
from app.models import db, KnowledgeDoc
import os


class RAGService:
    """RAG检索增强生成服务"""

    def __init__(self, dh_id: int):
        """
        初始化RAG服务

        Args:
            dh_id: 数字人ID
        """
        self.dh_id = dh_id
        self.vector_store = VectorStore(dh_id)
        self.chunker = ChunkingService(chunk_size=500, chunk_overlap=50)

    def process_document(self, doc_id: int, file_path: str, filename: str) -> Dict:
        """
        处理文档: 解析 -> 分块 -> 向量化 -> 存储

        Args:
            doc_id: 数据库中的文档ID
            file_path: 文件路径
            filename: 文件名

        Returns:
            {
                'success': bool,
                'chunks_count': int,
                'error': str
            }
        """
        try:
            # 1. 解析文件
            print(f"[RAG] 解析文件: {filename}")
            parse_result = FileParser.parse(file_path)

            if not parse_result['success']:
                return {
                    'success': False,
                    'error': parse_result['error']
                }

            content = parse_result['content']
            metadata = parse_result.get('metadata', {})

            print(f"[RAG] 解析成功: {metadata.get('words', 0)} 词")

            # 2. 文本分块
            print(f"[RAG] 开始分块...")
            chunks = self.chunker.split_text(content, metadata={
                'doc_id': doc_id,
                'filename': filename
            })

            if not chunks:
                return {
                    'success': False,
                    'error': '文档内容为空或分块失败'
                }

            print(f"[RAG] 分块完成: {len(chunks)} 个块")

            # 3. 向量化并存储
            print(f"[RAG] 生成向量并存储...")
            texts = [chunk['content'] for chunk in chunks]
            metadata_list = [chunk.get('metadata', {}) for chunk in chunks]

            success = self.vector_store.add_texts(texts, metadata_list)

            if not success:
                return {
                    'success': False,
                    'error': '向量化失败'
                }

            print(f"[RAG] 文档处理完成")

            return {
                'success': True,
                'chunks_count': len(chunks),
                'words': metadata.get('words', 0)
            }

        except Exception as e:
            print(f"[RAG] 处理文档失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        检索相关知识

        Args:
            query: 用户查询
            top_k: 返回top k个最相关的片段

        Returns:
            [
                {
                    'content': str,  # 文本内容
                    'score': float,  # 相似度分数
                    'source': str,  # 来源文档
                    'metadata': dict
                },
                ...
            ]
        """
        try:
            # 向量搜索
            results = self.vector_store.search(query, top_k=top_k)

            # 格式化结果
            knowledge_items = []
            for result in results:
                knowledge_items.append({
                    'content': result['text'],
                    'score': result['score'],
                    'source': result['metadata'].get('filename', '未知'),
                    'metadata': result['metadata']
                })

            return knowledge_items

        except Exception as e:
            print(f"[RAG] 检索失败: {e}")
            return []

    def build_context(self, query: str, top_k: int = 3, max_tokens: int = 2000) -> str:
        """
        构建RAG上下文

        Args:
            query: 用户查询
            top_k: 检索top k
            max_tokens: 最大token数(估算:1个汉字≈2 tokens)

        Returns:
            格式化的上下文字符串
        """
        knowledge_items = self.retrieve(query, top_k=top_k)

        if not knowledge_items:
            return ""

        # 构建上下文
        context_parts = ["【相关知识】\n"]

        total_chars = 0
        max_chars = max_tokens // 2  # 粗略估算

        for i, item in enumerate(knowledge_items, 1):
            content = item['content']
            source = item['source']

            # 检查是否超出限制
            if total_chars + len(content) > max_chars:
                # 截断内容
                remaining = max_chars - total_chars
                if remaining > 100:  # 至少保留100字
                    content = content[:remaining] + "..."
                else:
                    break

            context_parts.append(f"{i}. 【来源: {source}】")
            context_parts.append(content)
            context_parts.append("")  # 空行

            total_chars += len(content)

        return "\n".join(context_parts)

    def delete_document(self, doc_id: int) -> bool:
        """
        删除文档的向量数据

        Args:
            doc_id: 文档ID

        Returns:
            是否成功
        """
        try:
            return self.vector_store.delete_by_doc_id(doc_id)
        except Exception as e:
            print(f"[RAG] 删除文档向量失败: {e}")
            return False

    def get_stats(self) -> Dict:
        """获取RAG统计信息"""
        stats = self.vector_store.get_stats()

        # 查询数据库中的文档数
        doc_count = KnowledgeDoc.query.filter_by(
            dh_id=self.dh_id,
            status='completed'
        ).count()

        stats['documents_count'] = doc_count

        return stats


# 工具函数
def get_rag_service(dh_id: int) -> RAGService:
    """获取数字人的RAG服务实例"""
    return RAGService(dh_id)
