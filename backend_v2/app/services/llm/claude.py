"""
MindPal Backend V2 - Claude LLM Service
"""

from typing import AsyncGenerator, Dict, List, Optional
import httpx
import json

from app.services.llm.base import BaseLLMService
from app.config import settings


class ClaudeService(BaseLLMService):
    """Anthropic Claude服务 - 专门用于情感对话"""

    def __init__(self):
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.CLAUDE_MODEL
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.version = "2023-06-01"

    def _build_messages(
        self,
        messages: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        """构建Claude格式的消息列表"""
        result = []
        for msg in messages:
            role = msg["role"]
            # Claude使用"user"和"assistant"
            if role == "system":
                continue  # system消息单独处理
            result.append({
                "role": role,
                "content": msg["content"]
            })
        return result

    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> str:
        """同步对话"""
        if not self.api_key:
            return "[错误] 未配置ANTHROPIC_API_KEY"

        claude_messages = self._build_messages(messages)

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.version,
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": claude_messages,
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.base_url,
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                return f"[错误] API请求失败: {response.status_code} - {response.text}"

            result = response.json()

            if "content" in result and len(result["content"]) > 0:
                return result["content"][0]["text"]
            else:
                return f"[错误] 无法解析响应: {result}"

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        if not self.api_key:
            yield "[错误] 未配置ANTHROPIC_API_KEY"
            return

        claude_messages = self._build_messages(messages)

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.version,
            "content-type": "application/json",
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": claude_messages,
            "stream": True,
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream(
                "POST",
                self.base_url,
                headers=headers,
                json=payload
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            if chunk.get("type") == "content_block_delta":
                                delta = chunk.get("delta", {})
                                if delta.get("type") == "text_delta":
                                    text = delta.get("text", "")
                                    if text:
                                        yield text
                        except json.JSONDecodeError:
                            continue

    async def analyze_emotion(self, text: str) -> Dict[str, float]:
        """情感分析 - Claude擅长的领域"""
        prompt = f"""请分析以下文本的情感状态，我需要你返回一个JSON对象，包含以下情感的强度评分（0到1之间的小数）：

- joy（喜悦）
- sadness（悲伤）
- anger（愤怒）
- fear（恐惧）
- surprise（惊讶）
- neutral（中性）

所有分数之和应该等于1。

文本内容：
"{text}"

请直接返回JSON对象，不要有其他文字。"""

        response = await self.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="你是一位专业的情感分析专家。请只返回JSON格式的分析结果，不要包含任何其他文字说明。",
            temperature=0.3,
            max_tokens=200,
        )

        try:
            # 尝试提取JSON
            import re
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                result = json.loads(json_match.group())
                # 验证字段存在
                required_fields = ["joy", "sadness", "anger", "fear", "surprise", "neutral"]
                if all(field in result for field in required_fields):
                    return result
        except:
            pass

        # 默认返回中性
        return {
            "joy": 0.0,
            "sadness": 0.0,
            "anger": 0.0,
            "fear": 0.0,
            "surprise": 0.0,
            "neutral": 1.0,
        }

    def get_model_name(self) -> str:
        return self.model
