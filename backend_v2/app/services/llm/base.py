"""
MindPal Backend V2 - LLM Service Base Class
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional, Any


class BaseLLMService(ABC):
    """LLM服务抽象基类"""

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """
        同步对话

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大token数

        Returns:
            AI回复文本
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式对话

        Yields:
            AI回复文本片段
        """
        pass

    @abstractmethod
    async def analyze_emotion(self, text: str) -> Dict[str, float]:
        """
        情感分析

        Args:
            text: 待分析文本

        Returns:
            情感分数字典 {"joy": 0.8, "sadness": 0.1, ...}
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """获取模型名称"""
        pass
