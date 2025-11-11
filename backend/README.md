# MindPal Backend API

> 基于Flask + 阿里云通义千问的数字人对话平台后端服务

## 🚀 快速启动

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

`.env` 文件已包含阿里云API Key：
```env
DASHSCOPE_API_KEY=sk-71bb10435f134dfdab3a4b684e57b640
LLM_MODEL=qwen-turbo
```

### 3. 运行服务器

```bash
python app.py
```

服务将在 `http://localhost:5000` 启动

### 4. 测试API

```bash
# 健康检查
curl http://localhost:5000/health

# 查看API端点
curl http://localhost:5000/
```

---

## 📁 项目结构

```
backend/
├── app.py                      # Flask应用入口
├── requirements.txt            # Python依赖
├── .env                        # 环境变量配置
├── app/
│   ├── __init__.py
│   ├── models/
│   │   └── __init__.py        # 数据库模型（User, DigitalHuman, Message, KnowledgeDoc）
│   ├── routes/
│   │   ├── auth.py            # 认证API（注册/登录）
│   │   ├── digital_humans.py  # 数字人管理API
│   │   ├── chat.py            # 对话API
│   │   └── knowledge.py       # 知识库API
│   └── services/
│       └── qianwen_service.py # 阿里云通义千问服务集成
├── data/                       # 数据库文件目录
└── uploads/                    # 文件上传目录
```

---

## 📡 API 文档

### 基础信息
- **Base URL**: `http://localhost:5000/api`
- **认证方式**: JWT Token (Bearer Token)

---

### 🔐 认证 API (`/api/auth`)

#### 用户注册
```http
POST /api/auth/register
Content-Type: application/json

{
  "phone": "13800138000",
  "password": "password123"
}

响应:
{
  "success": true,
  "message": "注册成功",
  "data": {
    "id": 1,
    "phone": "13800138000",
    "created_at": "2025-01-11T10:00:00"
  }
}
```

#### 用户登录
```http
POST /api/auth/login
Content-Type: application/json

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

#### 验证Token
```http
GET /api/auth/verify
Authorization: Bearer <token>

响应:
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "phone": "13800138000"
    }
  }
}
```

---

### 🤖 数字人管理 API (`/api/digital-humans`)

#### 获取数字人列表
```http
GET /api/digital-humans
Authorization: Bearer <token>

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

#### 创建数字人
```http
POST /api/digital-humans
Authorization: Bearer <token>
Content-Type: application/json

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

#### 删除数字人
```http
DELETE /api/digital-humans/:id
Authorization: Bearer <token>

响应:
{
  "success": true,
  "message": "删除成功"
}
```

---

### 💬 对话 API (`/api/chat`)

#### 发送消息（流式）
```http
POST /api/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "dhId": 1,
  "message": "今天天气怎么样？"
}

响应 (Server-Sent Events):
data: {"chunk": "今天"}
data: {"chunk": "天气"}
data: {"chunk": "很好"}
data: {"done": true, "emotion": "happy"}
```

#### 获取对话历史
```http
GET /api/chat/history/:dhId?limit=50&offset=0
Authorization: Bearer <token>

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

#### 清除对话历史
```http
DELETE /api/chat/history/:dhId
Authorization: Bearer <token>

响应:
{
  "success": true,
  "message": "对话历史已清除"
}
```

---

### 📚 知识库 API (`/api/knowledge`)

#### 获取文档列表
```http
GET /api/knowledge/:dhId
Authorization: Bearer <token>

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

## 🔧 核心功能说明

### 1. 阿里云通义千问集成

**使用的服务**：
- **LLM**: `qwen-turbo` (可升级到 qwen-plus/qwen-max)
- **Embedding**: `text-embedding-v2` (用于知识库向量化)

**性格系统**：
- 根据前端设置的性格特质动态生成system prompt
- 支持6种基础性格 + 5维特质调节
- 自定义性格描述

**示例代码**：
```python
from app.services.qianwen_service import chat_with_qianwen

