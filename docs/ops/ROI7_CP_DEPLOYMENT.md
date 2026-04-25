# ROI-7（主动消息）+ C2（CP 双人共养）上线手册

> 本文档对应 commits `ef833a2`（ROI-7）+ `fadd40e`（C2 CP）。
> 上线前请把这份手册过一遍，按 step 一项一项做。

## 一、新增数据表（必做 · 不做就 500）

### 表清单

| 表名 | 模型 | 用途 |
|---|---|---|
| `proactive_messages` | [models/proactive.py](../../backend_v2/app/models/proactive.py) | 主动消息池，每天 cron 生成 |
| `cp_invitations` | [models/cp.py](../../backend_v2/app/models/cp.py) | CP 邀请码（6 位，TTL 7 天） |
| `cp_bonds` | [models/cp.py](../../backend_v2/app/models/cp.py) | 已建立的双人绑定关系 |

### 执行

```bash
cd backend_v2
python -m scripts.create_proactive_cp_tables
```

期望输出：

```
[migrate] starting create_proactive_cp_tables
  ✓ proactive_messages
  ✓ cp_invitations
  ✓ cp_bonds
[migrate] done
```

幂等：`Base.metadata.create_all` 对已存在的表跳过，可以重复跑。

### 回滚

如果需要回滚（只在 staging）：

```sql
DROP TABLE IF EXISTS cp_bonds;
DROP TABLE IF EXISTS cp_invitations;
DROP TABLE IF EXISTS proactive_messages;
```

⚠ 生产环境**不要**回滚 — 会丢用户已收到但没读的主动消息和 CP 关系数据。

---

## 二、定时任务 · ROI-7 主动消息生成器

每天给活跃用户的活跃数字人最多生成 3 条主动消息，由 chat 进入时一次性推送。

### 方案 A · docker-compose（推荐）

[backend_v2/docker-compose.yml](../../backend_v2/docker-compose.yml) 已新增 `proactive_worker` 服务：

```yaml
proactive_worker:
  command: 守护循环：sleep 到下个 10:00 → 跑 → 再 sleep
  restart: unless-stopped
```

启动：

```bash
cd backend_v2
docker compose up -d proactive_worker
docker compose logs -f proactive_worker
```

期望日志（首次启动）：

```
[proactive_worker] sleeping XXXX seconds until next 10:00
```

### 方案 B · 系统 cron（无 docker 部署）

```bash
sudo crontab -e
```

加这一行（每天 10:00）：

```
0 10 * * * /opt/mindpal/backend_v2/scripts/cron-proactive.sh >> /var/log/mindpal/proactive.log 2>&1
```

[cron-proactive.sh](../../backend_v2/scripts/cron-proactive.sh) 内置环境变量推断，把 `MINDPAL_ROOT` / `MINDPAL_PYTHON` 设成你的实际路径即可。

### 方案 C · systemd timer（更现代）

`/etc/systemd/system/mindpal-proactive.service`:

```ini
[Unit]
Description=MindPal proactive message generator
After=network.target postgresql.service

[Service]
Type=oneshot
User=mindpal
WorkingDirectory=/opt/mindpal/backend_v2
Environment="MINDPAL_PYTHON=/opt/mindpal/venv/bin/python"
ExecStart=/opt/mindpal/backend_v2/scripts/cron-proactive.sh
StandardOutput=append:/var/log/mindpal/proactive.log
StandardError=append:/var/log/mindpal/proactive.log
```

`/etc/systemd/system/mindpal-proactive.timer`:

```ini
[Unit]
Description=Daily ROI-7 proactive message run
[Timer]
OnCalendar=*-*-* 10:00:00
Persistent=true
[Install]
WantedBy=timers.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mindpal-proactive.timer
sudo systemctl list-timers | grep proactive
```

---

## 三、上线后冒烟检查（每个环境必做一次）

### 1. 数据库结构对吗？

```bash
psql $DATABASE_URL -c "\d proactive_messages"
psql $DATABASE_URL -c "\d cp_invitations"
psql $DATABASE_URL -c "\d cp_bonds"
```

