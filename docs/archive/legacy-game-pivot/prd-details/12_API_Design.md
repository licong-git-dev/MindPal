# 12. API接口设计

> MindPal PRD - API Interface Design
> 版本: 1.0 | 更新: 2024-01

---

## 1. API概述

### 1.1 基础规范

| 项目 | 规范 |
|------|------|
| 协议 | HTTPS (REST) + WSS (WebSocket) |
| 数据格式 | JSON |
| 字符编码 | UTF-8 |
| 时间格式 | ISO 8601 (UTC) |
| API版本 | URL路径: `/api/v1/` |
| 认证方式 | JWT Bearer Token |

### 1.2 通用响应格式

```json
// 成功响应
{
    "code": 0,
    "message": "success",
    "data": { ... },
    "timestamp": "2024-01-15T10:30:00Z"
}

// 错误响应
{
    "code": 10001,
    "message": "Invalid token",
    "error_detail": "Token has expired",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### 1.3 错误码定义

| 范围 | 类型 | 示例 |
|------|------|------|
| 0 | 成功 | 0 = 成功 |
| 10000-10999 | 认证错误 | 10001=Token无效, 10002=Token过期 |
| 20000-20999 | 参数错误 | 20001=参数缺失, 20002=格式错误 |
| 30000-30999 | 业务错误 | 30001=余额不足, 30002=物品不存在 |
| 40000-40999 | 系统错误 | 40001=服务不可用, 40002=限流 |

---

## 2. 用户认证 API

### 2.1 注册

```
POST /api/v1/auth/register

Request:
{
    "username": "player123",
    "email": "player@example.com",
    "password": "SecurePass123!",
    "verification_code": "123456"  // 邮箱验证码
}

Response:
{
    "code": 0,
    "data": {
        "user_id": "uuid",
        "username": "player123",
        "access_token": "eyJhbG...",
        "refresh_token": "eyJhbG...",
        "expires_in": 7200
    }
}
```

### 2.2 登录

```
POST /api/v1/auth/login

Request:
{
    "account": "player@example.com",  // 邮箱或用户名
    "password": "SecurePass123!"
}

Response:
{
    "code": 0,
    "data": {
        "user_id": "uuid",
        "username": "player123",
        "player_id": "uuid",  // 游戏角色ID
        "has_character": true,
        "access_token": "eyJhbG...",
        "refresh_token": "eyJhbG...",
        "expires_in": 7200
    }
}
```

### 2.3 第三方登录

```
POST /api/v1/auth/oauth/{provider}
provider: wechat | qq | google

Request:
{
    "code": "oauth_authorization_code",
    "state": "random_state"
}

Response:
{
    "code": 0,
    "data": {
        "is_new_user": false,
        "user_id": "uuid",
        "access_token": "eyJhbG...",
        ...
    }
}
```

### 2.4 刷新Token

```
POST /api/v1/auth/refresh

Request:
{
    "refresh_token": "eyJhbG..."
}

Response:
{
    "code": 0,
    "data": {
        "access_token": "new_token",
        "expires_in": 7200
    }
}
```

---

## 3. 玩家角色 API

### 3.1 创建角色

```
POST /api/v1/player/character

Request:
{
    "nickname": "星空旅人",
    "avatar_config": {
        "gender": "female",
        "face_shape": 2,
        "skin_color": "#FFE4C4",
        "hair_style": 5,
        "hair_color": "#4A4A4A",
        "eye_style": 3,
        "eye_color": "#8B4513"
    }
}

Response:
{
    "code": 0,
    "data": {
        "player_id": "uuid",
        "nickname": "星空旅人",
        "level": 1,
        "gold": 1000,
        "diamonds": 0,
        "current_zone": "central_plaza",
        "position": {"x": 0, "y": 0, "z": 0}
    }
}
```

### 3.2 获取角色信息

```
GET /api/v1/player/character

Response:
{
    "code": 0,
    "data": {
        "player_id": "uuid",
        "nickname": "星空旅人",
        "level": 15,
        "experience": 12500,
        "exp_to_next_level": 15000,
        "gold": 25000,
        "diamonds": 150,
        "current_zone": "mirror_city",
        "position": {"x": 100.5, "y": 0, "z": -50.2},
        "avatar_config": {...},
        "equipment": {...},
        "stats": {
            "total_playtime": 36000,
            "dialogues_count": 256,
            "keys_collected": [1, 2],
            "achievements_count": 12
        }
    }
}
```

### 3.3 更新位置

```
PUT /api/v1/player/position

