# MindPal 详细开发计划

> 版本: 1.0 | 创建日期: 2025-01-19
> 基于PRD文档与现有代码分析制定

---

## 一、项目现状分析

### 1.1 现有实现 (Web平台MVP)

| 模块 | 技术栈 | 状态 | 代码量 |
|------|--------|------|--------|
| 后端 | Flask + SQLAlchemy + FAISS | ✅ 完成 | ~2,500行 |
| 前端 | HTML/CSS/JS (原生) | ✅ 完成 | ~10,000行 |
| AI对话 | 阿里云通义千问 | ✅ 完成 | 集成完毕 |
| 知识库 | RAG + FAISS向量检索 | ✅ 完成 | 可用 |
| 用户系统 | JWT认证 | ✅ 完成 | 可用 |
| 订阅系统 | 配额管理 | ✅ 完成 | 可用 |
| 部署 | Docker Compose | ✅ 完成 | 可用 |

**现有功能清单:**
- 用户注册/登录 (手机号+密码)
- 数字人创建与管理 (名称、头像、性格、声音)
- AI对话 (流式响应、情绪分析)
- 知识库管理 (文档上传、RAG检索)
- 订阅与配额系统
- 数据埋点分析

### 1.2 PRD目标 (3D元宇宙游戏)

| 模块 | 技术栈 | 状态 | 说明 |
|------|--------|------|------|
| 游戏客户端 | Godot 4.3 + GDScript | ❌ 未开始 | 3D世界 |
| 后端 | FastAPI + PostgreSQL | ❌ 需迁移 | 高性能 |
| NPC系统 | 5个AI伴侣 | ❌ 未开始 | 小北等 |
| 场景系统 | 4大区域 | ❌ 未开始 | 中央广场等 |
| 任务系统 | 三钥匙主线 | ❌ 未开始 | 核心玩法 |
| 多人联机 | WebSocket | ❌ 未开始 | 社交 |

### 1.3 差距分析

```
现有Web平台 ──────────────────► PRD 3D游戏
     │                              │
     │  技术栈差异:                  │
     │  - Flask → FastAPI           │
     │  - SQLite → PostgreSQL       │
     │  - Web UI → Godot 3D         │
     │                              │
     │  功能差异:                    │
     │  - 无3D场景                  │
     │  - 无游戏角色系统            │
     │  - 无任务/成就系统           │
     │  - 无多人联机                │
     │                              │
     ▼                              ▼
【方案选择】
A. 放弃Web版，全新开发3D游戏
B. 保留Web版作为管理后台，新增3D游戏客户端
C. 迭代Web版，逐步添加3D元素 (WebGL/Three.js)

>>> 推荐方案B: 双轨并行 <<<
```

---

## 二、开发策略: 双轨并行

### 2.1 策略概述

