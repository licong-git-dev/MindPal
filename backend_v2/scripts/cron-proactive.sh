#!/usr/bin/env bash
# MindPal V2 · ROI-7 主动消息 cron wrapper
#
# 在不使用 docker-compose 的部署环境（裸机 / systemd）下，把这个脚本登记到 crontab：
#
#   sudo crontab -e
#   # 每天 10:00 生成主动消息
#   0 10 * * * /opt/mindpal/backend_v2/scripts/cron-proactive.sh >> /var/log/mindpal/proactive.log 2>&1
#
# 也可以做成 systemd timer：
#   /etc/systemd/system/mindpal-proactive.service
#   /etc/systemd/system/mindpal-proactive.timer
#
# 本脚本要求：
#   - $MINDPAL_ROOT 指向 backend_v2/（如未设置，会自动从脚本路径推断）
#   - $MINDPAL_PYTHON 指向 venv 里的 python（如未设置，用 python3）

set -euo pipefail

# 推断 backend_v2 根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MINDPAL_ROOT="${MINDPAL_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
MINDPAL_PYTHON="${MINDPAL_PYTHON:-python3}"

cd "$MINDPAL_ROOT"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] proactive run starting (root=$MINDPAL_ROOT)"
"$MINDPAL_PYTHON" -m scripts.generate_proactive_messages
echo "[$(date '+%Y-%m-%d %H:%M:%S')] proactive run finished"
