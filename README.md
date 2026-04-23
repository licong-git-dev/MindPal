# MindPal — 面向元宇宙的智能体数字人交互平台

<div align="center">

**你的智慧伙伴 · 陪伴 · 学习 · 服务**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.109%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Flask](https://img.shields.io/badge/flask-3.0-lightgrey.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/docker-compose-2496ED.svg)](https://www.docker.com/)

[在线演示](http://43.98.170.184) · [文档中心](docs/README.md) · [商业计划](docs/business/MindPal_深度解读.md) · [技术方案](docs/technical/TECHNICAL_STRATEGY.md) · [路线图](docs/roadmap/DEVELOPMENT_ROADMAP.md)

</div>

---

## 📌 一句话概括

**MindPal** 是一个通过"深度个性化塑造"+"长期记忆"+"多场景服务"来打造专属 AI 伙伴的平台，以 SaaS 模式起步，最终演进为元宇宙基础设施。

---

## 🌟 三大核心价值

| 价值维度 | 核心能力 | 当前实现状态 |
|---------|---------|-------------|
| **智能 (Intelligence)** | LLM + RAG + Agent | ✅ 通义千问 + FAISS 向量检索已落地 |
| **陪伴 (Companionship)** | 全天候情感倾听、共情 | ✅ 基础对话 / 🚧 长期记忆与情感引擎 |
| **服务 (Service)**      | 知识学习辅助 + 购物辅助 | ✅ 知识库 / 📋 购物助手（规划中）|

---

## ✅ 已落地能力（可跑通端到端）

### 前端（13 个页面，响应式）

| 模块 | 页面 |
|------|------|
| 注册登录 | `index.html` |
| 新手引导 | `onboarding.html` |
| 数字人列表 | `dh-list.html` |
| 5 步创建流程 | `create-dh-step1~5.html`（形象/性格/声音/知识库/确认）|
| 对话界面 | `chat.html`（SSE 流式打字机效果）|
| 知识库管理 | `knowledge.html`（拖拽上传，多格式解析）|
| 定价与会员 | `pricing.html` / `subscription.html` |

### 后端（双后端并存，详见「技术债」）

- `backend/`（Flask 3.0，MVP 版本）：认证 / 数字人 CRUD / 对话 / 知识库 / 订阅 / 埋点
- `backend_v2/`（FastAPI 0.109，下一代架构）：增加了情绪分析 / 危机检测 / 多 LLM 路由 / 语音 / 微信&支付宝 / 记忆引擎等模块骨架

### AI 能力

- 🤖 LLM：阿里云通义千问（qwen-turbo/plus），可切换 Claude
- 📚 Embedding + RAG：`text-embedding-v2` + FAISS `IndexFlatL2`
- 📄 文档解析：PDF / DOCX / TXT / MD 全支持
- 🔄 流式对话：Server-Sent Events + 情绪分析 + 对话历史

### 商业化骨架（已搭好，未闭环）

- 💳 订阅模型（`Subscription` + `UserQuota`）—— 免费版 / ¥19.9/月 / ¥199/年
- 📊 埋点系统（13 个关键事件，覆盖注册→创建→对话→付费全漏斗）
- 📈 会员中心与配额展示

### 部署

- 🐳 Docker Compose 一键部署（前端 Nginx + 后端 Gunicorn）
- 📜 `deploy.sh` 云服务器一键脚本

---

## 🧭 战略方向（基于商业与技术瓶颈的深度分析）

> 文档已经堆了 8000+ 行，代码双后端并存，愿景铺得从 AI 伴侣一路到元宇宙。**现在需要做的不是继续加功能，而是收敛到一个能赚钱的单点闭环。**

### 📉 当前关键瓶颈

#### 🔴 商业瓶颈（按阻塞程度排序）

1. **变现闭环未闭合** —— 订阅模型建好了，但支付集成卡在沙箱，**一分钱都没收到过**。这是比任何新功能都紧迫的事。
2. **赛道拥挤且同质化** —— Replika / Character.AI / MiniMax 星野 / Talkie / 豆包 已经占领情感陪伴心智，靠"功能多"打不赢，需要一个**别人没有的记忆点**。
3. **获客成本未验证** —— 未做过一次真实投放，CAC / LTV / 留存漏斗全部是计划书里的假设。
4. **LLM 成本吃利润** —— 免费用户的对话调用直接吃掉毛利，没有缓存层、没有 token 上限策略。

#### 🔴 技术瓶颈（按维护负担排序）

1. **双后端架构债** —— `backend/` 和 `backend_v2/` 同时在维护，API、数据模型、依赖包都分叉了。**必须砍掉一个。**
2. **SQLite 单机 + 无 Redis** —— 百级并发就会掉请求，而且每次对话都重复调 LLM。
3. **无异步队列** —— 文档上传/向量化直接阻塞 HTTP 请求，大文件必超时。
4. **无可观测性** —— 没有 Prometheus / ELK / Sentry，线上出问题只能翻 `server.log`。
5. **测试覆盖率极低** —— 仅有 3 个 smoke test 文件，重构靠勇气。
6. **无 CI/CD** —— 每次部署都要手动 SSH 跑 `deploy.sh`，人肉流程易错。
7. **愿景铺得过宽** —— 元宇宙 / 3D 世界 / 购物助手 / 游戏化经济系统都在规划，**资源严重稀释**。

### 🎯 接下来做什么：分 4 个波次，先闭环再扩张

#### 🌊 波次 1 ｜ 商业闭环（接下来 2 周，P0）

**目标：拿到第一笔真实收入，把假设变成数据**

- [ ] **统一后端架构**：把 `backend/` 的能力迁完到 `backend_v2/`，然后删 / 归档 Flask 版本（避免再分叉）
- [ ] **支付宝沙箱 → 生产闭环**：端到端跑通「下单 → 扫码 → 回调验签 → 订阅生效 → 配额升级」
- [ ] **硬性配额拦截**：免费用户达到 100 次/天、50MB 知识库后**真实阻断**并弹升级提示
- [ ] **埋点数据面板**：DAU / WACU / 注册→付费漏斗在 Grafana 或简易 dashboard 上可见
- [ ] **招 20 个种子用户跑 2 周**，拿到留存和付费意愿的真数据

**成功标准**：MRR ≥ ¥500，至少 10 个真实付费用户，每日数据可观测。

#### 🌊 波次 2 ｜ 差异化尖刀（4-8 周，P1）

**目标：建立「别人抄不走」的产品记忆点**

当下市面上的 AI 伴侣产品，最大的问题是**「每次对话像第一次见面」**。我们应该把"**有记忆、懂你、会成长的 AI 伙伴**"做到极致，而不是追着对手堆功能。

- [ ] **可视化长期记忆**：把 `backend_v2/services/memory/` 的记忆图谱做成用户能看见、能编辑的时间线（这是 Replika 和 Character.AI 都没有的）
- [ ] **真实语音对话**：接入阿里云 ASR/TTS + WebRTC，实现 < 2s 延迟的全双工语音
- [ ] **微信小程序**：国内分发成本最低的入口，直接基于已有 H5 快速复用
- [ ] **情感引擎 v1**：基于 `backend_v2/services/emotion/` 做"主动发消息 + 情绪适配回复"

**成功标准**：次日留存 ≥ 30%、7 日留存 ≥ 15%，微信小程序 DAU ≥ 500。

#### 🌊 波次 3 ｜ 规模化地基（2-6 个月，P2）

**目标：支撑 1 万 DAU、日千万 Token 调用**

- [ ] **PostgreSQL 迁移** + 连接池 + 索引优化
- [ ] **Redis 缓存层**（LLM 响应 / 会话 / 热点 embedding）——预期降 LLM 成本 30%+
- [ ] **Celery 异步队列**（文档处理 / TTS 生成 / 邮件推送）
- [ ] **Prometheus + Grafana 监控** + Sentry 报错 + 结构化日志
- [ ] **pytest 单元测试 + pytest-asyncio 集成测试**，覆盖率 ≥ 60%
- [ ] **GitHub Actions CI/CD**，自动 lint / 测试 / 构建镜像 / 蓝绿部署

#### 🌊 波次 4 ｜ 生态与愿景（6 个月后，P3，视数据决定）

> 只有在波次 1-3 跑通，且 MRR ≥ ¥10 万 的前提下再启动。不要在没有收入的时候先建虚拟世界。

- React Native 移动端（iOS / Android 原生推送）
- 开放 API + SDK，做 PaaS（企业定制数字人）
- 3D 虚拟形象（口型同步）
- HunyuanWorld 3D 场景接入（参见 [docs/technical/HUNYUAN_INTEGRATION_PLAN.md](docs/technical/HUNYUAN_INTEGRATION_PLAN.md)）
- Marketplace 数字人交易 + 元宇宙中央大厅

---

## 🏗️ 技术架构

### 架构现状（双后端并存）

```
┌─────────────────────────────────────────────────────────┐
│               Frontend (HTML5 + Vanilla JS)              │
│     13 pages │ api.js 封装 │ analytics.js 埋点           │
└────────────────────────┬────────────────────────────────┘
                         │ REST / SSE
            ┌────────────┴────────────┐
            │                         │
    ┌───────▼────────┐       ┌────────▼─────────┐
    │  backend/       │       │  backend_v2/     │
    │  Flask 3.0      │       │  FastAPI 0.109   │
    │  (MVP 现役)     │       │  (下一代, 在建)  │
    │                 │       │                  │
    │ • auth          │       │ • auth + JWT     │
    │ • digital_humans│       │ • dialogue/LLM   │
    │ • chat (SSE)    │       │ • memory 引擎    │
    │ • knowledge+RAG │       │ • emotion 分析   │
    │ • subscription  │       │ • crisis 检测    │
    │ • analytics     │       │ • voice (ASR/TTS)│
    │                 │       │ • payment (WX/支付宝)│
    │                 │       │ • three_keys 挑战│
    └───────┬─────────┘       └────────┬─────────┘
            │                          │
            └──────────┬───────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐  ┌──────▼──────┐  ┌───▼────────┐
   │ SQLite  │  │ 阿里云       │  │ FAISS      │
   │ (开发)  │  │ DashScope    │  │ Vector     │
   │  → PG   │  │ (qwen/embed) │  │ Store      │
   └─────────┘  └──────────────┘  └────────────┘
```

> ⚠️ **技术债提醒**：两套后端不是设计，是演进中未合并的遗留。详见「战略方向 · 波次 1」。

### 技术栈清单

| 层级 | 技术选型 |
|------|---------|
| 前端 | HTML5 + CSS3 + Vanilla JS（ES6+）、Glassmorphism UI |
| Web 服务器 | Nginx（反向代理 + 静态托管 + SSE 兼容）|
| 后端框架 | FastAPI（主线） / Flask（遗留） |
| ORM | SQLAlchemy 2.0（async）|
| 数据库 | SQLite（开发） → PostgreSQL（生产）|
| 缓存 | Redis（规划中）|
| 向量库 | FAISS → Qdrant（规划中）|
| LLM | 通义千问（主） + Claude（备） |
| ASR/TTS | 阿里云智能语音（规划中）|
| 部署 | Docker Compose + Gunicorn |
| 监控 | Prometheus + Grafana（规划中）|

---

## 📂 项目结构

经过深度归纳，**根目录只保留代码/部署/入口文档**，所有深度文档集中在 `docs/`。

```
MindPal/
├── README.md  CLAUDE.md              # 项目入口 + 团队协作规范
├── .gitignore  .ccb-config.json
│
├── frontend/                         # 前端（13 页面 + 4 JS + 4 CSS）
│   ├── *.html                        # index / dh-list / chat / knowledge / ...
│   ├── js/   { api.js, auth.js, config.js, analytics.js }
│   ├── css/  { variables, base, components, animations }
│   └── assets/
│
├── backend/                          # [遗留·Flask MVP] 波次 1 将归档
│   ├── app/  { models, routes, services, utils }
│   └── requirements.txt
│
├── backend_v2/                       # [主线·FastAPI] 新开发集中于此
│   ├── app/
│   │   ├── api/v1/        # 20+ 路由
│   │   ├── models/        # 9 个 ORM 模型
│   │   ├── services/      # ai / crisis / dialogue / emotion / llm /
│   │   │                  # memory / npc / payment / three_keys / voice
│   │   ├── schemas/       # Pydantic 输入输出
│   │   └── core/          # security / websocket
│   ├── alembic/           # 数据库迁移
│   ├── scripts/           # init_db / create_dh_tables / test_api
│   └── tests/             # pytest
│
├── scripts/                          # 多 AI（Claude+Codex+Gemini）协作工具
│   └── mp-ai.py  mp-multi-ai.py  ...
│
├── docs/                             # 🗂️ 所有深度文档集中地
│   ├── README.md                     # 文档导航索引
│   ├── product/                      # PRD + 设计规范
│   ├── technical/                    # 技术方案 + 后端实施 + 混元集成
│   ├── roadmap/                      # 开发/商业路线图 + TODO + 交付总结
│   ├── ops/                          # 部署指南 + 集成测试
│   ├── business/                     # 商业计划 + 14 份细化 PRD
│   ├── research/                     # 华为/字节/腾讯 外部调研
│   └── guides/                       # 多 AI 协作指南
│
├── deploy.sh                         # 云服务器一键部署
├── docker-compose.yml                # 容器编排（根级，context=当前目录）
├── Dockerfile.backend  Dockerfile.frontend
└── nginx.conf                        # 反向代理 + SSE 兼容
```

> ⚙️ 部署文件（Dockerfile / docker-compose / nginx.conf / deploy.sh）**必须保留在根目录**，因为 `docker-compose.yml` 使用 `context: .` 引用前端构建上下文。

---

## 🚀 本地开发

### 先决条件

- Python 3.10+
- Git
- 阿里云 DashScope API Key（[申请地址](https://dashscope.aliyun.com/)，新用户免费 100 万 tokens）
- Docker（可选，用于一键部署）

### 启动 backend_v2（主线，推荐）

```bash
cd backend_v2
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env       # 填入 DASHSCOPE_API_KEY
uvicorn app.main:app --reload --port 8000
```

验证：
```bash
curl http://localhost:8000/health
# 访问 http://localhost:8000/docs 查看 Swagger
```

### 启动前端

```bash
cd frontend
python -m http.server 3000
# 浏览器打开 http://localhost:3000
```

### 测试账号

- 手机号：`13800138000`
- 密码：`仅本地测试用示例密码，请勿用于生产环境`

---

## 🌐 生产部署

一键部署到阿里云 ECS（Ubuntu 20.04+）：

```bash
ssh root@your_server_ip
curl -O https://raw.githubusercontent.com/licong-git-dev/MindPal/master/deploy.sh
sudo bash deploy.sh
```

或使用 Docker Compose：

```bash
docker compose up -d
```

当前演示环境：**http://43.98.170.184**

---

## 📖 文档导航

> 完整索引见 **[docs/README.md](docs/README.md)**。以下是高频入口：

| 类别 | 文档 | 说明 |
|------|------|------|
| 入口 | [README.md](README.md) | 本文档（项目总览 + 战略方向）|
| 入口 | [docs/README.md](docs/README.md) | 文档中心导航 |
| 产品 | [docs/product/PRD.md](docs/product/PRD.md) | 产品需求（1500+ 行）|
| 产品 | [docs/product/DESIGN_SPEC.md](docs/product/DESIGN_SPEC.md) | UI/UX 设计规范（2300+ 行）|
| 技术 | [docs/technical/TECHNICAL_STRATEGY.md](docs/technical/TECHNICAL_STRATEGY.md) | 深度技术方案 |
| 技术 | [docs/technical/BACKEND_IMPLEMENTATION_PLAN.md](docs/technical/BACKEND_IMPLEMENTATION_PLAN.md) | 后端实施计划 |
| 技术 | [docs/technical/HUNYUAN_INTEGRATION_PLAN.md](docs/technical/HUNYUAN_INTEGRATION_PLAN.md) | 混元 3D 整合方案 |
| 路线 | [docs/roadmap/DEVELOPMENT_ROADMAP.md](docs/roadmap/DEVELOPMENT_ROADMAP.md) | 4 阶段开发路线图 |
| 路线 | [docs/roadmap/BUSINESS_ROADMAP_V2.md](docs/roadmap/BUSINESS_ROADMAP_V2.md) | 商业化路线图 V2 |
| 路线 | [docs/roadmap/TODO_DEVELOPMENT.md](docs/roadmap/TODO_DEVELOPMENT.md) | 细化任务清单 |
| 路线 | [docs/roadmap/SUMMARY.md](docs/roadmap/SUMMARY.md) | Phase 0 交付总结 |
| 运维 | [docs/ops/DEPLOYMENT.md](docs/ops/DEPLOYMENT.md) | 部署指南 |
| 运维 | [docs/ops/INTEGRATION_TEST_GUIDE.md](docs/ops/INTEGRATION_TEST_GUIDE.md) | 集成测试指南 |
| 商业 | [docs/business/MindPal_深度解读.md](docs/business/MindPal_深度解读.md) | 商业计划解读 |
| 商业 | [docs/business/MindPaL.pdf](docs/business/MindPaL.pdf) | 完整商业计划书 PDF |
| 指南 | [docs/guides/MULTI_AI_GUIDE.md](docs/guides/MULTI_AI_GUIDE.md) | 多 AI 协作指南 |

---

## 🎯 当前迭代焦点（Sprint）

**本周（P0 · 商业闭环）**

- [ ] 统一后端：将 `backend/` 特有路由迁移到 `backend_v2/`
- [ ] 支付宝沙箱联调：`/api/v1/payment/create` → 支付页 → 回调 `/notify` → 订阅激活
- [ ] 配额硬性拦截：对话接口、知识库上传接口上 quota middleware
- [ ] Grafana 面板：DAU / 新增注册 / 付费转化率

**下周（P0 · 数据验证）**

- [ ] 20 个种子用户内测计划（付费入口开放）
- [ ] 支付成功率监控 + 异常处理（超时/取消/失败）
- [ ] 关键事件告警（支付失败、LLM 异常、配额超限）

---

## 🔑 API 密钥申请

| 服务 | 申请地址 | 免费额度 | 用途 | 必需？ |
|------|---------|---------|------|-------|
| 阿里云 DashScope | https://dashscope.aliyun.com/ | 100 万 tokens | LLM + Embedding | ✅ 必需 |
| 阿里云智能语音 | https://nls.aliyun.com/ | 100 万字符 | TTS/ASR | ⏳ 波次 2 |
| 支付宝开放平台 | https://open.alipay.com/ | 沙箱免费 | 订阅支付 | ✅ 波次 1 |
| 微信支付 | https://pay.weixin.qq.com/ | 商户费率 | 订阅支付 | ⏳ 波次 2 |

---

## 🤝 贡献指南

1. Fork 项目 → 创建特性分支 `feature/XXX`
2. 提交改动（使用 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/)）
3. 确保 `cd backend_v2 && pytest` 通过
4. 发起 Pull Request，关联对应 Issue

**代码规范**

- Python：`ruff` + `mypy`，遵循 PEP 8
- JavaScript：StandardJS
- Git：`feat / fix / docs / refactor / test / chore(scope): 简述`

---

## 🐛 问题反馈

在 [GitHub Issues](https://github.com/licong-git-dev/MindPal/issues) 提交，提供：

- 复现步骤 + 环境信息（OS、Python 版本、后端版本）
- 错误日志 / 截图
- 已搜索过确认不是重复 Issue

---

## 📄 许可证

MIT License，详见 [LICENSE](LICENSE)。

---

## 👥 团队与致谢

**MindPal Team**

- 产品 & 技术负责人：[@licong-git-dev](https://github.com/licong-git-dev)
- AI 协同：Claude (Anthropic) · 通义千问 (阿里云)

感谢开源生态：FastAPI · SQLAlchemy · FAISS · Nginx · Docker · HunyuanWorld。

---

<div align="center">

**用 AI 重新定义陪伴，用技术连接未来世界**

⭐ 如果这个项目对你有启发，点个 Star 再走 —— 这是对我们最实在的鼓励。

</div>
