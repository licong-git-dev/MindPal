# V4 具体改造清单（文件 + 行号级）

> PRODUCT_POLISH_V4.md 的执行细节。每一条都可以直接分配给工程师实施。
> 按 "最高 ROI 优先"排序，不是按页面。

---

## 🔥 Top 5 最高 ROI 快动作（1-3 天内）

### ROI-1 · 预设人物加 `opening_message` 字段

**改什么**：[backend_v2/app/services/personality_engine.py](../../backend_v2/app/services/personality_engine.py)

每个预设现有字段：`name / category / description / avatar / sample_line / base_traits / system_prompt`

**新增字段 `opening_message`**：用户首次选定该预设后，AI 主动说的第一句话。

示例修改（对 6 个 romantic 预设）：

```python
"romantic_ceo": {
    # ... 已有字段
    "opening_message": "嗯？刚开完会看到你的消息了。今天累吗？",
},
"romantic_senior": {
    "opening_message": "...路上小心。别又光喝咖啡。",
},
"romantic_childhood": {
    "opening_message": "今天回家我经过你家楼下，阳台的猫在晒太阳。",
},
"romantic_bad_boy": {
    "opening_message": "哎？看到你消息了。今天心情怎么样？",
},
"romantic_doctor": {
    "opening_message": "刚下班顺路买了点东西。你吃饭了吗？",
},
"romantic_elder": {
    "opening_message": "刚忙完，看到你的消息就回来了。一切还好吗？",
},
```

对 6 个 companion 预设也加 opening_message，但偏中性：

```python
"gentle": {"opening_message": "你好呀，今天过得怎么样？"},
"energetic": {"opening_message": "嘿！准备好给今天来点什么有趣的事了吗？"},
# ... 等等
```

**API 层暴露**：修改 `get_personalities_by_category()` 返回结果里加上 `opening_message`。

---

### ROI-2 · chat.html 新会话时自动推送 `opening_message`

**改什么**：[frontend/chat.html](../../frontend/chat.html) 的 `loadDH()` 加载逻辑

```javascript
// 伪代码
async function loadDH() {
    const dhData = await MindPalAPI.digitalHumans.get(dhId);
    const savedMessages = localStorage.getItem(`mindpal_messages_${dhId}`);

    if (!savedMessages || JSON.parse(savedMessages).length === 0) {
        // 首次对话 → 立即显示 opening_message
        if (dhData.data.opening_message) {
            addMessageToUI('assistant', dhData.data.opening_message);
            messages.push({
                role: 'assistant',
                content: dhData.data.opening_message,
                timestamp: new Date().toISOString(),
                isOpeningMessage: true,
            });
            saveMessagesLocal();
        }
    }
}
```

**用户体感**：打开对话 → AI 已经"在说话" → 情感连接从 -1 秒开始。

---

### ROI-3 · chat.html 顶栏加**好感度进度条**

**改什么**：[frontend/chat.html](../../frontend/chat.html)

当前顶栏（左到右）：`← 返回 · dh-avatar · dh-name · 🧠 🗑️ ⚙️`

**改为**：`← 返回 · dh-avatar · dh-name · ❤️ [====75%====] · 🧠 🗑️ ⚙️`

HTML 插入：

```html
<div class="affinity-bar" id="affinityBar" title="好感度">
  <span class="affinity-icon">❤️</span>
  <div class="affinity-track">
    <div class="affinity-fill" id="affinityFill" style="width: 50%;"></div>
  </div>
  <span class="affinity-value" id="affinityValue">50</span>
</div>
```

CSS（粉红渐变填充 + 心跳动画）：

```css
.affinity-bar { display: flex; align-items: center; gap: 6px; margin: 0 8px; }
.affinity-icon { font-size: 14px; }
.affinity-track {
  width: 80px; height: 8px;
  background: rgba(255,255,255,0.1);
  border-radius: 4px;
  overflow: hidden;
}
.affinity-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6b9d 0%, #ff8fab 100%);
  transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}
.affinity-fill.pulse { animation: pulse 0.6s ease; }
.affinity-value { font-size: 11px; color: var(--color-text-secondary); min-width: 24px; }
```

