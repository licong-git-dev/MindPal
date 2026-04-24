"""
文本分块服务
将长文本切分为适合向量化的小块
"""

import re
from typing import List, Dict


class ChunkingService:
    """文本分块服务"""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        初始化分块服务

        Args:
            chunk_size: 每个块的最大字符数 (默认500字符)
            chunk_overlap: 块之间的重叠字符数 (默认50字符)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str, metadata: dict = None) -> List[Dict]:
        """
        将文本分割为多个块

        Args:
            text: 原始文本
            metadata: 元数据(文件名、来源等)

        Returns:
            [
                {
                    'content': str,  # 块内容
                    'index': int,  # 块索引
                    'metadata': dict  # 元数据
                },
                ...
            ]
        """
        if not text or not text.strip():
            return []

        # 清理文本
        text = self._clean_text(text)

        # 按段落分割
        paragraphs = self._split_by_paragraphs(text)

        # 生成块
        chunks = []
        current_chunk = ""
        chunk_index = 0

        for para in paragraphs:
            # 如果单个段落太长,需要进一步分割
            if len(para) > self.chunk_size:
                # 先保存当前块
                if current_chunk.strip():
                    chunks.append(self._create_chunk(
                        current_chunk.strip(),
                        chunk_index,
                        metadata
                    ))
                    chunk_index += 1
                    current_chunk = ""

                # 分割长段落
                sub_chunks = self._split_long_paragraph(para)
                for sub_chunk in sub_chunks:
                    chunks.append(self._create_chunk(
                        sub_chunk,
                        chunk_index,
                        metadata
                    ))
                    chunk_index += 1

            # 正常段落处理
            elif len(current_chunk) + len(para) + 2 > self.chunk_size:
                # 当前块已满,保存并开始新块
                if current_chunk.strip():
                    chunks.append(self._create_chunk(
                        current_chunk.strip(),
                        chunk_index,
                        metadata
                    ))
                    chunk_index += 1

                # 使用overlap创建新块
                current_chunk = self._get_overlap(current_chunk) + para
            else:
                # 添加到当前块
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        # 保存最后一个块
        if current_chunk.strip():
            chunks.append(self._create_chunk(
                current_chunk.strip(),
                chunk_index,
                metadata
            ))

        return chunks

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余空白
        text = re.sub(r'\s+', ' ', text)
        # 移除特殊字符
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        return text.strip()

    def _split_by_paragraphs(self, text: str) -> List[str]:
        """按段落分割文本"""
        # 按双换行或多个换行分割
        paragraphs = re.split(r'\n\s*\n', text)
        # 过滤空段落
        return [p.strip() for p in paragraphs if p.strip()]

    def _split_long_paragraph(self, paragraph: str) -> List[str]:
        """分割过长的段落"""
        chunks = []
        sentences = self._split_by_sentences(paragraph)

        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > self.chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _split_by_sentences(self, text: str) -> List[str]:
        """按句子分割文本"""
        # 中英文句子分割
        sentences = re.split(r'([。！？.!?])', text)

        result = []
        for i in range(0, len(sentences) - 1, 2):
            sentence = sentences[i] + (sentences[i + 1] if i + 1 < len(sentences) else '')
            if sentence.strip():
                result.append(sentence.strip())

        return result

    def _get_overlap(self, text: str) -> str:
        """获取重叠部分"""
        if len(text) <= self.chunk_overlap:
            return text

        # 从末尾取overlap长度的文本
        overlap_text = text[-self.chunk_overlap:]

        # 尝试从完整句子开始
        sentences = self._split_by_sentences(overlap_text)
        if sentences:
            return sentences[0] + "\n\n"

        return overlap_text + "\n\n"

    def _create_chunk(self, content: str, index: int, metadata: dict = None) -> Dict:
        """创建chunk对象"""
        chunk = {
            'content': content,
            'index': index,
            'char_count': len(content),
            'word_count': len(content.split())
        }

        if metadata:
            chunk['metadata'] = metadata

        return chunk


# 默认分块器实例
default_chunker = ChunkingService(chunk_size=500, chunk_overlap=50)
