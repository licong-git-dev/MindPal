#!/usr/bin/env python3
"""
MindPal Multi-AI 协作脚本
用于快速调度 Claude + Codex + Gemini 三体协作

使用方式:
    python mp-ai.py research "调研RAG最新技术"
    python mp-ai.py implement "实现情感识别模块"
    python mp-ai.py review backend/chat_engine.py
    python mp-ai.py optimize "对话响应延迟"
    python mp-ai.py workflow dialogue_engine
"""

import subprocess
import sys
import json
import os
from pathlib import Path

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

def print_step(step_num, text, ai=""):
    ai_colors = {
        "claude": Colors.BLUE,
        "codex": Colors.GREEN,
        "gemini": Colors.CYAN
    }
    color = ai_colors.get(ai.lower(), Colors.YELLOW)
    print(f"{color}[Step {step_num}] {text}{Colors.END}")

def run_command(cmd, description=""):
    """执行命令并返回结果"""
    if description:
        print(f"{Colors.YELLOW}>>> {description}{Colors.END}")
    print(f"{Colors.CYAN}$ {cmd}{Colors.END}")

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        if result.stdout:
            print(result.stdout)
        if result.returncode != 0 and result.stderr:
            print(f"{Colors.RED}Error: {result.stderr}{Colors.END}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"{Colors.RED}Command timed out{Colors.END}")
        return False
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.END}")
        return False

def check_ccb_status():
    """检查 CCB 状态"""
    print_header("检查多AI环境状态")

    # 检查 ccb 命令是否可用
    result = subprocess.run("ccb version", shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"{Colors.RED}CCB 未安装或不可用{Colors.END}")
        print(f"请先运行: cd claude_code_bridge-main && .\\install.ps1")
        return False

    print(f"{Colors.GREEN}CCB 版本: {result.stdout.strip()}{Colors.END}")

    # 检查各AI状态
    run_command("ccb status", "检查AI连接状态")
    return True

def research(topic):
    """技术调研 - Gemini 主导"""
    print_header(f"技术调研: {topic}")
    print_step(1, f"Gemini 开始调研: {topic}", "gemini")
    run_command(f'gask-w "请深入调研以下主题，提供2024年最新信息和最佳实践：{topic}"')

def implement(feature):
    """功能实现 - Codex 主导"""
    print_header(f"功能实现: {feature}")
    print_step(1, f"Codex 开始实现: {feature}", "codex")
    run_command(f'cask-w "请实现以下功能，遵循最佳实践，包含完整的类型提示和文档：{feature}"')

def review(file_path):
    """代码审查 - 三方并行"""
    print_header(f"代码审查: {file_path}")

    print_step(1, "启动并行审查...", "claude")

    # 并行审查
    print_step(2, f"Codex 审查代码质量和性能", "codex")
    run_command(f'cask "审查 {file_path} 的代码质量：命名规范、代码复杂度、性能瓶颈、可维护性"')

    print_step(3, f"Gemini 审查安全性和最佳实践", "gemini")
    run_command(f'gask "审查 {file_path} 的安全性：SQL注入、XSS、敏感数据泄露、以及行业最佳实践"')

    print(f"\n{Colors.YELLOW}等待审查结果...{Colors.END}")
    print(f"使用 'cpend' 查看 Codex 审查结果")
    print(f"使用 'gpend' 查看 Gemini 审查结果")

def optimize(target):
    """性能优化 - 迭代协作"""
    print_header(f"性能优化: {target}")

    print_step(1, f"Codex 分析性能瓶颈", "codex")
    run_command(f'cask-w "分析 {target} 的性能瓶颈，提供具体的优化建议和实现方案"')

    print_step(2, f"Gemini 调研优化最佳实践", "gemini")
    run_command(f'gask-w "调研 {target} 相关的性能优化最佳实践和行业案例"')

def workflow(workflow_name):
    """执行预定义工作流"""

    # 加载配置
    config_path = Path(__file__).parent.parent / ".ccb-config.json"
    if not config_path.exists():
        print(f"{Colors.RED}配置文件不存在: {config_path}{Colors.END}")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    workflows = config.get("workflows", {})

    if workflow_name not in workflows:
        print(f"{Colors.RED}未知工作流: {workflow_name}{Colors.END}")
        print(f"可用工作流: {', '.join(workflows.keys())}")
        return

    wf = workflows[workflow_name]
    print_header(f"执行工作流: {wf['description']}")

    for i, step in enumerate(wf['steps'], 1):
        ai, task = step.split(': ', 1)
        print_step(i, task, ai)

        if ai == "gemini":
            run_command(f'gask-w "{task}"')
        elif ai == "codex":
            run_command(f'cask-w "{task}"')
        else:
            print(f"{Colors.BLUE}[Claude] {task}{Colors.END}")
            print(f"{Colors.YELLOW}(需要人工介入完成此步骤){Colors.END}")

        print()