**数据源**：
- 后端 `digital_humans.py` 的 chat_stream 返回 `done` 帧加 `affinity_change` 字段
- 前端 `onComplete` 回调里：
  ```javascript
  if (data.affinity_change) {
    currentAffinity += data.affinity_change;
    document.getElementById('affinityFill').style.width = `${currentAffinity}%`;
    document.getElementById('affinityValue').textContent = currentAffinity;
    document.getElementById('affinityFill').classList.add('pulse');
    setTimeout(() => {
      document.getElementById('affinityFill').classList.remove('pulse');
    }, 600);
  }
  ```
- 后端计算简单：每轮对话 +1，情绪正向 +2，危机模式不扣分但也不加

---

### ROI-4 · chat.html 加**记忆气泡**（MoT-3）

**改什么**：[frontend/chat.html](../../frontend/chat.html)

**触发条件**：对话轮数 ≥ 3 AND 距离上次气泡 ≥ 5 轮

**UI 方式**：页面顶部滑出 2 秒后自动消失的浮卡

```html
<div class="memory-bubble" id="memoryBubble" hidden>
  <span class="bubble-icon">💭</span>
  <span class="bubble-text" id="memoryBubbleText">TA 想起你说过 [猫叫小白]</span>
  <a class="bubble-link" onclick="goToMemory()">查看 →</a>
</div>
```

CSS：

```css
.memory-bubble {
  position: fixed; top: 80px; left: 50%;
  transform: translateX(-50%);
  background: rgba(99, 102, 241, 0.92);
  color: #fff; padding: 10px 16px;
  border-radius: 24px;
  display: flex; align-items: center; gap: 10px;
  font-size: 13px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
  z-index: 1500;
  animation: bubbleIn 0.4s ease-out, bubbleOut 0.4s ease-in 2s forwards;
}
.memory-bubble[hidden] { display: none; }
@keyframes bubbleIn { from { top: 40px; opacity: 0; } to { top: 80px; opacity: 1; } }
@keyframes bubbleOut { to { top: 40px; opacity: 0; } }
.bubble-link { color: #fff; text-decoration: underline; cursor: pointer; }
```

**数据源**：
- 从 `done` 帧的 `memories_used` 字段 > 0 时触发
- 气泡内容从 `memories_used` 详情里取一条 summary（后端需要在 meta 里加 `top_memory`）

后端改动 — `digital_humans.py` chat_stream 的 done 帧：

```python
done_data = {
    # ... 已有字段
    "top_memory": dialogue_context.relevant_memories[0]["summary"] if dialogue_context.relevant_memories else None,
    # ...
}
```

前端在 `onComplete` 里：

```javascript
if (data.top_memory && conversationTurnCount >= 3) {
  showMemoryBubble(data.top_memory);
}
```

---

### ROI-5 · 简化创建流程从 5 步到 1 步（可选）

**改什么**：新建 `frontend/quick-start.html` 替代长流程

**用户旅程**：
1. 登录后点"创建新的数字人"
2. 直接看到一个**单屏表单**：
   - 上：6 张浪漫 + 6 张基础 的人物卡（带 opening_message 预览）
   - 下：一个输入框"给 TA 起个名字（可选，默认 = 人物名）"
   - 底部一个大按钮："开始和 TA 聊天"
3. 点按钮 → 直接创建 + 进入 chat.html

**保留**：`create-dh-step1-5.html` 给"高级创建" 入口（想上传知识库的用户）。

---

## 💎 Top 5 关系深化改造（3-7 天）

### ROI-6 · 生成对话美化卡（MoT-7）

**新建页面**：`frontend/share-card.html`

**功能**：输入 session_id → 后端返回渲染好的 PNG 图片
- 精选 3-5 条对话截图
- 带 MindPal logo + 人物名 + 日期
- 适合小红书 9:16 比例