# 对话
dh_data = {
    "name": "小智",
    "personality": "gentle",
    "traits": {"liveliness": 70, "humor": 80, ...}
}

messages = [
    {"role": "user", "content": "你好"}
]

for chunk in chat_with_qianwen(messages, dh_data, stream=True):
    print(chunk, end='')
```

### 2. JWT认证

**Token生成**：
```python
from app.routes.auth import generate_token

token = generate_token(user_id=1)
```

**Token验证**：
```python
from app.routes.auth import verify_token

user_id = verify_token(token)
```

**Token有效期**: 7天

### 3. 数据库Schema

```sql
users
├── id (PK)
├── phone (UNIQUE)
├── password_hash
└── created_at

digital_humans
├── id (PK)
├── user_id (FK)
├── name
├── avatar_type, avatar_emoji
├── personality, traits (JSON)
├── voice, voice_params (JSON)
└── message_count

messages
├── id (PK)
├── dh_id (FK)
├── role (user/assistant)
├── content
├── emotion
└── created_at

knowledge_docs
├── id (PK)
├── dh_id (FK)
├── filename, file_type
├── status
└── created_at
```

---

## 🧪 测试

### 完整测试流程

```bash
# 1. 注册用户
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800138000","password":"test123"}'

# 2. 登录获取token
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800138000","password":"test123"}'

# 3. 创建数字人
curl -X POST http://localhost:5000/api/digital-humans \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"小智","avatar":"boy-sunny","avatarEmoji":"👦","personality":"gentle","traits":{"liveliness":70}}'

# 4. 发送消息
curl -X POST http://localhost:5000/api/chat \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"dhId":1,"message":"你好"}'
```

---

## 🚧 开发路线图

### ✅ P0 - 已完成
- [x] Flask后端框架搭建
- [x] 阿里云通义千问集成
- [x] 用户认证系统 (JWT)
- [x] 数字人CRUD API
- [x] AI对话功能（流式）
- [x] 对话历史存储
- [x] 情绪识别
- [x] 性格系统

### 🔄 P1 - 进行中
- [ ] 知识库RAG系统实现
- [ ] 文档上传和解析
- [ ] FAISS向量检索
- [ ] 前后端联调

### 📅 P2 - 计划中
- [ ] PostgreSQL迁移
- [ ] Redis缓存
- [ ] 语音TTS集成
- [ ] 性能优化

---

## 📊 成本估算

### 阿里云API费用

#### 通义千问 (qwen-turbo)
- 输入: ¥0.0008/千tokens
- 输出: ¥0.002/千tokens
- **估算**: 每月1000次对话 ≈ ¥1.25/月

#### Text Embedding
- ¥0.0007/千tokens
- **估算**: 每月10个文档 ≈ ¥0.035/月

**总成本**: ¥2-5/月 (测试阶段)

---

## 🛠️ 故障排查

### 问题1: 无法启动服务

**解决**：
```bash
# 检查依赖
pip install -r requirements.txt

# 检查.env文件
cat .env
```

### 问题2: API Key错误

**解决**：
- 确认 `.env` 文件中 `DASHSCOPE_API_KEY` 正确
- 检查API Key是否有效：https://dashscope.console.aliyun.com/

### 问题3: CORS错误

**解决**：
- 在 `.env` 中添加前端URL到 `ALLOWED_ORIGINS`
- 例如: `ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:5500`

---

## 📚 相关文档

- [阿里云DashScope文档](https://help.aliyun.com/zh/dashscope/)
- [Flask文档](https://flask.palletsprojects.com/)
- [前端项目文档](../frontend/README.md)
- [后端实施方案](../BACKEND_IMPLEMENTATION_PLAN.md)

---

**开发团队**: MindPal Team
**最后更新**: 2025-01-11
