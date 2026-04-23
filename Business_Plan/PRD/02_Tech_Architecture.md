# MindPal PRD - 02 技术架构

> 本文档定义技术栈选型、系统架构、模块划分

---

## 1. 技术栈选型

### 1.1 总体技术栈

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                              │
│  游戏引擎: Godot 4.3+                                        │
│  脚本语言: GDScript (主) + C# (可选性能优化)                  │
│  3D资产: AI生成 (Meshy/Tripo3D) + 免费资产库                 │
│  音频: Godot内置音频系统                                      │
│  UI框架: Godot Control节点                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ WebSocket + REST API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        服务端层                              │
│  Web框架: FastAPI (Python 3.11+)                            │
│  实时通信: WebSocket (python-socketio)                       │
│  任务队列: Celery + Redis                                    │
│  缓存: Redis                                                 │
│  大模型调用: LangChain + 多模型适配器                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        数据层                                │
│  主数据库: PostgreSQL 15+                                    │
│  向量数据库: Qdrant (对话记忆检索)                            │
│  文件存储: MinIO (自托管S3兼容)                              │
│  会话存储: Redis                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        AI服务层                              │
│  代码生成: Google AI Studio (Gemini 2.5 Pro/Flash)          │
│  NPC对话: Qwen-Max / 火山引擎豆包                            │
│  复杂对话: Claude API (情感深度对话)                         │
│  本地降级: Qwen-7B-Chat                                      │
│  向量嵌入: text-embedding-ada-002 或 BGE                     │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 为什么选择这个技术栈

| 组件 | 选择 | 理由 |
|------|------|------|
| **游戏引擎** | Godot 4 | 开源免费、GDScript类似Python易学、内置网络支持、社区活跃 |
| **后端框架** | FastAPI | Python生态、异步支持、自动API文档、你能看懂 |
| **实时通信** | WebSocket | 低延迟、双向通信、适合多人游戏 |
| **数据库** | PostgreSQL | 成熟稳定、JSON支持好、免费 |
| **向量数据库** | Qdrant | 开源、性能好、适合对话记忆检索 |
| **大模型** | Qwen/火山 | 你已有额度、中文效果好、成本可控 |

### 1.3 开发环境要求

**客户端开发：**
```
- Godot Engine 4.3+
- 操作系统: Windows 10/11
- 显卡: 支持Vulkan的独立显卡（推荐）
- 内存: 16GB+
```

**服务端开发：**
```
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose
```

---

## 2. 系统架构图

### 2.1 整体架构

```
                                   ┌─────────────────┐
                                   │   玩家客户端     │
                                   │   (Godot 4)     │
                                   └────────┬────────┘
                                            │
                          ┌─────────────────┼─────────────────┐
                          │                 │                 │
                          ▼                 ▼                 ▼
              ┌───────────────┐  ┌───────────────┐  ┌───────────────┐
              │   REST API    │  │   WebSocket   │  │   静态资源    │
              │   (FastAPI)   │  │   (实时通信)   │  │   (CDN/MinIO) │
              └───────┬───────┘  └───────┬───────┘  └───────────────┘
                      │                  │
                      └────────┬─────────┘
                               │
                      ┌────────▼────────┐
                      │   API Gateway   │
                      │   (路由/认证)    │
                      └────────┬────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   用户服务     │    │   游戏服务     │    │   AI服务      │
│  - 注册登录    │    │  - 世界状态    │    │  - NPC对话    │
│  - 用户资料    │    │  - 多人同步    │    │  - 情绪分析    │
│  - 好友系统    │    │  - 任务系统    │    │  - 记忆管理    │
└───────┬───────┘    └───────┬───────┘    └───────┬───────┘
        │                    │                    │
        └──────────────────────────────────────────┘
                               │
                      ┌────────▼────────┐
                      │    数据层        │
                      │  PostgreSQL     │
                      │  Redis          │
                      │  Qdrant         │
                      └─────────────────┘
```

