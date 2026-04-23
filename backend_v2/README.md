# MindPal Backend V2

> FastAPI重构版本 - 面向元宇宙的智能体数字人交互平台

## 技术栈

| 类别 | 技术 | 版本 |
|------|------|------|
| 框架 | FastAPI | 0.109+ |
| ORM | SQLAlchemy | 2.0 (async) |
| 数据库 | PostgreSQL | 15 |
| 缓存 | Redis | 7 |
| 向量数据库 | Qdrant | 1.7 |
| LLM | Qwen / Claude | - |

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd backend_v2

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件，填写必要的API密钥
# 特别是: DASHSCOPE_API_KEY, ANTHROPIC_API_KEY
```

### 3. 启动服务

**方式一: Docker Compose (推荐)**

```bash
docker-compose up -d
```

**方式二: 本地开发**

```bash
# 确保PostgreSQL和Redis已启动

# 运行应用
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

## 项目结构

```
backend_v2/
├── app/
│   ├── main.py              # FastAPI入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   │
│   ├── models/              # 数据模型
│   │   ├── user.py          # 用户模型
│   │   ├── player.py        # 游戏角色
│   │   ├── dialogue.py      # 对话记录
│   │   ├── inventory.py     # 背包物品
│   │   └── quest.py         # 任务模型
│   │
│   ├── schemas/             # Pydantic模式
│   ├── api/v1/              # API路由
│   │
│   ├── services/            # 业务逻辑
│   │   ├── llm/             # LLM服务
│   │   │   ├── qwen.py      # 通义千问
│   │   │   ├── claude.py    # Claude
│   │   │   └── router.py    # LLM路由
│   │   └── npc/             # NPC系统
│   │       ├── manager.py   # NPC管理器
│   │       └── prompts/     # 人设配置
│   │
│   └── core/                # 核心组件
│       └── security.py      # JWT认证
│
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## API端点

### 认证 `/api/v1/auth`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /register | 用户注册 |
| POST | /login | 用户登录 |
| POST | /refresh | 刷新Token |
| GET | /me | 获取当前用户 |

### 角色 `/api/v1/player`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /character | 创建角色 |
| GET | /character | 获取角色信息 |
| PUT | /position | 更新位置 |
| GET | /inventory | 获取背包 |
| POST | /inventory/use | 使用物品 |

### 对话 `/api/v1/dialogue`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /chat | 与NPC对话 |
| POST | /stream | 流式对话(SSE) |
| GET | /history | 获取对话历史 |
| GET | /affinity | 获取好感度 |

## NPC系统

### 可用NPC

| ID | 名称 | 角色 | LLM |
|----|------|------|-----|
| bei | 小北 | 情感陪伴者 | Claude |
| aela | 艾拉 | 智慧引导者 | Qwen |
| momo | 莫莫 | 商人 | Qwen |
| chronos | 克洛诺斯 | 任务引导 | Qwen |
| sesame | 芝麻 | 宠物伙伴 | Qwen |

### 好感度等级

| 等级 | 称号 | 范围 |
|------|------|------|
| 1 | 初识 | 0-20 |
| 2 | 友好 | 21-40 |
| 3 | 熟悉 | 41-60 |
| 4 | 亲密 | 61-80 |
| 5 | 挚友 | 81-100 |

## 开发指南

### 添加新的NPC

1. 在 `app/services/npc/prompts/` 创建 `{npc_id}.yaml`
2. 定义 `base_prompt`, `affinity_levels`, `emotion_responses`
3. 在 `LLMRouter.npc_scene_map` 中配置LLM映射

### 数据库迁移

```bash
# 初始化Alembic
alembic init alembic

# 创建迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head
```

## 下一步开发

- [ ] WebSocket实时通信
- [ ] 商城API
- [ ] 任务系统API
- [ ] 社交系统API
- [ ] 记忆向量检索
- [ ] 危机干预检测

## 许可证

MIT License
