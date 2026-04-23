# 09. AI集成详细设计

> MindPal PRD - AI Integration Design
> 版本: 1.0 | 更新: 2024-01

---

## 1. AI服务架构总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        Godot 客户端                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 语音输入模块  │  │ 文字输入模块  │  │ 表情识别模块  │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                 │                 │                   │
│         └─────────────────┼─────────────────┘                   │
│                           ▼                                     │
│                  ┌────────────────┐                             │
│                  │  AI请求管理器   │                             │
│                  └────────┬───────┘                             │
└───────────────────────────┼─────────────────────────────────────┘
                            │ WebSocket / HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Python 后端服务                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    AI Gateway Layer                       │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │   │
│  │  │ 请求路由器   │ │ 上下文管理器 │ │ 响应处理器   │        │   │
│  │  └─────────────┘ └─────────────┘ └─────────────┘        │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                             │                                   │
│  ┌──────────────────────────┼───────────────────────────────┐   │
│  │              LLM Service Abstraction Layer                │   │
│  │                          │                                │   │
│  │    ┌─────────┐    ┌─────────┐    ┌─────────┐            │   │
│  │    │ Qwen    │    │ Claude  │    │ 火山引擎 │            │   │
│  │    │ Adapter │    │ Adapter │    │ Adapter │            │   │
│  │    └────┬────┘    └────┬────┘    └────┬────┘            │   │
│  └─────────┼──────────────┼──────────────┼──────────────────┘   │
│            │              │              │                       │
└────────────┼──────────────┼──────────────┼───────────────────────┘
             ▼              ▼              ▼
      ┌──────────┐   ┌──────────┐   ┌──────────┐
      │ 阿里云    │   │ Anthropic│   │ 火山引擎  │
      │ Qwen API │   │ Claude   │   │ 豆包 API │
      └──────────┘   └──────────┘   └──────────┘
```

---

## 2. LLM服务配置

### 2.1 服务分层策略

| 场景 | 主服务 | 备选服务 | 原因 |
|------|--------|----------|------|
| NPC日常对话 | Qwen-Turbo | 火山引擎-Lite | 成本低、响应快 |
| 深度情感对话 | Claude-3-Sonnet | Qwen-Max | 情感理解深度 |
| 商人交易对话 | Qwen-Plus | 火山引擎-Pro | 逻辑清晰 |
| 任务引导对话 | Qwen-Plus | Claude-3-Haiku | 结构化输出 |
| 宠物互动 | Qwen-Turbo | 火山引擎-Lite | 简单可爱 |
| 危机干预 | Claude-3-Opus | Qwen-Max | 安全最优先 |

### 2.2 服务配置文件

```yaml
# config/ai_services.yaml

services:
  qwen:
    base_url: "https://dashscope.aliyuncs.com/api/v1"
    models:
      turbo:
        name: "qwen-turbo"
        max_tokens: 1500
        temperature: 0.8
        cost_per_1k_tokens: 0.008  # 元
      plus:
        name: "qwen-plus"
        max_tokens: 2000
        temperature: 0.7
        cost_per_1k_tokens: 0.04
      max:
        name: "qwen-max"
        max_tokens: 4000
        temperature: 0.6
        cost_per_1k_tokens: 0.12
    rate_limit:
      requests_per_minute: 60
      tokens_per_minute: 100000

  claude:
    base_url: "https://api.anthropic.com/v1"
    models:
      haiku:
        name: "claude-3-haiku-20240307"
        max_tokens: 1000
        temperature: 0.7
        cost_per_1k_input: 0.00025
        cost_per_1k_output: 0.00125
      sonnet:
        name: "claude-3-sonnet-20240229"
        max_tokens: 2000
        temperature: 0.6
        cost_per_1k_input: 0.003
        cost_per_1k_output: 0.015
      opus:
        name: "claude-3-opus-20240229"
        max_tokens: 4000
        temperature: 0.5
        cost_per_1k_input: 0.015
        cost_per_1k_output: 0.075
    rate_limit:
      requests_per_minute: 50
      tokens_per_minute: 80000

  volcengine:
    base_url: "https://ark.cn-beijing.volces.com/api/v3"
    models:
      lite:
        name: "doubao-lite-32k"
        max_tokens: 1500
        temperature: 0.8
        cost_per_1k_tokens: 0.0003
      pro:
        name: "doubao-pro-32k"
        max_tokens: 2000
        temperature: 0.7
        cost_per_1k_tokens: 0.0008
    rate_limit:
      requests_per_minute: 100
      tokens_per_minute: 200000

routing:
  default_service: "qwen"
  fallback_chain:
    - "volcengine"
    - "claude"

  npc_routing:
    aela_guide:
      primary: "qwen.plus"
      fallback: "volcengine.pro"
    momo_merchant:
      primary: "qwen.plus"
      fallback: "volcengine.pro"
    chronos_quest:
      primary: "qwen.plus"
      fallback: "claude.haiku"
    bei_friend:
      primary: "claude.sonnet"
      fallback: "qwen.max"
      crisis: "claude.opus"
    sesame_pet:
      primary: "qwen.turbo"
      fallback: "volcengine.lite"
```

---

## 3. 对话系统实现

### 3.1 对话管理器 (Python)

```python
# app/services/dialogue/manager.py

from typing import Optional, List, Dict, Any
from enum import Enum
import asyncio
from datetime import datetime

from app.services.llm import LLMServiceFactory
from app.services.memory import ConversationMemory
from app.services.emotion import EmotionAnalyzer
from app.models.npc import NPCConfig
from app.models.dialogue import DialogueMessage, DialogueContext


