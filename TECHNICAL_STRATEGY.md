# MindPal 技术方案与实施策略

> 基于商业计划书的深度技术实施方案
> 生成时间: 2025-11-11

## 📋 目录

1. [商业计划核心要点](#商业计划核心要点)
2. [技术架构对齐分析](#技术架构对齐分析)
3. [核心技术选型](#核心技术选型)
4. [数字人能力实现方案](#数字人能力实现方案)
5. [多模态交互实现](#多模态交互实现)
6. [知识库与RAG系统](#知识库与rag系统)
7. [第三方API集成策略](#第三方api集成策略)
8. [安全与合规](#安全与合规)

---

## 1. 商业计划核心要点

### 1.1 产品定位

**MindPal** - 面向元宇宙的智能体数字人交互平台

**三大核心价值**:
- **智能 (Intelligence)**: 基于大语言模型的深度理解与推理能力
- **陪伴 (Companionship)**: 提供全天候、无条件的情感支持
- **服务 (Service)**: 知识服务 + 购物辅助的实用价值

### 1.2 目标用户

#### ToC（个人消费者）
- 寻求情感陪伴的用户（独居青年、老人）
- 有学习和知识需求的用户（学生、职场人士）
- 追求高效便捷生活的用户（智能购物助手）

#### ToB/ToPaaS（企业开发者）
- 电商、教育、文旅、金融等行业企业
- 独立开发者和内容创作者

### 1.3 长远愿景

**从SaaS平台到元宇宙基础设施**:
1. **初期**: SaaS平台（个人数字人服务）
2. **中期**: PaaS平台（开放API/SDK给开发者）
3. **长期**: 元宇宙基础设施（跨平台智能体服务枢纽）

**两大核心虚拟场景**:
- **智能体小家**: 用户私人虚拟空间
- **中央社交大厅**: 公共社交中心和服务市场

---

## 2. 技术架构对齐分析

### 2.1 当前实现 vs 商业计划要求

| 商业计划要求 | 当前实现状态 | 差距分析 | 优先级 |
|------------|------------|---------|-------|
| **多模态交互（语音+文字）** | ❌ 仅支持文字 | 缺少语音识别(ASR)和语音合成(TTS) | 🔴 高 |
| **个性化数字人塑造** | ✅ 前端UI完整 | 后端API未实现，数据库表已设计 | 🔴 高 |
| **陪伴型+老师型角色** | ✅ 前端支持 | 后端personality逻辑需完善 | 🟡 中 |
| **知识服务（RAG）** | ❌ 未实现 | 需要向量数据库+文档处理 | 🔴 高 |
| **智能购物辅助** | ❌ 未实现 | 需要电商API集成+推荐引擎 | 🟢 低 |
| **多终端适配** | ✅ Web端完整 | 缺少小程序、电视端 | 🟡 中 |
| **长期记忆网络** | ❌ 未实现 | 需要对话历史存储+记忆检索 | 🔴 高 |
| **云-边-端协同** | ⚠️ 仅云端 | 边缘计算未部署 | 🟢 低 |

### 2.2 技术债务清单

**关键缺失**:
1. **AI推理引擎**: 未集成大语言模型API
2. **语音能力**: ASR/TTS完全缺失
3. **知识库系统**: RAG检索未实现
4. **长期记忆**: 对话历史管理不完善

---

## 3. 核心技术选型

### 3.1 大语言模型 (LLM) 选型

根据商业计划强调**"数字人、推理模型，都可以用各大厂商的接口"**，我们采用以下策略：

#### 主力模型：阿里云通义千问系列

**推荐配置**:
```python
# 生产环境配置
LLM_CONFIG = {
    "primary": {
        "provider": "dashscope",  # 阿里云DashScope
        "model": "qwen-turbo",    # 性价比首选
        "api_key": os.getenv("DASHSCOPE_API_KEY"),
        "max_tokens": 2000,
        "temperature": 0.7
    },
    "advanced": {
        "provider": "dashscope",
        "model": "qwen-plus",      # 高级用户
        "api_key": os.getenv("DASHSCOPE_API_KEY"),
        "max_tokens": 6000,
        "temperature": 0.8
    }
}
```

**选择理由**:
1. **成本优势**: 相比GPT-4，qwen-turbo成本仅1/10
2. **中文优化**: 专为中文场景训练，理解更准确
3. **生态完善**: 已部署DashScope SDK
4. **合规性**: 国产模型，符合监管要求

#### 备选模型矩阵

| 厂商 | 模型 | 适用场景 | 成本 |
|-----|------|---------|-----|
| 阿里云 | qwen-turbo | 日常对话、陪伴型 | ¥0.003/1K tokens |
| 阿里云 | qwen-plus | 知识服务、老师型 | ¥0.012/1K tokens |
| 百度 | ERNIE-Bot-4 | 专业领域问答 | ¥0.012/1K tokens |
| 科大讯飞 | Spark-V3.5 | 多模态交互 | 按需议价 |

### 3.2 语音技术选型

#### ASR（自动语音识别）

**主力方案：科大讯飞语音听写API**

```python
# 科大讯飞ASR配置
ASR_CONFIG = {
    "provider": "iflytek",
    "api_url": "wss://iat-api.xfyun.cn/v2/iat",
    "app_id": os.getenv("IFLYTEK_APP_ID"),
    "api_key": os.getenv("IFLYTEK_API_KEY"),
    "features": {
        "dialect_support": True,      # 支持202种方言
        "realtime": True,              # 实时流式识别
        "accuracy": "high"             # 高准确率模式
    }
}
```

**选择理由**:
- ✅ 支持202种方言（满足商业计划中"多模态"要求）
- ✅ 实时流式识别（低延迟）
- ✅ 专业的中文语音处理能力
- ✅ 成熟的SDK和文档

**备选**: 阿里云智能语音（价格更优，但方言支持较少）

#### TTS（语音合成）

**主力方案：阿里云智能语音TTS**

```python
# 阿里云TTS配置
TTS_CONFIG = {
    "provider": "aliyun_nls",
    "access_key_id": os.getenv("ALIYUN_ACCESS_KEY_ID"),
    "access_key_secret": os.getenv("ALIYUN_ACCESS_KEY_SECRET"),
    "voices": {
        "xiaoya": "温柔甜美女声",
        "xiaoqing": "知性优雅女声",
        "xiaoxin": "活泼元气女声",
        "xiaoyu": "阳光温暖男声",
        "xiaozhi": "沉稳理性男声",
        "xiaohao": "幽默风趣男声"
    },
    "voice_clone": True  # 支持声音克隆
}
```

**选择理由**:
- ✅ 音色自然度高（接近真人）
- ✅ 支持声音克隆（满足个性化塑造需求）
- ✅ 流式合成（边合成边播放）
- ✅ 价格合理（¥4/万字符）

**备选**: 科大讯飞TTS（更多方言音色，适合特定场景）

### 3.3 向量数据库选型

#### 推荐方案：Milvus

```python
# Milvus配置
VECTOR_DB_CONFIG = {
    "provider": "milvus",
    "host": os.getenv("MILVUS_HOST", "localhost"),
    "port": int(os.getenv("MILVUS_PORT", 19530)),
    "collection": "mindpal_knowledge",
    "dimension": 1536,  # text-embedding-v2维度
    "metric_type": "COSINE",
    "index_type": "IVF_FLAT"
}
```

**选择理由**:
- ✅ 开源免费，可自部署
- ✅ 性能强大（支持百万级向量检索）
- ✅ 完善的Python SDK
- ✅ 支持混合检索（向量+标量过滤）

**备选**:
- **Pinecone**: 托管服务，运维简单（但成本较高）
- **Qdrant**: 轻量级，适合小规模部署
- **FAISS**: 本地库，适合原型验证

### 3.4 Embedding模型

**推荐：阿里云text-embedding-v2**

```python
# Embedding配置
EMBEDDING_CONFIG = {
    "provider": "dashscope",
    "model": "text-embedding-v2",
    "api_key": os.getenv("DASHSCOPE_API_KEY"),
    "dimension": 1536,
    "batch_size": 25  # 批量处理提升效率
}
```

**选择理由**:
- ✅ 与通义千问同生态，兼容性好
- ✅ 中文语义理解优秀
- ✅ 价格低廉（¥0.0007/1K tokens）
- ✅ API简单易用

---

## 4. 数字人能力实现方案

### 4.1 个性化塑造系统

#### 4.1.1 Personality Engine（性格引擎）

**实现策略**: 基于Prompt Engineering + Few-shot Learning

```python
class PersonalityEngine:
    """数字人性格引擎"""

    PERSONALITY_TEMPLATES = {
        "gentle": {
            "traits": {
                "liveliness": 40,
                "humor": 30,
                "empathy": 90,
                "initiative": 50,
                "creativity": 40
            },
            "system_prompt": """你是一个温柔体贴的伙伴。
特质：善解人意、温暖细腻、总是给予关怀和支持。
沟通风格：语气柔和、善于倾听、经常表达理解和关心。
回应方式：先共情用户情绪，再提供温暖的建议或陪伴。
禁止：避免过于直接或冷漠的表达。"""
        },
        "energetic": {
            "traits": {
                "liveliness": 90,
                "humor": 70,
                "empathy": 60,
                "initiative": 80,
                "creativity": 70
            },
            "system_prompt": """你是一个活泼开朗的伙伴。
特质：热情洋溢、充满活力、能带来欢乐和正能量。
沟通风格：语气轻松、经常使用emoji、喜欢分享趣事。
回应方式：积极乐观、主动引导话题、善于鼓励用户。
禁止：避免过于严肃或沉闷的表达。"""
        }
        # ... 其他性格模板
    }

    def generate_system_prompt(self, personality_config):
        """生成个性化的System Prompt"""
        base_template = self.PERSONALITY_TEMPLATES.get(
            personality_config.get("personality", "gentle")
        )

        # 根据特质值动态调整
        traits = personality_config.get("traits", {})
        custom_desc = personality_config.get("customPersonality", "")

        # 组合生成最终的System Prompt
        prompt = f"""{base_template['system_prompt']}

性格特质调整：
- 活泼度: {traits.get('liveliness', 50)}/100
- 幽默感: {traits.get('humor', 50)}/100
- 同理心: {traits.get('empathy', 50)}/100
- 主动性: {traits.get('initiative', 50)}/100
- 创造力: {traits.get('creativity', 50)}/100

{f'用户补充描述：{custom_desc}' if custom_desc else ''}

请严格按照以上性格设定进行对话。"""

        return prompt
```

#### 4.1.2 角色类型实现

**陪伴型 vs 老师型的差异化**:

```python
# 陪伴型数字人配置
COMPANION_CONFIG = {
    "role": "companion",
    "system_prompt_suffix": """
你的主要目标是提供情绪价值和情感支持。
- 优先共情用户的感受
- 主动关心用户的近况
- 记住用户分享的重要信息
- 在适当时候提供心理慰藉
- 避免过于说教或给出硬性建议
""",
    "response_style": {
        "empathy_first": True,
        "question_ratio": 0.3,  # 30%的回应包含关心式提问
        "emotional_words": ["理解", "陪伴", "支持", "关心"]
    }
}

# 老师型数字人配置
TEACHER_CONFIG = {
    "role": "teacher",
    "system_prompt_suffix": """
你的主要目标是提供知识服务和认知提升。
- 以结构化、逻辑清晰的方式讲解
- 善于引导用户思考
- 根据用户理解力调整难度
- 提供具体案例和练习
- 鼓励用户提问和探索
""",
    "response_style": {
        "structured": True,
        "use_examples": True,
        "knowledge_focus": True,
        "pedagogical_words": ["首先", "其次", "总结", "例如"]
    }
}
```

### 4.2 长期记忆系统

**实现方案**: 对话历史 + 记忆摘要 + 向量检索

```python
class MemorySystem:
    """长期记忆系统"""

    def __init__(self, db_session, vector_db):
        self.db = db_session
        self.vector_db = vector_db

    def store_conversation(self, user_id, dh_id, message, response):
        """存储对话历史"""
        conversation = Conversation(
            user_id=user_id,
            digital_human_id=dh_id,
            user_message=message,
            dh_response=response,
            timestamp=datetime.utcnow()
        )
        self.db.add(conversation)

        # 提取关键信息并向量化
        self.extract_and_vectorize(user_id, dh_id, message, response)

    def extract_and_vectorize(self, user_id, dh_id, message, response):
        """提取关键信息并存储到向量数据库"""
        # 调用LLM提取关键信息
        prompt = f"""从以下对话中提取用户的重要信息（如兴趣、偏好、重要事件等）：
用户：{message}
数字人：{response}

以JSON格式输出：
{{
    "key_info": "提取的关键信息",
    "category": "personal_info/interest/event/emotion",
    "importance": 1-10
}}"""

        # 提取后存储到向量数据库
        # ...

    def retrieve_relevant_memories(self, user_id, dh_id, current_message, top_k=5):
        """检索相关记忆"""
        # 向量检索
        query_vector = self.get_embedding(current_message)
        results = self.vector_db.search(
            collection="user_memories",
            vector=query_vector,
            filter=f"user_id == {user_id} and dh_id == {dh_id}",
            top_k=top_k
        )

        return results
```

---

## 5. 多模态交互实现

### 5.1 语音交互流程

```
用户语音输入
    ↓
[ASR] 科大讯飞语音识别
    ↓
文本消息
    ↓
[LLM] 通义千问生成回复
    ↓
回复文本
    ↓
[TTS] 阿里云语音合成
    ↓
数字人语音输出
```

### 5.2 实时流式处理

**WebSocket架构**:

```python
from flask_socketio import SocketIO, emit
import asyncio

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('voice_stream')
def handle_voice_stream(data):
    """处理实时语音流"""
    user_id = data['user_id']
    dh_id = data['dh_id']
    audio_chunk = data['audio_chunk']

    # 1. 流式ASR识别
    text_chunk = asr_service.recognize_stream(audio_chunk)

    if text_chunk:
        emit('transcription', {'text': text_chunk})

    # 2. 判断是否句子结束
    if asr_service.is_sentence_complete():
        full_text = asr_service.get_full_text()

        # 3. 调用LLM生成回复（流式）
        for token in llm_service.generate_stream(user_id, dh_id, full_text):
            emit('response_token', {'token': token})

        # 4. TTS合成（流式）
        full_response = llm_service.get_full_response()
        audio_stream = tts_service.synthesize_stream(full_response)

        for audio_chunk in audio_stream:
            emit('audio_chunk', {'audio': audio_chunk})
```

### 5.3 前端集成方案

**语音录制与播放**:

```javascript
// frontend/js/voice-chat.js

class VoiceChat {
    constructor(dhId) {
        this.dhId = dhId;
        this.socket = io('http://43.98.170.184:5000');
        this.mediaRecorder = null;
        this.audioContext = new AudioContext();
    }

    async startRecording() {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.mediaRecorder = new MediaRecorder(stream);

        this.mediaRecorder.ondataavailable = (e) => {
            // 发送音频chunk到后端
            this.socket.emit('voice_stream', {
                user_id: MindPalAuth.getCurrentUser().id,
                dh_id: this.dhId,
                audio_chunk: e.data
            });
        };

        this.mediaRecorder.start(100); // 每100ms发送一次
    }

    stopRecording() {
        this.mediaRecorder.stop();
    }

    // 接收并播放TTS音频
    setupAudioPlayback() {
        this.socket.on('audio_chunk', (data) => {
            const audioBuffer = this.base64ToArrayBuffer(data.audio);
            this.playAudioBuffer(audioBuffer);
        });
    }

    playAudioBuffer(buffer) {
        const source = this.audioContext.createBufferSource();
        this.audioContext.decodeAudioData(buffer, (audioBuffer) => {
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);
            source.start(0);
        });
    }
}
```

---

## 6. 知识库与RAG系统

### 6.1 RAG架构设计

```
用户问题
    ↓
[Embedding] 问题向量化
    ↓
[Vector DB] 检索相关知识片段（Top-K）
    ↓
[Re-ranking] 重排序（可选）
    ↓
[LLM] 结合检索结果生成回答
    ↓
回复用户
```

### 6.2 知识库构建流程

```python
class KnowledgeBaseBuilder:
    """知识库构建器"""

    def __init__(self, embedding_service, vector_db):
        self.embedding = embedding_service
        self.vector_db = vector_db

    def process_document(self, file_path, dh_id, user_id):
        """处理上传的文档"""
        # 1. 文件解析
        if file_path.endswith('.pdf'):
            text = self.extract_pdf(file_path)
        elif file_path.endswith('.docx'):
            text = self.extract_docx(file_path)
        elif file_path.endswith('.txt'):
            text = self.extract_txt(file_path)

        # 2. 文本分块（Chunking）
        chunks = self.split_text(text, chunk_size=500, overlap=50)

        # 3. 向量化
        vectors = []
        for i, chunk in enumerate(chunks):
            vector = self.embedding.get_embedding(chunk)
            vectors.append({
                "id": f"{dh_id}_{user_id}_{i}",
                "vector": vector,
                "metadata": {
                    "dh_id": dh_id,
                    "user_id": user_id,
                    "text": chunk,
                    "source": file_path,
                    "chunk_index": i
                }
            })

        # 4. 存储到向量数据库
        self.vector_db.insert(
            collection="knowledge_base",
            data=vectors
        )

        return len(chunks)

    def split_text(self, text, chunk_size=500, overlap=50):
        """智能文本分块"""
        # 按段落和句子分割
        sentences = re.split(r'[。！？\n]', text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks
```

### 6.3 RAG查询优化

```python
class RAGQueryEngine:
    """RAG查询引擎"""

    def query(self, question, dh_id, user_id, top_k=5):
        """RAG查询"""
        # 1. 问题向量化
        query_vector = self.embedding.get_embedding(question)

        # 2. 向量检索
        results = self.vector_db.search(
            collection="knowledge_base",
            vector=query_vector,
            filter=f"dh_id == {dh_id} and user_id == {user_id}",
            top_k=top_k
        )

        # 3. 构建上下文
        context = "\n\n".join([r['metadata']['text'] for r in results])

        # 4. 生成Prompt
        prompt = f"""基于以下知识库内容回答问题：

知识库内容：
{context}

用户问题：{question}

请根据知识库内容准确回答。如果知识库中没有相关信息，请诚实告知用户。"""

        # 5. 调用LLM生成答案
        response = self.llm.generate(prompt)

        return {
            "answer": response,
            "sources": [r['metadata']['source'] for r in results],
            "confidence": self.calculate_confidence(results)
        }

    def calculate_confidence(self, results):
        """计算答案置信度"""
        if not results:
            return 0.0

        # 基于相似度得分
        avg_score = sum([r['score'] for r in results]) / len(results)
        return min(avg_score * 100, 100)
```

---

## 7. 第三方API集成策略

### 7.1 统一API适配器模式

```python
# services/api_adapters/base.py

from abc import ABC, abstractmethod

class BaseAPIAdapter(ABC):
    """API适配器基类"""

    @abstractmethod
    def initialize(self, config):
        """初始化配置"""
        pass

    @abstractmethod
    def call_api(self, **kwargs):
        """调用API"""
        pass

    @abstractmethod
    def handle_error(self, error):
        """错误处理"""
        pass


# services/api_adapters/llm_adapter.py

class LLMAdapter(BaseAPIAdapter):
    """大语言模型适配器"""

    def __init__(self, provider="dashscope"):
        self.provider = provider
        self.client = None

    def initialize(self, config):
        if self.provider == "dashscope":
            import dashscope
            dashscope.api_key = config['api_key']
            self.client = dashscope
        elif self.provider == "baidu":
            # 百度千帆初始化
            pass

    def call_api(self, prompt, model="qwen-turbo", **kwargs):
        if self.provider == "dashscope":
            from dashscope import Generation
            response = Generation.call(
                model=model,
                prompt=prompt,
                **kwargs
            )
            return self.parse_dashscope_response(response)
        elif self.provider == "baidu":
            # 百度千帆API调用
            pass

    def parse_dashscope_response(self, response):
        if response.status_code == 200:
            return {
                "success": True,
                "text": response.output.text,
                "usage": response.usage
            }
        else:
            return {
                "success": False,
                "error": response.message
            }
```

### 7.2 API降级策略

```python
class APIFallbackManager:
    """API降级管理器"""

    def __init__(self):
        self.llm_providers = [
            {"name": "dashscope", "priority": 1, "adapter": LLMAdapter("dashscope")},
            {"name": "baidu", "priority": 2, "adapter": LLMAdapter("baidu")}
        ]
        self.current_provider_index = 0

    def call_with_fallback(self, func_name, *args, **kwargs):
        """带降级的API调用"""
        for i in range(len(self.llm_providers)):
            provider = self.llm_providers[self.current_provider_index]

            try:
                result = getattr(provider['adapter'], func_name)(*args, **kwargs)
                if result['success']:
                    return result
            except Exception as e:
                logger.error(f"Provider {provider['name']} failed: {e}")
                self.current_provider_index = (self.current_provider_index + 1) % len(self.llm_providers)
                continue

        raise Exception("All API providers failed")
```

### 7.3 成本优化策略

```python
class CostOptimizer:
    """成本优化器"""

    # 根据用户等级选择模型
    MODEL_STRATEGY = {
        "free": {
            "llm": "qwen-turbo",
            "embedding": "text-embedding-v2",
            "tts": "basic_voice"
        },
        "premium": {
            "llm": "qwen-plus",
            "embedding": "text-embedding-v2",
            "tts": "premium_voice"
        },
        "professional": {
            "llm": "qwen-max",
            "embedding": "text-embedding-v3",
            "tts": "custom_voice_clone"
        }
    }

    def get_model_config(self, user_tier):
        """根据用户等级获取模型配置"""
        return self.MODEL_STRATEGY.get(user_tier, self.MODEL_STRATEGY["free"])

    def should_use_cache(self, message):
        """判断是否使用缓存回复"""
        # 常见问候语使用缓存
        greetings = ["你好", "hi", "hello", "在吗"]
        return any(g in message.lower() for g in greetings)
```

---

## 8. 安全与合规

### 8.1 API Key管理

```python
# config/security.py

import os
from cryptography.fernet import Fernet

class SecureConfig:
    """安全配置管理"""

    # 使用环境变量 + 加密
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

    @classmethod
    def encrypt_api_key(cls, api_key):
        f = Fernet(cls.ENCRYPTION_KEY)
        return f.encrypt(api_key.encode()).decode()

    @classmethod
    def decrypt_api_key(cls, encrypted_key):
        f = Fernet(cls.ENCRYPTION_KEY)
        return f.decrypt(encrypted_key.encode()).decode()

    @classmethod
    def get_api_key(cls, service_name):
        """安全获取API Key"""
        encrypted = os.getenv(f"{service_name.upper()}_API_KEY_ENCRYPTED")
        if encrypted:
            return cls.decrypt_api_key(encrypted)
        return os.getenv(f"{service_name.upper()}_API_KEY")
```

### 8.2 用户数据隐私

```python
class PrivacyProtection:
    """隐私保护"""

    @staticmethod
    def anonymize_conversation(conversation):
        """对话数据脱敏"""
        # 移除敏感信息（手机号、身份证号等）
        import re
        text = conversation['content']

        # 手机号脱敏
        text = re.sub(r'1[3-9]\d{9}', '***********', text)

        # 身份证号脱敏
        text = re.sub(r'\d{17}[\dXx]', '******************', text)

        # 邮箱脱敏
        text = re.sub(r'[\w.-]+@[\w.-]+', '***@***', text)

        return text

    @staticmethod
    def user_consent_required(func):
        """需要用户授权的装饰器"""
        def wrapper(user_id, *args, **kwargs):
            # 检查用户是否已授权
            if not UserConsent.check(user_id, func.__name__):
                raise PermissionError(f"User {user_id} has not consented to {func.__name__}")
            return func(user_id, *args, **kwargs)
        return wrapper
```

### 8.3 内容审核

```python
class ContentModeration:
    """内容审核"""

    def __init__(self):
        # 使用阿里云内容安全API
        self.client = self.init_aliyun_content_security()

    def check_user_input(self, text):
        """审核用户输入"""
        result = self.client.text_scan(text)

        if result['risk'] == 'high':
            return {
                "allowed": False,
                "reason": "输入包含违规内容",
                "suggestion": result['suggestion']
            }

        return {"allowed": True}

    def check_ai_output(self, text):
        """审核AI输出"""
        # 检查AI生成内容是否合规
        result = self.client.text_scan(text)

        if result['risk'] != 'pass':
            # 触发人工审核或重新生成
            return self.regenerate_safe_response()

        return text
```

---

## 9. 监控与运维

### 9.1 API调用监控

```python
import time
from functools import wraps

class APIMonitor:
    """API监控"""

    @staticmethod
    def monitor_api_call(api_name):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()

                try:
                    result = func(*args, **kwargs)

                    # 记录成功调用
                    APIMetrics.record_success(
                        api_name=api_name,
                        latency=time.time() - start_time,
                        tokens_used=result.get('usage', {})
                    )

                    return result

                except Exception as e:
                    # 记录失败调用
                    APIMetrics.record_failure(
                        api_name=api_name,
                        error=str(e),
                        latency=time.time() - start_time
                    )
                    raise

            return wrapper
        return decorator
```

### 9.2 成本追踪

```python
class CostTracker:
    """成本追踪"""

    PRICING = {
        "qwen-turbo": {"input": 0.003, "output": 0.006},  # 每1K tokens
        "qwen-plus": {"input": 0.012, "output": 0.012},
        "text-embedding-v2": 0.0007,
        "tts": 4.0 / 10000  # 每字符
    }

    def calculate_llm_cost(self, model, input_tokens, output_tokens):
        """计算LLM成本"""
        price = self.PRICING.get(model, {"input": 0, "output": 0})
        cost = (input_tokens / 1000 * price['input'] +
                output_tokens / 1000 * price['output'])
        return cost

    def log_cost(self, user_id, dh_id, service, cost):
        """记录成本"""
        CostLog.create(
            user_id=user_id,
            digital_human_id=dh_id,
            service=service,
            cost=cost,
            timestamp=datetime.utcnow()
        )
```

---

## 总结

本技术方案完全基于商业计划书要求，采用**厂商API优先**策略：

**核心选型**:
- ✅ **LLM**: 阿里云通义千问（qwen-turbo/plus）
- ✅ **ASR**: 科大讯飞语音听写（支持202种方言）
- ✅ **TTS**: 阿里云智能语音（支持声音克隆）
- ✅ **Embedding**: 阿里云text-embedding-v2
- ✅ **向量DB**: Milvus（开源自部署）

**优势**:
1. **成本可控**: 全部采用国产厂商API，价格透明
2. **中文优化**: 专为中文场景训练，效果更好
3. **合规安全**: 满足国内监管要求
4. **易于扩展**: 统一适配器模式，可快速切换厂商

**下一步**: 制定分阶段开发路线图