Request:
{
    "zone": "mirror_city",
    "x": 100.5,
    "y": 0,
    "z": -50.2,
    "rotation_y": 45.0
}

Response:
{
    "code": 0,
    "data": {
        "synced": true
    }
}
```

---

## 4. 背包与物品 API

### 4.1 获取背包

```
GET /api/v1/player/inventory?category=all

Response:
{
    "code": 0,
    "data": {
        "capacity": 48,
        "used": 12,
        "items": [
            {
                "slot": 0,
                "item_id": "potion_hp_small",
                "name": "小型生命药水",
                "category": "consumable",
                "quantity": 5,
                "icon": "items/potion_hp_small.png"
            },
            ...
        ]
    }
}
```

### 4.2 使用物品

```
POST /api/v1/player/inventory/use

Request:
{
    "slot": 0,
    "quantity": 1
}

Response:
{
    "code": 0,
    "data": {
        "item_id": "potion_hp_small",
        "quantity_remaining": 4,
        "effect": {
            "type": "heal",
            "value": 50
        }
    }
}
```

### 4.3 丢弃/分解物品

```
DELETE /api/v1/player/inventory/{slot}

Request:
{
    "action": "discard",  // discard | decompose
    "quantity": 1
}

Response:
{
    "code": 0,
    "data": {
        "action": "decompose",
        "rewards": [
            {"item_id": "material_basic", "quantity": 2}
        ]
    }
}
```

---

## 5. 商城 API

### 5.1 获取商品列表

```
GET /api/v1/shop/items?category=consumable&page=1&size=20

Response:
{
    "code": 0,
    "data": {
        "items": [
            {
                "id": "potion_hp_large",
                "name": "大型生命药水",
                "description": "恢复150点生命值",
                "category": "consumable",
                "gold_price": 500,
                "diamond_price": null,
                "icon": "items/potion_hp_large.png",
                "daily_limit": 10,
                "purchased_today": 2
            },
            ...
        ],
        "total": 50,
        "page": 1,
        "size": 20
    }
}
```

### 5.2 购买商品

```
POST /api/v1/shop/purchase

Request:
{
    "item_id": "potion_hp_large",
    "quantity": 3,
    "currency": "gold"  // gold | diamond
}

Response:
{
    "code": 0,
    "data": {
        "item_id": "potion_hp_large",
        "quantity": 3,
        "total_cost": 1500,
        "currency": "gold",
        "balance": {
            "gold": 23500,
            "diamonds": 150
        }
    }
}
```

---

## 6. 对话 API

### 6.1 发起对话 (HTTP)

```
POST /api/v1/dialogue/chat

Request:
{
    "npc_id": "bei",
    "message": "我最近工作压力很大，不知道该怎么办",
    "session_id": "uuid",  // 可选，用于保持会话
    "emotion_data": {      // 可选，表情识别结果
        "joy": 0.1,
        "sadness": 0.6,
        "neutral": 0.3
    }
}

Response (流式):
{
    "code": 0,
    "data": {
        "session_id": "uuid",
        "npc_id": "bei",
        "response": "我能感受到你的疲惫...",  // 逐步追加
        "emotion": "empathy",
        "is_complete": false
    }
}

// 完成后:
{
    "code": 0,
    "data": {
        "session_id": "uuid",
        "response": "完整回复内容...",
        "is_complete": true,
        "affinity_change": 2,
        "current_affinity": 74
    }
}
```

### 6.2 获取对话历史

```
GET /api/v1/dialogue/history?npc_id=bei&limit=20&before=uuid

Response:
{
    "code": 0,
    "data": {
        "npc_id": "bei",
        "messages": [
            {
                "id": "uuid",
                "role": "user",
                "content": "我最近工作压力很大...",
                "emotion": "sadness",
                "timestamp": "2024-01-15T10:30:00Z"
            },
            {
                "id": "uuid",
                "role": "assistant",
                "content": "我能感受到你的疲惫...",
                "timestamp": "2024-01-15T10:30:05Z"
            },
            ...
        ],
        "has_more": true
    }
}
```

### 6.3 获取NPC好感度

```
GET /api/v1/dialogue/affinity

