# MindPal 文档中心

> 本目录是 MindPal 所有文档的聚合地。根目录仅保留 `README.md`、`CLAUDE.md`、代码和部署脚本；任何深度文档、设计规范、调研材料都进这里。

---

## 🗺️ 按类别浏览

### 📦 [product/](product/) · 产品规格

| 文档 | 用途 | 规模 |
|------|------|------|
| [PRD.md](product/PRD.md) | 产品需求文档（核心）| 1500+ 行 |
| [DESIGN_SPEC.md](product/DESIGN_SPEC.md) | UI/UX 设计规范 | 2300+ 行 |

### 🏗️ [technical/](technical/) · 技术方案

| 文档 | 用途 |
|------|------|
| [TECHNICAL_STRATEGY.md](technical/TECHNICAL_STRATEGY.md) | 深度技术方案（AI 选型、架构） |
| [BACKEND_IMPLEMENTATION_PLAN.md](technical/BACKEND_IMPLEMENTATION_PLAN.md) | 后端详细实施计划 |
| [HUNYUAN_INTEGRATION_PLAN.md](technical/HUNYUAN_INTEGRATION_PLAN.md) | 腾讯混元 3D 世界整合方案 |

### 🛣️ [roadmap/](roadmap/) · 路线与进度

| 文档 | 用途 |
|------|------|
| ⭐ [PRODUCT_STRATEGY_V3.md](roadmap/PRODUCT_STRATEGY_V3.md) | **战略过滤器**：三车道验证/差异化/规模化 + Kill Criteria + 不做清单 |
| [DEVELOPMENT_ROADMAP.md](roadmap/DEVELOPMENT_ROADMAP.md) | 4 阶段产品路线图（执行层）|
| [BUSINESS_ROADMAP_V2.md](roadmap/BUSINESS_ROADMAP_V2.md) | 商业化路线图 V2（执行层）|
| [TODO_DEVELOPMENT.md](roadmap/TODO_DEVELOPMENT.md) | 细化任务清单 |
| [SUMMARY.md](roadmap/SUMMARY.md) | Phase 0 交付总结 |

> 📌 **阅读顺序**：先读 V3 战略，再看 V1/V2 执行细节。V3 定义"做什么、不做什么"；V1/V2 定义"做的那些事怎么做"。

### 🚀 [ops/](ops/) · 部署与测试

| 文档 | 用途 |
|------|------|
| [DEPLOYMENT.md](ops/DEPLOYMENT.md) | 生产部署指南 |
| [INTEGRATION_TEST_GUIDE.md](ops/INTEGRATION_TEST_GUIDE.md) | 集成测试流程 |

### 💼 [business/](business/) · 商业计划

| 文档 | 用途 |
|------|------|
| [MindPal_深度解读.md](business/MindPal_深度解读.md) | 商业计划深度解读 |
| [DEVELOPMENT_PLAN.md](business/DEVELOPMENT_PLAN.md) | 开发计划 V1 |
| [DEVELOPMENT_PLAN_V2.md](business/DEVELOPMENT_PLAN_V2.md) | 开发计划 V2 |
| [MindPaL.pdf](business/MindPaL.pdf) | 完整商业计划书 PDF |
| [prd-details/](business/prd-details/) | 14 份游戏化 PRD 细化文档 |

### 🔬 [research/](research/) · 外部调研

| 文档 | 来源 |
|------|------|
| [华为员工管理协作模式深度分析.md](research/华为员工管理协作模式深度分析.md) | 组织研究 |
| [字节跳动抖音客服话术与方法论分析.md](research/字节跳动抖音客服话术与方法论分析.md) | 运营研究 |
| [腾讯世界模型技术架构与引擎分析.md](research/腾讯世界模型技术架构与引擎分析.md) | 技术前沿 |

每份调研均有 `.md` 和 `.docx` 两个版本。

### 📘 [guides/](guides/) · 使用指南

| 文档 | 用途 |
|------|------|
| [MULTI_AI_GUIDE.md](guides/MULTI_AI_GUIDE.md) | 多 AI（Claude+Codex+Gemini）协作指南 |

---

## 🧭 推荐阅读顺序

**新加入项目的开发者**：

1. 根目录 [`README.md`](../README.md) — 项目总览与战略方向
2. [product/PRD.md](product/PRD.md) — 产品定义
3. [technical/TECHNICAL_STRATEGY.md](technical/TECHNICAL_STRATEGY.md) — 技术选型
4. [roadmap/DEVELOPMENT_ROADMAP.md](roadmap/DEVELOPMENT_ROADMAP.md) — 迭代节奏
5. [ops/DEPLOYMENT.md](ops/DEPLOYMENT.md) — 跑起来

**投资人 / 决策者**：

1. 根目录 [`README.md`](../README.md) — 瓶颈分析与战略收敛
2. [business/MindPal_深度解读.md](business/MindPal_深度解读.md) — 商业模式
3. [roadmap/BUSINESS_ROADMAP_V2.md](roadmap/BUSINESS_ROADMAP_V2.md) — 商业化路线

**要做大改动的工程师**：

1. [roadmap/TODO_DEVELOPMENT.md](roadmap/TODO_DEVELOPMENT.md) — 谁在做什么
2. [technical/BACKEND_IMPLEMENTATION_PLAN.md](technical/BACKEND_IMPLEMENTATION_PLAN.md) — 后端边界
3. [product/DESIGN_SPEC.md](product/DESIGN_SPEC.md) — 前端边界

---

## ✍️ 文档维护规范

- **新文档按类别放入对应子目录**，不要再往根目录堆
- **命名**：全大写下划线（如 `FOO_BAR.md`），中文文档允许中文名
- **链接**：跨文档引用用相对路径，移动文档时同步更新索引
- **更新本索引**：新增/删除文档必须同步这份 README
- **弃用**：过时文档不要删，放到 `docs/archive/` 并在顶部加 `[ARCHIVED]` 标记

---

**最后更新**：2026-04-23（深度重组）
