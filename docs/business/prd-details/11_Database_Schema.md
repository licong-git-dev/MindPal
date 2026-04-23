# 11. 数据库设计

> MindPal PRD - Database Schema Design
> 版本: 1.0 | 更新: 2024-01

---

## 1. 数据库架构

```
┌─────────────────────────────────────────────────────────────────┐
│                       数据存储架构                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  PostgreSQL  │  │    Redis     │  │   Qdrant     │          │
│  │  (主数据库)   │  │  (缓存/会话)  │  │  (向量数据库) │          │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤          │
│  │ - 用户数据    │  │ - 会话状态   │  │ - 对话向量   │          │
│  │ - 角色数据    │  │ - 对话缓存   │  │ - 记忆检索   │          │
│  │ - 游戏进度    │  │ - 在线状态   │  │ - 情感聚类   │          │
│  │ - 交易记录    │  │ - 排行榜     │  │              │          │
│  │ - 对话历史    │  │ - 房间数据   │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. PostgreSQL 核心表设计

### 2.1 用户系统

```sql
-- 用户账号表
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(32) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),

    -- 账号状态
    status VARCHAR(20) DEFAULT 'active',  -- active, banned, deleted
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,

    -- OAuth绑定
    wechat_openid VARCHAR(64),
    qq_openid VARCHAR(64),
    google_id VARCHAR(64),

    -- 会员信息
    membership_type VARCHAR(20) DEFAULT 'free',  -- free, monthly, yearly, svip
    membership_expires_at TIMESTAMP,

    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login_at TIMESTAMP,

    CONSTRAINT valid_status CHECK (status IN ('active', 'banned', 'deleted')),
    CONSTRAINT valid_membership CHECK (membership_type IN ('free', 'monthly', 'yearly', 'svip'))
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_wechat ON users(wechat_openid) WHERE wechat_openid IS NOT NULL;


-- 玩家角色表 (游戏内角色)
CREATE TABLE player_characters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,

    -- 基本信息
    nickname VARCHAR(32) NOT NULL,
    avatar_config JSONB NOT NULL DEFAULT '{}',  -- 捏脸数据

    -- 属性
    level INTEGER DEFAULT 1,
    experience BIGINT DEFAULT 0,

    -- 货币
    gold BIGINT DEFAULT 1000,
    diamonds INTEGER DEFAULT 0,

    -- 位置
    current_zone VARCHAR(50) DEFAULT 'central_plaza',
    position_x FLOAT DEFAULT 0,
    position_y FLOAT DEFAULT 0,
    position_z FLOAT DEFAULT 0,
    rotation_y FLOAT DEFAULT 0,

    -- 游戏进度
    main_quest_progress JSONB DEFAULT '{"chapter": 1, "quest": 1}',
    keys_collected INTEGER[] DEFAULT '{}',  -- [1,2,3] 表示已获得的钥匙
    achievements INTEGER[] DEFAULT '{}',

    -- 统计
    total_playtime INTEGER DEFAULT 0,  -- 秒
    dialogues_count INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id)  -- 一个账号一个角色
);

CREATE INDEX idx_player_user ON player_characters(user_id);
CREATE INDEX idx_player_zone ON player_characters(current_zone);


-- 玩家背包表
CREATE TABLE player_inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES player_characters(id) ON DELETE CASCADE,

    item_id VARCHAR(50) NOT NULL,  -- 物品模板ID
    quantity INTEGER DEFAULT 1,
    slot_index INTEGER,  -- 背包格子位置

    -- 物品属性 (部分物品有特殊属性)
    properties JSONB DEFAULT '{}',

    acquired_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(player_id, slot_index)
);

CREATE INDEX idx_inventory_player ON player_inventory(player_id);


-- 玩家装备表
CREATE TABLE player_equipment (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES player_characters(id) ON DELETE CASCADE,

    slot VARCHAR(20) NOT NULL,  -- head, body, accessory, etc.
    item_id VARCHAR(50) NOT NULL,

    equipped_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(player_id, slot)
);
```

### 2.2 社交系统

```sql
-- 好友关系表
CREATE TABLE friendships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES player_characters(id) ON DELETE CASCADE,
    friend_id UUID REFERENCES player_characters(id) ON DELETE CASCADE,

    status VARCHAR(20) DEFAULT 'pending',  -- pending, accepted, blocked

    created_at TIMESTAMP DEFAULT NOW(),
    accepted_at TIMESTAMP,

    UNIQUE(player_id, friend_id),
    CONSTRAINT no_self_friend CHECK (player_id != friend_id),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'accepted', 'blocked'))
);

CREATE INDEX idx_friendship_player ON friendships(player_id);
CREATE INDEX idx_friendship_friend ON friendships(friend_id);