class DialogueState(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    STREAMING = "streaming"
    WAITING_INPUT = "waiting_input"
    CRISIS_MODE = "crisis_mode"


class DialogueManager:
    """NPC对话管理器 - 处理完整的对话流程"""

    def __init__(
        self,
        npc_config: NPCConfig,
        player_id: str,
        memory: ConversationMemory,
        emotion_analyzer: EmotionAnalyzer
    ):
        self.npc = npc_config
        self.player_id = player_id
        self.memory = memory
        self.emotion = emotion_analyzer
        self.state = DialogueState.IDLE
        self.context = DialogueContext()

        # 初始化LLM服务
        self.llm = LLMServiceFactory.create(
            service_config=npc_config.llm_routing
        )

    async def process_message(
        self,
        user_message: str,
        user_emotion: Optional[Dict[str, float]] = None,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        处理用户消息并生成NPC回复

        Args:
            user_message: 用户输入的文字
            user_emotion: 情感分析结果 {"joy": 0.2, "sadness": 0.6, ...}
            stream: 是否流式输出

        Yields:
            NPC回复的文字片段
        """
        self.state = DialogueState.PROCESSING

        try:
            # 1. 情感分析与危机检测
            emotion_context = await self._analyze_emotion(
                user_message, user_emotion
            )

            if emotion_context.get("crisis_detected"):
                self.state = DialogueState.CRISIS_MODE
                async for chunk in self._handle_crisis(user_message, emotion_context):
                    yield chunk
                return

            # 2. 构建上下文
            context = await self._build_context(user_message, emotion_context)

            # 3. 生成回复
            self.state = DialogueState.STREAMING
            full_response = ""

            async for chunk in self.llm.stream_chat(
                messages=context["messages"],
                system_prompt=context["system_prompt"],
                temperature=self._get_temperature(emotion_context)
            ):
                full_response += chunk
                yield chunk

            # 4. 保存对话记录
            await self._save_dialogue(user_message, full_response, emotion_context)

        except Exception as e:
            yield f"[系统] 抱歉，我似乎有些走神了... ({str(e)[:50]})"

        finally:
            self.state = DialogueState.IDLE

    async def _analyze_emotion(
        self,
        message: str,
        detected_emotion: Optional[Dict[str, float]]
    ) -> Dict[str, Any]:
        """分析用户情感状态"""

        # 文本情感分析
        text_emotion = await self.emotion.analyze_text(message)

        # 综合表情和文字分析
        if detected_emotion:
            combined = self.emotion.combine_modalities(
                text_emotion=text_emotion,
                facial_emotion=detected_emotion,
                weights={"text": 0.6, "facial": 0.4}
            )
        else:
            combined = text_emotion

        # 危机检测
        crisis_keywords = [
            "不想活", "自杀", "结束生命", "活着没意思",
            "伤害自己", "割", "跳楼", "死"
        ]
        crisis_detected = any(kw in message for kw in crisis_keywords)

        # 情感强度评估
        intensity = max(combined.values()) if combined else 0.5

        return {
            "emotions": combined,
            "dominant": max(combined, key=combined.get) if combined else "neutral",
            "intensity": intensity,
            "crisis_detected": crisis_detected,
            "needs_comfort": combined.get("sadness", 0) > 0.6 or combined.get("fear", 0) > 0.5
        }

    async def _build_context(
        self,
        user_message: str,
        emotion_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """构建LLM请求上下文"""

        # 获取历史对话
        history = await self.memory.get_recent(
            player_id=self.player_id,
            npc_id=self.npc.id,
            limit=10
        )

        # 获取玩家档案
        player_profile = await self.memory.get_player_profile(self.player_id)

        # 获取相关记忆
        relevant_memories = await self.memory.search_relevant(
            player_id=self.player_id,
            query=user_message,
            limit=3
        )

        # 构建系统提示词
        system_prompt = self._build_system_prompt(
            emotion_context=emotion_context,
            player_profile=player_profile,
            relevant_memories=relevant_memories
        )

        # 构建消息列表
        messages = []
        for msg in history:
            messages.append({"role": "user", "content": msg.user_message})
            messages.append({"role": "assistant", "content": msg.npc_response})

        messages.append({"role": "user", "content": user_message})

        return {
            "system_prompt": system_prompt,
            "messages": messages
        }

    def _build_system_prompt(
        self,
        emotion_context: Dict[str, Any],
        player_profile: Dict[str, Any],
        relevant_memories: List[str]
    ) -> str:
        """动态构建系统提示词"""

        base_prompt = self.npc.system_prompt

        # 添加情感适应指令
        emotion_instruction = self._get_emotion_instruction(emotion_context)

        # 添加玩家个性化信息
        player_context = ""
        if player_profile:
            player_context = f"""
## 玩家信息
- 昵称偏好: {player_profile.get('nickname', '旅行者')}
- 交流风格: {player_profile.get('communication_style', '友好')}
- 已知兴趣: {', '.join(player_profile.get('interests', []))}
- 近期话题: {', '.join(player_profile.get('recent_topics', []))}
"""

        # 添加相关记忆
        memory_context = ""
        if relevant_memories:
            memory_context = f"""
## 相关历史对话记忆
{chr(10).join(f'- {m}' for m in relevant_memories)}
"""

        return f"""{base_prompt}

{emotion_instruction}

{player_context}

{memory_context}

## 当前情感状态
用户当前情绪: {emotion_context['dominant']}
情绪强度: {emotion_context['intensity']:.1%}
需要安慰: {'是' if emotion_context['needs_comfort'] else '否'}
"""

    def _get_emotion_instruction(self, emotion_context: Dict[str, Any]) -> str:
        """根据情感状态获取回复指令"""

        dominant = emotion_context["dominant"]
        intensity = emotion_context["intensity"]

        instructions = {
            "sadness": """
## 情感回应指令
用户正在经历悲伤情绪。请：
- 首先表达理解和共情，不要急于给建议
- 使用温柔、包容的语气
- 可以适当询问发生了什么，但不要追问
- 如果用户愿意倾诉，耐心倾听
- 在适当时候轻轻引导看到希望
""",
            "anger": """
## 情感回应指令
用户似乎有些愤怒或烦躁。请：
- 先认可用户的感受，表示理解
- 不要否定或试图立刻讲道理
- 给用户发泄的空间
- 用冷静但不冷漠的语气回应
- 适时转移注意力到轻松话题
""",
            "fear": """
## 情感回应指令
用户表现出担忧或恐惧。请：
- 提供安全感和陪伴感
- 用稳定、可靠的语气说话
- 帮助用户理清思路，分析担忧的根源
- 提供具体可行的建议
- 强调你会陪伴在身边
""",
            "joy": """
## 情感回应指令
用户心情不错！请：
- 回应用户的积极情绪
- 可以开玩笑、活泼一些
- 分享用户的快乐
- 鼓励用户继续保持好心情
"""
        }

        return instructions.get(dominant, "")

    async def _handle_crisis(
        self,
        message: str,
        emotion_context: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """危机干预处理"""

        # 切换到最安全的模型
        crisis_llm = LLMServiceFactory.create(
            service_name="claude",
            model_name="opus"
        )

        crisis_prompt = """
## 危机干预模式已激活

你正在与一个可能处于心理危机中的用户对话。这是最高优先级的安全场景。

### 核心原则
1. **不要评判** - 无论用户说什么，都表示理解
2. **保持冷静** - 用平稳、温和的语气
3. **表达关心** - 让用户知道有人在乎他们
4. **不要说教** - 不要讲大道理或"想开点"
5. **陪伴为主** - 让用户感到不孤单

### 必须做的事
- 表达你很担心他/她
- 询问现在是否安全
- 鼓励寻求专业帮助
- 提供危机热线：全国心理援助热线 400-161-9995
- 保持对话，不要让用户独处

### 绝对不能做的事
- 不要说"别想太多"、"想开点"
- 不要讨论具体的自伤方式
- 不要承诺保密（如果涉及生命安全）
- 不要离开或结束对话

### 回复格式
用最真诚、温暖的语气回复，像一个真正关心用户的朋友。
"""

        async for chunk in crisis_llm.stream_chat(
            messages=[{"role": "user", "content": message}],
            system_prompt=crisis_prompt,
            temperature=0.3  # 低温度确保稳定
        ):
            yield chunk

        # 记录危机事件（用于后续人工审核）
        await self._log_crisis_event(message, emotion_context)

    async def _save_dialogue(
        self,
        user_message: str,
        npc_response: str,
        emotion_context: Dict[str, Any]
    ):
        """保存对话记录"""

        dialogue = DialogueMessage(
            player_id=self.player_id,
            npc_id=self.npc.id,
            user_message=user_message,
            npc_response=npc_response,
            emotion=emotion_context["dominant"],
            emotion_intensity=emotion_context["intensity"],
            timestamp=datetime.utcnow()
        )

        await self.memory.save_dialogue(dialogue)

        # 更新玩家档案
        await self.memory.update_player_profile(
            player_id=self.player_id,
            recent_emotion=emotion_context["dominant"],
            recent_topic=await self._extract_topic(user_message)
        )

    def _get_temperature(self, emotion_context: Dict[str, Any]) -> float:
        """根据情感状态调整温度参数"""

        if emotion_context.get("crisis_detected"):
            return 0.3  # 危机模式：稳定输出

        if emotion_context.get("needs_comfort"):
            return 0.5  # 安慰模式：温和稳定

        if emotion_context["dominant"] == "joy":
            return 0.9  # 开心模式：活泼多变

        return 0.7  # 默认
```

### 3.2 LLM服务抽象层 (Python)

```python
# app/services/llm/base.py

from abc import ABC, abstractmethod
from typing import List, Dict, AsyncGenerator
import aiohttp
import asyncio


class LLMServiceBase(ABC):
    """LLM服务基类"""

    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7
    ) -> str:
        """同步获取完整回复"""
        pass

    @abstractmethod
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """流式获取回复"""
        pass


# app/services/llm/qwen.py

class QwenService(LLMServiceBase):
    """阿里云通义千问服务"""

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:

        session = await self._get_session()

        payload = {
            "model": self.model,
            "input": {
                "messages": [
                    {"role": "system", "content": system_prompt},
                    *messages
                ]
            },
            "parameters": {
                "temperature": temperature,
                "result_format": "message",
                "incremental_output": True
            }
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-SSE": "enable"
        }

        async with session.post(
            f"{self.base_url}/services/aigc/text-generation/generation",
            json=payload,
            headers=headers
        ) as response:
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data:'):
                    data = json.loads(line[5:])
                    if content := data.get("output", {}).get("text"):
                        yield content


# app/services/llm/claude.py

class ClaudeService(LLMServiceBase):
    """Anthropic Claude服务"""

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:

        session = await self._get_session()

        payload = {
            "model": self.model,
            "max_tokens": 2000,
            "system": system_prompt,
            "messages": messages,
            "temperature": temperature,
            "stream": True
        }

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2024-01-01",
            "content-type": "application/json"
        }

        async with session.post(
            f"{self.base_url}/messages",
            json=payload,
            headers=headers
        ) as response:
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data:'):
                    data = json.loads(line[5:])
                    if data["type"] == "content_block_delta":
                        yield data["delta"]["text"]


# app/services/llm/factory.py

class LLMServiceFactory:
    """LLM服务工厂"""

    _services = {
        "qwen": QwenService,
        "claude": ClaudeService,
        "volcengine": VolcEngineService
    }

    @classmethod
    def create(
        cls,
        service_config: Dict[str, Any] = None,
        service_name: str = None,
        model_name: str = None
    ) -> LLMServiceBase:

        if service_config:
            service_name = service_config["primary"].split(".")[0]
            model_name = service_config["primary"].split(".")[1]

        config = get_service_config(service_name, model_name)
        service_class = cls._services[service_name]

        return service_class(
            api_key=config["api_key"],
            base_url=config["base_url"],
            model=config["model_name"]
        )
```

---

## 4. 记忆系统实现

### 4.1 对话记忆架构

```
┌─────────────────────────────────────────────────────────────┐
│                     Memory System                            │
│                                                              │
│  ┌─────────────────┐    ┌─────────────────┐                 │
│  │  Short-term     │    │  Long-term      │                 │
│  │  Memory         │    │  Memory         │                 │
│  │  (Redis)        │    │  (PostgreSQL)   │                 │
│  │                 │    │                 │                 │
│  │  - 最近10轮对话  │    │  - 所有历史对话  │                 │
│  │  - 当前会话状态  │    │  - 玩家档案      │                 │
│  │  - 临时上下文    │    │  - 重要事件      │                 │
│  └────────┬────────┘    └────────┬────────┘                 │
│           │                      │                           │
│           └──────────┬───────────┘                           │
│                      │                                       │
│           ┌──────────▼──────────┐                           │
│           │  Semantic Memory    │                           │
│           │  (Qdrant)           │                           │
│           │                     │                           │
│           │  - 对话向量索引      │                           │
│           │  - 语义相似度搜索    │                           │
│           │  - 情感标签聚类      │                           │
│           └─────────────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 记忆管理器 (Python)

```python
# app/services/memory/manager.py

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.models.dialogue import DialogueMessage, PlayerProfile


class ConversationMemory:
    """对话记忆管理系统"""

    def __init__(
        self,
        redis_client: redis.Redis,
        db_session: AsyncSession,
        qdrant_client: QdrantClient,
        embedding_service: EmbeddingService
    ):
        self.redis = redis_client
        self.db = db_session
        self.qdrant = qdrant_client
        self.embedding = embedding_service

        # 确保Qdrant集合存在
        self._ensure_collection()

    def _ensure_collection(self):
        """确保向量数据库集合存在"""
        collections = self.qdrant.get_collections().collections
        if "dialogue_memory" not in [c.name for c in collections]:
            self.qdrant.create_collection(
                collection_name="dialogue_memory",
                vectors_config=VectorParams(
                    size=1536,  # OpenAI embedding维度
                    distance=Distance.COSINE
                )
            )

    async def get_recent(
        self,
        player_id: str,
        npc_id: str,
        limit: int = 10
    ) -> List[DialogueMessage]:
        """获取最近对话（优先从Redis）"""

        cache_key = f"dialogue:{player_id}:{npc_id}:recent"

        # 尝试从Redis获取
        cached = await self.redis.lrange(cache_key, 0, limit - 1)
        if cached:
            return [DialogueMessage.parse_raw(m) for m in cached]

        # 从数据库获取并缓存
        messages = await self._get_from_db(player_id, npc_id, limit)

        if messages:
            pipe = self.redis.pipeline()
            for msg in reversed(messages):
                pipe.lpush(cache_key, msg.json())
            pipe.expire(cache_key, 3600)  # 1小时过期
            await pipe.execute()

        return messages

    async def search_relevant(
        self,
        player_id: str,
        query: str,
        limit: int = 3
    ) -> List[str]:
        """语义搜索相关历史对话"""

        # 生成查询向量
        query_vector = await self.embedding.encode(query)

        # 在Qdrant中搜索
        results = self.qdrant.search(
            collection_name="dialogue_memory",
            query_vector=query_vector,
            query_filter={
                "must": [
                    {"key": "player_id", "match": {"value": player_id}}
                ]
            },
            limit=limit,
            score_threshold=0.7  # 相似度阈值
        )

        return [hit.payload["summary"] for hit in results]

    async def save_dialogue(self, dialogue: DialogueMessage):
        """保存对话记录"""

        # 1. 保存到数据库
        self.db.add(dialogue)
        await self.db.commit()

        # 2. 更新Redis缓存
        cache_key = f"dialogue:{dialogue.player_id}:{dialogue.npc_id}:recent"
        await self.redis.lpush(cache_key, dialogue.json())
        await self.redis.ltrim(cache_key, 0, 19)  # 保留最近20条

        # 3. 生成摘要并存入向量数据库
        summary = await self._generate_summary(dialogue)
        vector = await self.embedding.encode(summary)

        self.qdrant.upsert(
            collection_name="dialogue_memory",
            points=[
                PointStruct(
                    id=str(dialogue.id),
                    vector=vector,
                    payload={
                        "player_id": dialogue.player_id,
                        "npc_id": dialogue.npc_id,
                        "summary": summary,
                        "emotion": dialogue.emotion,
                        "timestamp": dialogue.timestamp.isoformat()
                    }
                )
            ]
        )

    async def get_player_profile(self, player_id: str) -> Dict:
        """获取玩家档案"""

        cache_key = f"player:{player_id}:profile"

        # 尝试从Redis获取
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # 从数据库获取
        profile = await self.db.get(PlayerProfile, player_id)
        if profile:
            profile_dict = profile.to_dict()
            await self.redis.setex(cache_key, 1800, json.dumps(profile_dict))
            return profile_dict

        return {}

    async def update_player_profile(
        self,
        player_id: str,
        **updates
    ):
        """更新玩家档案"""

        profile = await self.db.get(PlayerProfile, player_id)
        if not profile:
            profile = PlayerProfile(id=player_id)
            self.db.add(profile)

        # 更新字段
        if "recent_emotion" in updates:
            profile.emotion_history.append({
                "emotion": updates["recent_emotion"],
                "timestamp": datetime.utcnow().isoformat()
            })
            # 保留最近50条情绪记录
            profile.emotion_history = profile.emotion_history[-50:]

        if "recent_topic" in updates:
            if updates["recent_topic"] not in profile.recent_topics:
                profile.recent_topics.append(updates["recent_topic"])
                profile.recent_topics = profile.recent_topics[-10:]

        await self.db.commit()

        # 清除缓存
        await self.redis.delete(f"player:{player_id}:profile")

    async def _generate_summary(self, dialogue: DialogueMessage) -> str:
        """生成对话摘要用于语义搜索"""

        # 使用轻量级模型生成摘要
        prompt = f"""
请用一句话概括这段对话的主题和情感：

用户: {dialogue.user_message}
NPC: {dialogue.npc_response}

格式: [情感] 关于[主题]的对话
示例: [悲伤] 关于工作压力和焦虑的倾诉
"""

        summary = await self.llm_lite.chat(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="你是一个对话摘要助手",
            temperature=0.3
        )

        return summary.strip()
```

---

## 5. 情感识别系统

### 5.1 多模态情感分析

```python
# app/services/emotion/analyzer.py

from typing import Dict, Optional, List
import numpy as np
from transformers import pipeline
import cv2


class EmotionAnalyzer:
    """多模态情感分析器"""

    EMOTION_LABELS = [
        "joy", "sadness", "anger", "fear",
        "surprise", "disgust", "neutral"
    ]

    def __init__(self):
        # 文本情感分析模型
        self.text_analyzer = pipeline(
            "text-classification",
            model="uer/roberta-base-finetuned-jd-binary-chinese",
            top_k=None
        )

        # 表情识别模型（轻量级）
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.emotion_model = self._load_emotion_model()

    async def analyze_text(self, text: str) -> Dict[str, float]:
        """分析文本情感"""

        # 关键词快速检测
        keyword_emotions = self._keyword_detection(text)

        # 模型分析
        result = self.text_analyzer(text)[0]
        model_emotions = self._map_to_emotions(result)

        # 综合结果
        combined = {}
        for emotion in self.EMOTION_LABELS:
            keyword_score = keyword_emotions.get(emotion, 0)
            model_score = model_emotions.get(emotion, 0)
            combined[emotion] = keyword_score * 0.3 + model_score * 0.7

        return self._normalize(combined)

    def analyze_face(self, frame: np.ndarray) -> Optional[Dict[str, float]]:
        """分析面部表情"""

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)

        if len(faces) == 0:
            return None

        # 取最大的脸
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        face_roi = gray[y:y+h, x:x+w]
        face_roi = cv2.resize(face_roi, (48, 48))

        # 模型预测
        predictions = self.emotion_model.predict(
            face_roi.reshape(1, 48, 48, 1) / 255.0
        )[0]

        return {
            emotion: float(score)
            for emotion, score in zip(self.EMOTION_LABELS, predictions)
        }

    def combine_modalities(
        self,
        text_emotion: Dict[str, float],
        facial_emotion: Optional[Dict[str, float]],
        weights: Dict[str, float] = {"text": 0.6, "facial": 0.4}
    ) -> Dict[str, float]:
        """综合多模态情感分析结果"""

        if facial_emotion is None:
            return text_emotion

        combined = {}
        for emotion in self.EMOTION_LABELS:
            text_score = text_emotion.get(emotion, 0)
            face_score = facial_emotion.get(emotion, 0)
            combined[emotion] = (
                text_score * weights["text"] +
                face_score * weights["facial"]
            )

        return self._normalize(combined)

    def _keyword_detection(self, text: str) -> Dict[str, float]:
        """基于关键词的快速情感检测"""

        keywords = {
            "joy": ["开心", "高兴", "快乐", "哈哈", "太好了", "棒", "爱", "喜欢"],
            "sadness": ["难过", "伤心", "哭", "痛苦", "失望", "孤独", "累", "烦"],
            "anger": ["生气", "愤怒", "讨厌", "烦死", "气死", "混蛋", "该死"],
            "fear": ["害怕", "担心", "焦虑", "恐惧", "紧张", "不安", "慌"],
            "surprise": ["惊讶", "意外", "天哪", "不敢相信", "居然", "竟然"]
        }

        scores = {emotion: 0.0 for emotion in self.EMOTION_LABELS}

        for emotion, words in keywords.items():
            for word in words:
                if word in text:
                    scores[emotion] += 0.3

        return scores

    def _normalize(self, emotions: Dict[str, float]) -> Dict[str, float]:
        """归一化情感分数"""
        total = sum(emotions.values())
        if total == 0:
            return {e: 1/len(emotions) for e in emotions}
        return {e: s/total for e, s in emotions.items()}
```

### 5.2 客户端表情捕捉 (GDScript)

```gdscript
# scripts/ai/emotion_capture.gd

extends Node

class_name EmotionCapture

signal emotion_detected(emotions: Dictionary)
signal capture_error(message: String)

var camera: Camera
var capture_timer: Timer
var is_capturing := false
var last_frame: Image

# 配置
const CAPTURE_INTERVAL := 2.0  # 每2秒捕捉一次
const MIN_FACE_SIZE := 100  # 最小脸部像素


func _ready():
    _setup_camera()
    _setup_timer()


func _setup_camera():
    # 请求摄像头权限
    if OS.has_feature("web"):
        JavaScriptBridge.eval("navigator.mediaDevices.getUserMedia({video: true})")

    camera = Camera.new()
    add_child(camera)


func _setup_timer():
    capture_timer = Timer.new()
    capture_timer.wait_time = CAPTURE_INTERVAL
    capture_timer.timeout.connect(_on_capture_timeout)
    add_child(capture_timer)


func start_capture():
    """开始表情捕捉"""
    if not camera.is_open():
        var err = camera.open()
        if err != OK:
            emit_signal("capture_error", "无法打开摄像头")
            return

    is_capturing = true
    capture_timer.start()


func stop_capture():
    """停止表情捕捉"""
    is_capturing = false
    capture_timer.stop()
    camera.close()


func _on_capture_timeout():
    if not is_capturing:
        return

    # 捕捉当前帧
    var frame = camera.get_image()
    if frame == null:
        return

    last_frame = frame

    # 发送到服务器分析
    _send_for_analysis(frame)


func _send_for_analysis(frame: Image):
    """发送图像到服务器进行表情分析"""

    # 压缩图像
    var png_data = frame.save_png_to_buffer()
    var base64_data = Marshalls.raw_to_base64(png_data)

    # 通过WebSocket发送
    var request = {
        "type": "emotion_analysis",
        "data": {
            "image": base64_data,
            "timestamp": Time.get_unix_time_from_system()
        }
    }

    NetworkManager.send_message(request)


func _on_emotion_result(result: Dictionary):
    """处理服务器返回的情感分析结果"""

    if result.has("error"):
        emit_signal("capture_error", result.error)
        return

    var emotions = result.get("emotions", {})
    emit_signal("emotion_detected", emotions)
```

---

## 6. 语音交互系统

### 6.1 语音处理流程

```
用户说话
    │
    ▼
┌─────────────────┐
│  语音活动检测   │ ← 检测用户是否在说话
│  (VAD)          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  语音识别      │ ← 阿里云ASR / 火山引擎ASR
│  (ASR)         │
└────────┬────────┘
         │ 文字
         ▼
┌─────────────────┐
│  对话管理器    │ ← DialogueManager
│                │
└────────┬────────┘
         │ NPC回复文字
         ▼
┌─────────────────┐
│  语音合成      │ ← 阿里云TTS / CosyVoice
│  (TTS)         │
└────────┬────────┘
         │ 音频
         ▼
    NPC说话 + 口型同步
```

### 6.2 语音服务实现 (Python)

```python
# app/services/voice/speech_service.py

from typing import AsyncGenerator, Optional
import aiohttp
import base64
import json


class SpeechService:
    """语音服务（ASR + TTS）"""

    def __init__(self, config: dict):
        self.config = config
        self.asr_url = config["asr"]["url"]
        self.tts_url = config["tts"]["url"]
        self._session: Optional[aiohttp.ClientSession] = None

    async def speech_to_text(
        self,
        audio_data: bytes,
        format: str = "pcm",
        sample_rate: int = 16000
    ) -> str:
        """语音转文字"""

        session = await self._get_session()

        # 阿里云ASR API
        payload = {
            "format": format,
            "sample_rate": sample_rate,
            "enable_punctuation": True,
            "enable_inverse_text_normalization": True
        }

        headers = {
            "Authorization": f"Bearer {self.config['asr']['api_key']}",
            "Content-Type": "application/octet-stream",
            "X-NLS-Token": self.config['asr']['token']
        }

        async with session.post(
            self.asr_url,
            data=audio_data,
            headers=headers,
            params=payload
        ) as response:
            result = await response.json()
            return result.get("result", "")

    async def text_to_speech_stream(
        self,
        text: str,
        voice_id: str = "xiaoyun",
        speed: float = 1.0,
        pitch: float = 1.0
    ) -> AsyncGenerator[bytes, None]:
        """文字转语音（流式）"""

        session = await self._get_session()

        # 分句处理，实现边生成边播放
        sentences = self._split_sentences(text)

        for sentence in sentences:
            if not sentence.strip():
                continue

            payload = {
                "text": sentence,
                "voice": voice_id,
                "format": "mp3",
                "sample_rate": 16000,
                "speech_rate": int(speed * 100),
                "pitch_rate": int(pitch * 100)
            }

            headers = {
                "Authorization": f"Bearer {self.config['tts']['api_key']}",
                "Content-Type": "application/json"
            }

            async with session.post(
                self.tts_url,
                json=payload,
                headers=headers
            ) as response:
                async for chunk in response.content.iter_chunked(4096):
                    yield chunk

    def _split_sentences(self, text: str) -> list:
        """分句处理"""
        import re
        # 按标点符号分句
        sentences = re.split(r'([。！？；\n])', text)

        result = []
        for i in range(0, len(sentences) - 1, 2):
            result.append(sentences[i] + sentences[i + 1] if i + 1 < len(sentences) else sentences[i])

        return [s for s in result if s.strip()]


# NPC音色配置
NPC_VOICE_CONFIG = {
    "aela_guide": {
        "voice_id": "zhimiao_emo",  # 温柔女声
        "speed": 1.0,
        "pitch": 1.05
    },
    "momo_merchant": {
        "voice_id": "ailun",  # 活泼童声
        "speed": 1.1,
        "pitch": 1.2
    },
    "chronos_quest": {
        "voice_id": "ninger",  # 沧桑男声
        "speed": 0.95,
        "pitch": 0.9
    },
    "bei_friend": {
        "voice_id": "zhiyan_emo",  # 温暖女声
        "speed": 1.0,
        "pitch": 1.0
    },
    "sesame_pet": {
        "voice_id": "taozi",  # 可爱童声
        "speed": 1.15,
        "pitch": 1.3
    }
}
```

### 6.3 客户端语音处理 (GDScript)

```gdscript
# scripts/ai/voice_manager.gd

extends Node

class_name VoiceManager

signal speech_started
signal speech_ended
signal text_recognized(text: String)
signal tts_audio_ready(audio: AudioStream)

var audio_capture: AudioEffectCapture
var audio_player: AudioStreamPlayer
var is_listening := false
var is_speaking := false

# 语音活动检测
var vad_threshold := 0.02
var silence_duration := 0.0
var max_silence := 1.5  # 静音超过1.5秒结束

var audio_buffer: PackedByteArray


func _ready():
    _setup_audio_capture()
    _setup_audio_player()


func _setup_audio_capture():
    # 设置麦克风录音
    var idx = AudioServer.get_bus_index("Record")
    audio_capture = AudioServer.get_bus_effect(idx, 0) as AudioEffectCapture


func _setup_audio_player():
    audio_player = AudioStreamPlayer.new()
    add_child(audio_player)
    audio_player.finished.connect(_on_audio_finished)


func start_listening():
    """开始监听用户语音"""
    if is_listening:
        return

    is_listening = true
    audio_buffer = PackedByteArray()
    silence_duration = 0.0

    # 开始录音
    audio_capture.clear_buffer()
    emit_signal("speech_started")


func stop_listening():
    """停止监听"""
    if not is_listening:
        return

    is_listening = false
    emit_signal("speech_ended")

    # 发送音频进行识别
    if audio_buffer.size() > 0:
        _send_for_recognition()


func _process(delta: float):
    if not is_listening:
        return

    # 获取音频数据
    var frames = audio_capture.get_buffer(audio_capture.get_frames_available())

    if frames.size() == 0:
        return

    # 计算音量
    var volume = _calculate_volume(frames)

    if volume > vad_threshold:
        # 有声音，重置静音计时
        silence_duration = 0.0
        _append_audio_data(frames)
    else:
        # 静音
        silence_duration += delta

        if silence_duration > max_silence and audio_buffer.size() > 0:
            # 静音超时，结束录音
            stop_listening()


func _calculate_volume(frames: PackedVector2Array) -> float:
    var sum := 0.0
    for frame in frames:
        sum += abs(frame.x) + abs(frame.y)
    return sum / (frames.size() * 2)


func _append_audio_data(frames: PackedVector2Array):
    # 转换为PCM格式
    for frame in frames:
        var sample = int(frame.x * 32767)
        audio_buffer.append(sample & 0xFF)
        audio_buffer.append((sample >> 8) & 0xFF)


func _send_for_recognition():
    """发送音频到服务器进行语音识别"""

    var base64_audio = Marshalls.raw_to_base64(audio_buffer)

    var request = {
        "type": "speech_recognition",
        "data": {
            "audio": base64_audio,
            "format": "pcm",
            "sample_rate": 16000
        }
    }

    NetworkManager.send_message(request)
    audio_buffer = PackedByteArray()


func _on_recognition_result(result: Dictionary):
    """处理语音识别结果"""
    var text = result.get("text", "")
    if text.length() > 0:
        emit_signal("text_recognized", text)


# TTS播放
func play_tts(audio_data: PackedByteArray):
    """播放TTS音频"""

    var audio_stream = AudioStreamMP3.new()
    audio_stream.data = audio_data

    audio_player.stream = audio_stream
    audio_player.play()

    is_speaking = true
    emit_signal("tts_audio_ready", audio_stream)


func stop_tts():
    """停止TTS播放"""
    audio_player.stop()
    is_speaking = false


func _on_audio_finished():
    is_speaking = false
```

---

## 7. NPC行为控制

### 7.1 行为状态机

```gdscript
# scripts/npc/npc_behavior_controller.gd

extends Node

class_name NPCBehaviorController

enum State {
    IDLE,           # 待机
    WANDERING,      # 闲逛
    TALKING,        # 对话中
    LISTENING,      # 倾听中
    THINKING,       # 思考中
    EMOTING,        # 表达情绪
    PERFORMING      # 执行特定动作
}

var current_state: State = State.IDLE
var npc: CharacterBody3D
var animation_player: AnimationPlayer
var dialogue_manager: DialogueManager
var emotion_display: EmotionDisplay

# 行为参数
var wander_radius := 5.0
var wander_interval := 10.0
var think_duration := 1.5


func _ready():
    _setup_state_machine()


func _setup_state_machine():
    # 状态转换定时器
    var timer = Timer.new()
    timer.wait_time = wander_interval
    timer.timeout.connect(_on_wander_timer)
    add_child(timer)
    timer.start()


func set_state(new_state: State, data: Dictionary = {}):
    """切换状态"""

    if current_state == new_state:
        return

    # 退出当前状态
    _exit_state(current_state)

    current_state = new_state

    # 进入新状态
    _enter_state(new_state, data)


func _exit_state(state: State):
    match state:
        State.TALKING:
            animation_player.play("idle")
        State.EMOTING:
            emotion_display.fade_out()


func _enter_state(state: State, data: Dictionary):
    match state:
        State.IDLE:
            animation_player.play("idle")

        State.WANDERING:
            _start_wandering()

        State.TALKING:
            animation_player.play("talking")
            _start_lip_sync(data.get("audio_stream"))

        State.LISTENING:
            animation_player.play("listening")
            _play_listening_gestures()

        State.THINKING:
            animation_player.play("thinking")
            await get_tree().create_timer(think_duration).timeout
            set_state(State.TALKING, data)

        State.EMOTING:
            var emotion = data.get("emotion", "neutral")
            _play_emotion(emotion)

        State.PERFORMING:
            var action = data.get("action", "wave")
            animation_player.play(action)


func _start_wandering():
    """开始闲逛行为"""
    var target = _get_random_wander_point()
    npc.navigate_to(target)
    animation_player.play("walk")


func _get_random_wander_point() -> Vector3:
    var angle = randf() * TAU
    var distance = randf() * wander_radius
    var offset = Vector3(cos(angle) * distance, 0, sin(angle) * distance)
    return npc.home_position + offset


func _start_lip_sync(audio_stream: AudioStream):
    """开始口型同步"""
    if audio_stream == null:
        return

    # 简化版口型同步：根据音量控制嘴巴开合
    # 实际项目可以使用更复杂的音素分析
    var lip_sync = npc.get_node("LipSync")
    lip_sync.start(audio_stream)


func _play_listening_gestures():
    """播放倾听时的小动作"""
    var gestures = ["nod", "tilt_head", "blink"]

    while current_state == State.LISTENING:
        await get_tree().create_timer(randf_range(2.0, 5.0)).timeout
        if current_state == State.LISTENING:
            var gesture = gestures[randi() % gestures.size()]
            animation_player.play(gesture)


func _play_emotion(emotion: String):
    """播放情绪表情"""

    var emotion_anims = {
        "joy": "smile",
        "sadness": "sad_expression",
        "surprise": "surprised",
        "anger": "frown",
        "neutral": "neutral"
    }

    var anim = emotion_anims.get(emotion, "neutral")
    animation_player.play(anim)
    emotion_display.show_emotion(emotion)


# 对话回调
func on_user_start_speaking():
    """用户开始说话"""
    set_state(State.LISTENING)


func on_user_stop_speaking():
    """用户停止说话"""
    set_state(State.THINKING)


func on_npc_start_response(audio_stream: AudioStream):
    """NPC开始回复"""
    set_state(State.TALKING, {"audio_stream": audio_stream})


func on_npc_finish_response():
    """NPC回复结束"""
    set_state(State.IDLE)


func on_emotion_detected(emotion: String, intensity: float):
    """检测到用户情绪变化"""
    if intensity > 0.7:
        # 强烈情绪，NPC做出反应
        set_state(State.EMOTING, {"emotion": emotion})
```

---

## 8. AI服务监控与降级

### 8.1 服务健康检查

```python
# app/services/ai/health_checker.py

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from dataclasses import dataclass, field


@dataclass
class ServiceHealth:
    name: str
    is_healthy: bool = True
    last_check: datetime = field(default_factory=datetime.utcnow)
    error_count: int = 0
    avg_latency_ms: float = 0.0
    success_rate: float = 1.0

    # 熔断配置
    error_threshold: int = 5
    recovery_timeout: int = 60  # 秒
    last_error_time: datetime = None


class AIServiceHealthChecker:
    """AI服务健康检查与熔断"""

    def __init__(self):
        self.services: Dict[str, ServiceHealth] = {}
        self.check_interval = 30  # 秒
        self._running = False

    async def start(self):
        """启动健康检查"""
        self._running = True
        while self._running:
            await self._check_all_services()
            await asyncio.sleep(self.check_interval)

    def stop(self):
        self._running = False

    async def _check_all_services(self):
        """检查所有服务"""
        tasks = [
            self._check_service(name, health)
            for name, health in self.services.items()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_service(self, name: str, health: ServiceHealth):
        """检查单个服务"""
        try:
            start = datetime.utcnow()

            # 发送健康检查请求
            llm = LLMServiceFactory.create(service_name=name.split(".")[0])
            await llm.chat(
                messages=[{"role": "user", "content": "ping"}],
                system_prompt="Reply with 'pong'",
                temperature=0
            )

            latency = (datetime.utcnow() - start).total_seconds() * 1000

            # 更新健康状态
            health.is_healthy = True
            health.last_check = datetime.utcnow()
            health.avg_latency_ms = (health.avg_latency_ms * 0.8) + (latency * 0.2)

        except Exception as e:
            health.error_count += 1
            health.last_error_time = datetime.utcnow()

            if health.error_count >= health.error_threshold:
                health.is_healthy = False
                logger.warning(f"Service {name} marked unhealthy: {e}")

    def record_request(self, service_name: str, success: bool, latency_ms: float):
        """记录请求结果"""
        health = self.services.get(service_name)
        if not health:
            health = ServiceHealth(name=service_name)
            self.services[service_name] = health

        # 更新统计
        if success:
            health.avg_latency_ms = (health.avg_latency_ms * 0.9) + (latency_ms * 0.1)
            health.success_rate = (health.success_rate * 0.95) + (1.0 * 0.05)
        else:
            health.error_count += 1
            health.success_rate = (health.success_rate * 0.95) + (0.0 * 0.05)
            health.last_error_time = datetime.utcnow()

            if health.error_count >= health.error_threshold:
                health.is_healthy = False

    def is_available(self, service_name: str) -> bool:
        """检查服务是否可用"""
        health = self.services.get(service_name)
        if not health:
            return True  # 未知服务默认可用

        if health.is_healthy:
            return True

        # 检查是否可以尝试恢复
        if health.last_error_time:
            recovery_time = health.last_error_time + timedelta(
                seconds=health.recovery_timeout
            )
            if datetime.utcnow() > recovery_time:
                health.error_count = 0
                return True

        return False

    def get_best_service(self, candidates: List[str]) -> str:
        """从候选服务中选择最佳的"""
        available = [s for s in candidates if self.is_available(s)]

        if not available:
            # 所有服务都不可用，选择最近出错的（可能已恢复）
            return min(
                candidates,
                key=lambda s: self.services.get(s, ServiceHealth(s)).last_error_time or datetime.min
            )

        # 选择延迟最低的
        return min(
            available,
            key=lambda s: self.services.get(s, ServiceHealth(s)).avg_latency_ms
        )
```

### 8.2 请求重试与降级

```python
# app/services/ai/resilient_client.py

import asyncio
from typing import AsyncGenerator, Optional
from functools import wraps


class ResilientAIClient:
    """弹性AI客户端 - 支持重试、降级、熔断"""

    def __init__(
        self,
        health_checker: AIServiceHealthChecker,
        config: dict
    ):
        self.health = health_checker
        self.config = config
        self.max_retries = 3
        self.retry_delay = 1.0  # 秒

    async def chat_with_fallback(
        self,
        npc_id: str,
        messages: list,
        system_prompt: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """带降级的对话请求"""

        routing = self.config["npc_routing"][npc_id]
        services_to_try = [routing["primary"]] + routing.get("fallback", [])

        last_error = None

        for service_name in services_to_try:
            if not self.health.is_available(service_name):
                continue

            try:
                async for chunk in self._try_service(
                    service_name, messages, system_prompt, **kwargs
                ):
                    yield chunk
                return  # 成功，结束

            except Exception as e:
                last_error = e
                self.health.record_request(service_name, success=False, latency_ms=0)
                continue

        # 所有服务都失败
        yield "[系统] 服务暂时不可用，请稍后再试"
        raise AIServiceUnavailable(f"All services failed: {last_error}")

    async def _try_service(
        self,
        service_name: str,
        messages: list,
        system_prompt: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """尝试单个服务"""

        llm = LLMServiceFactory.create(
            service_name=service_name.split(".")[0],
            model_name=service_name.split(".")[1]
        )

        start_time = asyncio.get_event_loop().time()

        try:
            async for chunk in llm.stream_chat(
                messages=messages,
                system_prompt=system_prompt,
                **kwargs
            ):
                yield chunk

            latency = (asyncio.get_event_loop().time() - start_time) * 1000
            self.health.record_request(service_name, success=True, latency_ms=latency)

        except Exception as e:
            raise
```

---

## 9. 成本控制

### 9.1 Token用量追踪

```python
# app/services/ai/cost_tracker.py

from datetime import datetime, date
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession


class CostTracker:
    """AI服务成本追踪"""

    # 价格表（元/1K tokens）
    PRICING = {
        "qwen.turbo": {"input": 0.008, "output": 0.008},
        "qwen.plus": {"input": 0.04, "output": 0.04},
        "qwen.max": {"input": 0.12, "output": 0.12},
        "claude.haiku": {"input": 0.00025, "output": 0.00125},
        "claude.sonnet": {"input": 0.003, "output": 0.015},
        "claude.opus": {"input": 0.015, "output": 0.075},
        "volcengine.lite": {"input": 0.0003, "output": 0.0003},
        "volcengine.pro": {"input": 0.0008, "output": 0.0008}
    }

    def __init__(self, db: AsyncSession, redis):
        self.db = db
        self.redis = redis

    async def record_usage(
        self,
        player_id: str,
        service: str,
        input_tokens: int,
        output_tokens: int
    ):
        """记录使用量"""

        pricing = self.PRICING.get(service, {"input": 0, "output": 0})
        cost = (
            input_tokens / 1000 * pricing["input"] +
            output_tokens / 1000 * pricing["output"]
        )

        # 更新Redis计数器
        today = date.today().isoformat()

        pipe = self.redis.pipeline()
        pipe.hincrby(f"usage:{today}:{service}", "input_tokens", input_tokens)
        pipe.hincrby(f"usage:{today}:{service}", "output_tokens", output_tokens)
        pipe.hincrbyfloat(f"usage:{today}:{service}", "cost", cost)
        pipe.hincrby(f"user_usage:{player_id}:{today}", "tokens", input_tokens + output_tokens)
        pipe.hincrbyfloat(f"user_usage:{player_id}:{today}", "cost", cost)
        await pipe.execute()

        # 检查配额
        await self._check_quota(player_id)

    async def _check_quota(self, player_id: str):
        """检查用户配额"""

        today = date.today().isoformat()
        usage = await self.redis.hgetall(f"user_usage:{player_id}:{today}")

        daily_cost = float(usage.get("cost", 0))

        # 获取用户配额
        player = await self.db.get(Player, player_id)
        daily_limit = player.membership.daily_ai_cost_limit  # 如：免费用户0.1元/天

        if daily_cost >= daily_limit:
            # 触发配额警告
            await self._notify_quota_exceeded(player_id)

    async def get_daily_report(self) -> Dict:
        """获取每日成本报告"""

        today = date.today().isoformat()
        report = {
            "date": today,
            "services": {},
            "total_cost": 0
        }

        for service in self.PRICING.keys():
            usage = await self.redis.hgetall(f"usage:{today}:{service}")
            if usage:
                report["services"][service] = {
                    "input_tokens": int(usage.get("input_tokens", 0)),
                    "output_tokens": int(usage.get("output_tokens", 0)),
                    "cost": float(usage.get("cost", 0))
                }
                report["total_cost"] += float(usage.get("cost", 0))

        return report
```

### 9.2 免费用户配额策略

| 用户类型 | 每日AI对话次数 | 每日Token限额 | 每日成本上限 |
|----------|---------------|--------------|-------------|
| 免费用户 | 50次 | 50K | ¥0.10 |
| 月卡会员 | 500次 | 500K | ¥1.00 |
| 年卡会员 | 无限 | 2000K | ¥5.00 |
| SVIP | 无限 | 无限 | 无限 |

---

## 10. 文档版本

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | 2024-01 | 初版，完整AI集成设计 |

---

**下一篇 → 10_UI_UX_Design.md（UI/UX设计规范）**