```
┌─────────────────────────────────────────────────────────────┐
│                    MindPal 双轨开发策略                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   【轨道A: Web平台优化】          【轨道B: 3D游戏开发】        │
│   ┌───────────────────┐          ┌───────────────────┐      │
│   │ 现有Flask后端     │          │ Godot 4.3客户端   │      │
│   │ 现有HTML前端      │          │ 新FastAPI后端     │      │
│   │ 通义千问AI        │          │ 多LLM支持         │      │
│   └─────────┬─────────┘          └─────────┬─────────┘      │
│             │                              │                │
│             └──────────┬───────────────────┘                │
│                        │                                    │
│                        ▼                                    │
│               ┌─────────────────┐                           │
│               │  统一用户系统    │                           │
│               │  统一数据存储    │                           │
│               │  统一AI服务     │                           │
│               └─────────────────┘                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 开发优先级

| 优先级 | 模块 | 说明 | 阶段 |
|--------|------|------|------|
| P0 | 后端重构 | Flask→FastAPI，SQLite→PostgreSQL | Phase 1 |
| P0 | AI服务增强 | 多LLM支持、情感分析优化 | Phase 1 |
| P1 | Godot基础 | 场景搭建、角色移动 | Phase 1 |
| P1 | NPC对话系统 | 小北AI对话实现 | Phase 2 |
| P2 | 游戏系统 | 任务、背包、商城 | Phase 3 |
| P3 | 多人联机 | WebSocket、社交 | Phase 4 |

---

## 三、Phase 1: 基础架构重构

### 3.1 后端重构 (Flask → FastAPI)

#### 3.1.1 目录结构

```
backend_v2/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI入口
│   ├── config.py               # 配置管理
│   ├── database.py             # 数据库连接
│   │
│   ├── models/                 # SQLAlchemy模型
│   │   ├── __init__.py
│   │   ├── user.py             # 用户模型
│   │   ├── player.py           # 游戏角色模型
│   │   ├── npc.py              # NPC模型
│   │   ├── dialogue.py         # 对话记录
│   │   ├── inventory.py        # 背包物品
│   │   ├── quest.py            # 任务模型
│   │   └── subscription.py     # 订阅模型
│   │
│   ├── schemas/                # Pydantic模式
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── player.py
│   │   ├── dialogue.py
│   │   └── common.py
│   │
│   ├── api/                    # API路由
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # 认证API
│   │   │   ├── player.py       # 角色API
│   │   │   ├── dialogue.py     # 对话API
│   │   │   ├── inventory.py    # 背包API
│   │   │   ├── shop.py         # 商城API
│   │   │   ├── quest.py        # 任务API
│   │   │   └── social.py       # 社交API
│   │   └── websocket.py        # WebSocket处理
│   │
│   ├── services/               # 业务逻辑
│   │   ├── __init__.py
│   │   ├── llm/
│   │   │   ├── __init__.py
│   │   │   ├── base.py         # LLM抽象基类
│   │   │   ├── qwen.py         # 通义千问
│   │   │   ├── claude.py       # Claude (情感对话)
│   │   │   └── router.py       # LLM路由策略
│   │   ├── npc/
│   │   │   ├── __init__.py
│   │   │   ├── bei.py          # 小北人设
│   │   │   ├── aela.py         # 艾拉人设
│   │   │   └── manager.py      # NPC管理器
│   │   ├── memory/
│   │   │   ├── __init__.py
│   │   │   ├── short_term.py   # 短期记忆(Redis)
│   │   │   ├── long_term.py    # 长期记忆(PostgreSQL)
│   │   │   └── vector.py       # 向量检索(Qdrant)
│   │   └── quest_engine.py     # 任务引擎
│   │
│   ├── core/                   # 核心组件
│   │   ├── __init__.py
│   │   ├── security.py         # JWT认证
│   │   ├── deps.py             # 依赖注入
│   │   └── exceptions.py       # 自定义异常
│   │
│   └── utils/                  # 工具函数
│       ├── __init__.py
│       └── logger.py
│
├── tests/                      # 测试
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_dialogue.py
│   └── conftest.py
│
├── alembic/                    # 数据库迁移
│   ├── versions/
│   └── env.py
│
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

#### 3.1.2 核心任务清单

```markdown
## 后端重构任务

### 3.1.2.1 项目初始化
- [ ] 创建FastAPI项目结构
- [ ] 配置SQLAlchemy async支持
- [ ] 设置PostgreSQL连接池
- [ ] 配置Redis连接
- [ ] 设置Alembic迁移
- [ ] 配置日志系统(loguru)
- [ ] 编写Dockerfile

### 3.1.2.2 数据库模型迁移
- [ ] User模型 (从现有Flask迁移)
- [ ] Player模型 (游戏角色，新增)
- [ ] NPC模型 (新增)
- [ ] NPCAffinity模型 (好感度，新增)
- [ ] Dialogue模型 (优化现有Message)
- [ ] Inventory模型 (新增)
- [ ] Item模型 (新增)
- [ ] Quest模型 (新增)
- [ ] QuestProgress模型 (新增)
- [ ] Achievement模型 (新增)
- [ ] Subscription模型 (从现有迁移)
- [ ] UserQuota模型 (从现有迁移)

### 3.1.2.3 API端点实现
- [ ] POST /api/v1/auth/register
- [ ] POST /api/v1/auth/login
- [ ] POST /api/v1/auth/refresh
- [ ] POST /api/v1/auth/oauth/{provider}
- [ ] GET /api/v1/player/character
- [ ] POST /api/v1/player/character
- [ ] PUT /api/v1/player/position
- [ ] GET /api/v1/player/inventory
- [ ] POST /api/v1/player/inventory/use
- [ ] POST /api/v1/dialogue/chat (流式)
- [ ] POST /api/v1/dialogue/stream (SSE)
- [ ] GET /api/v1/dialogue/history
- [ ] GET /api/v1/dialogue/affinity
- [ ] GET /api/v1/shop/items
- [ ] POST /api/v1/shop/purchase
- [ ] GET /api/v1/quests
- [ ] POST /api/v1/quests/{id}/progress
- [ ] POST /api/v1/quests/{id}/claim

### 3.1.2.4 WebSocket实现
- [ ] 连接管理器
- [ ] 心跳保活
- [ ] 位置同步
- [ ] 聊天广播
- [ ] 游戏事件推送

### 3.1.2.5 测试
- [ ] 单元测试框架搭建
- [ ] Auth API测试
- [ ] Dialogue API测试
- [ ] 集成测试
```