### 2.2 客户端架构（Godot）

```
MindPal/
├── project.godot              # 项目配置
├── assets/                    # 资源文件
│   ├── models/               # 3D模型
│   ├── textures/             # 纹理贴图
│   ├── audio/                # 音效音乐
│   ├── fonts/                # 字体
│   └── ui/                   # UI图片
├── scenes/                    # 场景文件
│   ├── main/                 # 主场景
│   │   ├── Main.tscn         # 主入口场景
│   │   └── Main.gd           # 主脚本
│   ├── world/                # 世界场景
│   │   ├── CentralPlaza.tscn # 中央广场
│   │   ├── MirrorCity.tscn   # 现代区
│   │   ├── MemoryForest.tscn # 奇幻区
│   │   └── FutureStation.tscn# 科幻区
│   ├── characters/           # 角色场景
│   │   ├── Player.tscn       # 玩家角色
│   │   ├── NPCAela.tscn      # 导游艾拉
│   │   ├── NPCMomo.tscn      # 商人老莫
│   │   ├── NPCChronos.tscn   # 时守
│   │   ├── NPCBei.tscn       # 朋友小北
│   │   └── PetSesame.tscn    # 宠物芝麻
│   ├── ui/                   # UI场景
│   │   ├── MainMenu.tscn     # 主菜单
│   │   ├── HUD.tscn          # 游戏内UI
│   │   ├── DialogBox.tscn    # 对话框
│   │   ├── Inventory.tscn    # 背包
│   │   └── Settings.tscn     # 设置
│   └── minigames/            # 小游戏场景
│       ├── MirrorDialogue.tscn    # 镜像对话
│       ├── MemoryMaze.tscn        # 记忆迷宫
│       └── FutureArchitect.tscn   # 未来建筑师
├── scripts/                   # 脚本文件
│   ├── autoload/             # 自动加载（全局单例）
│   │   ├── GameManager.gd    # 游戏状态管理
│   │   ├── NetworkManager.gd # 网络通信
│   │   ├── AudioManager.gd   # 音频管理
│   │   └── DataManager.gd    # 数据管理
│   ├── player/               # 玩家相关
│   │   ├── PlayerController.gd    # 玩家控制
│   │   ├── PlayerCamera.gd        # 摄像机控制
│   │   └── PlayerInventory.gd     # 背包系统
│   ├── npc/                  # NPC相关
│   │   ├── NPCBase.gd        # NPC基类
│   │   ├── NPCDialogue.gd    # 对话系统
│   │   └── NPCAIController.gd# AI控制
│   ├── multiplayer/          # 多人相关
│   │   ├── MultiplayerManager.gd  # 多人管理
│   │   ├── PlayerSync.gd          # 玩家同步
│   │   └── ChatSystem.gd          # 聊天系统
│   └── utils/                # 工具类
│       ├── Constants.gd      # 常量定义
│       └── Helpers.gd        # 辅助函数
└── addons/                    # 插件
    └── (第三方插件)
```

### 2.3 服务端架构（Python）

