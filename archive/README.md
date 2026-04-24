# 🗄️ Archive · 已归档代码与文档

> ⚠️ **本目录所有内容都是历史遗留**，不是项目的现行组成部分。

## 当前归档内容

### [`backend-flask-mvp/`](backend-flask-mvp/) — Flask MVP 版本（P2-2 归档）

2026 年 4 月归档。原位置 `backend/`。

**为什么归档**：MindPal 项目经历过 Flask → FastAPI 的重构。新主线 `backend_v2/`
（FastAPI + async）已完成所有关键能力迁移：

- 认证 JWT
- 数字人 CRUD
- 流式对话（含 crisis / emotion / memory / quota pipeline，见 DEEP_AUDIT_V3 P0）
- 知识库 RAG（待）
- 订阅系统（含 Alipay 真接入，见 DEEP_AUDIT_V3 P0-3）
- 埋点

Flask 版本保留只是为了**历史参考**（FAISS RAG 实现、初期 API 设计思路）。

**注意**:

- 不要在 `backend-flask-mvp/` 写新代码
- 生产部署用 `backend_v2/`，docker-compose.yml 已指向那里
- 原 `Dockerfile.backend` 是指向 Flask 版本的孤立文件，本次归档时一并删除

### 归档策略说明

采用 `git mv` 而非 `rm -rf`，保留完整 git 历史。如果将来要追溯：

```bash
git log --follow archive/backend-flask-mvp/app/app.py
git blame archive/backend-flask-mvp/app/routes/chat.py
```

仍能看到文件在原路径下的所有提交。

## 其他归档

- [`legacy-game-pivot/`](../docs/archive/legacy-game-pivot/) · 游戏化方向 PRD（P2-1 归档，位于 docs 下）

---

**归档规范**：新增归档内容时同步更新本 README 的"当前归档内容"章节。
