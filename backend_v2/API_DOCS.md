# MindPal Backend V2 - API 文档

## 概述

MindPal 后端 V2 是一个基于 FastAPI 的异步 REST API 服务，为 MindPal 数字人交互平台提供完整的后端支持。

### 技术栈
- **框架**: FastAPI 0.109+
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **缓存**: Redis
- **向量数据库**: Qdrant
- **LLM**: 通义千问 + Claude
- **语音**: 阿里云TTS/ASR
- **支付**: 微信支付 + 支付宝

---

## API 端点总览 (17个模块，80+ 端点)

### 🔐 认证 (Auth) - `/api/v1/auth`
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | /register | 用户注册 |
| POST | /login | 用户登录 |
| POST | /refresh | 刷新Token |
| GET | /me | 获取当前用户信息 |

### 👤 角色 (Player) - `/api/v1/player`
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /profile | 获取角色信息 |
| POST | /create | 创建角色 |
| PUT | /update | 更新角色信息 |
| GET | /stats | 获取角色统计 |

### 💬 对话 (Dialogue) - `/api/v1/dialogue`
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | /chat | 普通对话 |
| POST | /stream | 流式对话 (SSE) |
| GET | /history/{npc_id} | 获取对话历史 |
| DELETE | /history/{npc_id} | 清空对话历史 |

### 🎒 背包 (Inventory) - `/api/v1/inventory`
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | / | 获取背包物品 |
| POST | /use | 使用物品 |
| POST | /move | 移动物品 |
| DELETE | /{slot} | 丢弃物品 |

### 🏪 商城 (Shop) - `/api/v1/shop`
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /items | 商品列表 |
| GET | /items/{item_id} | 商品详情 |
| POST | /purchase | 购买商品 |

### 📜 任务 (Quest) - `/api/v1/quests`
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | / | 任务列表 |
| GET | /{quest_id} | 任务详情 |
| POST | /{quest_id}/accept | 接受任务 |
| POST | /{quest_id}/progress | 更新进度 |
| POST | /{quest_id}/claim | 领取奖励 |
| GET | /daily | 每日任务 |

### 👥 社交 (Social) - `/api/v1/social`
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /search | 搜索玩家 |
| POST | /friends/request | 发送好友申请 |
| GET | /friends/requests | 好友申请列表 |
| PUT | /friends/request/{id} | 处理申请 |
| GET | /friends | 好友列表 |
| DELETE | /friends/{id} | 删除好友 |
| POST | /block | 屏蔽玩家 |
| DELETE | /block/{id} | 取消屏蔽 |

### 💭 聊天 (Chat) - `/api/v1/chat`
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | /send | 发送消息 |
| GET | /messages | 获取消息 |
| GET | /channels | 频道列表 |

### 🎮 队伍 (Party) - `/api/v1/party`
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | /create | 创建队伍 |
| GET | / | 当前队伍 |
| POST | /invite | 邀请玩家 |
| POST | /join | 加入队伍 |
| POST | /leave | 离开队伍 |
| POST | /kick | 踢出成员 |
| DELETE | /dissolve | 解散队伍 |

### 🏆 成就 (Achievement) - `/api/v1/achievements`
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | / | 成就列表 |
| GET | /{id} | 成就详情 |
| POST | /{id}/claim | 领取奖励 |
| GET | /progress | 成就进度 |

### 📊 排行榜 (Leaderboard) - `/api/v1/leaderboard`
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | / | 排行榜列表 |
| GET | /{type} | 具体排行 |
| GET | /my-rank | 我的排名 |

### 🧠 记忆 (Memory) - `/api/v1/memory`
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /profile | 玩家档案 |
| GET | /search | 语义检索 |
| POST | /add | 添加记忆 |
| GET | /summary | 记忆摘要 |

### 🤖 AI服务 (AI) - `/api/v1/ai`
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /health | 服务健康检查 |
| GET | /models | 可用模型列表 |
| POST | /route | 智能路由 |
| GET | /cost | 成本统计 |

### 🔑 三钥匙挑战 (Three Keys) - `/api/v1/three-keys`
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /status | 挑战状态 |
| POST | /start | 开始挑战 |
| POST | /respond | 提交回答 |
| GET | /prompt/{key_type}/{stage} | 获取阶段提示 |
| GET | /history/{key_type} | 挑战历史 |

### 🎤 语音 (Voice) - `/api/v1/voice`
| 方法 | 端点 | 描述 |
|------|------|------|
| POST | /tts | 文本转语音 |
| POST | /tts/npc | NPC语音合成 |
| POST | /tts/stream | 流式语音合成 |
| POST | /asr | 语音识别 (Base64) |
| POST | /asr/upload | 语音识别 (文件上传) |
| GET | /voices | 可用语音列表 |
| GET | /npc-voices | NPC语音映射 |

### 💳 支付 (Payment) - `/api/v1/payment`
| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /products | 充值商品列表 |
| POST | /orders | 创建订单 |
| GET | /orders | 订单列表 |
| GET | /orders/{order_no} | 订单详情 |
| POST | /orders/{order_no}/cancel | 取消订单 |
| POST | /notify/wechat | 微信支付回调 |
| POST | /notify/alipay | 支付宝回调 |
| GET | /vip/status | VIP状态 |

---

## 数据模型

### 用户 (User)
```json
{
  "id": 1,
  "phone": "13800000000",
  "nickname": "玩家昵称",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### 角色 (Player)
```json
{
  "id": 1,
  "user_id": 1,
  "name": "心灵旅者",
  "gender": "neutral",
  "level": 10,
  "exp": 5000,
  "gold": 10000,
  "diamonds": 100,
  "energy": 80
}
```

### NPC好感度
```json
{
  "npc_id": "bei",
  "affinity": 75,
  "level": 3,
  "title": "知心好友"
}
```

---

## 认证

所有需要认证的端点需要在请求头中包含:
```
Authorization: Bearer <access_token>
```

---

## 错误响应

标准错误响应格式:
```json
{
  "code": 40001,
  "message": "Error description",
  "error_detail": "Detailed error info (debug only)"
}
```

### 错误码
| 错误码 | 描述 |
|--------|------|
| 0 | 成功 |
| 40001 | 通用错误 |
| 40101 | 未认证 |
| 40301 | 无权限 |
| 40401 | 未找到 |
| 42201 | 参数验证失败 |

---

## 开发指南

### 本地运行
```bash
cd backend_v2
pip install -r requirements.txt
python -m scripts.init_db  # 初始化数据库
uvicorn app.main:app --reload
```

### 测试账号
- 手机: 13800000000
- 密码: test123456

### API文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

*最后更新: 2024-12*