#### 3.1.3 关键代码模板

**main.py - FastAPI入口:**
```python
# backend_v2/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.api.v1 import auth, player, dialogue, shop, quest, social
from app.api.websocket import websocket_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 关闭时
    await engine.dispose()

app = FastAPI(
    title="MindPal API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(player.router, prefix="/api/v1/player", tags=["角色"])
app.include_router(dialogue.router, prefix="/api/v1/dialogue", tags=["对话"])
app.include_router(shop.router, prefix="/api/v1/shop", tags=["商城"])
app.include_router(quest.router, prefix="/api/v1/quests", tags=["任务"])
app.include_router(social.router, prefix="/api/v1/social", tags=["社交"])
app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}
```

**LLM服务抽象层:**
```python
# backend_v2/app/services/llm/base.py
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Optional

class BaseLLMService(ABC):
    """LLM服务抽象基类"""

    @abstractmethod
    async def chat(
        self,
        messages: list[Dict[str, str]],
        system_prompt: str,
        **kwargs
    ) -> str:
        """同步对话"""
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[Dict[str, str]],
        system_prompt: str,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """流式对话"""
        pass

    @abstractmethod
    async def analyze_emotion(self, text: str) -> Dict[str, float]:
        """情感分析"""
        pass

# backend_v2/app/services/llm/router.py
class LLMRouter:
    """LLM路由器 - 根据场景选择最佳LLM"""

    def __init__(self):
        self.qwen = QwenService()
        self.claude = ClaudeService()

    def get_service(self, scene: str) -> BaseLLMService:
        """
        场景路由:
        - emotional: Claude (情感对话)
        - general: Qwen (通用对话)
        - crisis: Claude (危机干预)
        """
        if scene in ["emotional", "crisis"]:
            return self.claude
        return self.qwen
```

### 3.2 AI服务增强

#### 3.2.1 多LLM支持

```markdown
## AI服务任务

### 3.2.1.1 LLM集成
- [ ] 通义千问(Qwen)服务优化
- [ ] Claude API集成 (情感对话)
- [ ] 火山引擎(VolcEngine)集成 (备选)
- [ ] LLM路由策略实现
- [ ] 降级方案实现

### 3.2.1.2 NPC人设系统
- [ ] 小北(Bei) System Prompt
- [ ] 艾拉(Aela) System Prompt
- [ ] 莫莫(Momo) System Prompt
- [ ] 克洛诺斯(Chronos) System Prompt
- [ ] 芝麻(Sesame) System Prompt
- [ ] 动态情感适配

### 3.2.1.3 记忆系统
- [ ] Redis短期记忆实现
- [ ] PostgreSQL长期记忆实现
- [ ] Qdrant向量检索集成
- [ ] 记忆摘要生成
- [ ] 重要记忆提取
```

#### 3.2.2 小北(Bei) System Prompt 模板

