# 首次上线 · 阿里云 ECS 全流程检查表

> 这是一个**手动**检查表 — 你照着一项一项做。
> 自动化部署用 [deploy/aliyun-bootstrap.sh](../../deploy/aliyun-bootstrap.sh)，但 **prereq 必须手动完成**。
>
> 部署目标（来自项目 memory）：阿里云 ECS · `aliyun-lc-server-43` · `8.136.34.43`
>
> ⚠ 全程**不要**把密码贴到 shell history / git / chat。需要密码时只在登录窗口输入一次。

---

## P0 · 安全凭证（10 分钟）

- [ ] **改阿里云账号 `lc-opc-dev` 密码** — 之前那个密码在 chat 里泄露过，必须立即改
  - 控制台 → 账号管理 → 修改密码
- [ ] **改 ECS root 密码** — 同样泄露过，必须改
  - 阿里云控制台 → ECS → 实例 → 重置实例密码（需要重启实例）
- [ ] 给 ECS 配置**安全组**
  - 入方向：22（SSH，限你的本地 IP）+ 80/443（外部访问）
  - 不要开 5432/6379/6333 给公网（这些是 docker 内部走）

---

## P1 · SSH 公钥免密（5 分钟）

> 让 `aliyun-bootstrap.sh` 能从你本地 ssh 进生产机不用输密码。

在你**本地** `/home/yake/MindPal` 这台机器上：

```bash
# 1) 看看有没有现成的公钥
ls ~/.ssh/id_*.pub 2>/dev/null

# 2) 没有就生成一个
ssh-keygen -t ed25519 -C "yake@local-dev"
# 一路回车，passphrase 可留空（自动化用）也可设密（更安全 + 走 ssh-agent）

# 3) 把公钥推到生产机（这一步会**最后一次**输 root 密码）
ssh-copy-id root@8.136.34.43

# 4) 测试免密能不能跑
ssh root@8.136.34.43 'echo ok && hostname'
```

期望最后一步直接打印 `ok` + `aliyun-lc-server-43`，不再问密码。

可选：在本地 `~/.ssh/config` 加个 alias，方便后续：

```
Host aliyun-mindpal
    HostName 8.136.34.43
    User root
    IdentityFile ~/.ssh/id_ed25519
```

---

## P2 · 生产机基础环境（10 分钟）

通过 `ssh root@8.136.34.43` 登录后跑：

```bash
# Docker + docker compose v2
which docker || curl -fsSL https://get.docker.com | sh
docker compose version || apt-get update && apt-get install -y docker-compose-plugin

# git
which git || apt-get install -y git

# 工作目录
mkdir -p /opt/mindpal /var/log/mindpal

# 时区（生成主动消息按 10:00 跑，需要正确时区）
timedatectl set-timezone Asia/Shanghai
date  # 检查是不是 CST
```

---

## P3 · `.env` 真实密钥（10 分钟，**最容易遗漏**）

`.env` **不在仓库里**（被 .gitignore），需要生产手动创建。

```bash
ssh root@8.136.34.43
mkdir -p /opt/mindpal/backend_v2
nano /opt/mindpal/backend_v2/.env
```

**最简方式** — 用仓库里的模板：

```bash
cp /opt/mindpal/backend_v2/.env.example /opt/mindpal/backend_v2/.env
nano /opt/mindpal/backend_v2/.env
```

[backend_v2/.env.example](../../backend_v2/.env.example) 已经覆盖所有字段。生产改 4 个就够：