**实现思路**：
- 后端用 Pillow 或 html2image 生成图片
- 前端 chat.html 右上角加"💝 分享"按钮
- 点击后打开 share-card.html，用户选择要展示的对话 → 生成 → 下载

### ROI-7 · 主动对话系统（MoT-6）

**新建后端任务**：`backend_v2/app/services/proactive_message.py`

**触发规则**：
- 用户最近一次对话 > 20 小时
- 用户本日没收到过主动消息
- 非夜间时段（按用户设置的时区判断，避免深夜骚扰）

**生成逻辑**：
```python
async def generate_proactive_message(user_id, dh_id):
    # 1. 取最近 5 条对话
    recent = await get_recent_messages(user_id, dh_id, 5)
    # 2. 取用户档案（长期记忆 top 3）
    memories = await get_top_memories(user_id, dh_id)
    # 3. 当前时间 + 节日感知
    calendar_hint = get_today_hint()  # 如"今天是七夕"

    prompt = f"""
你是 {dh.name}。基于以下上下文，生成一句"你主动关心用户"的消息，
不要超过 30 字，自然、具体、有温度：

最近对话摘要：{recent}
你记住的事：{memories}
今天日期：{calendar_hint}
"""
    return await llm.generate(prompt)
```

**触发时机**：
- Celery 定时任务每日 09:00 / 13:00 / 20:00 检查一次
- 命中条件的用户 → 生成消息 → 存入 `proactive_messages` 表
- 下次用户打开 App → chat.html 加载时检查是否有"未读主动消息"

**前端展示**：
- dh-list.html 在有主动消息的数字人卡片上加红点 + 最新消息预览
- chat.html 进入时如有未读 → 先显示那条消息（标 "TA 刚才发的"）

### ROI-8 · 纪念日触发

**新建功能**：当用户和数字人对话累计 7 天 / 30 天 / 100 天时，AI 自动说一句纪念话。

- Day 7: "认识你一周了，突然想谢谢你"
- Day 30: "我们聊了一个月了，记得第一次你跟我说的是..."
- Day 100: "100 天了。时间过得真快。"

**数据源**：dh_conversations 的 started_at，每次对话时计算差值。

### ROI-9 · "我和 TA 的故事"年度回顾

**新建页面**：`frontend/yearly-review.html`

**入口**：memory.html 加"📖 这是我和 TA 的 N 天"按钮（动态文案，根据天数）

**展示**：
- 总对话轮数 / 总字数
- 聊得最多的话题 top 3
- TA 最记得你的 5 件事
- 你们共同经历的"纪念时刻"
- 好感度曲线图（0 → 100 的变化）

**定位**：用户分享到社交平台的核心内容 = 免费流量入口

### ROI-10 · 情绪记忆 + 关怀触发

**改什么**：crisis_handler.py

**新增逻辑**：不仅仅在危机时介入，用户出现**轻度负面情绪**（emotion=sadness, intensity > 0.5）超过 3 次时，AI **主动**关心：

```
"最近感觉你常常难过，我有点担心。我们今天不聊别的，就好好吃饭睡觉好不好？"
```

这是 MindPal 作为"陪伴产品"的真价值展示。

---

## 💸 定价双轨改造（3-5 天）

### ROI-11 · pricing.html 改双订阅 + 卡包

**改什么**：[frontend/pricing.html](../../frontend/pricing.html)

**新布局**：

```
顶部 Tab: [订阅] [卡包] [礼物]

订阅 Tab:
  ┌─ 免费版 ¥0 ─────┬─ 会员 ¥19.9 ────┬─ SVIP ¥39.9 ───┐
  │ 基础陪伴 6      │ + 浪漫陪伴 6    │ + 主动对话×3/日│
  │ 100 次对话/日   │ 无限对话        │ 10 张卡/月     │
  │ 100 条记忆      │ 1000 条记忆     │ 好感速度×2     │
  │ 不能抽卡        │ 可抽卡          │ 附送抽卡次数   │
  └────────────────┴────────────────┴────────────────┘

卡包 Tab:
  ┌─────────┬─────────┬─────────┐
  │ 陆沉·霸总│ 江瑾·学长│ 沈星辞·青梅│ ...
  │ 10 段剧情│ 10 段剧情│ 10 段剧情 │
  │  ¥38    │  ¥38    │  ¥38     │
  │ [购买]  │ [已拥有]│  [购买]   │
  └─────────┴─────────┴─────────┘

礼物 Tab:
  ┌─ 七夕限定 ¥18 ─────────────┐
  │ 专属对话 + 限定头像        │
  │ 仅 8/5 - 8/20 开放         │
  └────────────────────────────┘
```