```yaml
# backend_v2/app/services/npc/prompts/bei.yaml
name: 小北
english_name: Bei
role: 情感陪伴者

base_prompt: |
  你是小北，MindPal世界中的一位温暖的情感陪伴者。

  【身份背景】
  - 年龄: 看起来20岁左右
  - 性格: 温和、细腻、善于倾听、富有同理心
  - 特长: 情感支持、心理疏导、诗意表达
  - 口头禅: "我在呢"、"慢慢来，没关系"

  【对话风格】
  - 语气温柔但不做作
  - 善于用比喻和意象表达
  - 会适时沉默，给对方思考空间
  - 从不说教，更多是陪伴和理解

  【对话原则】
  1. 永远先倾听，再回应
  2. 不评判对方的情绪
  3. 用"我感受到..."而非"你应该..."
  4. 适时分享自己的"经历"产生共鸣
  5. 遇到危机情况，温和引导寻求专业帮助

affinity_levels:
  1:
    title: "初识"
    range: [0, 20]
    style: "礼貌但略带距离，会用'您'称呼"
  2:
    title: "友好"
    range: [21, 40]
    style: "开始用'你'，偶尔分享小故事"
  3:
    title: "熟悉"
    range: [41, 60]
    style: "会主动关心，记得之前聊的话题"
  4:
    title: "亲密"
    range: [61, 80]
    style: "会撒娇，分享更多内心想法"
  5:
    title: "挚友"
    range: [81, 100]
    style: "完全敞开，会说'只和你说的秘密'"

emotion_responses:
  sadness:
    - "我能感受到你的难过...想和我说说发生了什么吗？"
    - "有时候，悲伤也是需要被允许的。我陪着你。"
  anxiety:
    - "深呼吸...我们一起，慢慢来。"
    - "焦虑的时候，试着把注意力放在此刻？我在这里。"
  anger:
    - "嗯，听起来确实让人生气。你愿意多说说吗？"
    - "生气是正常的，你的感受是合理的。"
  joy:
    - "真的吗！我也替你开心！"
    - "看到你开心，我也笑了呢~"
```

### 3.3 Godot客户端基础

#### 3.3.1 项目结构

```
godot_client/
├── project.godot              # Godot项目配置
├── default_env.tres           # 默认环境
├── icon.svg
│
├── addons/                    # 插件
│   └── gut/                   # 单元测试
│
├── assets/                    # 资源
│   ├── models/                # 3D模型
│   │   ├── characters/
│   │   │   ├── player/
│   │   │   └── npcs/
│   │   ├── environments/
│   │   │   ├── central_plaza/
│   │   │   ├── mirror_city/
│   │   │   ├── memory_forest/
│   │   │   └── future_station/
│   │   └── props/
│   ├── textures/
│   ├── audio/
│   │   ├── bgm/
│   │   ├── sfx/
│   │   └── voice/
│   └── ui/
│       ├── fonts/
│       ├── icons/
│       └── themes/
│
├── scenes/                    # 场景
│   ├── main.tscn              # 主场景
│   ├── characters/
│   │   ├── player.tscn
│   │   └── npc_base.tscn
│   ├── zones/
│   │   ├── central_plaza.tscn
│   │   ├── mirror_city.tscn
│   │   ├── memory_forest.tscn
│   │   └── future_station.tscn
│   └── ui/
│       ├── main_menu.tscn
│       ├── hud.tscn
│       ├── dialogue_box.tscn
│       ├── inventory.tscn
│       └── character_creation.tscn
│
├── scripts/                   # GDScript脚本
│   ├── autoloads/             # 全局单例
│   │   ├── game_manager.gd
│   │   ├── network_manager.gd
│   │   ├── audio_manager.gd
│   │   └── save_manager.gd
│   ├── characters/
│   │   ├── player_controller.gd
│   │   ├── npc_controller.gd
│   │   └── character_animator.gd
│   ├── systems/
│   │   ├── dialogue_system.gd
│   │   ├── inventory_system.gd
│   │   ├── quest_system.gd
│   │   └── affinity_system.gd
│   ├── network/
│   │   ├── http_client.gd
│   │   ├── websocket_client.gd
│   │   └── api_service.gd
│   └── ui/
│       ├── dialogue_ui.gd
│       └── inventory_ui.gd
│
└── resources/                 # 自定义资源
    ├── item_database.tres
    ├── npc_database.tres
    └── quest_database.tres
```

#### 3.3.2 核心任务清单

