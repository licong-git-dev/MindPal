# MindPal 详细开发计划

> 基于PRD 00-13深度分析制定
> 版本: 2.0 | 日期: 2024-12

---

## 1. 现有实现与PRD差距分析

### 1.1 backend_v2 已完成功能

| 模块 | 状态 | 覆盖率 |
|------|------|--------|
| 用户认证 (auth) | ✅ 完成 | 90% |
| 角色系统 (player) | ✅ 完成 | 70% |
| 对话系统 (dialogue) | ✅ 完成 | 60% |
| LLM服务 (qwen/claude) | ✅ 完成 | 80% |
| NPC人设系统 | ✅ 完成 | 70% |
| 好感度系统 | ✅ 完成 | 80% |

### 1.2 PRD要求但尚未实现

| 功能 | PRD文档 | 优先级 | 复杂度 |
|------|---------|--------|--------|
| 背包/物品系统 | 06, 08 | 高 | 中 |
| 商城购买流程 | 08, 12 | 高 | 中 |
| 任务系统 | 05, 12 | 高 | 高 |
| 成就系统 | 05 | 中 | 中 |
| 社交/好友系统 | 07, 12 | 中 | 高 |
| 聊天系统 | 07 | 中 | 中 |
| 组队系统 | 07 | 低 | 高 |
| WebSocket同步 | 07, 12 | 高 | 高 |
| 流式对话(SSE) | 09, 12 | 高 | 中 |
| 情感分析 | 09 | 中 | 高 |
| 语音识别/合成 | 09 | 低 | 高 |
| 记忆检索(Qdrant) | 09 | 中 | 高 |
| 危机干预系统 | 09 | 中 | 中 |
| 支付/充值 | 08 | 中 | 高 |
| 会员订阅 | 08 | 中 | 中 |
| 三钥匙挑战 | 05 | 低 | 高 |

---

## 2. 开发阶段规划

### Phase 2A: 完善核心后端 (2-3周)

#### 2A.1 流式对话 SSE 实现
```
目标: 实现真正的流式AI对话

任务清单:
□ app/api/v1/dialogue.py - 重写 /stream 端点
  - 使用 LLM的 stream_chat 方法
  - 正确构建SSE响应格式
  - 边生成边发送chunk

□ app/services/llm/qwen.py - 完善流式响应
  - 实现 stream_chat 异步生成器
  - 处理DashScope SSE格式

□ 前端测试 - EventSource 连接测试
```

#### 2A.2 背包与物品系统
```
目标: 完整的背包管理功能

任务清单:
□ app/api/v1/inventory.py - 新建API路由
  - GET /inventory - 获取背包物品
  - POST /inventory/use - 使用物品
  - DELETE /inventory/{slot} - 丢弃/分解
  - PUT /inventory/move - 移动物品

□ app/schemas/inventory.py - 完善Schema
  - InventoryItemResponse
  - UseItemRequest
  - InventoryResponse

□ 测试用例
```

#### 2A.3 商城系统
```
目标: 商品展示与购买

任务清单:
□ app/api/v1/shop.py - 新建商城API
  - GET /shop/items - 商品列表(分类筛选)
  - GET /shop/items/{item_id} - 商品详情
  - POST /shop/purchase - 购买商品

□ app/models/shop.py - 完善商品模型
  - ShopItem增加 daily_limit, total_limit
  - PurchaseRecord 购买记录

□ 初始商品数据种子
```

#### 2A.4 任务系统
```
目标: 主线/支线/每日任务

任务清单:
□ app/api/v1/quest.py - 任务API
  - GET /quests - 任务列表(按状态)
  - GET /quests/{quest_id} - 任务详情
  - POST /quests/{quest_id}/progress - 更新进度
  - POST /quests/{quest_id}/claim - 领取奖励

□ app/models/quest.py - 完善任务模型
  - Quest模型增加 objectives JSONB
  - QuestProgress增加 progress JSONB

□ 任务配置文件 (YAML/JSON)
  - 主线任务定义
  - 每日任务模板
```

---

### Phase 2B: 社交与实时通信 (2-3周)

#### 2B.1 WebSocket 基础设施
```
目标: 建立实时通信能力

任务清单:
□ app/websocket/__init__.py - WebSocket管理器
  - ConnectionManager类
  - 房间管理
  - 消息广播

□ app/api/v1/ws.py - WebSocket端点
  - WS /ws/game - 主连接
  - 认证验证
  - 心跳保活

□ 消息协议定义
  - ClientMessage / ServerMessage
  - 位置同步协议
  - 聊天消息协议
```

#### 2B.2 好友系统
```
目标: 完整好友功能

任务清单:
□ app/models/social.py - 社交模型
  - Friendship 好友关系
  - FriendRequest 好友申请
  - BlockedPlayer 屏蔽列表

□ app/api/v1/social.py - 社交API
  - GET /social/search - 搜索玩家
  - POST /social/friends/request - 发送申请
  - PUT /social/friends/request/{id} - 处理申请
  - GET /social/friends - 好友列表
  - DELETE /social/friends/{id} - 删除好友
  - POST /social/block - 屏蔽玩家
```

#### 2B.3 聊天系统
```
目标: 多频道文字聊天

任务清单:
□ app/models/chat.py - 聊天模型
  - ChatMessage 聊天消息
  - 世界/区域/私聊/队伍频道

□ WebSocket消息处理
  - 聊天消息路由
  - 敏感词过滤
  - 消息持久化
```

