#!/usr/bin/env python3
"""
MindPal Multi-AI 协作工具 (支持阿里云通义千问)
支持: 阿里云DashScope(通义千问) + Google Gemini

使用方式:
    python mp-multi-ai.py qwen "实现情感识别模块"
    python mp-multi-ai.py gemini "调研RAG最新技术"
    python mp-multi-ai.py both "优化对话响应延迟"

环境变量 (从 backend/.env 自动加载):
    DASHSCOPE_API_KEY - 阿里云DashScope API Key
    GEMINI_API_KEY - Google Gemini API Key (可选)
"""

import os
import sys
from pathlib import Path
from typing import Optional

# 自动加载 .env 文件
def load_env():
    """从 backend/.env 加载环境变量"""
    env_paths = [
        Path(__file__).parent.parent / "backend" / ".env",
        Path(__file__).parent.parent / "backend_v2" / ".env",
        Path(__file__).parent.parent / ".env",
    ]

    for env_path in env_paths:
        if env_path.exists():
            print(f"Loading env from: {env_path}")
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        if key not in os.environ:  # 不覆盖已有的
                            os.environ[key] = value
            break

load_env()

# 设置输出编码
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

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

def print_ai_response(ai_name: str, response: str, color: str):
    print(f"\n{color}{'─'*50}{Colors.END}")
    print(f"{color}{Colors.BOLD}[{ai_name}]{Colors.END}")
    print(f"{color}{'─'*50}{Colors.END}")
    print(response)
    print(f"{color}{'─'*50}{Colors.END}\n")