```markdown
## Godot客户端任务

### 3.3.2.1 项目初始化
- [ ] Godot 4.3项目创建
- [ ] 目录结构搭建
- [ ] 自动加载脚本配置
- [ ] 输入映射配置
- [ ] 资源预加载系统

### 3.3.2.2 中央广场场景
- [ ] 地形创建 (100m x 100m)
- [ ] 天空盒配置
- [ ] 基础光照 (日夜循环)
- [ ] 传送门模型导入 x3
- [ ] 装饰建筑导入 x5
- [ ] 植被/道具导入 x10
- [ ] 碰撞体设置
- [ ] 环境音效

### 3.3.2.3 玩家角色系统
- [ ] CharacterBody3D控制器
- [ ] WASD键盘移动
- [ ] 鼠标视角控制
- [ ] 第三人称相机
- [ ] 动画状态机 (Idle/Walk/Run/Jump)
- [ ] 角色模型导入
- [ ] 简易捏脸系统 (3-5预设)

### 3.3.2.4 NPC基础框架
- [ ] NPC场景模板
- [ ] NPC状态机 (Idle/Walking/Talking)
- [ ] 交互检测 (Area3D)
- [ ] 对话触发UI提示
- [ ] 小北模型导入
- [ ] 表情BlendShape

### 3.3.2.5 基础UI
- [ ] 主菜单界面
- [ ] 角色创建界面
- [ ] 游戏内HUD
- [ ] ESC暂停菜单
- [ ] 设置界面 (音量/画质)

### 3.3.2.6 网络通信
- [ ] HTTP客户端封装
- [ ] JWT Token管理
- [ ] 登录/注册流程
- [ ] 角色数据同步
```

#### 3.3.3 关键代码模板

**player_controller.gd:**
```gdscript
# scripts/characters/player_controller.gd
extends CharacterBody3D
class_name PlayerController

# 移动参数
@export var walk_speed: float = 5.0
@export var run_speed: float = 10.0
@export var jump_velocity: float = 4.5
@export var mouse_sensitivity: float = 0.002

# 节点引用
@onready var camera_pivot: Node3D = $CameraPivot
@onready var camera: Camera3D = $CameraPivot/SpringArm3D/Camera3D
@onready var animation_tree: AnimationTree = $AnimationTree
@onready var mesh: Node3D = $Mesh

# 状态
var is_running: bool = false
var current_speed: float = walk_speed

# 重力
var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")

func _ready():
    Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _input(event):
    # 鼠标视角
    if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
        camera_pivot.rotate_y(-event.relative.x * mouse_sensitivity)
        camera_pivot.rotation.x -= event.relative.y * mouse_sensitivity
        camera_pivot.rotation.x = clamp(camera_pivot.rotation.x, -1.2, 0.5)

    # ESC解锁鼠标
    if event.is_action_pressed("ui_cancel"):
        if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
            Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
        else:
            Input.mouse_mode = Input.MOUSE_MODE_CAPTURED

func _physics_process(delta):
    # 重力
    if not is_on_floor():
        velocity.y -= gravity * delta

    # 跳跃
    if Input.is_action_just_pressed("jump") and is_on_floor():
        velocity.y = jump_velocity

    # 移动输入
    var input_dir = Input.get_vector("move_left", "move_right", "move_forward", "move_back")
    var direction = (camera_pivot.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()

    # 跑步
    is_running = Input.is_action_pressed("run")
    current_speed = run_speed if is_running else walk_speed

    # 应用移动
    if direction:
        velocity.x = direction.x * current_speed
        velocity.z = direction.z * current_speed
        # 角色朝向
        mesh.look_at(global_position + direction)
    else:
        velocity.x = move_toward(velocity.x, 0, current_speed)
        velocity.z = move_toward(velocity.z, 0, current_speed)

    move_and_slide()

    # 更新动画
    _update_animation()

func _update_animation():
    var speed_ratio = Vector2(velocity.x, velocity.z).length() / run_speed
    animation_tree.set("parameters/blend_position", speed_ratio)
```