-- 私聊消息表
CREATE TABLE private_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_id UUID REFERENCES player_characters(id) ON DELETE SET NULL,
    receiver_id UUID REFERENCES player_characters(id) ON DELETE CASCADE,

    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_pm_receiver ON private_messages(receiver_id, created_at DESC);
CREATE INDEX idx_pm_conversation ON private_messages(
    LEAST(sender_id, receiver_id),
    GREATEST(sender_id, receiver_id),
    created_at DESC
);


-- 队伍表
CREATE TABLE parties (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    leader_id UUID REFERENCES player_characters(id) ON DELETE CASCADE,

    name VARCHAR(32),
    max_members INTEGER DEFAULT 4,
    is_public BOOLEAN DEFAULT FALSE,

    current_zone VARCHAR(50),

    created_at TIMESTAMP DEFAULT NOW(),
    disbanded_at TIMESTAMP
);

CREATE INDEX idx_party_leader ON parties(leader_id);


-- 队伍成员表
CREATE TABLE party_members (
    party_id UUID REFERENCES parties(id) ON DELETE CASCADE,
    player_id UUID REFERENCES player_characters(id) ON DELETE CASCADE,

    role VARCHAR(20) DEFAULT 'member',  -- leader, member
    joined_at TIMESTAMP DEFAULT NOW(),

    PRIMARY KEY (party_id, player_id)
);
```

### 2.3 对话系统

```sql
-- NPC对话记录表
CREATE TABLE dialogue_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES player_characters(id) ON DELETE CASCADE,
    npc_id VARCHAR(50) NOT NULL,  -- aela, momo, chronos, bei, sesame

    -- 对话内容
    user_message TEXT NOT NULL,
    npc_response TEXT NOT NULL,

    -- 情感数据
    user_emotion VARCHAR(20),
    emotion_intensity FLOAT,

    -- AI服务信息
    ai_service VARCHAR(50),  -- qwen.plus, claude.sonnet
    input_tokens INTEGER,
    output_tokens INTEGER,
    response_time_ms INTEGER,

    -- 会话追踪
    session_id UUID,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_dialogue_player ON dialogue_logs(player_id, created_at DESC);
CREATE INDEX idx_dialogue_npc ON dialogue_logs(player_id, npc_id, created_at DESC);
CREATE INDEX idx_dialogue_session ON dialogue_logs(session_id);

-- 按月分区
CREATE TABLE dialogue_logs_2024_01 PARTITION OF dialogue_logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');


-- 玩家心理档案表
CREATE TABLE player_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES player_characters(id) ON DELETE CASCADE UNIQUE,

    -- 偏好设置
    preferred_nickname VARCHAR(32),
    communication_style VARCHAR(20) DEFAULT 'friendly',  -- formal, casual, friendly

    -- 兴趣标签 (AI学习得出)
    interests TEXT[] DEFAULT '{}',
    recent_topics TEXT[] DEFAULT '{}',

    -- 情绪历史摘要
    emotion_summary JSONB DEFAULT '{}',
    -- 示例: {"avg_mood": 0.6, "common_emotions": ["joy", "neutral"], "crisis_count": 0}

    -- 敏感话题标记 (避免触及)
    sensitive_topics TEXT[] DEFAULT '{}',

    -- NPC好感度
    npc_affinity JSONB DEFAULT '{"aela": 50, "momo": 50, "chronos": 50, "bei": 50, "sesame": 50}',

    updated_at TIMESTAMP DEFAULT NOW()
);


-- 危机事件记录表 (需要人工审核)
CREATE TABLE crisis_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES player_characters(id) ON DELETE SET NULL,

    dialogue_id UUID REFERENCES dialogue_logs(id),

    trigger_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,

    severity VARCHAR(20) DEFAULT 'medium',  -- low, medium, high, critical
    status VARCHAR(20) DEFAULT 'pending',   -- pending, reviewed, escalated, resolved

    reviewer_notes TEXT,
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_crisis_status ON crisis_events(status, created_at DESC);
```

### 2.4 经济系统

```sql
-- 交易记录表
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES player_characters(id) ON DELETE CASCADE,

    -- 交易类型
    type VARCHAR(30) NOT NULL,  -- purchase, reward, gift, refund, etc.

    -- 货币变动
    gold_change BIGINT DEFAULT 0,
    diamonds_change INTEGER DEFAULT 0,

    -- 变动后余额
    gold_balance BIGINT,
    diamonds_balance INTEGER,

    -- 关联信息
    item_id VARCHAR(50),
    item_quantity INTEGER,
    reference_id VARCHAR(100),  -- 订单号、任务ID等

    description TEXT,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_transaction_player ON transactions(player_id, created_at DESC);