```
mindpal-server/
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI入口
│   ├── config.py             # 配置管理
│   ├── dependencies.py       # 依赖注入
│   │
│   ├── api/                  # API路由
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py       # 认证接口
│   │   │   ├── users.py      # 用户接口
│   │   │   ├── game.py       # 游戏接口
│   │   │   ├── social.py     # 社交接口
│   │   │   ├── shop.py       # 商店接口
│   │   │   └── ai.py         # AI对话接口
│   │   └── websocket/
│   │       ├── __init__.py
│   │       ├── game_sync.py  # 游戏状态同步
│   │       └── chat.py       # 实时聊天
│   │
│   ├── services/             # 业务逻辑
│   │   ├── __init__.py
│   │   ├── auth_service.py   # 认证服务
│   │   ├── user_service.py   # 用户服务
│   │   ├── game_service.py   # 游戏服务
│   │   ├── npc_service.py    # NPC服务
│   │   ├── ai_service.py     # AI服务
│   │   ├── memory_service.py # 记忆服务
│   │   └── economy_service.py# 经济服务
│   │
│   ├── models/               # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py           # 用户模型
│   │   ├── player.py         # 玩家模型
│   │   ├── npc.py            # NPC模型
│   │   ├── dialogue.py       # 对话模型
│   │   ├── item.py           # 道具模型
│   │   └── quest.py          # 任务模型
│   │
│   ├── schemas/              # Pydantic模式
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── game.py
│   │   ├── dialogue.py
│   │   └── social.py
│   │
│   ├── ai/                   # AI相关
│   │   ├── __init__.py
│   │   ├── llm_client.py     # 大模型客户端
│   │   ├── prompts/          # Prompt模板
│   │   │   ├── __init__.py
│   │   │   ├── npc_aela.py   # 艾拉的Prompt
│   │   │   ├── npc_momo.py   # 老莫的Prompt
│   │   │   ├── npc_chronos.py# 时守的Prompt
│   │   │   ├── npc_bei.py    # 小北的Prompt
│   │   │   └── pet_sesame.py # 芝麻的Prompt
│   │   ├── memory.py         # 记忆管理
│   │   └── emotion.py        # 情绪分析
│   │
│   └── db/                   # 数据库
│       ├── __init__.py
│       ├── database.py       # 数据库连接
│       ├── redis.py          # Redis连接
│       └── qdrant.py         # 向量数据库连接
│
├── migrations/               # 数据库迁移
├── tests/                    # 测试
├── docker/                   # Docker配置
│   ├── Dockerfile
│   └── docker-compose.yml
├── scripts/                  # 脚本
│   ├── init_db.py           # 初始化数据库
│   └── seed_data.py         # 填充测试数据
├── requirements.txt
├── .env.example
└── README.md
```

---

## 3. 核心模块设计

### 3.1 网络通信模块

#### 3.1.1 通信协议

| 场景 | 协议 | 说明 |
|------|------|------|
| 登录/注册 | HTTPS REST | 安全性要求高 |
| 数据查询/修改 | HTTPS REST | 非实时操作 |
| 玩家位置同步 | WebSocket | 实时性要求高 |
| NPC对话 | WebSocket | 流式输出 |
| 聊天消息 | WebSocket | 实时性要求高 |
| 文件上传 | HTTPS REST | 大文件 |

#### 3.1.2 WebSocket消息格式

```json
{
  "type": "message_type",
  "timestamp": 1702368000000,
  "data": {
    // 具体数据
  }
}
```

**消息类型定义：**

```python
# 客户端 -> 服务端
CLIENT_PLAYER_MOVE = "client.player.move"        # 玩家移动
CLIENT_PLAYER_ACTION = "client.player.action"    # 玩家动作
CLIENT_CHAT_SEND = "client.chat.send"            # 发送聊天
CLIENT_NPC_TALK = "client.npc.talk"              # 与NPC对话
CLIENT_NPC_TALK_STREAM = "client.npc.talk.stream"# 流式对话

# 服务端 -> 客户端
SERVER_PLAYER_SYNC = "server.player.sync"        # 同步其他玩家
SERVER_PLAYER_JOIN = "server.player.join"        # 玩家加入
SERVER_PLAYER_LEAVE = "server.player.leave"      # 玩家离开
SERVER_CHAT_RECEIVE = "server.chat.receive"      # 收到聊天
SERVER_NPC_RESPONSE = "server.npc.response"      # NPC回复
SERVER_NPC_STREAM = "server.npc.stream"          # NPC流式回复
SERVER_WORLD_EVENT = "server.world.event"        # 世界事件
```

#### 3.1.3 玩家同步策略

```
同步频率: 20Hz (每50ms一次)
同步内容: 位置(x,y,z) + 旋转(y) + 动画状态
插值方式: 客户端预测 + 服务端校正
延迟容忍: <200ms正常，>500ms警告
```

### 3.2 AI对话模块

