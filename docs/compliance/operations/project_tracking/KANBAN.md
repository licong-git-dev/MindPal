# 任务 Kanban

> 每日 update。移动任务卡片时**直接改这个 md 文件**提交 Git。
> 所有任务卡片都含：`[标签] 负责人 · 截止日期`

---

## 🧊 Backlog（未排期）

- [ ] 备案后考虑：订阅式合规顾问（¥2-5K/月）
- [ ] 评测集每季度增量 20% 更新
- [ ] 监督学习模型替代部分规则（长期）

---

## 📋 To Do（已排期待执行）

### 🔧 工程
- [ ] [engineering] 运维 · 🟨配置 MODERATION_ALIYUN_ENABLED + AccessKey · 截止 🟨
- [ ] [engineering] 运维 · 🟨配置 CRISIS_WEBHOOK_URL (企业微信) · 截止 🟨
- [ ] [engineering] 运维 · 🟨 部署 Redis 生产环境 · 截止 🟨
- [ ] [engineering] 工程 · 🟨 从 CRISIS_RESOURCES 抽一份热线测试消息发到告警群 · 截止 🟨
- [ ] [engineering] 工程 · 🟨 初次真实 E2E 测试（从注册到完成对话）· 截止 🟨

### 📝 评测
- [ ] [evaluation] 运营 · 🟨 联系 1 位法学背景顾问（¥1500-3000）· 截止 🟨
- [ ] [evaluation] 运营 · 🟨 联系 1 位心理学背景顾问 · 截止 🟨
- [ ] [evaluation] 运营 · 🟨 顾问抽查 50-80 题 + 签评测报告 · 截止 🟨
- [ ] [evaluation] 工程 · 🟨 跑 run_safety_eval.py 输出 JSON + PDF · 截止 🟨

### ⚖️ 法务
- [ ] [legal] 创始人 · 🟨 发 RFP 给 3-5 家律所 · 截止 🟨
- [ ] [legal] 创始人 · 🟨 电话询价 3 家（30 分钟/家）· 截止 🟨
- [ ] [legal] 创始人 · 🟨 签约选定律所 · 截止 🟨
- [ ] [legal] 创始人 · 🟨 review 律所首稿 · 截止 🟨
- [ ] [legal] 创始人 + 工程 · 🟨 定稿上线 frontend/legal.html · 截止 🟨

### 🏢 资质
- [ ] [qualification] 行政 · 🟨 营业执照扫描件 · 截止 🟨
- [ ] [qualification] 法定代表人 · 🟨 身份证扫描 · 截止 🟨
- [ ] [qualification] 创始人 · 🟨 签安全负责人/DPO/审核员任命书 · 截止 🟨
- [ ] [qualification] 产品 · 🟨 10 张界面截图（含 crisis/moderation）· 截止 🟨

### 📤 提交
- [ ] [submission] 合规 · 🟨 网信办平台注册账号 · 截止 🟨
- [ ] [submission] 合规 · 🟨 完成 40 项 SUBMISSION_PREFLIGHT 自检 · 截止 🟨
- [ ] [submission] 法定代表人 · 🟨 签字声明 · 截止 🟨
- [ ] [submission] 合规 · 🎉 正式提交 · 截止 🟨

---

## 🏃 Doing（进行中 · 每人最多 2 个）

_当任务开始做时从 To Do 移到这里，**写上你的名字 + 今日状态**_

- [ ] 🟨 示例: [legal] 张三 · 已发出 RFP，等 2 家律所回复中

---

## 🚧 Blocked（阻塞超 24 小时的任务）

_任何阻塞 > 24 小时必须移到这里 + 写阻塞原因 + CC 创始人_

- [ ] 🟨 示例: [legal] 金杜律所报价过高等谈判，阻塞于对方迟迟不回 · Since 🟨

---

## ✅ Done（已完成 · 本周）

_每周五归档到 _DONE_ARCHIVE.md 避免本文件变长_

- [x] 🟨 示例: [engineering] 工程 · 完成 crisis_handler webhook 代码 · Done 🟨

---

## 🎖️ 本周关键事件（手写）

_记录让项目推进的关键里程碑、重大决定、意外变化_

- 🟨 Week YYYY-MM-DD: ...

---

## 📦 Done 归档（本月之前）

移到 [_DONE_ARCHIVE.md](_DONE_ARCHIVE.md)

---

## 更新节奏

- **每日**：移动 To Do → Doing → Done 卡片
- **每周一**：从 Backlog 挑出 5-10 个新的 To Do
- **每周五**：Done 区写好的 commit + archive 上周卡片
- **每月**：整体 review Timeline 是否还能按期
