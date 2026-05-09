#!/usr/bin/env bash
# MindPal · 阿里云生产环境一键部署 / 升级脚本
#
# 设计原则：
#   - 从你的**本地**机器跑（不在生产机执行）
#   - 完全幂等：可以反复跑，不会破坏已部署的状态
#   - 不存任何明文密码：所有 SSH 走公钥免密
#   - 不下任何破坏性命令：rm/drop/down 都需要明示
#
# 前置条件（**首次部署前**必须做完，详见 docs/ops/FIRST_DEPLOY_CHECKLIST.md）：
#   1. 你的 SSH 公钥（~/.ssh/id_rsa.pub 或 id_ed25519.pub）已加到生产机的
#      /root/.ssh/authorized_keys
#   2. 生产机已装 docker + docker compose v2 + git
#   3. 生产机 /opt/mindpal/ 已是 clone 后的 git 仓库（首次用 ./deploy/aliyun-bootstrap.sh init）
#   4. 生产机 /opt/mindpal/backend_v2/.env 已配好真实密钥（不在仓库里）
#
# 用法：
#   ./deploy/aliyun-bootstrap.sh init            首次部署（会拉代码 + 建表 + 起服务）
#   ./deploy/aliyun-bootstrap.sh update          常规升级（git pull + docker rebuild + restart）
#   ./deploy/aliyun-bootstrap.sh migrate         只跑 migration（建新表）
#   ./deploy/aliyun-bootstrap.sh status          查看 backend / proactive_worker 状态
#   ./deploy/aliyun-bootstrap.sh logs            tail backend 日志
#   ./deploy/aliyun-bootstrap.sh logs proactive  tail proactive_worker 日志
#
# 环境变量覆盖：
#   PROD_HOST     默认 root@8.136.34.43
#   PROD_PATH     默认 /opt/mindpal
#   GIT_REMOTE    默认 https://github.com/licong-git-dev/MindPal.git
#   GIT_BRANCH    默认 master

set -euo pipefail

PROD_HOST="${PROD_HOST:-root@8.136.34.43}"
PROD_PATH="${PROD_PATH:-/opt/mindpal}"
GIT_REMOTE="${GIT_REMOTE:-https://github.com/licong-git-dev/MindPal.git}"
GIT_BRANCH="${GIT_BRANCH:-master}"

CMD="${1:-help}"

color() { printf '\033[%sm%s\033[0m\n' "$1" "$2"; }
ok()    { color '32' "✓ $*"; }
info()  { color '36' "→ $*"; }
warn()  { color '33' "⚠ $*"; }
die()   { color '31' "✗ $*"; exit 1; }

# 远程执行包装：所有动作过 ssh，失败即终止
remote() {
  ssh -o BatchMode=yes -o ConnectTimeout=10 "$PROD_HOST" "$@"
}

# 远程检查 SSH 公钥是否能免密登录
check_ssh() {
  info "checking SSH access to $PROD_HOST..."
  if ! remote 'echo ok' >/dev/null 2>&1; then
    die "SSH 公钥免密未生效。请先把本地 ~/.ssh/id_*.pub 的内容追加到 $PROD_HOST 的 /root/.ssh/authorized_keys，详见 docs/ops/FIRST_DEPLOY_CHECKLIST.md"
  fi
  ok "SSH ready"
}

cmd_help() {
  cat <<EOF
MindPal · 阿里云部署脚本

  init      首次部署（克隆 + 建表 + 启动）
  update    日常升级（pull + rebuild + restart）
  migrate   只跑 migration（建表脚本，幂等）
  smoketest 上线后冒烟：curl 5 个关键端点 + 检查 worker 进程
  status    服务状态
  logs [proactive]   日志
  shell     直接 SSH 进生产机交互（你来执行）

环境变量：
  PROD_HOST=$PROD_HOST
  PROD_PATH=$PROD_PATH
  GIT_REMOTE=$GIT_REMOTE
  GIT_BRANCH=$GIT_BRANCH
EOF
}