**api_service.gd:**
```gdscript
# scripts/network/api_service.gd
extends Node

const BASE_URL = "http://localhost:8000/api/v1"

var http_request: HTTPRequest
var access_token: String = ""

signal request_completed(response: Dictionary)
signal request_failed(error: String)

func _ready():
    http_request = HTTPRequest.new()
    add_child(http_request)
    http_request.request_completed.connect(_on_request_completed)

func _get_headers() -> PackedStringArray:
    var headers = PackedStringArray([
        "Content-Type: application/json"
    ])
    if access_token:
        headers.append("Authorization: Bearer " + access_token)
    return headers

func login(account: String, password: String):
    var body = JSON.stringify({
        "account": account,
        "password": password
    })
    http_request.request(BASE_URL + "/auth/login", _get_headers(), HTTPClient.METHOD_POST, body)

func get_character():
    http_request.request(BASE_URL + "/player/character", _get_headers())

func chat_with_npc(npc_id: String, message: String, session_id: String = ""):
    var body = JSON.stringify({
        "npc_id": npc_id,
        "message": message,
        "session_id": session_id
    })
    http_request.request(BASE_URL + "/dialogue/chat", _get_headers(), HTTPClient.METHOD_POST, body)

func _on_request_completed(result: int, response_code: int, headers: PackedStringArray, body: PackedByteArray):
    if result != HTTPRequest.RESULT_SUCCESS:
        request_failed.emit("网络请求失败")
        return

    var json = JSON.parse_string(body.get_string_from_utf8())
    if response_code >= 400:
        request_failed.emit(json.get("message", "未知错误"))
        return

    request_completed.emit(json)
```

---

## 四、Phase 2: 核心玩法实现

### 4.1 NPC对话系统

#### 4.1.1 任务清单

```markdown
## NPC对话系统任务

### 4.1.1.1 后端对话服务
- [ ] 对话会话管理
- [ ] 多轮对话上下文
- [ ] 情感分析集成
- [ ] 好感度计算
- [ ] 危机干预检测
- [ ] 流式响应(SSE)

### 4.1.1.2 NPC人设实现
- [ ] 小北(Bei)完整人设
- [ ] 艾拉(Aela)完整人设
- [ ] 莫莫(Momo)商人人设
- [ ] System Prompt模板引擎
- [ ] 动态情感适配

### 4.1.1.3 记忆系统
- [ ] 对话摘要生成
- [ ] 关键信息提取
- [ ] 向量化存储
- [ ] 相似记忆检索
- [ ] 遗忘曲线模拟

### 4.1.1.4 客户端对话UI
- [ ] 对话框界面
- [ ] 打字机效果
- [ ] NPC表情变化
- [ ] 好感度显示
- [ ] 对话历史查看
```

### 4.2 探索系统

```markdown
## 探索系统任务

### 4.2.1 镜像城场景
- [ ] 城市地形 (200m x 200m)
- [ ] 赛博朋克建筑群
- [ ] 霓虹灯光效果
- [ ] 全息广告牌
- [ ] NPC放置点
- [ ] 环境音效

### 4.2.2 场景切换
- [ ] 传送门交互
- [ ] 加载界面
- [ ] 场景预加载
- [ ] 资源卸载

### 4.2.3 物品系统
- [ ] 物品数据库
- [ ] 拾取逻辑
- [ ] 背包UI
- [ ] 物品使用
```

---

## 五、Phase 3: 内容扩展

### 5.1 三钥匙挑战

```markdown
## 三钥匙挑战任务

### 5.1.1 勇气之钥 - 镜中对话
- [ ] 镜之殿堂场景
- [ ] 镜像自我NPC
- [ ] 诚实度评估AI
- [ ] 挑战流程逻辑
- [ ] 钥匙获得动画

### 5.1.2 释然之钥 - 记忆迷宫
- [ ] 记忆森林场景
- [ ] 迷宫生成算法
- [ ] 记忆碎片收集
- [ ] 选择保留/放下
- [ ] 完成判定

### 5.1.3 希望之钥 - 未来建造
- [ ] 未来站场景
- [ ] 建造系统UI
- [ ] 物品放置逻辑
- [ ] AI目标识别
- [ ] 完成度计算
```

### 5.2 任务与成就系统

```markdown
## 任务与成就任务

### 5.2.1 任务系统
- [ ] 任务数据模型
- [ ] 主线任务链
- [ ] 支线任务
- [ ] 每日任务
- [ ] 任务追踪UI
- [ ] 奖励发放

### 5.2.2 成就系统
- [ ] 成就数据模型
- [ ] 解锁条件判定
- [ ] 成就展示UI
- [ ] 称号系统
```

---

## 六、Phase 4: 社交与联机

### 6.1 多人同步