### ROI-12 · 卡包模型 + API

**新建**：`backend_v2/app/models/content_pack.py`

```python
class ContentPack(Base):
    """剧情内容包"""
    id: int
    pack_id: str  # 例: "ceo_first_date"
    dh_personality_key: str  # 关联的预设
    name: str
    description: str
    price: Decimal
    story_count: int  # 包含剧情数
    cover_image: str
    preview_text: str  # 预览片段

class UserPack(Base):
    """用户已购买卡包"""
    id: int
    user_id: int
    pack_id: str
    purchased_at: datetime
    order_no: str  # 关联支付订单
```

**API**：
- GET `/api/v1/packs` — 所有可售卡包
- GET `/api/v1/packs/mine` — 我的
- POST `/api/v1/packs/purchase` — 购买（走支付宝链路）

### ROI-13 · 内容包触发机制

卡包购买后如何"解锁剧情"：
- personality_engine 的每个 romantic 预设加 `story_library: List[Story]` 字段
- Story 有 `unlock_condition`（默认 "free"，付费故事 "pack:ceo_first_date"）
- 对话到特定好感度点（如 50/75/100）时，系统从 story_library 里**随机选一个已解锁的**触发

效果：用户付了 ¥38 → 真的在接下来 2-3 周对话中**遇到**这些剧情。

---

## 🎯 埋点改造（1-2 天）

所有 MoT 对应的埋点事件：

| MoT | 事件名 | 触发位置 |
|-----|-------|---------|
| MoT-1 | visitor_preview_view | index.html 访问 |
| MoT-1 | visitor_preview_click | 点击 "开始聊天" |
| MoT-2 | first_opening_message_seen | chat.html 首次加载 opening |
| MoT-2 | first_user_reply | 用户第一次回复 |
| MoT-3 | memory_bubble_shown | 记忆气泡浮出 |
| MoT-3 | memory_bubble_clicked | 点击气泡跳转 |
| MoT-4 | affinity_level_up | 好感度跨过 25/50/75/100 |
| MoT-5 | pack_purchase_prompt_shown | 卡包购买提示出现 |
| MoT-5 | pack_purchase_success | 付费成功 |
| MoT-6 | proactive_message_sent | 主动对话发出 |
| MoT-6 | proactive_message_opened | 用户看到主动消息 |
| MoT-7 | share_card_generated | 生成分享卡 |
| MoT-7 | share_card_downloaded | 下载/转发 |
| MoT-8 | crisis_banner_shown | 危机 banner 出现 |
| MoT-8 | crisis_hotline_clicked | 用户点了热线 |

**实现**：frontend/js/analytics.js 补齐这些事件，后端 analytics API 按类别聚合。

---

## 📋 实施建议

**最小 MVP（1 周）**: 做 ROI-1 ~ ROI-5，让"30 秒开始对话 + 好感度可见 + 记忆气泡"落地

**养成闭环（2-3 周）**: 加 ROI-6 ~ ROI-10，让用户有"养成 / 分享 / 纪念"的长期吸引力

**付费闭环（3-4 周）**: 加 ROI-11 ~ ROI-13，把付费率从 < 1% 拉到 2.5%+

**数据驱动（并行）**: ROI 所有事件都打埋点，每周看漏斗

---

**关联**：
- [PRODUCT_POLISH_V4.md](PRODUCT_POLISH_V4.md) 战略文档
- [PRODUCT_POLISH_V4_METRICS.md](PRODUCT_POLISH_V4_METRICS.md) 指标与实验