期望看到列：`is_acked`, `expires_at`, `code`, `status` 等。

### 2. 路由活了吗？

```bash
# 主动消息
curl -H "Authorization: Bearer $JWT" $API/api/v1/proactive/mine | jq

# CP
curl -H "Authorization: Bearer $JWT" $API/api/v1/cp/bonds | jq
```

第一次拉应该返回 `{code: 0, data: {items: []}}`。

### 3. cron 真的跑了吗？

```bash
# 方案 A
docker compose logs proactive_worker | tail -50

# 方案 B/C
tail -50 /var/log/mindpal/proactive.log
```

应该看到形如 `[proactive] done: total_dhs=X generated=Y skipped=Z` 的输出。

### 4. 端到端体验

1. 用一个 7 天没登录的账号登录
2. 进 `dh-list.html`，第一时间应该看到红点徽标（脉动 1.6s）
3. 点进 chat → 顶部插入 1-3 条「TA 想你了」气泡
4. 进 chat 时主动消息自动 ack（再回到 dh-list 红点消失）

---

## 四、需要监控的关键指标

| 指标 | 目标 | 出问题的可能原因 |
|---|---|---|
| `proactive_messages` 每天生成量 | 100-1000+ 条/天（看活跃 DH 数） | 0 = cron 没跑；爆量 = 重复生成（generator 去重失效） |
| 主动消息 `delivered/created` 比例 | > 70% | 用户不打开 chat（可能要再加红点入口曝光） |
| 主动消息 `acked/delivered` 比例 | > 90% | 进 chat 后未自动 ack（前端 bug） |
| CP `cp_invitations.accepted` 占 `pending` 比 | > 30% | 接受流程卡（前端 prompt UX 太弱） |
| 同一 `dh_id` 多条 active `cp_bonds` | 必须 = 0 | 后端 409 校验失效（数据腐烂） |

---

## 五、回退与降级

### 紧急关闭 ROI-7

最快：停 worker，用户进 chat 时 `pushProactiveMessages()` 拿到空数组，无副作用。

```bash
docker compose stop proactive_worker
# 或
sudo systemctl disable --now mindpal-proactive.timer
```

已生成的 `proactive_messages` 还会被前端拉到 — 如果要立刻消音：

```sql
UPDATE proactive_messages
SET is_dismissed = true
WHERE is_acked = false AND is_dismissed = false;
```

### 紧急关闭 CP

把 `/api/v1/cp` 整个 router 从 [api/v1/__init__.py](../../backend_v2/app/api/v1/__init__.py) 注释掉，重启 backend。前端 dh-list 调用会 404 但被 try/catch 兜底，不影响主流程。

---

## 六、相关文件索引

后端：
- [backend_v2/app/models/proactive.py](../../backend_v2/app/models/proactive.py)
- [backend_v2/app/models/cp.py](../../backend_v2/app/models/cp.py)
- [backend_v2/app/services/proactive/generator.py](../../backend_v2/app/services/proactive/generator.py)
- [backend_v2/app/api/v1/proactive.py](../../backend_v2/app/api/v1/proactive.py)
- [backend_v2/app/api/v1/cp.py](../../backend_v2/app/api/v1/cp.py)
- [backend_v2/scripts/create_proactive_cp_tables.py](../../backend_v2/scripts/create_proactive_cp_tables.py)
- [backend_v2/scripts/generate_proactive_messages.py](../../backend_v2/scripts/generate_proactive_messages.py)
- [backend_v2/scripts/cron-proactive.sh](../../backend_v2/scripts/cron-proactive.sh)

前端：
- [frontend/dh-list.html](../../frontend/dh-list.html) — 红点徽标 + CP 邀请/接受
- [frontend/chat.html](../../frontend/chat.html) — 主动消息推送
- [frontend/js/api.js](../../frontend/js/api.js) — `MindPalAPI.proactive` / `MindPalAPI.cp`

文档：
- 本文档
- [docs/roadmap/PRODUCT_POLISH_V4.md](../roadmap/PRODUCT_POLISH_V4.md) — V4 路线图