CREATE INDEX idx_transaction_type ON transactions(type, created_at DESC);


-- 充值订单表
CREATE TABLE payment_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES player_characters(id) ON DELETE CASCADE,

    -- 订单信息
    order_no VARCHAR(64) UNIQUE NOT NULL,
    product_id VARCHAR(50) NOT NULL,  -- 商品ID
    product_name VARCHAR(100),

    -- 金额
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'CNY',
    diamonds_amount INTEGER NOT NULL,  -- 充值获得钻石
    bonus_diamonds INTEGER DEFAULT 0,  -- 赠送钻石

    -- 支付信息
    payment_method VARCHAR(30),  -- wechat, alipay, apple
    payment_status VARCHAR(20) DEFAULT 'pending',
    paid_at TIMESTAMP,

    -- 第三方信息
    third_party_order_no VARCHAR(100),

    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP
);

CREATE INDEX idx_order_player ON payment_orders(player_id, created_at DESC);
CREATE INDEX idx_order_status ON payment_orders(payment_status);


-- 商城商品表
CREATE TABLE shop_items (
    id VARCHAR(50) PRIMARY KEY,

    category VARCHAR(30) NOT NULL,  -- consumable, decoration, functional, bundle
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- 价格
    gold_price INTEGER,
    diamond_price INTEGER,

    -- 限购
    daily_limit INTEGER,
    total_limit INTEGER,

    -- 上架状态
    is_active BOOLEAN DEFAULT TRUE,
    start_time TIMESTAMP,
    end_time TIMESTAMP,

    -- 物品数据
    item_data JSONB NOT NULL,
    -- 示例: {"type": "potion", "effect": "heal", "value": 50}

    sort_order INTEGER DEFAULT 0,

    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_shop_category ON shop_items(category, is_active);
```

### 2.5 任务与成就

```sql
-- 任务进度表
CREATE TABLE quest_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES player_characters(id) ON DELETE CASCADE,
    quest_id VARCHAR(50) NOT NULL,

    status VARCHAR(20) DEFAULT 'in_progress',  -- in_progress, completed, failed

    -- 进度数据
    progress JSONB DEFAULT '{}',
    -- 示例: {"objectives": [{"id": "talk_npc", "current": 1, "target": 3}]}

    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    UNIQUE(player_id, quest_id)
);

CREATE INDEX idx_quest_player ON quest_progress(player_id);


-- 成就解锁表
CREATE TABLE achievement_unlocks (
    player_id UUID REFERENCES player_characters(id) ON DELETE CASCADE,
    achievement_id VARCHAR(50) NOT NULL,

    unlocked_at TIMESTAMP DEFAULT NOW(),

    PRIMARY KEY (player_id, achievement_id)
);


-- 三钥匙挑战记录
CREATE TABLE key_challenge_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES player_characters(id) ON DELETE CASCADE,

    key_type INTEGER NOT NULL,  -- 1=勇气, 2=释然, 3=希望

    -- 挑战数据
    challenge_data JSONB NOT NULL,
    -- 镜中对话: {"questions_answered": 5, "honest_rate": 0.8}
    -- 记忆迷宫: {"memories_processed": 5, "release_count": 3}
    -- 未来建造: {"objects_built": 10, "completion_rate": 0.9}

    result VARCHAR(20),  -- success, partial, failed
    key_obtained BOOLEAN DEFAULT FALSE,

    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

CREATE INDEX idx_key_challenge_player ON key_challenge_records(player_id);
```

---

## 3. Redis 数据结构

### 3.1 会话与在线状态

```redis
# 用户会话
SET session:{session_id} {user_id, player_id, login_time, ip}
EXPIRE session:{session_id} 86400  # 24小时

# 在线状态
HSET online:{player_id} status "online" zone "central_plaza" last_active {timestamp}
EXPIRE online:{player_id} 300  # 5分钟未活动过期

# 在线玩家列表 (按区域)
SADD zone_players:{zone_id} {player_id}
SREM zone_players:{zone_id} {player_id}  # 离开时移除
```

### 3.2 对话缓存

```redis
# 最近对话缓存
LPUSH dialogue:{player_id}:{npc_id}:recent {dialogue_json}
LTRIM dialogue:{player_id}:{npc_id}:recent 0 19  # 保留20条
EXPIRE dialogue:{player_id}:{npc_id}:recent 3600  # 1小时

# 对话会话ID
SET dialogue_session:{player_id}:{npc_id} {session_uuid}
EXPIRE dialogue_session:{player_id}:{npc_id} 1800  # 30分钟