cmd_init() {
  check_ssh
  warn "init 会在 $PROD_HOST 上创建 $PROD_PATH 并克隆仓库（如果不存在）。"
  warn "数据库 / Redis / Qdrant 都会通过 docker-compose 启动。"
  read -r -p "继续？(yes/N) " ans
  [[ "$ans" == "yes" ]] || die "aborted"

  remote bash -se <<EOF
set -euo pipefail
mkdir -p '$PROD_PATH' /var/log/mindpal
cd '$PROD_PATH'
if [ ! -d .git ]; then
  echo "[init] cloning $GIT_REMOTE..."
  git clone -b $GIT_BRANCH '$GIT_REMOTE' .
else
  echo "[init] repo already exists, skip clone"
fi

if [ ! -f backend_v2/.env ]; then
  echo "[init] WARNING: backend_v2/.env 不存在，请先填好再继续。"
  echo "       参考 backend_v2/.env.example（如有），或者手动创建包含："
  echo "         DATABASE_URL=..."
  echo "         JWT_SECRET_KEY=..."
  echo "         REDIS_URL=..."
  echo "         （以及阿里云 / Anthropic API key 等）"
  exit 2
fi

cd backend_v2
echo "[init] building docker images..."
docker compose build
echo "[init] starting infra (postgres/redis/qdrant)..."
docker compose up -d postgres redis qdrant
echo "[init] waiting 10s for db to be ready..."
sleep 10
echo "[init] running migrations..."
docker compose run --rm backend python -m scripts.create_dh_tables || true
docker compose run --rm backend python -m scripts.create_proactive_cp_tables
docker compose run --rm backend python -m scripts.seed_products || true
echo "[init] starting backend + proactive_worker + frontend..."
docker compose up -d backend proactive_worker frontend
docker compose ps
EOF
  ok "init done. 验证："
  cmd_status
}

cmd_update() {
  check_ssh
  info "git pull + docker rebuild + restart..."
  remote bash -se <<EOF
set -euo pipefail
cd '$PROD_PATH'
echo "[update] pulling latest..."
git fetch --all
git checkout $GIT_BRANCH
git pull --ff-only origin $GIT_BRANCH
cd backend_v2
echo "[update] rebuilding..."
docker compose build backend proactive_worker frontend
echo "[update] restarting..."
docker compose up -d backend proactive_worker frontend
docker compose ps
EOF
  ok "update done"
}

cmd_migrate() {
  check_ssh
  info "running create_proactive_cp_tables（幂等，可重复）..."
  remote bash -se <<EOF
set -euo pipefail
cd '$PROD_PATH/backend_v2'
docker compose run --rm backend python -m scripts.create_proactive_cp_tables
EOF
  ok "migrate done"
}

cmd_status() {
  check_ssh
  remote bash -se <<EOF
set -euo pipefail
cd '$PROD_PATH/backend_v2'
docker compose ps
echo
echo "--- backend health ---"
curl -fsS http://localhost:8000/health 2>/dev/null || echo "(health endpoint not reachable from within prod machine)"
EOF
}

cmd_logs() {
  check_ssh
  local svc="${1:-backend}"
  case "$svc" in
    backend|proactive|proactive_worker) ;;
    *) die "unknown service: $svc (expected backend or proactive)" ;;
  esac
  [[ "$svc" == "proactive" ]] && svc="proactive_worker"
  info "tailing $svc logs (Ctrl-C to exit)..."
  remote bash -se <<EOF
cd '$PROD_PATH/backend_v2'
docker compose logs --tail 200 -f $svc
EOF
}

cmd_shell() {
  check_ssh
  warn "进入生产机交互式 shell。注意一切操作都是真的。"
  ssh "$PROD_HOST"
}