Response:
{
    "code": 0,
    "data": {
        "aela": {"level": 3, "value": 65, "title": "熟悉"},
        "momo": {"level": 2, "value": 45, "title": "友好"},
        "chronos": {"level": 1, "value": 25, "title": "初识"},
        "bei": {"level": 4, "value": 78, "title": "亲密"},
        "sesame": {"level": 5, "value": 95, "title": "挚友"}
    }
}
```

---

## 7. 任务 API

### 7.1 获取任务列表

```
GET /api/v1/quests?status=in_progress

Response:
{
    "code": 0,
    "data": {
        "main_quest": {
            "id": "main_chapter1_quest3",
            "title": "寻找第一把钥匙",
            "description": "艾拉说镜像城深处藏着勇气之钥...",
            "chapter": 1,
            "objectives": [
                {"id": "obj1", "desc": "前往镜像城", "current": 1, "target": 1, "completed": true},
                {"id": "obj2", "desc": "找到镜之殿堂入口", "current": 0, "target": 1, "completed": false}
            ],
            "rewards": {
                "exp": 500,
                "gold": 1000,
                "items": [{"id": "key_courage", "name": "勇气之钥"}]
            }
        },
        "side_quests": [
            {
                "id": "side_momo_001",
                "title": "莫莫的收集请求",
                "npc": "momo",
                "objectives": [...],
                "rewards": {...}
            }
        ],
        "daily_quests": [...]
    }
}
```

### 7.2 更新任务进度

```
POST /api/v1/quests/{quest_id}/progress

Request:
{
    "objective_id": "obj2",
    "progress": 1
}

Response:
{
    "code": 0,
    "data": {
        "quest_id": "main_chapter1_quest3",
        "objective_id": "obj2",
        "current": 1,
        "target": 1,
        "completed": true,
        "quest_completed": false
    }
}
```

### 7.3 领取任务奖励

```
POST /api/v1/quests/{quest_id}/claim

Response:
{
    "code": 0,
    "data": {
        "rewards_claimed": {
            "exp": 500,
            "exp_new_total": 13000,
            "level_up": false,
            "gold": 1000,
            "items": [
                {"id": "key_courage", "name": "勇气之钥", "quantity": 1}
            ]
        },
        "next_quest": {
            "id": "main_chapter1_quest4",
            "title": "勇气的试炼"
        }
    }
}
```

---

## 8. 社交 API

### 8.1 搜索玩家

```
GET /api/v1/social/search?keyword=星空&page=1

Response:
{
    "code": 0,
    "data": {
        "players": [
            {
                "player_id": "uuid",
                "nickname": "星空旅人",
                "level": 15,
                "avatar_thumbnail": "url",
                "is_online": true,
                "is_friend": false
            }
        ]
    }
}
```

### 8.2 发送好友申请

```
POST /api/v1/social/friends/request

Request:
{
    "target_player_id": "uuid",
    "message": "你好，可以加个好友吗？"
}

Response:
{
    "code": 0,
    "data": {
        "request_id": "uuid",
        "status": "pending"
    }
}
```

### 8.3 处理好友申请

```
PUT /api/v1/social/friends/request/{request_id}

Request:
{
    "action": "accept"  // accept | reject
}

Response:
{
    "code": 0,
    "data": {
        "action": "accept",
        "friend": {
            "player_id": "uuid",
            "nickname": "星空旅人",
            "level": 15
        }
    }
}
```

### 8.4 获取好友列表

```
GET /api/v1/social/friends

Response:
{
    "code": 0,
    "data": {
        "friends": [
            {
                "player_id": "uuid",
                "nickname": "星空旅人",
                "level": 15,
                "avatar_thumbnail": "url",
                "is_online": true,
                "current_zone": "mirror_city",
                "last_online": "2024-01-15T10:00:00Z"
            }
        ],
        "total": 5
    }
}
```

---

## 9. WebSocket 实时通信

### 9.1 连接建立

```
WS /ws/game?token={access_token}