#### 3.2.1 对话流程

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  玩家    │───▶│  客户端  │───▶│  服务端  │───▶│  AI服务  │
│  输入    │    │  预处理  │    │  处理    │    │  生成    │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                   │
┌─────────┐    ┌─────────┐    ┌─────────┐         │
│  显示    │◀───│  客户端  │◀───│  服务端  │◀────────┘
│  回复    │    │  渲染    │    │  流式发送 │
└─────────┘    └─────────┘    └─────────┘
```

#### 3.2.2 AI服务调用策略

```python
# 模型选择策略
def select_model(npc_type: str, message_complexity: int) -> str:
    """
    根据NPC类型和消息复杂度选择模型
    """
    if npc_type == "bei":  # 小北需要最高质量
        if message_complexity > 7:
            return "claude-3-sonnet"  # 复杂情感对话
        return "qwen-max"
    elif npc_type == "chronos":  # 时守需要哲学深度
        return "qwen-max"
    else:  # 其他NPC用更快的模型
        return "qwen-turbo"

# 降级策略
def get_fallback_model(primary_model: str) -> str:
    """
    主模型失败时的降级方案
    """
    fallback_chain = {
        "claude-3-sonnet": "qwen-max",
        "qwen-max": "qwen-turbo",
        "qwen-turbo": "local-qwen-7b",  # 本地模型兜底
    }
    return fallback_chain.get(primary_model, "local-qwen-7b")
```

#### 3.2.3 对话记忆架构

```
┌─────────────────────────────────────────────────────────┐
│                     记忆层次                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐   短期记忆 (Redis)                     │
│  │ 当前对话    │   - 当前会话的对话历史                  │
│  │ 上下文      │   - 最近10轮对话                       │
│  └─────────────┘   - TTL: 30分钟                        │
│                                                         │
│  ┌─────────────┐   中期记忆 (PostgreSQL)                │
│  │ 会话摘要    │   - 每次会话的摘要                      │
│  │ 重要事件    │   - 用户分享的重要信息                  │
│  └─────────────┘   - 最近30天的数据                     │
│                                                         │
│  ┌─────────────┐   长期记忆 (Qdrant向量库)              │
│  │ 用户画像    │   - 性格、偏好、关注话题                │
│  │ 情感轨迹    │   - 历史情绪变化                       │
│  │ 深度对话    │   - 有价值的对话片段向量化存储          │
│  └─────────────┘   - 永久保存                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 3.3 多人同步模块

#### 3.3.1 房间系统

```python
# 房间配置
ROOM_CONFIG = {
    "max_players_per_room": 50,      # 每房间最大人数
    "room_types": {
        "central_plaza": {           # 中央广场
            "max_players": 100,
            "is_social_hub": True,
        },
        "mirror_city": {             # 现代区
            "max_players": 50,
            "is_social_hub": False,
        },
        "memory_forest": {           # 奇幻区
            "max_players": 50,
            "is_social_hub": False,
        },
        "future_station": {          # 科幻区
            "max_players": 50,
            "is_social_hub": False,
        },
    },
    "sync_rate_hz": 20,              # 同步频率
    "position_interpolation": True,  # 位置插值
}
```

#### 3.3.2 同步状态机

```
玩家状态:
┌─────────┐    移动    ┌─────────┐
│  Idle   │ ────────▶ │ Walking │
│  站立   │ ◀──────── │  行走   │
└─────────┘    停止    └─────────┘
     │                      │
     │ 对话                 │ 跑步
     ▼                      ▼
┌─────────┐           ┌─────────┐
│ Talking │           │ Running │
│  对话中  │           │  跑步   │
└─────────┘           └─────────┘
```

---

## 4. 安全设计

### 4.1 认证与授权

