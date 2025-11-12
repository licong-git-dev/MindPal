"""
文件解析服务
支持 PDF, DOCX, TXT, MD 等格式的文本提取
"""

import os
from typing import Optional
from PyPDF2 import PdfReader
from docx import Document


class FileParser:
    """文件解析器"""

    SUPPORTED_FORMATS = {
        'pdf': 'PDF文档',
        'docx': 'Word文档',
        'txt': '文本文件',
        'md': 'Markdown文件'
    }

    @staticmethod
    def is_supported(filename: str) -> bool:
        """检查文件格式是否支持"""
        ext = filename.lower().split('.')[-1]
        return ext in FileParser.SUPPORTED_FORMATS

    @staticmethod
    def get_file_type(filename: str) -> Optional[str]:
        """获取文件类型"""
        ext = filename.lower().split('.')[-1]
        return ext if ext in FileParser.SUPPORTED_FORMATS else None

    @staticmethod
    def parse(file_path: str) -> dict:
        """
        解析文件,提取文本内容

        Args:
            file_path: 文件路径

        Returns:
            {
                'success': bool,
                'content': str,  # 提取的文本内容
                'metadata': dict,  # 元数据(页数、字数等)
                'error': str  # 错误信息(如果失败)
            }
        """
        if not os.path.exists(file_path):
            return {
                'success': False,
                'error': '文件不存在'
            }

        filename = os.path.basename(file_path)
        file_type = FileParser.get_file_type(filename)

        if not file_type:
            return {
                'success': False,
                'error': f'不支持的文件格式'
            }

        try:
            if file_type == 'pdf':
                return FileParser._parse_pdf(file_path)
            elif file_type == 'docx':
                return FileParser._parse_docx(file_path)
            elif file_type in ['txt', 'md']:
                return FileParser._parse_text(file_path)
            else:
                return {
                    'success': False,
                    'error': f'未实现的文件类型: {file_type}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'解析文件失败: {str(e)}'
            }

    @staticmethod
    def _parse_pdf(file_path: str) -> dict:
        """解析PDF文件"""
        try:
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)

            # 提取所有页面的文本
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text.strip():
                    text_parts.append(text)

            content = '\n\n'.join(text_parts)

            return {
                'success': True,
                'content': content,
                'metadata': {
                    'pages': num_pages,
                    'words': len(content.split()),
                    'chars': len(content)
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'PDF解析失败: {str(e)}'
            }

    @staticmethod
    def _parse_docx(file_path: str) -> dict:
        """解析DOCX文件"""
        try:
            doc = Document(file_path)

            # 提取所有段落
            paragraphs = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraphs.append(text)

            content = '\n\n'.join(paragraphs)

            return {
                'success': True,
                'content': content,
                'metadata': {
                    'paragraphs': len(paragraphs),
                    'words': len(content.split()),
                    'chars': len(content)
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'DOCX解析失败: {str(e)}'
            }

    @staticmethod
    def _parse_text(file_path: str) -> dict:
        """解析纯文本文件"""
        try:
            # 尝试多种编码
            encodings = ['utf-8', 'gbk', 'gb2312', 'utf-16']
            content = None

            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                return {
                    'success': False,
                    'error': '无法识别文件编码'
                }

            return {
                'success': True,
                'content': content,
                'metadata': {
                    'lines': len(content.split('\n')),
                    'words': len(content.split()),
                    'chars': len(content)
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'文本解析失败: {str(e)}'
            }
