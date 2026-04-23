# 🚀 MindPal + Claude Code Bridge 多AI协作指南

## 目录
- [概述](#概述)
- [快速开始](#快速开始)
- [架构设计](#架构设计)
- [AI分工策略](#ai分工策略)
- [工作流详解](#工作流详解)
- [命令参考](#命令参考)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

---

## 概述

本文档介绍如何利用 **Claude Code Bridge (CCB)** 实现 **Claude + Codex + Gemini** 三体协作，大幅提升 MindPal 项目的开发效率。

### 核心优势

| 指标 | 传统单AI | 三体协作 | 提升 |
|------|---------|---------|------|
| Token消耗 | 5k-20k/次 | 50-200/次 | **100x** |
| 响应延迟 | 5-30秒 | 1-5秒 | **6x** |
| 任务并行度 | 1 | 3 | **3x** |
| 知识覆盖 | 单一模型 | 多模型互补 | **更全面** |

### 原理说明

传统的 MCP（Model Context Protocol）是**无状态调用**，每次都需要传递完整上下文。

CCB 采用**持久化会话**模式：
- 每个AI在独立终端窗口运行
- 保持完整的对话上下文
- Claude 只发送轻量指令
- AI 自主读取项目文件

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude (团队协调者)                       │
│  负责: 架构设计、方案决策、代码审查、任务分配                 │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
   ┌─────▼─────┐ ┌───▼───┐ ┌─────▼─────┐
   │  Codex    │ │Claude │ │  Gemini   │
   │  (实现者) │ │(审查) │ │  (研究员) │
   └───────────┘ └───────┘ └───────────┘
```

---

## 快速开始

### 1. 安装 CCB

```powershell
# Windows PowerShell
cd D:\app\PythonFiles\MindPal\claude_code_bridge-main
.\install.ps1

# 或 Linux/macOS/WSL
cd ~/MindPal/claude_code_bridge-main
./install.sh
```

### 2. 启动多AI环境

```bash
# 进入项目目录
cd D:\app\PythonFiles\MindPal

# 启动三体协作 (Claude + Codex + Gemini)
ccb up codex gemini

# 或单独启动
ccb up codex    # Claude + Codex
ccb up gemini   # Claude + Gemini
```

### 3. 验证连接

```bash
# 检查状态
ccb status

# 测试连通性
cping   # 测试 Codex
gping   # 测试 Gemini
```

### 4. 开始协作

```bash
# 技术调研 (Gemini)
gask-w "调研2024年RAG最新技术"

# 代码实现 (Codex)
cask-w "实现数字人情感识别模块"

# Claude 进行综合分析和决策
```

---

## 架构设计

### 整体架构

```
D:\app\PythonFiles\MindPal\
├── .ccb-config.json              # CCB 配置文件
├── .claude\prompts\
│   ├── multi_ai_coordinator.md   # 多AI协调者提示词
│   ├── ai_engineer.md            # AI工程师 (已增强)
│   └── ...                       # 其他Agent
├── scripts\
│   ├── mp-ai.py                  # 协作脚本 (Python)
│   ├── mp-ai.bat                 # Windows快捷方式
│   └── mp-ai.sh                  # Linux/macOS快捷方式
└── claude_code_bridge-main\      # CCB 源码
```

### 数据流

```
用户请求
    │
    ▼
┌───────────┐
│  Claude   │ ─── 分析任务，制定策略
└─────┬─────┘
      │
      ├── 研究类任务 ──▶ gask-w "..." ──▶ Gemini ──▶ 调研报告
      │
      ├── 实现类任务 ──▶ cask-w "..." ──▶ Codex ──▶ 代码实现
      │
      └── 审查类任务 ──▶ 并行审查 ──▶ 综合报告
```

---

## AI分工策略

### 角色定位

| AI | 角色 | 核心能力 | 适用场景 |
|---|------|---------|---------|
| **Claude** | 协调者 | 架构设计、全局视角、方案决策 | 复杂问题分析、团队协调 |
| **Codex** | 实现者 | 代码生成、算法优化、重构 | 编码任务、性能优化 |
| **Gemini** | 研究员 | 信息检索、技术调研、趋势分析 | 新技术调研、方案对比 |

### MindPal 模块分工

| 模块 | 主导 | 辅助 | 说明 |
|------|-----|------|------|
| 对话引擎 | Claude | Codex | Claude设计架构，Codex实现 |
| 情感识别 | Gemini | Codex | Gemini调研模型，Codex实现 |
| 知识库RAG | Claude | Gemini | Claude设计，Gemini优化检索 |
| 数字人性格 | Claude | - | Prompt工程，Claude独立完成 |
| 前端UI | Claude | Codex | Claude设计，Codex复杂动画 |
| 后端API | Codex | Claude | Codex实现，Claude审查 |
| 数据库 | Claude | Gemini | Claude设计，Gemini验证 |

---

## 工作流详解

### 1. 对话引擎开发工作流

```bash
# 使用快捷脚本
python scripts/mp-ai.py dialogue

# 或手动执行
# Step 1: Gemini 调研框架
gask-w "对比分析 LangChain vs LlamaIndex 在数字人对话场景的优劣"

# Step 2: Claude 设计架构 (直接对话)
# "基于调研结果，设计数字人对话引擎架构"

# Step 3: Codex 实现核心类
cask-w "实现 DialogueManager 类，包含状态机、上下文管理、多轮对话"

# Step 4: Codex 实现意图分类
cask-w "实现 IntentClassifier，支持陪伴/知识/购物/闲聊等意图"

# Step 5: Codex 实现情感分析
cask-w "实现 EmotionAnalyzer，支持文本和语音情感识别"

# Step 6: Claude 集成测试
# 综合审查所有实现
```

### 2. 知识库RAG开发工作流

```bash
# 使用快捷脚本
python scripts/mp-ai.py rag

# 或手动执行
# Step 1: Gemini 调研RAG技术
gask-w "调研2024年RAG最新进展：HyDE、Self-RAG、CRAG"

# Step 2: Gemini 对比向量模型
gask-w "对比 BGE vs M3E vs OpenAI Embedding 中文效果"

# Step 3: Codex 实现RAG核心
cask-w "实现 KnowledgeBaseRAG，支持混合检索（关键词+向量）"

# Step 4: Codex 实现重排序
cask-w "实现 Reranker，使用 cross-encoder 提升准确率"
```

### 3. 代码审查工作流

```bash
# 使用快捷脚本
python scripts/mp-ai.py review backend/services/chat_service.py

# 或手动执行 (并行)
cask "审查代码质量：命名规范、复杂度、性能" &
gask "审查安全性：SQL注入、XSS、数据泄露" &

# 查看结果
cpend  # Codex结果
gpend  # Gemini结果

# Claude 综合分析
```

### 4. 性能优化工作流

```bash
# 使用快捷脚本
python scripts/mp-ai.py optimize "对话响应延迟"

# 或手动执行
# Step 1: Codex 分析瓶颈
cask-w "分析对话响应延迟的性能瓶颈"

# Step 2: Gemini 调研最佳实践
gask-w "调研对话系统性能优化的行业最佳实践"

# Step 3: 迭代优化
cask-w "根据分析结果优化对话响应延迟"
```

---

## 命令参考

### CCB 核心命令

| 命令 | 说明 |
|------|------|
| `ccb up codex` | 启动 Claude + Codex |
| `ccb up gemini` | 启动 Claude + Gemini |
| `ccb up codex gemini` | 启动三体协作 |
| `ccb status` | 查看AI连接状态 |
| `ccb kill codex` | 终止Codex会话 |
| `ccb restore codex` | 恢复Codex会话 |

### Codex 通信命令

| 命令 | 说明 |
|------|------|
| `cask "任务"` | 异步发送 (不等待) |
| `cask-w "任务"` | 同步发送 (等待回复) |
| `cpend` | 查看待处理回复 |
| `cping` | 检测连通性 |

### Gemini 通信命令

| 命令 | 说明 |
|------|------|
| `gask "任务"` | 异步发送 (不等待) |
| `gask-w "任务"` | 同步发送 (等待回复) |
| `gpend` | 查看待处理回复 |
| `gping` | 检测连通性 |

### MindPal 快捷脚本

```bash
python scripts/mp-ai.py <command> [args]

# 命令列表
research <topic>      # 技术调研 (Gemini)
implement <feature>   # 功能实现 (Codex)
review <file>         # 代码审查 (三方并行)
optimize <target>     # 性能优化 (迭代)
dialogue              # 对话引擎开发流程
rag                   # RAG系统开发流程
status                # 检查环境状态
```

---

## 最佳实践

### 1. 任务分配原则

```
研究调研类 → Gemini (广度优先)
  - 技术选型
  - 方案对比
  - 最新趋势

代码实现类 → Codex (深度优先)
  - 算法实现
  - 代码重构
  - 性能优化

架构设计类 → Claude (全局视角)
  - 系统架构
  - 方案决策
  - 代码审查
```

### 2. 上下文传递

```bash
# ✅ 好的做法：传递完整上下文
cask-w "基于以下架构设计实现 DialogueManager：
  - 使用状态机模式管理对话状态
  - Redis存储会话上下文
  - 支持多轮对话和长期记忆
  - 参考 backend/services/chat_service.py 的风格"

# ❌ 避免：上下文不完整
cask-w "实现 DialogueManager"
```

### 3. 结果验证

```bash
# 每个AI的输出都应该验证

# Gemini 调研结果 → Claude 评估准确性
gask-w "调研xxx"
# Claude: "这个调研结果是否准确和完整？"

# Codex 代码实现 → Claude 审查质量
cask-w "实现xxx"
# Claude: "审查代码质量、安全性、性能"
```

### 4. 并行任务管理

```bash
# 使用 & 后台执行
cask "任务1" &
gask "任务2" &

# 等待完成后查看结果
sleep 30  # 等待执行
cpend     # Codex结果
gpend     # Gemini结果
```

### 5. 错误处理

```bash
# 检查连接
cping && echo "Codex OK" || echo "Codex 断开"
gping && echo "Gemini OK" || echo "Gemini 断开"

# 重启会话
ccb kill codex && ccb up codex

# 查看详细状态
ccb status
```

---

## 常见问题

### Q1: CCB 安装失败？

```powershell
# 检查 Python 版本 (需要 3.10+)
python --version

# 检查 WezTerm 是否安装
wezterm --version

# 手动安装依赖
pip install pathlib
```

### Q2: AI 无响应？

```bash
# 1. 检查连接状态
ccb status

# 2. 检查单个AI
cping  # Codex
gping  # Gemini

# 3. 重启会话
ccb kill codex gemini
ccb up codex gemini
```

### Q3: 如何选择用哪个AI？

| 需求 | 选择 | 原因 |
|------|------|------|
| 需要最新信息 | Gemini | 知识更新更快 |
| 需要写代码 | Codex | 代码生成专精 |
| 需要架构设计 | Claude | 全局视角更强 |
| 不确定 | Claude | 让Claude来分配 |

### Q4: 并行任务如何同步？

```bash
# 方法1: 使用 & 后台执行
cask "任务1" &
gask "任务2" &
wait  # 等待所有后台任务

# 方法2: 查看pending结果
cpend  # 检查Codex
gpend  # 检查Gemini
```

### Q5: Token消耗如何这么低？

传统MCP每次调用都传递完整上下文（5k-20k tokens）。

CCB使用持久化会话：
- AI在独立窗口运行
- 保持完整对话历史
- Claude只发送轻量指令（50-200 tokens）
- AI自主读取项目文件

---

## 快速参考卡

```
┌─────────────────────────────────────────────────────────────┐
│               MindPal Multi-AI 快速参考                     │
├─────────────────────────────────────────────────────────────┤
│ 启动环境:  ccb up codex gemini                              │
│ 检查状态:  ccb status                                       │
├─────────────────────────────────────────────────────────────┤
│ Codex:     cask-w "实现xxx功能"     # 同步                  │
│            cask "实现xxx功能"       # 异步                  │
│            cpend                    # 查看结果              │
├─────────────────────────────────────────────────────────────┤
│ Gemini:    gask-w "调研xxx技术"     # 同步                  │
│            gask "调研xxx技术"       # 异步                  │
│            gpend                    # 查看结果              │
├─────────────────────────────────────────────────────────────┤
│ 快捷脚本:  python scripts/mp-ai.py dialogue   # 对话引擎    │
│            python scripts/mp-ai.py rag        # RAG系统     │
│            python scripts/mp-ai.py review <file>  # 代码审查│
└─────────────────────────────────────────────────────────────┘
```

---

## 更新日志

- **v1.0** (2024-12-22): 初始版本，完成CCB整合
  - 创建多AI协调者提示词
  - 配置CCB环境
  - 编写快捷脚本
  - 完善使用文档

---

**三体协作，效率倍增！** 🚀🤖✨