---

### Phase 2C: AI增强功能 (2周)

#### 2C.1 对话记忆增强
```
目标: 长期记忆与语义检索

任务清单:
□ Qdrant集成 (可选Redis替代)
  - 向量存储配置
  - 对话嵌入生成
  - 语义相似度搜索

□ app/services/memory/manager.py
  - ConversationMemory类
  - 短期记忆(Redis)
  - 长期记忆(PostgreSQL)
  - 记忆摘要生成

□ 玩家档案系统
  - PlayerProfile模型
  - 自动更新兴趣/话题
  - 情绪历史追踪
```

#### 2C.2 危机干预系统
```
目标: 心理安全保障

任务清单:
□ app/services/crisis/detector.py
  - 危机关键词检测
  - 情感强度阈值
  - 触发专用LLM提示词

□ app/models/crisis.py
  - CrisisEvent模型
  - 人工审核状态

□ 危机提示词库
  - 安全回复模板
  - 心理援助热线集成
```

#### 2C.3 情感分析 (基础版)
```
目标: 文本情感识别

任务清单:
□ app/services/emotion/analyzer.py
  - 关键词快速检测
  - 情感分类(joy/sadness/anger/fear/neutral)
  - 情感强度评估

□ 集成到对话流程
  - 情感影响NPC回复
  - 动态调整temperature
```

---

### Phase 3: 游戏内容 (3-4周)

#### 3.1 成就系统
```
□ app/api/v1/achievement.py
  - GET /achievements - 成就列表
  - POST /achievements/{id}/claim - 领取奖励

□ 成就配置文件
  - 探索类成就
  - 社交类成就
  - 对话类成就
```

#### 3.2 三钥匙挑战
```
□ 勇气之钥 - 镜中对话
  - 特殊NPC prompt
  - 诚实度评估

□ 释然之钥 - 记忆迷宫
  - 记忆碎片机制
  - 选择保留/放下

□ 希望之钥 - 未来建造
  - 建造目标评估
```

#### 3.3 更多NPC人设
```
□ 完善现有NPC prompt
  - aela.yaml (向导)
  - momo.yaml (商人)
  - chronos.yaml (任务)

□ 好感度等级内容
  - 不同等级解锁对话
  - 特殊互动
```

---

### Phase 4: 高级功能 (按需)

#### 4.1 支付系统
```
□ 微信支付集成
□ 支付宝集成
□ 订单管理
□ 会员订阅
```

#### 4.2 语音系统
```
□ 阿里云ASR集成
□ 阿里云TTS集成
□ 语音流处理
```

#### 4.3 多人同步
```
□ 位置同步优化
□ 客户端预测
□ 延迟补偿
```

---

## 3. 即刻执行任务 (Phase 2A优先)

### 3.1 流式对话SSE - 立即实施

**文件修改**: `app/api/v1/dialogue.py`

```python
# 需要重写 chat_stream 函数实现真正的流式响应
# 当前是模拟的逐字输出，需要调用真实LLM流式API
```

### 3.2 背包API - 立即实施

**新建文件**: `app/api/v1/inventory.py`

```python
# 基于现有 InventoryItem 模型实现CRUD API
```

### 3.3 商城API - 立即实施

**新建文件**: `app/api/v1/shop.py`

```python
# 基于现有 ShopItem 模型实现商品列表和购买功能
```

---

## 4. 技术栈确认

### 后端技术栈
- FastAPI + SQLAlchemy 2.0 (async)
- PostgreSQL / SQLite (开发)
- Redis (缓存/会话/实时)
- Qdrant (向量检索, 可选)
- 阿里云通义千问 (主LLM)
- Anthropic Claude (情感对话)

### 前端技术栈 (待开发)
- Godot 4.3 (3D游戏客户端)
- 或 Web前端 (React/Vue + Three.js)

---

## 5. 里程碑检查点

| 里程碑 | 目标 | 验收标准 |
|--------|------|----------|
| M2A.1 | 流式对话 | SSE实时输出AI回复 |
| M2A.2 | 背包系统 | 物品增删改查正常 |
| M2A.3 | 商城系统 | 可购买商品扣除货币 |
| M2A.4 | 任务系统 | 可接受/完成任务领奖 |
| M2B.1 | WebSocket | 客户端可建立WS连接 |
| M2B.2 | 好友系统 | 可添加/删除好友 |
| M2B.3 | 聊天系统 | 可发送/接收聊天消息 |
| M2C.1 | 记忆增强 | 语义检索相关对话 |
| M2C.2 | 危机干预 | 触发关键词切换安全模式 |

---

## 6. 风险与应对

| 风险 | 概率 | 影响 | 应对 |
|------|------|------|------|
| LLM成本超支 | 高 | 高 | 免费配额限制、缓存优化 |
| WebSocket性能 | 中 | 中 | 房间隔离、消息压缩 |
| 向量检索延迟 | 中 | 低 | Redis缓存热点记忆 |
| 敏感内容风险 | 中 | 高 | 关键词过滤、人工审核 |

---

## 7. 下一步行动

### 立即执行
1. 实现真正的SSE流式对话
2. 新建背包API (`/api/v1/inventory`)
3. 新建商城API (`/api/v1/shop`)

### 本周目标
完成 Phase 2A 的全部任务，使后端具备完整的核心游戏功能。

---

*文档更新: 2024-12-19*
