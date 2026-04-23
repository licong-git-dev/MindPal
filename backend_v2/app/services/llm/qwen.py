"""
MindPal Backend V2 - Qwen (通义千问) LLM Service
"""

from typing import AsyncGenerator, Dict, List, Optional
import httpx
import json

from app.services.llm.base import BaseLLMService
from app.config import settings


class QwenService(BaseLLMService):
    """阿里云通义千问服务"""

    def __init__(self):
        self.api_key = settings.DASHSCOPE_API_KEY
        self.model = settings.QWEN_MODEL
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

    def _build_messages(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str
    ) -> List[Dict[str, str]]:
        """构建消息列表，添加系统提示"""
        result = [{"role": "system", "content": system_prompt}]
        result.extend(messages)
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
            return "[错误] 未配置DASHSCOPE_API_KEY"

        full_messages = self._build_messages(messages, system_prompt)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "input": {
                "messages": full_messages
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "result_format": "message",
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.base_url,
                headers=headers,
                json=payload
            )

            if response.status_code != 200:
                return f"[错误] API请求失败: {response.status_code}"

            result = response.json()

            if "output" in result and "choices" in result["output"]:
                return result["output"]["choices"][0]["message"]["content"]
            elif "output" in result and "text" in result["output"]:
                return result["output"]["text"]
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
            yield "[错误] 未配置DASHSCOPE_API_KEY"
            return

        full_messages = self._build_messages(messages, system_prompt)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-SSE": "enable",
        }

        payload = {
            "model": self.model,
            "input": {
                "messages": full_messages
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "result_format": "message",
                "incremental_output": True,
            }
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
                            if "output" in chunk:
                                if "choices" in chunk["output"]:
                                    content = chunk["output"]["choices"][0]["message"].get("content", "")
                                    if content:
                                        yield content
                                elif "text" in chunk["output"]:
                                    yield chunk["output"]["text"]
                        except json.JSONDecodeError:
                            continue

    async def analyze_emotion(self, text: str) -> Dict[str, float]:
        """情感分析"""
        prompt = f"""请分析以下文本的情感，返回JSON格式的情感分数（0-1）：
- joy（喜悦）
- sadness（悲伤）
- anger（愤怒）
- fear（恐惧）
- surprise（惊讶）
- neutral（中性）

文本：{text}

请只返回JSON，格式如：{{"joy": 0.8, "sadness": 0.1, "anger": 0.0, "fear": 0.0, "surprise": 0.1, "neutral": 0.0}}"""

        response = await self.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="你是一个情感分析专家，只返回JSON格式的分析结果。",
            temperature=0.3,
            max_tokens=200,
        )

        try:
            # 尝试提取JSON
            import re
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                return json.loads(json_match.group())
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
