# MindPal 深度审计与修改方案 V3-Audit

> **审计日期**：2026-04-23
> **方法**：市场研究 + 监管合规研究 + 代码逐行走查 + 5 个用户 persona 模拟
> **与 V3 战略的关系**：V3 提出了战略，本文档是战略落地前的**真实诊断**
> **核心结论**：**代码库的能力足够，问题是链路没接通**。另外一个重大发现要求调整 V3 的方向推荐。

---

## 摘要（给忙人看）

1. **重大战略调整**：市场研究发现**筑梦岛乙女向 AI 男友**是中国唯一被验证的付费模型（500 万用户 + 千万美元融资，VIP ¥16/月、SVIP ¥36/月）。V3 原推荐的 "D 心理健康 + E ToB" 需要并入"**F. 乙女向情感陪伴**"作为**首选方向**。
2. **技术真相**：代码库技术库存**充足**（crisis detector 108 关键词、memory 向量检索、Alipay RSA2 签名全都是真的），但**关键链路断裂**——前端用的 chat 端点绕开了所有护城河功能。
3. **P0 阻塞 Bug**：前后端 **SSE 协议不匹配**，用户看不到流式对话；emotion 显示是**前端硬编码**；支付走的是 **mock 链路**，没有接通真 Alipay。
4. **架构分裂**：`backend_v2` 里有大量**游戏化模型**（player/quest/inventory/shop/party/achievement）与"AI 陪伴"产品定位**严重冲突**，这是过去某次方向摇摆留下的重债。

---

## 一、战略方向的重审（基于市场数据）

### V3 原推荐 vs 新证据

V3 推荐押宝 **D（心理轻度支持）+ E（ToB 员工福利）**。

**市场研究发现的更好方向**：

#### 🏆 新首选方向：**F. 乙女向深度情感陪伴（中国版筑梦岛升级版）**

**证据**（来源：新浪财经 2025-01-10 + 月狐数据 + 36氪）：
- 筑梦岛 2025 年 1 月融资 **超 1000 万美元**
- 注册用户近 **500 万**，**80% 为年轻女性**
- 日均输入 **4000 字、对话 120 轮**（超高黏性）
- VIP ¥16/月 / ¥42/季 · SVIP ¥36/月 / ¥94/季
- 女性用户是 AI 陪伴最大需求方；男性付费意愿更强（订阅+买断），**女性则通过卡池/抽卡/剧情解锁变现**

**为什么比 D/E 更优**：
| 维度 | D. 心理健康 | E. ToB 员工福利 | **F. 乙女向陪伴** |
|------|------------|----------------|------------------|
| 市场验证 | 61% 用户感兴趣但付费率无数据 | 销售周期长、合同金额大 | **500 万用户 + 千万美元融资** |
| 获客难度 | 需要专业背书 | 需要销售团队 | **小红书+抖音情感种草，已有成功路径** |
| 合规风险 | 心理诊疗红线（等同医疗器械） | 数据合规 | **内容分级即可** |
| 产品差异化点 | 不会超过持牌机构 | 标准化即可 | **人设深度+抽卡+剧情**都可做 |
| 验证周期 | 6 个月起 | 6-12 个月 | **2-3 个月可见首批付费** |

**为什么重要**：中国已经有人把 AI 陪伴赚到钱了，所以不要问"能不能赚"而是问"怎么做得更好"。

#### 退路方向（如果 F 做不动）：

- **D 保留但定位调整**：从"心理健康"改为"情绪陪伴 + 轻度疏导"（避免医疗器械红线）
- **E 作为 B 端补充**：在 F 跑通后，把乙女向的对话引擎白牌给 HR/EAP 平台
- **绝不做**：老年陪伴（技术适配+监管双重高门槛）、儿童陪伴（未成年保护红线）

### Replika 2023 事件的启示

2023 年意大利数据保护局威胁罚款 2150 万美元，Replika **一刀切关闭亲密对话功能**，大批用户流失到竞品。

**对 MindPal 的教训**：
1. **不要一刀切合规**，做**功能分级**（免费/付费/成人认证）
2. **不要事后阉割**，**合规要内嵌到产品一开始的设计**
3. **警惕监管突袭**，2025 年 6 月已有 AI 陪伴 App 头部被约谈（参考新浪财经 2025-06-22）

