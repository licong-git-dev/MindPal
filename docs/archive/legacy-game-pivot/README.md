# 🗄️ Legacy Game Pivot · 归档文档

> ⚠️ **这个目录里的文档全部已归档**。请不要以此为参考。

## 为什么归档

2026 年 4 月的产品战略审计（见 [`docs/roadmap/DEEP_AUDIT_V3.md`](../../roadmap/DEEP_AUDIT_V3.md)）
确认 MindPal 的产品方向是 **AI 数字人陪伴 SaaS**，不是游戏 / 元宇宙。

过去一段时间，项目里同时存在两套互不兼容的 PRD/代码方向：

1. **AI 陪伴**（前端 + `backend_v2/app/api/v1/digital_humans.py` 等主链路）
2. **元宇宙游戏**（backend_v2 里的 player/quest/inventory/shop/party/achievement/three_keys 模块，以及本目录的 14 份 PRD）

市场研究（筑梦岛 500 万用户 + 千万美元融资数据）和代码审计都支持收敛到方向 1。
本目录是方向 2 的完整文档归档。

## 本目录内容

- **prd-details/** — 14 份游戏化 PRD 细化文档（含世界观设计 / NPC 系统 / 核心玩法 /
  玩家系统 / 多人系统 / 经济系统 / 数据库 schema / API 设计 / 等）

## 什么情况下可能再用到

- 如果未来产品规模化到年 MRR > ¥100 万，可以重启 3D 虚拟场景 / 元宇宙方向
  （参考 [`docs/technical/HUNYUAN_INTEGRATION_PLAN.md`](../../technical/HUNYUAN_INTEGRATION_PLAN.md)）
- 游戏化的 NPC 人设模板 / 经济系统设计可能对将来的数字人商业化（卡池抽卡、剧情包）有参考价值

## 请勿

- 把本目录的内容当作**现行**需求
- 在新代码中 import 本目录引用的模块 `player / quest / inventory / ...`
  （这些路由已从 `backend_v2/app/api/v1/__init__.py` 禁用）
- 对新团队成员推荐这里的文档作为入门

## 新方向的官方文档入口

- [`docs/roadmap/DEEP_AUDIT_V3.md`](../../roadmap/DEEP_AUDIT_V3.md) — 深度审计 + P0-P3 修改清单
- [`docs/roadmap/PRODUCT_STRATEGY_V3.md`](../../roadmap/PRODUCT_STRATEGY_V3.md) — V3 战略过滤器（三车道 + 不做清单）
- [`docs/business/MindPal_深度解读.md`](../../business/MindPal_深度解读.md) — 商业计划解读

---

**归档日期**：2026-04-23（P2-1 清理游戏化代码时同步归档）