// 连接成功
{
    "type": "connected",
    "data": {
        "player_id": "uuid",
        "server_time": "2024-01-15T10:30:00Z"
    }
}
```

### 9.2 消息类型定义

```typescript
// 客户端 → 服务端
interface ClientMessage {
    type: "position_update" | "chat" | "action" | "heartbeat";
    data: any;
    seq: number;  // 序列号
}

// 服务端 → 客户端
interface ServerMessage {
    type: "player_update" | "chat" | "event" | "error" | "ack";
    data: any;
    timestamp: string;
}
```

### 9.3 位置同步

```json
// 客户端发送
{
    "type": "position_update",
    "data": {
        "x": 100.5,
        "y": 0,
        "z": -50.2,
        "ry": 45.0,
        "velocity": {"x": 1.0, "y": 0, "z": 0.5},
        "animation": "walk"
    },
    "seq": 12345
}

// 服务端广播 (其他玩家)
{
    "type": "player_update",
    "data": {
        "player_id": "uuid",
        "nickname": "星空旅人",
        "position": {"x": 100.5, "y": 0, "z": -50.2},
        "rotation_y": 45.0,
        "velocity": {"x": 1.0, "y": 0, "z": 0.5},
        "animation": "walk"
    },
    "timestamp": "2024-01-15T10:30:00.123Z"
}
```

### 9.4 聊天消息

```json
// 发送聊天
{
    "type": "chat",
    "data": {
        "channel": "world",  // world | zone | party | private
        "content": "大家好！",
        "target_id": null  // 私聊时填写
    },
    "seq": 12346
}

// 接收聊天
{
    "type": "chat",
    "data": {
        "channel": "world",
        "sender": {
            "player_id": "uuid",
            "nickname": "星空旅人",
            "level": 15
        },
        "content": "大家好！",
        "message_id": "uuid"
    },
    "timestamp": "2024-01-15T10:30:05Z"
}
```

### 9.5 游戏事件

```json
// NPC交互开始
{
    "type": "event",
    "data": {
        "event": "npc_interaction_start",
        "player_id": "uuid",
        "npc_id": "bei"
    }
}

// 玩家进入/离开区域
{
    "type": "event",
    "data": {
        "event": "player_zone_change",
        "player_id": "uuid",
        "from_zone": "central_plaza",
        "to_zone": "mirror_city"
    }
}

// 系统公告
{
    "type": "event",
    "data": {
        "event": "system_announcement",
        "title": "维护通知",
        "content": "服务器将于30分钟后进行维护..."
    }
}
```

### 9.6 心跳保活

```json
// 客户端每30秒发送
{
    "type": "heartbeat",
    "data": {
        "client_time": 1705312200000
    },
    "seq": 12347
}

// 服务端响应
{
    "type": "ack",
    "data": {
        "seq": 12347,
        "server_time": 1705312200050,
        "latency": 50
    }
}
```

---

## 10. 流式对话 API (SSE)

### 10.1 流式对话接口

```
POST /api/v1/dialogue/stream
Content-Type: application/json
Accept: text/event-stream

Request:
{
    "npc_id": "bei",
    "message": "我想和你聊聊最近的烦恼",
    "session_id": "uuid"
}

Response (SSE):
event: start
data: {"session_id": "uuid", "npc_id": "bei"}

event: delta
data: {"content": "我"}

event: delta
data: {"content": "很"}

event: delta
data: {"content": "高兴"}

event: delta
data: {"content": "你愿意"}

event: delta
data: {"content": "和我分享..."}

event: done
data: {"full_response": "我很高兴你愿意和我分享...", "affinity_change": 1}
```

---

## 11. 限流与安全

### 11.1 限流策略

| API类型 | 限制 | 窗口 |
|---------|------|------|
| 普通API | 100次 | 1分钟 |
| 登录API | 5次 | 1分钟 |
| 对话API | 30次 | 1分钟 |
| 支付API | 10次 | 1分钟 |

### 11.2 限流响应

```json
{
    "code": 40002,
    "message": "Rate limit exceeded",
    "error_detail": "Too many requests. Please retry after 30 seconds.",
    "retry_after": 30
}

Headers:
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705312260
```

---

**下一篇 → 13_Development_Phases.md（开发阶段规划）**
