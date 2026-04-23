@echo off
:: MindPal Multi-AI 协作快捷脚本 (Windows)
:: 用法: mp-ai <command> [args]

setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PYTHON_SCRIPT=%SCRIPT_DIR%mp-ai.py

if "%1"=="" (
    python "%PYTHON_SCRIPT%" help
    exit /b
)

python "%PYTHON_SCRIPT%" %*