# 玩家档案缓存
SET player_profile:{player_id} {profile_json}
EXPIRE player_profile:{player_id} 1800
```

### 3.3 实时通信

```redis
# 房间玩家列表
HSET room:{room_id}:players {player_id} {player_data_json}

# 玩家位置 (高频更新)
HSET room:{room_id}:positions {player_id} {x},{y},{z},{ry}

# 聊天消息队列
LPUSH chat:{channel}:messages {message_json}
LTRIM chat:{channel}:messages 0 99  # 保留100条

# 发布订阅 - 实时通知
PUBLISH room:{room_id}:events {event_json}
PUBLISH player:{player_id}:notifications {notification_json}
```

### 3.4 排行榜

```redis
# 等级排行榜
ZADD leaderboard:level {score} {player_id}

# 财富排行榜
ZADD leaderboard:wealth {gold + diamonds*100} {player_id}

# 获取排名
ZREVRANK leaderboard:level {player_id}
ZREVRANGE leaderboard:level 0 99 WITHSCORES
```

### 3.5 限流与配额

```redis
# API限流
INCR ratelimit:{player_id}:{api_name}:{minute}
EXPIRE ratelimit:{player_id}:{api_name}:{minute} 60

# AI对话配额
HINCRBY ai_quota:{player_id}:{date} count 1
HINCRBYFLOAT ai_quota:{player_id}:{date} cost 0.01
EXPIRE ai_quota:{player_id}:{date} 172800  # 2天
```

---

## 4. Qdrant 向量存储

### 4.1 Collection 设计

```python
# 对话记忆向量集合
collection_config = {
    "name": "dialogue_memory",
    "vectors": {
        "size": 1536,  # text-embedding-ada-002
        "distance": "Cosine"
    }
}

# 点数据结构
point = {
    "id": "uuid",
    "vector": [0.1, 0.2, ...],  # 1536维向量
    "payload": {
        "player_id": "uuid",
        "npc_id": "bei",
        "summary": "关于工作压力的倾诉",
        "emotion": "sadness",
        "timestamp": "2024-01-15T10:30:00Z",
        "importance": 0.8  # 重要程度
    }
}
```

### 4.2 检索示例

```python
# 语义搜索相关记忆
results = qdrant.search(
    collection_name="dialogue_memory",
    query_vector=query_embedding,
    query_filter={
        "must": [
            {"key": "player_id", "match": {"value": player_id}},
            {"key": "importance", "range": {"gte": 0.5}}
        ]
    },
    limit=5,
    score_threshold=0.7
)
```

---

## 5. 数据迁移与备份

### 5.1 备份策略

| 数据类型 | 备份频率 | 保留时长 | 方式 |
|----------|----------|----------|------|
| PostgreSQL全量 | 每日 | 30天 | pg_dump |
| PostgreSQL增量 | 每小时 | 7天 | WAL归档 |
| Redis RDB | 每6小时 | 7天 | BGSAVE |
| Qdrant快照 | 每日 | 14天 | Snapshot API |

### 5.2 数据保留政策

```sql
-- 删除超过90天的对话日志详情 (保留统计)
DELETE FROM dialogue_logs
WHERE created_at < NOW() - INTERVAL '90 days';

-- 删除超过30天的临时数据
DELETE FROM private_messages
WHERE created_at < NOW() - INTERVAL '30 days' AND is_read = TRUE;
```

---

## 6. 性能优化

### 6.1 索引策略

```sql
-- 复合索引优化查询
CREATE INDEX idx_dialogue_query ON dialogue_logs(player_id, npc_id, created_at DESC);

-- 部分索引减少存储
CREATE INDEX idx_active_players ON player_characters(current_zone)
WHERE updated_at > NOW() - INTERVAL '1 hour';

-- 表达式索引
CREATE INDEX idx_player_level_tier ON player_characters((level / 10));
```

### 6.2 分区策略

```sql
-- 对话日志按月分区
CREATE TABLE dialogue_logs (
    ...
) PARTITION BY RANGE (created_at);

-- 自动创建分区
CREATE OR REPLACE FUNCTION create_monthly_partition()
RETURNS void AS $$
DECLARE
    partition_date DATE;
    partition_name TEXT;
BEGIN
    partition_date := DATE_TRUNC('month', NOW() + INTERVAL '1 month');
    partition_name := 'dialogue_logs_' || TO_CHAR(partition_date, 'YYYY_MM');

    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I PARTITION OF dialogue_logs
         FOR VALUES FROM (%L) TO (%L)',
        partition_name,
        partition_date,
        partition_date + INTERVAL '1 month'
    );
END;
$$ LANGUAGE plpgsql;
```

---

**下一篇 → 12_API_Design.md（API接口设计）**