```python
# JWT配置
JWT_CONFIG = {
    "algorithm": "HS256",
    "access_token_expire_minutes": 60,      # 访问令牌1小时
    "refresh_token_expire_days": 30,        # 刷新令牌30天
}

# 权限等级
PERMISSION_LEVELS = {
    "guest": 0,        # 游客（未登录）
    "user": 1,         # 普通用户
    "vip": 2,          # VIP会员
    "moderator": 3,    # 版主
    "admin": 4,        # 管理员
    "superadmin": 5,   # 超级管理员
}
```

### 4.2 内容安全

```python
# 敏感词检测
CONTENT_FILTER_CONFIG = {
    "enabled": True,
    "check_user_input": True,       # 检查用户输入
    "check_ai_output": True,        # 检查AI输出
    "action_on_detect": "filter",   # filter/block/log
}

# 危机检测关键词（需要特殊处理）
CRISIS_KEYWORDS = [
    "自杀", "自残", "不想活", "想死",
    # ... 更多关键词
]

# 检测到危机时的处理
def handle_crisis_detection(user_id: str, message: str):
    """
    检测到危机信号时：
    1. 记录日志
    2. 触发温和的关怀回复
    3. 提供专业帮助资源
    4. 通知管理员（严重情况）
    """
    pass
```

### 4.3 反作弊

```python
# 基础反作弊措施
ANTI_CHEAT_CONFIG = {
    "rate_limit": {
        "api_calls_per_minute": 60,
        "messages_per_minute": 20,
        "move_speed_max": 10.0,  # 最大移动速度
    },
    "position_validation": True,     # 服务端验证位置
    "economy_validation": True,      # 服务端验证经济操作
}
```

---

## 5. 部署架构

### 5.1 开发环境

```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  # 后端服务
  api:
    build: ./mindpal-server
    ports:
      - "8000:8000"
    volumes:
      - ./mindpal-server:/app
    environment:
      - DEBUG=true
    depends_on:
      - postgres
      - redis
      - qdrant

  # PostgreSQL
  postgres:
    image: postgres:15
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_USER=mindpal
      - POSTGRES_PASSWORD=dev_password
      - POSTGRES_DB=mindpal
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis
  redis:
    image: redis:7
    ports:
      - "6379:6379"

  # Qdrant向量数据库
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  # MinIO对象存储
  minio:
    image: minio/minio
    ports:
      - "9000:9000"
      - "9001:9001"
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data

volumes:
  postgres_data:
  qdrant_data:
  minio_data:
```

### 5.2 生产环境（未来）

```
                        ┌─────────────┐
                        │   CDN       │
                        │  (静态资源)  │
                        └──────┬──────┘
                               │
                        ┌──────▼──────┐
                        │   Nginx     │
                        │  (反向代理)  │
                        └──────┬──────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
       ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
       │   API Pod   │  │   API Pod   │  │   API Pod   │
       │   (容器1)   │  │   (容器2)   │  │   (容器3)   │
       └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
              │                │                │
              └────────────────┼────────────────┘
                               │
                        ┌──────▼──────┐
                        │   数据层     │
                        │  (托管服务)  │
                        └─────────────┘
```

---

## 6. 监控与日志

### 6.1 日志配置

```python
LOGGING_CONFIG = {
    "version": 1,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/mindpal.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
        }
    },
    "loggers": {
        "mindpal": {"level": "INFO", "handlers": ["console", "file"]},
        "mindpal.ai": {"level": "DEBUG"},  # AI相关详细日志
        "mindpal.game": {"level": "INFO"},
    }
}
```

### 6.2 关键指标

| 指标 | 说明 | 告警阈值 |
|------|------|---------|
| `api_response_time_p99` | API响应时间P99 | > 2000ms |
| `websocket_connections` | WebSocket连接数 | > 5000 |
| `ai_request_latency` | AI请求延迟 | > 5000ms |
| `ai_request_error_rate` | AI请求错误率 | > 5% |
| `db_connection_pool_usage` | 数据库连接池使用率 | > 80% |
| `memory_usage_percent` | 内存使用率 | > 85% |

---

**下一篇 → `03_World_Design.md`（世界观设计）**
