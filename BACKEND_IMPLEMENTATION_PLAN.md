# MindPal 后端实施方案

**文档版本**: v1.0
**创建日期**: 2025-01-11
**API提供商**: 阿里云 (通义千问)
**API Key**: `sk-71bb10435f134dfdab3a4b684e57b640`

---

## 📋 目录

1. [技术架构总览](#1-技术架构总览)
2. [阿里云服务集成方案](#2-阿里云服务集成方案)
3. [数据库设计](#3-数据库设计)
4. [API接口设计](#4-api接口设计)
5. [RAG知识库方案](#5-rag知识库方案)
6. [分阶段实施路线图](#6-分阶段实施路线图)
7. [部署方案](#7-部署方案)

---

## 1. 技术架构总览

### 1.1 技术栈选型

```
前端 (已完成)
├── HTML5 + CSS3 + JavaScript (ES6+)
├── LocalStorage (临时数据持久化)
└── 响应式设计

后端 (待开发)
├── Python 3.9+
├── Flask 3.0 (轻量级Web框架)
├── SQLite (P0阶段) → PostgreSQL (P1阶段)
├── 阿里云通义千问 API (LLM)
├── 阿里云DashScope SDK
└── FAISS / Chroma (向量数据库)

部署
├── Docker + Docker Compose
├── Nginx (反向代理)
└── 阿里云ECS (可选)
```

### 1.2 架构图

```
┌─────────────────────────────────────────────────────┐
│                    前端 (Browser)                    │
│  index.html, chat.html, dh-list.html, etc.          │
└─────────────────┬───────────────────────────────────┘
                  │ HTTPS/REST API
┌─────────────────▼───────────────────────────────────┐
│                 Flask Backend Server                 │
│  ┌──────────────────────────────────────────────┐  │
│  │  API Routes (/api/chat, /api/dh, /api/kb)   │  │
│  └──────────────┬───────────────────────────────┘  │
│                 │                                    │
│  ┌──────────────▼──────────┬─────────────────────┐ │
│  │   Core Services         │   Data Layer        │ │
│  │  - Chat Service         │  - SQLite DB        │ │
│  │  - DH Manager           │  - FAISS Vector DB  │ │
│  │  - Knowledge Service    │  - File Storage     │ │
│  └──────────────┬──────────┴─────────────────────┘ │
│                 │                                    │
└─────────────────┼────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│              阿里云 DashScope API                    │
│  - 通义千问 (qwen-turbo / qwen-plus)                │
│  - Text Embedding (text-embedding-v2)               │
│  - 流式对话支持                                      │
└─────────────────────────────────────────────────────┘
```

---

## 2. 阿里云服务集成方案

### 2.1 DashScope SDK 配置

#### 安装依赖
```bash
pip install dashscope flask flask-cors python-dotenv
```

#### 环境变量配置 (.env)
```env
# 阿里云配置
DASHSCOPE_API_KEY=sk-71bb10435f134dfdab3a4b684e57b640

# 模型配置
LLM_MODEL=qwen-turbo          # 或 qwen-plus, qwen-max
EMBEDDING_MODEL=text-embedding-v2

# 应用配置
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///mindpal.db

# CORS配置
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

### 2.2 通义千问对话集成

#### 核心代码示例
```python
from dashscope import Generation
import dashscope

# 配置API Key
dashscope.api_key = "sk-71bb10435f134dfdab3a4b684e57b640"

def chat_with_qianwen(messages, personality_prompt="", stream=True):
    """
    与通义千问进行对话

    Args:
        messages: 对话历史 [{"role": "user", "content": "..."}]
        personality_prompt: 数字人性格系统提示词
        stream: 是否使用流式输出

    Returns:
        生成器或完整响应
    """
    # 构建系统提示词
    system_message = {
        "role": "system",
        "content": f"""你是一个温暖、善解人意的数字人助手。

{personality_prompt}

请用自然、友好的语气回复，像真实的朋友一样交流。"""
    }

    # 构建完整消息列表
    full_messages = [system_message] + messages

    if stream:
        # 流式对话
        responses = Generation.call(
            model='qwen-turbo',
            messages=full_messages,
            result_format='message',
            stream=True,
            incremental_output=True
        )

        for response in responses:
            if response.status_code == 200:
                yield response.output.choices[0].message.content
            else:
                yield f"Error: {response.message}"
    else:
        # 非流式对话
        response = Generation.call(
            model='qwen-turbo',
            messages=full_messages,
            result_format='message'
        )

        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            raise Exception(f"API Error: {response.message}")
```

### 2.3 性格系统提示词映射

根据前端设置的性格特质，生成对应的系统提示词：

```python
PERSONALITY_TEMPLATES = {
    "gentle": "你性格温柔体贴，善解人意，总是给予关怀和支持。说话温和细腻。",
    "energetic": "你性格活泼开朗，热情洋溢，充满活力，能带来欢乐和正能量。",
    "intellectual": "你知性理性，逻辑清晰，善于分析和解决问题。",
    "humorous": "你幽默风趣，机智诙谐，妙语连珠，总能逗对方开心。",
    "calm": "你沉稳冷静，成熟稳重，遇事不慌，给人安全感。",
    "creative": "你富有创意，想象力丰富，思维跳跃，总有新奇想法。"
}

def generate_personality_prompt(dh_data):
    """
    根据数字人数据生成性格提示词

    Args:
        dh_data: {
            "personality": "gentle",
            "traits": {
                "liveliness": 70,
                "humor": 80,
                "empathy": 90,
                "initiative": 60,
                "creativity": 50
            },
            "customPersonality": "希望你在我心情不好时能安慰我..."
        }
    """
    prompt_parts = []

    # 基础性格
    base = PERSONALITY_TEMPLATES.get(dh_data.get("personality", "gentle"))
    prompt_parts.append(base)

    # 特质描述
    traits = dh_data.get("traits", {})
    if traits.get("liveliness", 50) > 70:
        prompt_parts.append("你说话时很活泼外向。")
    elif traits.get("liveliness", 50) < 30:
        prompt_parts.append("你说话时比较沉稳内敛。")

    if traits.get("humor", 50) > 70:
        prompt_parts.append("你经常使用幽默的语言。")

    if traits.get("empathy", 50) > 70:
        prompt_parts.append("你有很强的同理心，能感知对方的情绪。")

    if traits.get("initiative", 50) > 70:
        prompt_parts.append("你会主动发起话题和关心对方。")

    # 自定义描述
    if dh_data.get("customPersonality"):
        prompt_parts.append(dh_data["customPersonality"])

    return "\n".join(prompt_parts)
```

### 2.4 Embedding文本向量化

用于知识库RAG检索：

```python
from dashscope import TextEmbedding

def get_embeddings(texts):
    """
    文本向量化

    Args:
        texts: 文本列表

    Returns:
        向量列表
    """
    response = TextEmbedding.call(
        model='text-embedding-v2',
        input=texts
    )

    if response.status_code == 200:
        return [item['embedding'] for item in response.output['embeddings']]
    else:
        raise Exception(f"Embedding Error: {response.message}")
```

---

## 3. 数据库设计

### 3.1 SQLite Schema (P0阶段)

```sql
-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone VARCHAR(11) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- 数字人表
CREATE TABLE digital_humans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name VARCHAR(50) NOT NULL,
    avatar_type VARCHAR(50),
    avatar_emoji TEXT,
    avatar_custom_url TEXT,
    personality VARCHAR(50),
    traits JSON,  -- {"liveliness": 70, "humor": 80, ...}
    custom_personality TEXT,
    voice VARCHAR(50),
    voice_params JSON,  -- {"speed": 1.0, "pitch": 0, "volume": 80}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_chat_at TIMESTAMP,
    message_count INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 对话消息表
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dh_id INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    emotion VARCHAR(20),  -- 'happy', 'sad', 'calm', etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dh_id) REFERENCES digital_humans(id)
);

-- 知识库文档表
CREATE TABLE knowledge_docs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dh_id INTEGER NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(20),
    file_size INTEGER,
    file_url TEXT,
    status VARCHAR(20) DEFAULT 'processing',  -- processing, completed, failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dh_id) REFERENCES digital_humans(id)
);

-- 知识库分块表
CREATE TABLE knowledge_chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER,
    embedding BLOB,  -- 存储向量（可选，或使用FAISS）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES knowledge_docs(id)
);

-- 创建索引
CREATE INDEX idx_messages_dh_id ON messages(dh_id);
CREATE INDEX idx_dh_user_id ON digital_humans(user_id);
CREATE INDEX idx_kb_dh_id ON knowledge_docs(dh_id);
```

### 3.2 SQLAlchemy ORM 模型

```python
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(11), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)

    digital_humans = db.relationship('DigitalHuman', backref='user', lazy=True)

class DigitalHuman(db.Model):
    __tablename__ = 'digital_humans'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    avatar_type = db.Column(db.String(50))
    avatar_emoji = db.Column(db.Text)
    personality = db.Column(db.String(50))
    traits = db.Column(db.Text)  # JSON string
    voice = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_chat_at = db.Column(db.DateTime)
    message_count = db.Column(db.Integer, default=0)

    messages = db.relationship('Message', backref='digital_human', lazy=True)
    knowledge_docs = db.relationship('KnowledgeDoc', backref='digital_human', lazy=True)

    def get_traits(self):
        return json.loads(self.traits) if self.traits else {}

    def set_traits(self, traits_dict):
        self.traits = json.dumps(traits_dict)

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    dh_id = db.Column(db.Integer, db.ForeignKey('digital_humans.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    emotion = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class KnowledgeDoc(db.Model):
    __tablename__ = 'knowledge_docs'

    id = db.Column(db.Integer, primary_key=True)
    dh_id = db.Column(db.Integer, db.ForeignKey('digital_humans.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(20))
    file_size = db.Column(db.Integer)
    file_url = db.Column(db.Text)
    status = db.Column(db.String(20), default='processing')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

---

## 4. API接口设计

### 4.1 用户认证 API

#### POST /api/auth/login
```json
请求:
{
  "phone": "13800138000",
  "password": "password123"
}

响应:
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "phone": "13800138000"
    }
  }
}
```

#### POST /api/auth/register
```json
请求:
{
  "phone": "13800138000",
  "password": "password123"
}

响应:
{
  "success": true,
  "message": "注册成功"
}
```

### 4.2 数字人管理 API

#### GET /api/digital-humans
获取用户的所有数字人

```json
响应:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "小智",
      "avatarEmoji": "👦",
      "personality": "gentle",
      "messageCount": 42,
      "lastChatAt": "2025-01-11T10:30:00Z"
    }
  ]
}
```

#### POST /api/digital-humans
创建新数字人

```json
请求:
{
  "name": "小智",
  "avatar": "boy-sunny",
  "avatarEmoji": "👦",
  "personality": "gentle",
  "traits": {
    "liveliness": 70,
    "humor": 80,
    "empathy": 90,
    "initiative": 60,
    "creativity": 50
  },
  "voice": "xiaoyu",
  "voiceParams": {
    "speed": 1.0,
    "pitch": 0,
    "volume": 80
  }
}

响应:
{
  "success": true,
  "data": {
    "id": 1,
    "name": "小智",
    "createdAt": "2025-01-11T10:00:00Z"
  }
}
```

#### GET /api/digital-humans/:id
获取单个数字人详情

#### DELETE /api/digital-humans/:id
删除数字人

### 4.3 对话 API

#### POST /api/chat
发送消息并获取回复（流式）

```json
请求:
{
  "dhId": 1,
  "message": "今天天气怎么样？"
}

响应 (Server-Sent Events 流式):
data: {"chunk": "今天"}
data: {"chunk": "天气"}
data: {"chunk": "很好"}
data: {"done": true, "emotion": "happy"}
```

#### GET /api/chat/history/:dhId
获取对话历史

```json
响应:
{
  "success": true,
  "data": {
    "messages": [
      {
        "role": "user",
        "content": "你好",
        "timestamp": "2025-01-11T10:00:00Z"
      },
      {
        "role": "assistant",
        "content": "你好！很高兴见到你",
        "emotion": "happy",
        "timestamp": "2025-01-11T10:00:01Z"
      }
    ],
    "total": 50
  }
}
```

#### DELETE /api/chat/history/:dhId
清除对话历史

### 4.4 知识库 API

#### POST /api/knowledge/upload
上传文档

```json
请求 (multipart/form-data):
{
  "dhId": 1,
  "file": <file>
}

响应:
{
  "success": true,
  "data": {
    "docId": 1,
    "filename": "document.pdf",
    "status": "processing"
  }
}
```

#### GET /api/knowledge/:dhId
获取知识库文档列表

```json
响应:
{
  "success": true,
  "data": {
    "docs": [
      {
        "id": 1,
        "filename": "document.pdf",
        "fileSize": 1024000,
        "status": "completed",
        "createdAt": "2025-01-11T10:00:00Z"
      }
    ]
  }
}
```

---

## 5. RAG知识库方案

### 5.1 文档处理流程

```
上传文档
    ↓
提取文本 (PyPDF2, python-docx, etc.)
    ↓
文本分块 (chunk_size=500, overlap=50)
    ↓
向量化 (阿里云 text-embedding-v2)
    ↓
存储到 FAISS 向量数据库
    ↓
建立索引
```

### 5.2 RAG检索流程

```
用户提问
    ↓
问题向量化
    ↓
FAISS 相似度检索 (Top-K=3)
    ↓
构建增强 Prompt: [系统提示词] + [检索到的知识] + [用户问题]
    ↓
调用通义千问生成回答
    ↓
返回结果
```

### 5.3 核心代码示例

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter
import faiss
import numpy as np

class KnowledgeBaseManager:
    def __init__(self):
        self.dimension = 1536  # text-embedding-v2 维度
        self.index = faiss.IndexFlatL2(self.dimension)
        self.doc_chunks = []

    def add_document(self, doc_text, doc_id):
        """添加文档到知识库"""
        # 1. 文本分块
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        chunks = splitter.split_text(doc_text)

        # 2. 向量化
        embeddings = get_embeddings(chunks)

        # 3. 添加到FAISS
        embeddings_np = np.array(embeddings).astype('float32')
        self.index.add(embeddings_np)

        # 4. 保存chunk文本和doc_id的映射
        for i, chunk in enumerate(chunks):
            self.doc_chunks.append({
                'doc_id': doc_id,
                'chunk_index': i,
                'text': chunk
            })

    def search(self, query, top_k=3):
        """检索相关文档"""
        # 1. 查询向量化
        query_embedding = get_embeddings([query])[0]
        query_np = np.array([query_embedding]).astype('float32')

        # 2. FAISS检索
        distances, indices = self.index.search(query_np, top_k)

        # 3. 返回相关文档块
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.doc_chunks):
                results.append({
                    'text': self.doc_chunks[idx]['text'],
                    'score': float(distances[0][i])
                })

        return results

    def generate_rag_response(self, query, dh_data):
        """RAG增强生成"""
        # 1. 检索相关知识
        relevant_docs = self.search(query, top_k=3)

        # 2. 构建增强Prompt
        context = "\n\n".join([doc['text'] for doc in relevant_docs])

        enhanced_prompt = f"""基于以下知识回答用户问题：

【知识库内容】
{context}

【用户问题】
{query}

请根据知识库内容回答，如果知识库中没有相关信息，可以基于常识回答。"""

        # 3. 调用通义千问
        messages = [{"role": "user", "content": enhanced_prompt}]
        personality_prompt = generate_personality_prompt(dh_data)

        response = chat_with_qianwen(messages, personality_prompt, stream=False)
        return response
```

---

## 6. 分阶段实施路线图

### Phase 1: 后端基础架构 (1-2周)

**目标**: 搭建基础后端框架，实现基本的认证和数据库

#### 任务清单
- ✅ 创建Flask项目结构
- ✅ 配置阿里云DashScope SDK
- ✅ 设计并创建SQLite数据库schema
- ✅ 实现用户注册/登录API (JWT)
- ✅ 实现数字人CRUD API
- ✅ 编写单元测试

#### 技术难点
- JWT token管理
- 密码加密 (bcrypt)
- CORS配置

---

### Phase 2: 核心AI对话功能 (1周)

**目标**: 实现基于通义千问的对话功能

#### 任务清单
- ✅ 实现对话API接口 (/api/chat)
- ✅ 集成通义千问流式对话
- ✅ 实现对话历史存储和检索
- ✅ 实现情绪识别功能 (基于对话内容分析)
- ✅ 性格系统提示词生成

#### 技术难点
- SSE (Server-Sent Events) 流式响应
- 对话上下文管理 (限制token数量)
- 情绪分类算法

---

### Phase 3: 数字人管理API (3-5天)

**目标**: 完善数字人管理功能

#### 任务清单
- ✅ 数字人列表、详情、创建、删除API
- ✅ 性格特质映射到Prompt
- ✅ 声音参数API (预留TTS接口)
- ✅ 数字人统计数据 (消息数、最后对话时间)

---

### Phase 4: 知识库RAG系统 (1-2周)

**目标**: 实现文档上传和RAG检索增强生成

#### 任务清单
- ✅ 文档上传和解析 (PDF, Word, TXT)
- ✅ 文本向量化 (阿里云embedding)
- ✅ FAISS向量数据库集成
- ✅ RAG检索增强生成
- ✅ 知识库管理API

#### 技术难点
- 大文件处理
- 文本分块策略
- 向量检索优化

---

### Phase 5: 前后端联调 (3-5天)

**目标**: 修改前端对接真实API

#### 任务清单
- ✅ 修改 chat.html 对接真实对话API
- ✅ 修改 dh-list.html 对接数字人列表API
- ✅ 修改创建流程对接后端
- ✅ 测试完整用户流程
- ✅ 性能优化和错误处理

---

### Phase 6: 部署和文档 (2-3天)

**目标**: 部署到生产环境并编写文档

#### 任务清单
- ✅ 创建Dockerfile
- ✅ 编写docker-compose.yml
- ✅ 编写API文档
- ✅ 编写部署指南
- ✅ 性能测试和优化

---

## 7. 部署方案

### 7.1 Docker部署

#### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```

#### docker-compose.yml
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - FLASK_ENV=production
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend:/usr/share/nginx/html
    depends_on:
      - backend
    restart: unless-stopped
```

### 7.2 环境变量管理

```bash
# .env.production
DASHSCOPE_API_KEY=sk-71bb10435f134dfdab3a4b684e57b640
LLM_MODEL=qwen-plus
FLASK_ENV=production
SECRET_KEY=<生产环境随机密钥>
DATABASE_URL=postgresql://user:pass@host:5432/mindpal
```

---

## 8. 预估成本

### 8.1 阿里云API费用

#### 通义千问 (qwen-turbo)
- 输入: ¥0.0008/千tokens
- 输出: ¥0.002/千tokens
- 估算: 每次对话平均500 tokens，每月1000次对话 ≈ ¥1.25/月

#### Text Embedding
- ¥0.0007/千tokens
- 估算: 每个文档5000 tokens，每月10个文档 ≈ ¥0.035/月

**总成本预估**: ¥2-5/月 (测试阶段)

### 8.2 服务器成本
- 阿里云ECS (2核4G): ¥60-100/月
- 或使用免费额度 (新用户)

---

## 9. 风险和挑战

### 9.1 技术风险
1. **API限流**: 阿里云API有QPS限制，需要实现请求队列
2. **token超限**: 对话历史过长导致token超限，需要实现智能截断
3. **向量数据库性能**: FAISS在大规模数据下的性能问题

### 9.2 缓解措施
1. 实现请求限流和重试机制
2. 对话历史保留最近10轮，超过部分总结后存储
3. P1阶段迁移到 Milvus 或 Weaviate

---

## 10. 下一步行动

### 立即开始 (今天)
1. ✅ 创建后端项目目录结构
2. ✅ 安装依赖 (Flask, dashscope, etc.)
3. ✅ 配置 .env 文件 (API Key)
4. ✅ 实现第一个测试API (Hello World)
5. ✅ 测试阿里云API连通性

### 本周完成
- Phase 1: 后端基础架构
- Phase 2: 核心AI对话功能

### 下周完成
- Phase 3: 数字人管理API
- Phase 4: 知识库RAG系统
- Phase 5: 前后端联调

---

## 附录

### A. 阿里云DashScope文档
- 官方文档: https://help.aliyun.com/zh/dashscope/
- API参考: https://help.aliyun.com/zh/dashscope/developer-reference/api-details
- Python SDK: https://github.com/aliyun/alibabacloud-dashscope-sdk-python

### B. 相关资源
- Flask文档: https://flask.palletsprojects.com/
- SQLAlchemy文档: https://docs.sqlalchemy.org/
- FAISS文档: https://github.com/facebookresearch/faiss

---

**文档维护者**: MindPal开发团队
**最后更新**: 2025-01-11