---

## 二、代码真相：技术库存 vs 集成现状

### 2.1 能力盘点（代码库中存在的）

| 模块 | 代码位置 | 实际能力 | 是否接入用户链路 |
|------|---------|---------|----------------|
| LLM 调用 | [backend_v2/services/llm/](../../backend_v2/app/services/llm/) | ✅ 通义+Claude双 provider + router | ✅ 已接入 |
| 危机检测 | [crisis/detector.py](../../backend_v2/app/services/crisis/detector.py) | ✅ 108 关键词 + 7 正则 + 5 级危机分类 + 真实热线 + 危机干预 system prompt | ❌ **仅接入 dialogue.py（游戏NPC路），用户对话走 digital_humans.py 完全绕开** |
| 情感分析 | [emotion/analyzer.py](../../backend_v2/app/services/emotion/analyzer.py) | ✅ 310 行情感分析器 | ❌ **未接入用户对话** |
| 长期记忆 | [memory/manager.py](../../backend_v2/app/services/memory/manager.py) + [vector_store.py](../../backend_v2/app/services/memory/vector_store.py) | ✅ InMemoryVectorStore（JSON持久化+余弦相似度）+ ChromaVectorStore + Retriever + 情感召回 + 玩家画像 | ❌ **用户对话仅用 session 内最近 20 条 message，跨会话记忆完全没接** |
| 语音 ASR | [voice/asr.py](../../backend_v2/app/services/voice/asr.py) | ✅ 267 行，能力存在 | ❌ 前端无对应 UI |
| 语音 TTS | [voice/tts.py](../../backend_v2/app/services/voice/tts.py) | ✅ 251 行 | ❌ 前端无对应 UI |
| 支付宝 | [payment/alipay.py](../../backend_v2/app/services/payment/alipay.py) | ✅ RSA2 签名+验签（PKCS1v15+SHA256）+ 沙箱/生产切换 | ❌ **payment API 暴露的是 `/mock/pay/{order_no}` 测试链路** |
| 订阅系统 | backend_v2/models/payment.py | ✅ 数据模型完整 | ⚠️ 缺配额拦截中间件 |
| 埋点 | backend_v2/api/v1/analytics.py + frontend/js/analytics.js | ✅ 埋点 API + 前端 SDK | ⚠️ 缺数据面板 |

### 2.2 真正该用的 Pipeline 在哪里