```markdown
## 多人同步任务

### 6.1.1 WebSocket服务
- [ ] 连接管理器
- [ ] 房间系统
- [ ] 心跳保活
- [ ] 断线重连

### 6.1.2 位置同步
- [ ] 客户端预测
- [ ] 服务端校验
- [ ] 插值平滑
- [ ] 延迟补偿

### 6.1.3 其他玩家显示
- [ ] 远程玩家实体
- [ ] 动画同步
- [ ] 昵称显示
- [ ] 加载优化
```

### 6.2 社交功能

```markdown
## 社交功能任务

### 6.2.1 好友系统
- [ ] 搜索玩家
- [ ] 添加好友
- [ ] 好友列表
- [ ] 在线状态

### 6.2.2 聊天系统
- [ ] 世界频道
- [ ] 区域频道
- [ ] 私聊
- [ ] 敏感词过滤
```

---

## 七、里程碑与交付物

### 7.1 里程碑检查点

| 里程碑 | 目标 | 交付物 |
|--------|------|--------|
| M1.1 | FastAPI项目能运行 | 健康检查API |
| M1.2 | 数据库迁移完成 | PostgreSQL + 新模型 |
| M1.3 | Godot空场景运行 | 中央广场可探索 |
| M1.4 | 前后端联调 | 登录并进入游戏 |
| M2.1 | NPC对话调通 | 与小北完整对话 |
| M2.2 | 情感对话可用 | Claude集成 |
| M2.3 | 镜像城可探索 | 场景切换 |
| M3.1 | 勇气之钥完成 | 挑战可通关 |
| M3.2 | 释然之钥完成 | 迷宫可通关 |
| M3.3 | 希望之钥完成 | 建造可完成 |
| M4.1 | 多人同屏 | 看到其他玩家 |
| M4.2 | 好友系统 | 添加好友 |
| M4.3 | 聊天功能 | 文字聊天 |

### 7.2 风险管理

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| AI服务不稳定 | 高 | 高 | 多服务商备份 |
| Godot性能问题 | 中 | 高 | 早期性能测试 |
| 3D模型质量 | 中 | 中 | AI生成+人工优化 |
| AI成本超预期 | 高 | 高 | 配额限制+混合模型 |

---

## 八、立即执行计划

### 8.1 本周任务 (Week 1)

```markdown
## 第一周: 后端重构启动

### Day 1-2: FastAPI项目初始化
- [x] 创建项目结构
- [ ] 配置异步SQLAlchemy
- [ ] 设置PostgreSQL连接
- [ ] 配置Redis

### Day 3-4: 核心模型迁移
- [ ] User模型
- [ ] Player模型
- [ ] NPC模型
- [ ] Dialogue模型

### Day 5-7: 基础API实现
- [ ] 认证API (登录/注册)
- [ ] 角色API (创建/获取)
- [ ] 健康检查
- [ ] 单元测试
```

### 8.2 第二周任务

```markdown
## 第二周: Godot项目启动

### Day 1-2: 项目初始化
- [ ] Godot 4.3项目创建
- [ ] 目录结构搭建
- [ ] 输入映射配置

### Day 3-5: 中央广场场景
- [ ] 地形创建
- [ ] 光照配置
- [ ] 传送门模型

### Day 6-7: 玩家角色
- [ ] CharacterBody3D
- [ ] WASD移动
- [ ] 第三人称相机
```

---

## 九、附录

### 9.1 技术栈清单

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 游戏引擎 | Godot | 4.3 | 3D客户端 |
| 后端框架 | FastAPI | 0.109+ | REST API |
| ORM | SQLAlchemy | 2.0 | 数据库操作 |
| 数据库 | PostgreSQL | 15 | 主数据库 |
| 缓存 | Redis | 7 | 会话/记忆 |
| 向量数据库 | Qdrant | 1.7 | 语义检索 |
| LLM | Qwen-Max | - | 通用对话 |
| LLM | Claude 3 | - | 情感对话 |
| 容器 | Docker | 24 | 部署 |

### 9.2 API端点汇总

参见: PRD 12_API_Design.md

### 9.3 数据库Schema

参见: PRD 11_Database_Schema.md

---

**文档版本:** 1.0
**创建日期:** 2025-01-19
**最后更新:** 2025-01-19