| 字段 | 怎么改 |
|---|---|
| `DEBUG` | 设 `false`（生产硬性要求） |
| `SECRET_KEY` | `openssl rand -hex 32` 随机生成。**保管好** — 一旦换所有用户被踢下线 |
| `DATABASE_URL` | docker compose 默认即 `postgresql+asyncpg://mindpal:mindpal123@postgres:5432/mindpal`，**生产必须**改 postgres 密码 |
| `ALLOWED_ORIGINS` | 生产域名 JSON 数组：`["https://your-domain.com"]`（不能用 `*`） |
| `DASHSCOPE_API_KEY` | 去 [阿里云 DashScope 控制台](https://dashscope.console.aliyun.com/) 拿真 key |

**必填**字段（缺会启动失败）：上表 4 个。

**进阶**字段（按需启用）：
- `ANTHROPIC_API_KEY` — Claude 备份通道
- `ALIPAY_APP_ID/PRIVATE_KEY/PUBLIC_KEY/ALIPAY_PUBLIC_KEY` — 支付要用
- `ALIYUN_ACCESS_KEY_ID/SECRET` + `MODERATION_ALIYUN_ENABLED=true` — 阿里云绿网内容审核
- `CRISIS_WEBHOOK_URL` — 危机告警推送（slack/dingtalk/feishu/wechat_work）

⚠ `SECRET_KEY` 一旦切换所有用户被强制重新登录。生产不要再随便重新生成。
⚠ config.py `validate_security_defaults` 会在 DEBUG=false 且 SECRET_KEY 是默认值时**直接拒绝启动**。

---

## P4 · 用 bootstrap.sh 拉首次部署（5 分钟）

回到本地 `/home/yake/MindPal/`：

```bash
# init 会：clone 仓库到生产 → docker build → 起 postgres/redis/qdrant → 跑 migration → 起 backend + proactive_worker
./deploy/aliyun-bootstrap.sh init
```

它会先问 `yes/N` 确认，再开始动手。

---

## P5 · 上线后验证（10 分钟）

```bash
# 在本地
./deploy/aliyun-bootstrap.sh status
```

应该看到：

```
NAME                       STATUS         PORTS
mindpal_backend_v2        Up (healthy)
mindpal_postgres          Up (healthy)
mindpal_redis             Up (healthy)
mindpal_qdrant            Up
mindpal_proactive_worker  Up
```

然后从浏览器访问：

```
http://8.136.34.43:8000/docs    # OpenAPI 自动文档
```

确认能看到（在路由列表里）：
- `/api/v1/auth/*`
- `/api/v1/digital-humans/*`
- `/api/v1/proactive/*` ← 新
- `/api/v1/cp/*` ← 新
- `/api/v1/account/quota` ← 新

---

## P6 · 前端部署（如果还没做）

前端是纯静态文件，可以：

**方案 A**：托管到阿里云 OSS + CDN（推荐生产）
**方案 B**：放在同一台 ECS 用 nginx 服务

`nginx.conf` 已经在 repo 根，参考它配置：把 `frontend/` 目录指给 nginx。

---

## P6.5 · GitHub Actions 自动部署（推荐 · 一次配完终身受益）

让 push 到 master 自动调 `bootstrap.sh update` + smoketest。

仓库 → **Settings → Secrets and variables → Actions** → `New repository secret`：

| Secret 名 | 值 | 怎么拿 |
|---|---|---|
| `SSH_PRIVATE_KEY` | 你**本地**那对部署 key 的私钥（**完整**，含 `-----BEGIN... -----END...`）| `cat ~/.ssh/id_ed25519` |
| `SSH_HOST_KEY` | 生产机的 SSH host key 指纹（防 MITM） | `ssh-keyscan -H 8.136.34.43` 整段粘贴 |
| `PROD_HOST` | `root@8.136.34.43` | 直接填（不是密码） |

加完之后：
- push 到 master 触发自动 update + smoketest
- Actions 页 → Run workflow 可以手动跑 `update / migrate / smoketest`
- 工作流 [.github/workflows/deploy.yml](../../.github/workflows/deploy.yml) **不会**跑 `init`（首次部署必须人工）

⚠ `SSH_PRIVATE_KEY` 一旦泄露，攻击者就拿到了你的生产 root。强烈建议给 CI 单独建一对 ed25519 key（不要复用你本地登录用的 key），并在 ECS 上用 `~/.ssh/authorized_keys` 加 `from="<github-runner-cidr>"` 限制 IP（可选）。

## P7 · 域名 + HTTPS（可选，**算法备案**前要）

- [ ] 阿里云控制台买域名，做 ICP 备案
- [ ] 域名解析到 8.136.34.43
- [ ] 申请 SSL 证书（阿里云 SSL 服务有免费的）
- [ ] nginx 配置 SSL，强制 HTTPS

---

## 下次部署（日常更新）

```bash
# 改完代码 → 推 GitHub → 在本地：
./deploy/aliyun-bootstrap.sh update

# 只跑新表 migration（如果新版本加了表）：
./deploy/aliyun-bootstrap.sh migrate
```

---

## 常见问题排查

### bootstrap.sh 报 "SSH 公钥免密未生效"

P1 没做完。重做 `ssh-copy-id` 那步，确认 `ssh root@8.136.34.43 'echo ok'` 不需要输密码。

### `.env` 里 JWT_SECRET_KEY 留空 → 启动报 500

`app/config.py` 用 pydantic-settings 检查，留空会直接拒绝启动。看 `docker compose logs backend | head -20`。

### proactive_worker 起来了但没生成消息

```bash
./deploy/aliyun-bootstrap.sh logs proactive
```

容器是用 `sleep 到下个 10:00 → 跑 → 再 sleep` 的循环。第一次启动后**不会马上跑**，要等下一个 10 点。如果想立即跑一次：

```bash
ssh root@8.136.34.43 'cd /opt/mindpal/backend_v2 && docker compose run --rm backend python -m scripts.generate_proactive_messages'
```

### CP 邀请接受后还看不到对方的 DH

是因为 dh-list 端点没扩展 partner 视图，只 GET /digital-humans/{id} 改过。partner 接受后给的 chat URL 直接打开应该能用。如果想让"我加入的 CP TA"出现在我的 dh-list 里，需要再加一个 `GET /api/v1/digital-humans?include_cp=1` —— 这是 next iteration 的事。