**残缺版** — [digital_humans.py:332-444](../../backend_v2/app/api/v1/digital_humans.py#L332-L444)（前端实际调用）：

```
user msg → 取最近20条DHMessage → 拼prompt → 调 llm.chat() → 返回
（没有：配额检查 / 危机检测 / 情感分析 / 长期记忆）
```

**完整版** — [dialogue.py:64-230](../../backend_v2/app/api/v1/dialogue.py#L64-L230)（仅游戏 NPC）：

```
user msg
 ├→ cost_tracker.check_quota() [配额]
 ├→ enhanced_processor 处理（包含 emotion + crisis）
 ├→ is_crisis_mode → temperature=0.5 + 危机 system prompt
 ├→ llm_router.get_service_for_npc(npc_id) [按 NPC 路由 LLM]
 ├→ llm.chat()
 ├→ enhanced_processor.store_conversation_memory() [存记忆]
 └→ 返回 {response, emotion, crisis_detected, crisis_resources, ...}
```

**整个问题是**：`dialogue.py` 需要 `npc_id` 参数 + `Player` 模型，而用户创建的数字人是 `DigitalHuman` 模型（两套不兼容的数据流）。

### 2.3 P0 阻塞 Bug：SSE 协议不匹配

前端 [api.js:237-257](../../frontend/js/api.js#L237-L257) 期望：
```js
if (data.type === 'chunk' && data.content) { ... }
else if (data.type === 'done') { ... }
else if (data.type === 'error') { ... }
```

后端 [digital_humans.py:522-539](../../backend_v2/app/api/v1/digital_humans.py#L522-L539) 发送：
```python
yield f"event: start\ndata: {json.dumps({'session_id': ..., 'dh_id': ...})}\n\n"
yield f"event: delta\ndata: {json.dumps({'content': chunk})}\n\n"
yield f"event: done\ndata: {json.dumps({'full_response': ...})}\n\n"
```

**结果**：每一个 `data.type` 字段都是 `undefined`，所有分支都走不进去 → **用户看不到流式消息**。

（除非浏览器 EventSource 能解析 `event:` 字段并重组 —— 但代码用的是 `fetch + reader`，手动解析 `data:` 行，没处理 `event:` 前缀）

### 2.4 其他前端硬编码/断点

- [chat.html:351](../../frontend/chat.html#L351) `emotion-icon` 显示 `😊` 是**硬编码**，后端从不返回 emotion 字段
- 前端数字人列表"上次对话"时间可能是假数据（后端统计字段名与前端期望不一致，需要核对）
- `subscription.html` 的升级按钮点击后去哪？从代码看跳 pricing.html 但 pricing.html 的"立即购买"最终走 mock

---

## 三、5 个 persona 用户旅程模拟 + 断点

### Persona 1：**25 岁一线城市独居女性 @林小桐**（乙女向目标用户）

**动机**：想找一个可以倾诉的"AI 男友"，正在对比筑梦岛和 MindPal

**旅程**：
1. ✅ 首页→创建账户 → 顺利登录
2. 🟡 创建数字人 5 步流程 → **界面没有"乙女向男友"人格模板**（只有温柔/活泼/知性等 6 种通用性格）
3. ❌ **聊了 3 条消息但看不到 AI 回复**（SSE 协议 Bug）→ 认为产品坏了 → 关掉
4. 假设修掉 SSE → 聊了 1 周 → **AI 不记得她养猫叫小白**（记忆链路没接）→ 觉得"AI 没有筑梦岛懂我"→ 流失

**筑梦岛怎么做**：卡池抽卡式人设解锁 + 每天主动早安/晚安 + 关键纪念日提醒 + 长对话记忆 + 剧情触发。

**需要改的**：
- 加"乙女向男友"为独立人格大类，下面 4-6 个预设（霸总/冷漠学长/温柔青梅/痞帅等）
- SSE 协议修复
- 记忆链路接通

### Persona 2：**30 岁职场男白领 @张默**（内测种子）

**动机**：情感抑郁、工作压力大，需要一个倾诉对象

**旅程**：
1. ✅ 登录 → 创建"温柔" 数字人
2. ⚠️ 聊到第 5 条时发："今天加班到现在，累到想死"
3. 🚨 **致命问题**：后端不经 crisis detector，直接把 "想死" 原文送给 LLM
4. LLM 可能回复："是的，人生确实很累..."（LLM 本身没专门训练危机响应）
5. ❌ **没有弹出心理援助热线号码**（crisis/detector.py 的 `CRISIS_RESOURCES` 没被前端用）
6. **监管和舆情风险**：如果这个用户真的出了事，责任在谁？

**必须改的**：
- digital_humans chat 端点必须接 crisis detector
- 高/极危级别时前端必须**强制弹窗**显示热线号码，不能靠 LLM"自觉"提示

### Persona 3：**付费冲动用户 @小雅**（测试付费流程）

**旅程**：
1. ✅ 看到"配额达到上限"→ 点"升级"→ 跳 pricing.html
2. ✅ 选择 ¥19.9/月 → 点"立即购买"
3. ❌ 前端会请求后端创建支付订单 → 实际进的是 `/api/v1/payment/mock/create` → 返回一个 `http://localhost:8000/api/v1/payment/mock/pay/xxx` 的 URL
4. ❌ 生产环境这个 URL 会失败（localhost + 路径都是假的）

**必须改的**：
- 完成 Alipay 真实接入（代码已有）
- 完成 回调 URL 配置 + 签名验证
- 支付成功后自动更新 Subscription 和 UserQuota

### Persona 4：**技术调研用户 @程序员老李**

**动机**：对 AI 陪伴产品技术感兴趣，想知道"它是不是真的有记忆"

**测试**：
- Day 1：告诉数字人"我是程序员，喜欢写 Rust"
- Day 3：问"你还记得我的职业吗？"
- ❌ 后端只取同 session_id 的最近 20 条（新开 session → 完全失忆）
- 就算老 session，超过 20 条就遗忘

**结论**：测完说"和豆包一样嘛"→ 流失

### Persona 5：**监管检查员**（合规压力测试）

**检查项**：
1. ❌ **备案**：未看到算法备案公示 + 生成式 AI 服务备案（根据《生成式人工智能服务管理暂行办法》必须备案才能开放公众服务）
2. ❌ **未成年人保护**：注册无年龄验证 + 无防沉迷机制
3. ⚠️ **内容安全**：无输入过滤、无输出审核（用户可诱导 LLM 生成违规内容）
4. ❌ **心理危机响应**：没有强制干预机制（见 Persona 2）
5. ⚠️ **用户数据**：长期记忆涉及个人信息但**无用户查看/导出/删除记忆的 UI 入口**
6. ❌ **未成年人防沉迷**：无时长限制

→ **监管一查就凉，甚至没有申诉空间**。

---

## 四、修改清单：接下来真正该改什么（按优先级）

### P0：2 周内必须修（阻塞产品能上线）

#### P0-1. 修 SSE 协议不匹配【半天】
**文件**：[frontend/js/api.js](../../frontend/js/api.js) OR [backend_v2/app/api/v1/digital_humans.py](../../backend_v2/app/api/v1/digital_humans.py)
**做法**（推荐改前端）：
```javascript
// api.js:236-260
// 把 data.type === 'chunk' 改为监听 event: delta 的 data.content
// 解析 SSE 的 event: 行
```
或者改后端让它发 `data: {"type": "chunk", ...}` 格式（同等简单）。
**验收**：curl /chat/stream 和前端实际看到流式回复。

#### P0-2. 数字人对话接入完整 pipeline【3 天】
**目标**：让 `digital_humans.py/chat/stream` 具备 `dialogue.py` 的所有能力
**做法**：
1. 新建 `backend_v2/app/services/dialogue/dh_processor.py`（仿 `enhanced_processor.py` 但基于 DigitalHuman 模型）
2. 在 chat 端点按顺序调：
   - `cost_tracker.check_quota(user_id, dh_id, estimated_tokens)`
   - `crisis_detector.detect(message, recent_context)` → 如果 HIGH/CRITICAL 走安全路径
   - `emotion_analyzer.analyze(message)`
   - `memory_retriever.retrieve_relevant(user_id, dh_id, message)` → 注入 system prompt
   - LLM stream → yield
   - `memory_retriever.store_memory(...)` → 异步存记忆
3. SSE 流增加字段：`{"type": "meta", "emotion": ..., "crisis_level": ...}` 单独帧

**验收**：
- 用户说"我想死"→ crisis_level="high" + 前端强制弹窗
- 跨 session 提问"我养的猫叫什么"→ AI 正确回答

#### P0-3. 支付真实接入【3 天】
**文件**：[backend_v2/app/api/v1/payment.py](../../backend_v2/app/api/v1/payment.py)（已有 Alipay 调用骨架）
**做法**：
1. 注册支付宝沙箱账号 → 配置 `ALIPAY_APP_ID/PRIVATE_KEY/PUBLIC_KEY` 到 `.env`
2. 前端 pricing.html "立即购买" 改调 `/api/v1/payment/alipay/create`（不是 /mock/create）
3. 回调 URL 必须是公网可达的 HTTPS → 本地开发用 ngrok 或服务器部署
4. 回调验签通过后，**事务性**地创建 Subscription 并升级 UserQuota
5. 加 idempotency key，防重放

**验收**：沙箱账号支付 ¥0.01 测试订单，订阅状态变为 active。

#### P0-4. 配额拦截中间件【1 天】
**文件**：新建 `backend_v2/app/core/quota.py`
**做法**：FastAPI Dependency，在 chat / upload / tts 接口前查 `UserQuota`，超限抛 `402 Payment Required` + 升级引导

**验收**：免费用户第 101 次对话被拦截，前端显示升级弹窗。

#### P0-5. 危机响应前端组件【1 天】
**文件**：[frontend/chat.html](../../frontend/chat.html) + [frontend/js/api.js](../../frontend/js/api.js)
**做法**：当 SSE 的 meta 帧里 `crisis_level >= "high"`：
- 对话区顶部滑出紧急 banner 显示热线号码
- 不可 dismiss，直到用户点"我知道了"
- 同时异步调 backend 的 `crisis_handler` 做管理员通知

### P1：4-8 周内做（差异化护城河）

#### P1-1. 可视化长期记忆 UI【✅ 已完成 2026-04-23】
**目标**：让用户看见 / 编辑 / 删除 AI 记住了什么
**完成文件**：
- 前端：[frontend/memory.html](../../frontend/memory.html)（约 450 行）
- 后端：[backend_v2/app/api/v1/digital_humans.py](../../backend_v2/app/api/v1/digital_humans.py)
  新增 5 个路由在 `/api/v1/digital-humans/{dh_id}/memories/*`
- 底层：[vector_store.py](../../backend_v2/app/services/memory/vector_store.py)
  加 `count(filter)` / `list_by_metadata` / `delete_by_metadata`；
  [retriever.py](../../backend_v2/app/services/memory/retriever.py)
  加 `list_memories` / `count_memories_by_emotion` / `delete_all_memories`

**落地能力**：
- 时间线视图（最新在前） + 情感图标 + 重要性星级 + 用户原话/TA 回复
- 8 种情感筛选 Chip（joy/sadness/anger/fear/surprise/disgust/love/neutral）
- 语义搜索（`?q=...`，debounce 300ms，显示相关度百分比）
- 单条删除（confirm 对话框）+ 清空全部（二次输入"删除"校验）
- 入口：dh-list.html 卡片"🧠 记忆"按钮 + chat.html 顶栏 🧠 图标
- 安全：所有端点验证 DigitalHuman.user_id 归属；单删再校 memory_id 前缀

**为什么押这个**：筑梦岛/星野/Character.AI/豆包都没有可视化记忆 UI，
这是市场研究确认的差异化护城河（详见本文第一部分）。

#### P1-2. 乙女向 / 角色扮演人格大类【✅ 已完成 2026-04-23】
**目标**：新增"浪漫陪伴"人格类别，下 6 个预设男主
**完成文件**：
- 后端：[backend_v2/app/services/personality_engine.py](../../backend_v2/app/services/personality_engine.py)
  扩展 `PERSONALITY_TEMPLATES` 字段（+category/description/avatar/sample_line），
  新增 6 个 `romantic_*` 预设 + 安全红线自动拼接，新增
  `get_personalities_by_category()` 方法
- 后端 API：新增 `GET /api/v1/digital-humans/options/personalities/grouped`
- 前端：[frontend/create-dh-step2.html](../../frontend/create-dh-step2.html)
  动态 tab 切换（基础陪伴 / 浪漫陪伴）+ 骨架屏 + 年龄 gate + 卡片渲染
- 前端支撑：config.js 加 `PERSONALITIES_GROUPED` 常量，api.js 加 `getPersonalitiesGrouped()`

**6 个虚构人物预设**：
- romantic_ceo       陆沉 · 霸总 🤵
- romantic_senior    江瑾 · 冷漠学长 🎓
- romantic_childhood 沈星辞 · 温柔青梅 🌻
- romantic_bad_boy   许南川 · 痞帅学长 🎸
- romantic_doctor    林砚 · 腹黑医生 🩺
- romantic_elder     苏屿 · 温柔哥哥 ☀️

每个预设 system prompt 含：背景 / 性格 / 说话风格 / 互动 / 绝不做 五大章，
自动拼接 `_ROMANTIC_SAFETY_RULES`（6 条硬约束：禁色情/暴力/未成年/违法/等）。

#### P1-3. 语音交互最小版【✅ 已完成 2026-04-23】
**目标**：用户能用语音发消息 + 听 AI 语音回复
**完成文件**：
- 前端 [frontend/js/api.js](../../frontend/js/api.js) 新增 `voice` 模块：
  `asrUpload(blob, format, sampleRate)` / `ttsSynthesize(text, voice, format)` / `getVoices()`
- 前端 [frontend/chat.html](../../frontend/chat.html)：
  - `toggleVoiceInput()` 真实 MediaRecorder 录音 → 停止后上传 `/voice/asr/upload`
    → 文本填入输入框（用户可编辑后再发送）
  - 每条 AI 消息追加扬声器按钮 🔊 → 点击调 `/voice/tts` 下载 Blob → `<audio>.play()`
  - 录音中 UI：红色 + `pulseRec` 脉冲光晕
  - 浏览器不支持 MediaRecorder / 拒绝麦克风权限都有友好提示

**已知限制**：浏览器默认 webm/opus，阿里云 ASR 主要支持 wav/mp3/pcm；
生产前需要前端 Web Audio API 转 wav 或后端加 ffmpeg 转换层。

#### P1-4. Redis LLM 缓存【✅ 已完成 2026-04-23】
**目标**：降 20-30% LLM 调用成本
**完成文件**：
- [backend_v2/app/core/cache.py](../../backend_v2/app/core/cache.py) 新建（350+ 行）
  - 三后端抽象：`NullCache` / `InMemoryCache` / `RedisCache`
  - Key 生成：`llm_cache_key(model, messages, system_prompt, temperature)`
    → sha256 稳定 hash，浮点温度规范化到 3 位小数
  - Skip 策略：`should_skip_cache()` — 危机模式 / 高温 / 极短极长消息
  - 流式兼容：`fake_stream_from_cache()` 把缓存文本按 16 字符分段回放
- digital_humans.py 的 chat 和 chat_stream 都集成了缓存查/写
- SSE start 帧新增 `cache_hit: bool` 字段供前端监控
- .env.example 补 `REDIS_URL` / `CACHE_ENABLED` / `CACHE_TTL_SECONDS`

**功能测试已过**：key 稳定性、skip 策略、TTL 过期、NullCache fallback 全部绿灯。

**预期收益**：
- 高频问候"你好"、"在吗"命中率 > 50%
- 相同预设的常见提问（"你是谁"、"几岁"）几乎 100% 命中
- 浪漫预设开场白场景大量命中

### P2：清理技术债（与 P1 并行）

#### P2-1. 砍掉游戏化代码【✅ 已完成 2026-04-23】
**目标**：产品不是游戏，清掉冲突代码 / 统一定位

**第一阶段：禁用游戏化 API 路由**
- [backend_v2/app/api/v1/__init__.py](../../backend_v2/app/api/v1/__init__.py) 大幅简化：
  从 19 个 router 降到 5 个核心 router（auth / digital_humans / voice /
  payment / analytics），其余 14 个游戏化 router 不再注册
- [backend_v2/app/main.py](../../backend_v2/app/main.py) root endpoint 的 endpoints
  导航同步精简
- 代码文件仍保留在 `api/v1/` 下，避免其他代码还在 import 时的破坏性崩塌

**第二阶段：归档游戏化 PRD 文档**
- 新建 [docs/archive/legacy-game-pivot/](../archive/legacy-game-pivot/) 目录
- `git mv docs/business/prd-details/` → `docs/archive/legacy-game-pivot/prd-details/`
  （完整 14 份游戏 PRD 一次性归档，保留 git 历史）
- 归档目录顶部放 README 明确说明：
  - 为什么归档（方向收敛）
  - 什么情况下可能再用
  - 请勿：新代码 import / 当作现行需求 / 向新人推荐
- 更新 docs/README.md 文档导航，移除 business/prd-details 链接，新增 archive 章节

**未触动**（保留，因为其他路径仍引用 Player 模型作数据 key）:
- `backend_v2/app/models/player.py` / social.py / inventory.py 等 ORM 文件
  保留，payment.py 的 Player fallback 仍依赖 Player 记录（见 P0-3）
- `backend_v2/app/services/npc/` / three_keys/ / achievement_loader.py 保留，
  供未来可能的"数字人商业化"参考（卡池 / 剧情包 / 等）

**验证**: 5 个保留路由 py_compile 全部通过，active set 校验脚本已通过

#### P2-2. 归档 backend/（Flask MVP）【✅ 已完成 2026-04-23】

**执行动作**：
- `git mv backend/` → `archive/backend-flask-mvp/`（保留完整 git 历史）
- 删除孤立的 `Dockerfile.backend`（docker-compose 早已指向 backend_v2）
- 新建 [archive/README.md](../../archive/README.md) 作为归档总索引
- 更新根 README.md 项目结构图与架构图（从"双后端"改为"单主线"）

**为什么现在可以归档**：backend_v2 已接管所有主链路（P0-P1 完成确认），
deploy.sh / docker-compose 均不再引用 `backend/`。保留代码的唯一价值
变成"历史参考"，归档比保留在活跃目录更清晰。

**未触动**：`docs/ops/DEPLOYMENT.md` 和 `docs/ops/INTEGRATION_TEST_GUIDE.md`
里的 Flask 版本说明段落（需要独立的文档重写工作，不在 P2-2 范围）。
**做法**：把 `backend/` 目录整个 `git mv` 到 `archive/backend-flask-mvp/`
- 前提：确认所有 API 都已迁到 `backend_v2/`
- 保留只读，用于 SUMMARY.md 历史参考

### P3：合规准备（法律顾问 + 技术同步）

（等监管研究 agent 完成后补充更细的清单）

#### P3-1. 算法备案（生成式 AI 服务备案）【4-12 周流程】
根据《生成式人工智能服务管理暂行办法》（2023-08-15 施行）+ 2024-2026 最新要求：
- 向所在地省级网信办提交备案
- 申请材料包括：算法安全自评估报告、拟公开信息、训练数据合规声明

#### P3-2. 内容安全体系【2 周】
- 接入云厂商内容审核 API（阿里云/腾讯云）覆盖输入+输出
- 敏感词过滤规则库
- 用户举报 + 审核员工作台

#### P3-3. 用户数据权利 UI【✅ 已完成 2026-04-23】

**完成文件**：
- 后端：[backend_v2/app/api/v1/account.py](../../backend_v2/app/api/v1/account.py)
  （4 个端点：data-summary / data-export / DELETE memories / DELETE account）
- 前端：[frontend/account-data.html](../../frontend/account-data.html)
  （数据摘要卡片 + 导出 / 清空记忆 / 注销账户三个操作区）
- 入口：dh-list.html 和 subscription.html 顶栏加 🔒 图标

**对应法条**：
- PIPL §44 知情权 → `/data-summary` 告诉用户存储了哪些类别
- PIPL §45 查阅复制权 → `/data-export` 下载 JSON 副本
- PIPL §47 删除权 → `DELETE /memories`（记忆）+ `DELETE /account`（全部）

**安全设计**：
- 清空记忆需前端 prompt "删除" 校验 + 后端 `?confirm=true` 兜底
- 注销账户需：前端 Modal 显示影响范围 + 输入密码 + 二次确认 + `?confirm=true`
- 注销后端：密码校验 → 级联按外键顺序删除（memories/messages/conversations/
  digital_humans/orders/user）→ 订单失败 fallback 不阻塞主流程
- 注销成功：前端清 localStorage/sessionStorage + 跳回登录页

**待优化**：
- Order 删除被 Payment 外键约束可能阻塞 —— 合规建议改为"假名化"（PIPL §51）
  而非物理删除订单（需要财务审计留底）
- 缺注销操作日志打点（合规审计建议）

---

## 五、重新定义的 Lane A 验证问题（基于本次审计）

V3 原版 Lane A 的 3 个问题（Q1/Q2/Q3），根据审计结果优化为：

### Q1（新版）：乙女向赛道是否适合我们？

**验证方式**：用 2 周，不用开发功能，只做 3 件事：
1. 付费使用筑梦岛 7 天，总结 "哪里惊艳 / 哪里失望"
2. 访谈 15 个筑梦岛现有付费用户："你为什么付费 / 什么会让你换 App"
3. 投放 3 个落地页（筑梦岛升级版 / 心理陪伴版 / 通用陪伴版）各 ¥500 比较 CTR

**Kill**：如果 CTR 差距 < 30%，说明我们无法"更好"，转退路方向（D）。

### Q2（新版）：我们的差异化记忆点是什么？

**候选答案**（按成本排序，**都建立在 F 方向上**）：
- 🥇 **真正的长期记忆可视化** —— 用户能看见自己和"TA"的关系成长轨迹（筑梦岛目前没有）
- 🥈 **真实语音 + 方言** —— 筑梦岛语音还比较机械
- 🥉 **主动发起对话** —— 节日/纪念日/情绪感知式的主动触达

### Q3（新版）：¥19.9 太低吗？

**审计后观点**：
- 筑梦岛 VIP ¥16/月说明价格敏感度存在，但它还有 SVIP ¥36 + 卡池付费
- 建议学筑梦岛**双档订阅 + 内容付费**组合：
  - VIP ¥19.9/月（无限对话 + 基础记忆）
  - SVIP ¥39.9/月（解锁角色剧情 + 语音 + 纪念日主动联系）
  - 单次抽卡/剧情包（¥6-18）
- 验证：种子用户 100 人先跑 SVIP 定价 2 周，看续订率

---

## 六、本月立即行动清单（替代 V3 原版）

### 第 1 周（技术紧急）
- [ ] D1-2：修 SSE 协议不匹配（P0-1）
- [ ] D3-5：接通危机检测到用户对话（P0-2 子任务 1）
- [ ] D6-7：长期记忆链路接入（P0-2 子任务 2）

### 第 2 周（市场验证同步启动）
- [ ] 工程线 ↑：配额中间件 + 支付宝沙箱（P0-3 + P0-4）
- [ ] 产品线：付费注册筑梦岛 7 天深度体验 + 差异化报告
- [ ] 增长线：起草 3 个落地页 + 目标用户访谈名单

### 第 3 周（尖刀开工）
- [ ] 工程线 ↑：可视化记忆 UI（P1-1）
- [ ] 产品线：访谈 15 人（Q1 新版验证）
- [ ] 增长线：落地页上线 + 投流 ¥1500 比较

### 第 4 周（决策 + 启动 Alpha）
- [ ] 决策会：用访谈+投流数据决定走 F 还是退 D
- [ ] 工程线 ↑：如果决定走 F，开工"乙女向人格模板"（P1-2）
- [ ] 合规线：咨询律师 + 启动算法备案流程（P3-1）

---

## 七、给创始人的最新判断

1. **代码库不缺功能，缺接通**。过去一段时间在写服务模块，但没人把它们串成"用户真正用得到的链路"。这是**整合工程师**的工作，不是新功能开发。

2. **乙女向方向比心理健康方向更可行**。筑梦岛 500 万用户 + 千万美元融资是中国市场唯一被验证的 AI 陪伴付费案例。你有机会做"升级版"而不是"从零探索"。

3. **游戏化代码是历史债，必须砍**。backend_v2 里的 player/quest/inventory/shop/party 等模块与"AI 陪伴 SaaS"定位严重冲突。保留它们 = 告诉未来加入的工程师"这个产品定位还没想清楚"。

4. **合规不能等**。Replika 事件 + 国内监管约谈已经证明这是高压线。算法备案至少需要 4-12 周，越早启动越好。

5. **V3 战略框架仍然有效**，但"不做清单"里增加一条：**不做游戏化**。这比不做元宇宙更紧急，因为游戏化代码已经在库里了。

---

**下一步**（本文档交付后）：
- 向团队 review 本审计
- 如果同意方向调整，更新 `PRODUCT_STRATEGY_V3.md` 的 Q1 细分推荐（从 D+E 改为 F 为主 + D 为退路）
- 如果同意技术诊断，立即启动 P0 修复（特别是 SSE 协议 Bug 已经在阻塞所有用户）
- 合规线立即并行启动（不要等产品完善）

---

**关联文档**：
- [PRODUCT_STRATEGY_V3.md](PRODUCT_STRATEGY_V3.md) — V3 战略原版
- [BUSINESS_ROADMAP_V2.md](BUSINESS_ROADMAP_V2.md) — 商业化操作路线
- [../technical/BACKEND_IMPLEMENTATION_PLAN.md](../technical/BACKEND_IMPLEMENTATION_PLAN.md) — 后端实施（需要根据本审计更新）