class MultiAI:
    def __init__(self):
        # 初始化 DashScope (通义千问)
        self.dashscope_key = os.environ.get('DASHSCOPE_API_KEY')
        if self.dashscope_key:
            try:
                import dashscope
                dashscope.api_key = self.dashscope_key
                self.dashscope = dashscope
                print(f"{Colors.GREEN}✓ DashScope (通义千问) 已配置{Colors.END}")
            except ImportError:
                print(f"{Colors.YELLOW}请安装 dashscope: pip install dashscope{Colors.END}")
                self.dashscope = None
        else:
            self.dashscope = None
            print(f"{Colors.YELLOW}警告: DASHSCOPE_API_KEY 未设置{Colors.END}")

        # 初始化 Gemini (可选)
        self.gemini_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
        if self.gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
                print(f"{Colors.GREEN}✓ Gemini 已配置{Colors.END}")
            except ImportError:
                print(f"{Colors.YELLOW}Gemini 未安装 (可选): pip install google-generativeai{Colors.END}")
                self.gemini_model = None
            except Exception as e:
                print(f"{Colors.YELLOW}Gemini 配置失败: {e}{Colors.END}")
                self.gemini_model = None
        else:
            self.gemini_model = None
            print(f"{Colors.YELLOW}提示: GEMINI_API_KEY 未设置 (可选){Colors.END}")

    def call_qwen(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """调用通义千问 API"""
        if not self.dashscope:
            return "错误: DashScope API Key 未配置"

        try:
            from dashscope import Generation
            from http import HTTPStatus

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            response = Generation.call(
                model="qwen-max",
                messages=messages,
                temperature=0.7,
                max_tokens=2000,
                result_format='message'
            )

            if response.status_code == HTTPStatus.OK:
                return response.output.choices[0].message.content
            else:
                return f"通义千问调用错误: {response.message}"
        except Exception as e:
            return f"通义千问调用错误: {str(e)}"

    def call_gemini(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """调用 Google Gemini API"""
        if not self.gemini_model:
            # 如果 Gemini 不可用，回退到通义千问
            print(f"{Colors.YELLOW}Gemini 不可用，使用通义千问代替{Colors.END}")
            return self.call_qwen(prompt, system_prompt)

        try:
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"

            response = self.gemini_model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"{Colors.YELLOW}Gemini 调用失败，回退到通义千问: {e}{Colors.END}")
            return self.call_qwen(prompt, system_prompt)

    def implement(self, task: str) -> str:
        """使用通义千问实现功能 (代码实现专家)"""
        system_prompt = """你是一位资深的Python开发工程师，专注于代码实现。
你的任务是:
1. 理解用户需求
2. 设计清晰的代码架构
3. 编写高质量、可维护的代码
4. 包含完整的类型提示和文档字符串

请直接给出实现代码，并简要说明关键设计决策。"""

        print(f"{Colors.GREEN}[通义千问] 正在实现: {task[:50]}...{Colors.END}")
        return self.call_qwen(task, system_prompt)

    def research(self, topic: str) -> str:
        """进行技术调研 (优先使用Gemini)"""
        system_prompt = """你是一位技术研究专家，擅长调研和分析最新技术趋势。
你的任务是:
1. 深入分析技术主题
2. 总结关键技术点和最佳实践
3. 对比不同方案的优缺点
4. 给出具体的实施建议

请提供结构化的调研报告。"""

        if self.gemini_model:
            print(f"{Colors.CYAN}[Gemini] 正在调研: {topic[:50]}...{Colors.END}")
            return self.call_gemini(topic, system_prompt)
        else:
            print(f"{Colors.GREEN}[通义千问] 正在调研: {topic[:50]}...{Colors.END}")
            return self.call_qwen(topic, system_prompt)

    def review(self, code_or_file: str) -> dict:
        """代码审查"""
        quality_prompt = f"""请审查以下代码，关注:
1. 代码质量和可读性
2. 性能优化建议
3. 潜在的bug和边界情况
4. 架构设计问题

代码:
{code_or_file}

请给出具体的改进建议。"""

        security_prompt = f"""请审查以下代码的安全性，关注:
1. 安全漏洞 (SQL注入、XSS等)
2. 敏感数据处理
3. 认证授权问题
4. 最佳安全实践

代码:
{code_or_file}

请给出安全审查报告。"""

        print(f"{Colors.YELLOW}启动代码审查...{Colors.END}")

        # 质量审查用通义千问
        quality_result = self.call_qwen(quality_prompt, "你是代码质量审查专家")

        # 安全审查用Gemini（如果可用）
        if self.gemini_model:
            security_result = self.call_gemini(security_prompt, "你是安全审查专家")
        else:
            security_result = self.call_qwen(security_prompt, "你是安全审查专家")

        return {
            "quality_review": quality_result,
            "security_review": security_result
        }

    def collaborate(self, task: str) -> dict:
        """双AI协作完成任务"""
        research_prompt = f"作为技术研究专家，请分析以下任务的技术要点和最佳实践:\n{task}"
        implement_prompt = f"作为代码实现专家，请完成以下任务:\n{task}"

        print(f"{Colors.YELLOW}启动AI协作...{Colors.END}\n")

        # Phase 1: 调研
        print(f"{Colors.CYAN}[Phase 1] 技术调研{Colors.END}")
        research_result = self.research(research_prompt)
        print_ai_response("调研报告", research_result, Colors.CYAN)

        # Phase 2: 实现
        print(f"{Colors.GREEN}[Phase 2] 代码实现{Colors.END}")
        implement_result = self.implement(implement_prompt)
        print_ai_response("实现方案", implement_result, Colors.GREEN)

        return {
            "research": research_result,
            "implementation": implement_result
        }


def print_help():
    help_text = """
MindPal Multi-AI 协作工具
=========================

用法:
    python mp-multi-ai.py <command> <prompt>

命令:
    qwen <prompt>        使用通义千问 (代码实现)
    gemini <prompt>      使用 Gemini (技术调研, 需配置API Key)
    research <topic>     技术调研 (自动选择可用AI)
    implement <task>     代码实现 (通义千问)
    both <prompt>        AI协作 (调研+实现)
    review <code>        代码审查

示例:
    python mp-multi-ai.py qwen "实现数字人情感识别模块"
    python mp-multi-ai.py research "2024年RAG最新技术"
    python mp-multi-ai.py both "优化对话响应延迟"
    python mp-multi-ai.py review "def hello(): pass"

配置:
    自动从 backend/.env 加载 DASHSCOPE_API_KEY
    可选配置 GEMINI_API_KEY 启用 Gemini

AI分工:
    通义千问  → 代码实现、算法优化、架构设计
    Gemini    → 技术调研、方案对比 (可选)
"""
    print(help_text)


def main():
    if len(sys.argv) < 2:
        print_help()
        return

    command = sys.argv[1].lower()
    prompt = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    if command in ["help", "-h", "--help"]:
        print_help()
        return

    ai = MultiAI()

    if command == "qwen":
        if not prompt:
            print(f"{Colors.RED}请提供任务描述{Colors.END}")
            return
        print_header("通义千问")
        result = ai.call_qwen(prompt)
        print_ai_response("通义千问", result, Colors.GREEN)

    elif command == "gemini":
        if not prompt:
            print(f"{Colors.RED}请提供调研主题{Colors.END}")
            return
        print_header("Gemini")
        result = ai.call_gemini(prompt)
        print_ai_response("Gemini", result, Colors.CYAN)

    elif command == "research":
        if not prompt:
            print(f"{Colors.RED}请提供调研主题{Colors.END}")
            return
        print_header("技术调研")
        result = ai.research(prompt)
        print_ai_response("调研报告", result, Colors.CYAN)

    elif command == "implement":
        if not prompt:
            print(f"{Colors.RED}请提供任务描述{Colors.END}")
            return
        print_header("代码实现")
        result = ai.implement(prompt)
        print_ai_response("实现方案", result, Colors.GREEN)

    elif command == "both":
        if not prompt:
            print(f"{Colors.RED}请提供任务描述{Colors.END}")
            return
        print_header("AI协作")
        ai.collaborate(prompt)

    elif command == "review":
        if not prompt:
            print(f"{Colors.RED}请提供要审查的代码{Colors.END}")
            return
        print_header("代码审查")
        results = ai.review(prompt)
        print_ai_response("质量审查", results["quality_review"], Colors.GREEN)
        print_ai_response("安全审查", results["security_review"], Colors.CYAN)

    else:
        print(f"{Colors.RED}未知命令: {command}{Colors.END}")
        print_help()


if __name__ == "__main__":
    main()