def dialogue_engine():
    """数字人对话引擎开发工作流"""
    print_header("数字人对话引擎开发")

    steps = [
        ("gemini", "调研对话框架", "对比分析 LangChain vs LlamaIndex vs 自研方案 在数字人对话场景的优劣"),
        ("gemini", "调研情感识别", "调研2024年最新的对话情感识别方案，包括模型选择和部署方案"),
        ("codex", "实现DialogueManager", "实现 DialogueManager 类，包含状态机、上下文管理、多轮对话支持"),
        ("codex", "实现IntentClassifier", "实现 IntentClassifier 意图分类器，支持陪伴/知识/购物/闲聊等意图"),
        ("codex", "实现EmotionAnalyzer", "实现 EmotionAnalyzer 情感分析器，支持文本和语音情感识别"),
    ]

    for i, (ai, title, task) in enumerate(steps, 1):
        print_step(i, title, ai)
        if ai == "gemini":
            run_command(f'gask-w "{task}"')
        elif ai == "codex":
            run_command(f'cask-w "{task}"')
        print()

def rag_system():
    """知识库RAG系统开发工作流"""
    print_header("知识库RAG系统开发")

    steps = [
        ("gemini", "调研RAG技术", "调研2024年RAG最新进展：HyDE、Self-RAG、CRAG等技术的原理和适用场景"),
        ("gemini", "对比向量模型", "对比 BGE vs M3E vs OpenAI Embedding 在中文知识库场景的效果"),
        ("codex", "实现RAG核心", "实现 KnowledgeBaseRAG 类，支持混合检索（关键词+向量）"),
        ("codex", "实现Reranker", "实现 Reranker 重排序模块，使用 cross-encoder 提升检索准确率"),
    ]

    for i, (ai, title, task) in enumerate(steps, 1):
        print_step(i, title, ai)
        if ai == "gemini":
            run_command(f'gask-w "{task}"')
        elif ai == "codex":
            run_command(f'cask-w "{task}"')
        print()

def print_help():
    """打印帮助信息"""
    help_text = """
MindPal Multi-AI 协作脚本
==========================

用法:
    python mp-ai.py <command> [arguments]

命令:
    research <topic>      技术调研 (Gemini主导)
    implement <feature>   功能实现 (Codex主导)
    review <file>         代码审查 (三方并行)
    optimize <target>     性能优化 (迭代协作)
    workflow <name>       执行预定义工作流
    dialogue              数字人对话引擎开发工作流
    rag                   知识库RAG系统开发工作流
    status                检查多AI环境状态
    help                  显示帮助信息

示例:
    python mp-ai.py research "2024年RAG最新技术"
    python mp-ai.py implement "数字人情感识别模块"
    python mp-ai.py review backend/services/chat_service.py
    python mp-ai.py optimize "对话响应延迟"
    python mp-ai.py dialogue
    python mp-ai.py rag

预定义工作流:
    dialogue_engine       数字人对话引擎开发
    rag_system            知识库RAG系统开发
    emotion_recognition   情感识别模块开发
    code_review           代码审查流程
"""
    print(help_text)

def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1].lower()
    args = sys.argv[2:] if len(sys.argv) > 2 else []

    if command == "help" or command == "-h" or command == "--help":
        print_help()
    elif command == "status":
        check_ccb_status()
    elif command == "research":
        if not args:
            print(f"{Colors.RED}请提供调研主题{Colors.END}")
            return
        research(" ".join(args))
    elif command == "implement":
        if not args:
            print(f"{Colors.RED}请提供要实现的功能{Colors.END}")
            return
        implement(" ".join(args))
    elif command == "review":
        if not args:
            print(f"{Colors.RED}请提供要审查的文件路径{Colors.END}")
            return
        review(args[0])
    elif command == "optimize":
        if not args:
            print(f"{Colors.RED}请提供优化目标{Colors.END}")
            return
        optimize(" ".join(args))
    elif command == "workflow":
        if not args:
            print(f"{Colors.RED}请提供工作流名称{Colors.END}")
            return
        workflow(args[0])
    elif command == "dialogue":
        dialogue_engine()
    elif command == "rag":
        rag_system()
    else:
        print(f"{Colors.RED}未知命令: {command}{Colors.END}")
        print_help()

if __name__ == "__main__":
    main()