# F4 · 上线后冒烟
# 走 ssh 在生产机内 curl localhost:8000，避免被 nginx / 安全组干扰判断真实状态
cmd_smoketest() {
  check_ssh
  info "running smoketest on $PROD_HOST..."
  remote bash -se <<'EOF'
set -uo pipefail   # 不要 -e: 单点失败不要中断整体冒烟，用打印总结
RC=0
PASS=0
FAIL=0

color() { printf '\033[%sm%s\033[0m\n' "$1" "$2"; }
oks()    { color '32' "  ✓ $*"; PASS=$((PASS+1)); }
fails()  { color '31' "  ✗ $*"; FAIL=$((FAIL+1)); RC=1; }

cd /opt/mindpal/backend_v2 2>/dev/null || { color 31 "✗ /opt/mindpal/backend_v2 不存在 — 先跑 init"; exit 2; }

color 36 "[1/6] docker compose 进程"
ps_out=$(docker compose ps --format json 2>/dev/null || true)
for svc in postgres redis qdrant backend proactive_worker frontend; do
  if echo "$ps_out" | grep -q "\"Service\":\"$svc\".*\"State\":\"running\""; then
    oks "$svc up"
  else
    fails "$svc not running"
  fi
done

color 36 "[2/6] backend /docs (OpenAPI 自动文档)"
http=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/docs || echo 000)
if [ "$http" = "200" ]; then oks "/docs → 200"; else fails "/docs → $http (期望 200)"; fi

color 36 "[3/6] backend /openapi.json 含新路由"
oa=$(curl -s http://localhost:8000/openapi.json || true)
for path in '/api/v1/proactive/mine' '/api/v1/cp/bonds' '/api/v1/account/quota'; do
  if echo "$oa" | grep -q "\"$path\""; then oks "$path 已注册"; else fails "$path 缺失"; fi
done

color 36 "[4/6] frontend (nginx) 出 200"
http=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:80/ || echo 000)
if [ "$http" = "200" ] || [ "$http" = "304" ]; then oks "/ → $http"; else fails "/ → $http (期望 200/304)"; fi
http=$(curl -s -o /dev/null -w '%{http_code}' http://localhost:80/api/v1/auth/health 2>/dev/null || echo 000)
# 反代是否打通：404 也算 OK（端点不存在是后端的事，nginx 至少接到了）
if [ "$http" != "000" ]; then oks "nginx → backend 反代联通 (got $http)"; else fails "nginx → backend 不通"; fi

color 36 "[5/6] 数据库表"
tables=$(docker compose exec -T postgres psql -U mindpal -d mindpal -tA -c "SELECT tablename FROM pg_tables WHERE schemaname='public';" 2>/dev/null || echo "")
for tbl in users digital_humans dh_messages proactive_messages cp_invitations cp_bonds; do
  if echo "$tables" | grep -qx "$tbl"; then oks "table $tbl"; else fails "table $tbl 缺失"; fi
done

color 36 "[6/6] proactive_worker 心跳"
last=$(docker compose logs --tail 50 proactive_worker 2>/dev/null | tail -10 | grep -E 'sleeping|done|FAIL' | tail -1 || true)
if [ -n "$last" ]; then oks "proactive_worker 最近一行: ${last:0:80}"; else fails "proactive_worker 无近期日志"; fi

echo ""
color 36 "==== 总结 ===="
[ "$FAIL" -eq 0 ] && color 32 "✓ ALL PASS ($PASS checks)" || color 31 "✗ FAIL=$FAIL  PASS=$PASS"
exit $RC
EOF
  rc=$?
  if [ $rc -eq 0 ]; then
    ok "smoketest passed"
  else
    die "smoketest failed (rc=$rc)"
  fi
}

case "$CMD" in
  init)       cmd_init ;;
  update)     cmd_update ;;
  migrate)    cmd_migrate ;;
  smoketest)  cmd_smoketest ;;
  status)     cmd_status ;;
  logs)       cmd_logs "${2:-backend}" ;;
  shell)      cmd_shell ;;
  help|*)     cmd_help ;;
esac
