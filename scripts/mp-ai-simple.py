#!/usr/bin/env python3
"""
MindPal AI 协作脚本 (简化版)
直接调用 Codex 和 Gemini CLI，无需 CCB 终端分屏

使用方式:
    python mp-ai-simple.py codex "实现情感识别模块"
    python mp-ai-simple.py gemini "调研RAG最新技术"
    python mp-ai-simple.py both "优化对话响应延迟"
"""

import subprocess
import sys
import os

# 颜色输出
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")

def run_codex(prompt, wait=True):
    """调用 Codex CLI"""
    print(f"{Colors.GREEN}[Codex] 执行任务: {prompt[:50]}...{Colors.END}")

    cmd = ["codex", "exec", prompt] if not wait else ["codex", prompt]

    try:
        if wait:
            # 交互模式 - 使用 exec 子命令
            result = subprocess.run(
                ["codex", "exec", "-q", prompt],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=os.getcwd()
            )
            if result.stdout:
                print(f"{Colors.GREEN}[Codex 回复]{Colors.END}")
                print(result.stdout)
            if result.stderr:
                print(f"{Colors.YELLOW}[Codex 日志] {result.stderr[:200]}{Colors.END}")
            return result.returncode == 0
        else:
            # 后台执行
            subprocess.Popen(
                ["codex", prompt],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"{Colors.GREEN}[Codex] 任务已提交到后台{Colors.END}")
            return True
    except subprocess.TimeoutExpired:
        print(f"{Colors.RED}[Codex] 任务超时{Colors.END}")
        return False
    except Exception as e:
        print(f"{Colors.RED}[Codex] 错误: {e}{Colors.END}")
        return False

def run_gemini(prompt, wait=True):
    """调用 Gemini CLI"""
    print(f"{Colors.CYAN}[Gemini] 执行任务: {prompt[:50]}...{Colors.END}")

    try:
        if wait:
            result = subprocess.run(
                ["gemini", "-p", prompt],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=os.getcwd()
            )
            if result.stdout:
                print(f"{Colors.CYAN}[Gemini 回复]{Colors.END}")
                print(result.stdout)
            if result.stderr:
                print(f"{Colors.YELLOW}[Gemini 日志] {result.stderr[:200]}{Colors.END}")
            return result.returncode == 0
        else:
            subprocess.Popen(
                ["gemini", prompt],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print(f"{Colors.CYAN}[Gemini] 任务已提交到后台{Colors.END}")
            return True
    except subprocess.TimeoutExpired:
        print(f"{Colors.RED}[Gemini] 任务超时{Colors.END}")
        return False
    except Exception as e:
        print(f"{Colors.RED}[Gemini] 错误: {e}{Colors.END}")
        return False

def run_both(prompt):
    """同时调用 Codex 和 Gemini"""
    print_header(f"并行执行: {prompt}")

    # Codex 负责实现
    codex_prompt = f"作为代码实现专家，{prompt}"

    # Gemini 负责调研
    gemini_prompt = f"作为技术研究专家，{prompt}"

    print(f"{Colors.YELLOW}启动并行任务...{Colors.END}\n")

    # 简单串行执行（真正并行需要多线程）
    print(f"{Colors.GREEN}--- Codex (实现视角) ---{Colors.END}")
    run_codex(codex_prompt)

    print(f"\n{Colors.CYAN}--- Gemini (研究视角) ---{Colors.END}")
    run_gemini(gemini_prompt)

def print_help():
    help_text = """
MindPal AI 协作脚本 (简化版)
============================

用法:
    python mp-ai-simple.py <ai> <prompt>

AI选项:
    codex     使用 Codex (代码实现专家)
    gemini    使用 Gemini (技术研究专家)
    both      同时使用两者 (不同视角)

示例:
    python mp-ai-simple.py codex "实现数字人情感识别模块"
    python mp-ai-simple.py gemini "调研2024年RAG最新技术"
    python mp-ai-simple.py both "优化对话响应延迟"

快捷方式:
    研究类任务 → gemini
    实现类任务 → codex
    多角度分析 → both
"""
    print(help_text)

def main():
    if len(sys.argv) < 2:
        print_help()
        return

    ai = sys.argv[1].lower()
    prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    if ai in ["help", "-h", "--help"]:
        print_help()
    elif ai == "codex":
        if not prompt:
            print(f"{Colors.RED}请提供任务描述{Colors.END}")
            return
        print_header(f"Codex 任务")
        run_codex(prompt)
    elif ai == "gemini":
        if not prompt:
            print(f"{Colors.RED}请提供任务描述{Colors.END}")
            return
        print_header(f"Gemini 任务")
        run_gemini(prompt)
    elif ai == "both":
        if not prompt:
            print(f"{Colors.RED}请提供任务描述{Colors.END}")
            return
        run_both(prompt)
    else:
        print(f"{Colors.RED}未知AI: {ai}{Colors.END}")
        print_help()

if __name__ == "__main__":
    main()
