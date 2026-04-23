#!/bin/bash
# MindPal Multi-AI 协作快捷脚本 (Linux/macOS/WSL)
# 用法: mp-ai <command> [args]

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/mp-ai.py"

if [ -z "$1" ]; then
    python3 "$PYTHON_SCRIPT" help
    exit 0
fi

python3 "$PYTHON_SCRIPT" "$@"
