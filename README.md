# MindPal - 面向元宇宙的智能体数字人交互平台

<div align="center">

![MindPal Logo](https://via.placeholder.com/150?text=MindPal)

**你的智慧伙伴，陪伴你探索数字世界**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/flask-2.0.3-green.svg)](https://flask.palletsprojects.com/)
[![Vue](https://img.shields.io/badge/vue-3.0-brightgreen.svg)](https://vuejs.org/)

[在线演示](http://43.98.170.184) | [技术文档](TECHNICAL_STRATEGY.md) | [开发路线图](DEVELOPMENT_ROADMAP.md) | [商业计划](Business_Plan/MindPaL.pdf)

</div>

---

## 🌟 项目简介

MindPal 是一个**面向元宇宙的智能体数字人交互平台**，致力于打造集**智能、陪伴、服务**于一体的个性化AI伙伴。

### 三大核心价值

- **智能 (Intelligence)**: 基于大语言模型的深度理解与推理能力
- **陪伴 (Companionship)**: 提供全天候、无条件的情感支持
- **服务 (Service)**: 知识服务 + 购物辅助的实用价值

### 产品愿景

从SaaS平台演进为元宇宙基础设施，成为连接所有虚拟世界的智能体服务枢纽。

---

## ✨ 核心功能

### 已实现功能

- ✅ **用户认证系统**: 注册/登录/会话管理
- ✅ **个性化数字人塑造**: 6种性格模板 + 5维特质调整
  - 选择形象（8种预设 + 自定义上传）
  - 设置性格（温柔体贴/活泼开朗/知性理性/幽默风趣/沉稳冷静/富有创意）
  - 选择声音（6种预设音色）
  - 设置知识库（文档上传）
- ✅ **多终端适配**: 响应式Web设计（手机/平板/桌面）
- ✅ **数据持久化**: PostgreSQL数据库 + LocalStorage

### 开发中功能（阶段1 MVP）

- 🚧 **基础对话能力**: 集成阿里云通义千问LLM
- 🚧 **对话历史**: 存储和展示历史对话
- 🚧 **长期记忆**: 记住用户重要信息

### 规划中功能（阶段2+）

- 📋 **多模态交互**: 语音对话（ASR + TTS）
- 📋 **知识服务**: RAG知识库检索
- 📋 **购物辅助**: 智能推荐与下单
- 📋 **元宇宙场景**: 智能体小家 + 中央社交大厅

---

## 🏗️ 技术架构

### 技术栈

#### 前端
- **框架**: 原生 HTML5 + CSS3 + JavaScript
- **设计**: Glassmorphism + 渐变色
- **存储**: LocalStorage + SessionStorage
- **部署**: Nginx静态托管

#### 后端
- **语言**: Python 3.6+
- **框架**: Flask 2.0.3
- **数据库**: PostgreSQL (生产) / SQLite (开发)
- **API**: RESTful API
- **部署**: Gunicorn + Nginx + Systemd

#### AI能力
- **LLM**: 阿里云通义千问（qwen-turbo/plus）
- **Embedding**: text-embedding-v2
- **ASR**: 科大讯飞语音听写（规划中）
- **TTS**: 阿里云智能语音（规划中）
- **向量数据库**: Milvus（规划中）

### 系统架构图

```
┌─────────────────────────────────────────────────┐
│              Frontend（多终端）                  │
│  ┌───────┐  ┌───────┐  ┌───────┐  ┌───────┐   │
│  │ Web   │  │ 手机  │  │ 平板  │  │小程序 │   │
│  └───────┘  └───────┘  └───────┘  └───────┘   │
└──────────────────┬──────────────────────────────┘
                   │ HTTPS/WSS
┌──────────────────▼──────────────────────────────┐
│              Nginx (反向代理)                    │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│          Gunicorn (WSGI Server)                 │
│  ┌─────────────────────────────────────────┐   │
│  │         Flask Application                │   │
│  │  ┌────────┐  ┌────────┐  ┌──────────┐  │   │
│  │  │ Auth   │  │ DH API │  │ Chat API │  │   │
│  │  └────────┘  └────────┘  └──────────┘  │   │
│  └─────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌────────▼────────┐
│  PostgreSQL    │   │  第三方AI服务   │
│  (用户/数字人) │   │  - 通义千问     │
│                │   │  - 科大讯飞     │
└────────────────┘   │  - 阿里云TTS    │
                     └─────────────────┘
```

---

## 🚀 快速开始

### 前置要求

- Python 3.6+
- PostgreSQL 12+ (可选，开发环境可用SQLite)
- Git
- 阿里云DashScope API Key

### 本地开发环境搭建

#### 1. 克隆项目

```bash
git clone https://github.com/licong-git-dev/MindPal.git
cd MindPal
```

#### 2. 后端配置

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

**.env 配置示例**:
```bash
# 阿里云配置
DASHSCOPE_API_KEY=your_dashscope_api_key

# 模型配置
LLM_MODEL=qwen-turbo
EMBEDDING_MODEL=text-embedding-v2

# 应用配置
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///mindpal.db

# CORS配置
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

#### 3. 初始化数据库

```bash
python
>>> from app import db
>>> db.create_all()
>>> exit()
```

#### 4. 启动后端服务

```bash
# 开发模式
python app.py

# 生产模式
gunicorn --workers 2 --bind 0.0.0.0:5000 app:app
```

后端服务将在 `http://localhost:5000` 启动

#### 5. 前端配置

```bash
cd ../frontend

# 直接用浏览器打开 index.html
# 或者使用HTTP服务器
python -m http.server 3000
```

前端将在 `http://localhost:3000` 可访问

#### 6. 访问应用

打开浏览器访问 `http://localhost:3000`

**测试账号**:
- 手机号: `13800138000`
- 密码: `123456`

---

## 🌐 生产环境部署

### 阿里云服务器部署

我们提供了一键部署脚本 `deploy.sh`

#### 1. 准备服务器

- 操作系统: Ubuntu 20.04/22.04 LTS
- 配置: 2核4G (最低)
- 公网IP: 已配置

#### 2. 执行部署

```bash
# SSH登录服务器
ssh root@your_server_ip

# 下载部署脚本
curl -O https://raw.githubusercontent.com/licong-git-dev/MindPal/master/deploy.sh

# 执行部署
sudo bash deploy.sh
```

#### 3. 部署完成

脚本将自动完成：
- ✅ 系统更新和依赖安装
- ✅ 代码克隆
- ✅ Python环境配置
- ✅ 数据库初始化
- ✅ Gunicorn服务配置
- ✅ Nginx反向代理配置

部署完成后访问 `http://your_server_ip`

**当前演示环境**: http://43.98.170.184

---

## 📂 项目结构

```
MindPal/
├── frontend/                   # 前端代码
│   ├── index.html             # 登录页
│   ├── dh-list.html           # 数字人列表
│   ├── create-dh-step1-5.html # 创建数字人流程（5步）
│   ├── chat.html              # 对话界面
│   ├── css/                   # 样式文件
│   │   ├── variables.css      # CSS变量定义
│   │   ├── base.css           # 基础样式
│   │   ├── components.css     # 组件样式
│   │   └── animations.css     # 动画效果
│   └── js/                    # JavaScript文件
│       └── auth.js            # 认证管理模块
├── backend/                    # 后端代码
│   ├── app.py                 # Flask应用入口
│   ├── models.py              # 数据库模型
│   ├── requirements.txt       # Python依赖
│   ├── .env                   # 环境变量（gitignored）
│   └── services/              # 业务逻辑服务（规划中）
│       ├── llm_service.py     # LLM调用服务
│       ├── memory_service.py  # 记忆管理服务
│       └── rag_service.py     # RAG检索服务
├── Business_Plan/              # 商业计划
│   └── MindPaL.pdf            # 详细商业计划书
├── deploy.sh                   # 一键部署脚本
├── .gitignore                 # Git忽略配置
├── README.md                   # 本文档
├── TECHNICAL_STRATEGY.md       # 技术方案文档
├── DEVELOPMENT_ROADMAP.md      # 开发路线图
└── BACKEND_IMPLEMENTATION_PLAN.md  # 后端实现计划
```

---

## 🛣️ 开发路线图

### 阶段1: MVP验证 (第1-4周) - **当前阶段**

**目标**: 验证核心价值假设

- [x] 用户认证系统
- [x] 数字人创建流程（UI）
- [ ] 基础对话能力（LLM集成）
- [ ] 个性化塑造系统（后端）
- [ ] 对话历史存储

**里程碑**: 100个用户，次日留存率 ≥ 30%

### 阶段2: SaaS平台完善 (第5-12周)

- [ ] 多模态交互（语音对话）
- [ ] 知识服务（RAG系统）
- [ ] 长期记忆优化
- [ ] 多终端优化（小程序）
- [ ] 订阅付费系统

**里程碑**: 1000付费用户，MRR ≥ 5万元

### 阶段3: PaaS平台开放 (第13-24周)

- [ ] RESTful API开放
- [ ] Python/JS SDK发布
- [ ] 开发者控制台
- [ ] 企业级功能
- [ ] Marketplace建设

**里程碑**: 50家企业客户，API调用量 ≥ 100万次/月

### 阶段4: 元宇宙布局 (2026+)

- [ ] 3D虚拟空间（智能体小家）
- [ ] 多人在线（中央社交大厅）
- [ ] VR/AR支持
- [ ] 跨平台智能体协议
- [ ] 世界模型接入

**里程碑**: 100万MAU，接入5+虚拟世界

详见 [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md)

---

## 📖 文档导航

| 文档 | 说明 |
|-----|------|
| [README.md](README.md) | 项目概览和快速开始（本文档）|
| [TECHNICAL_STRATEGY.md](TECHNICAL_STRATEGY.md) | 深度技术方案（AI选型、架构设计）|
| [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md) | 4阶段开发路线图 |
| [BACKEND_IMPLEMENTATION_PLAN.md](BACKEND_IMPLEMENTATION_PLAN.md) | 后端详细实现计划 |
| [Business_Plan/MindPaL.pdf](Business_Plan/MindPaL.pdf) | 完整商业计划书 |

---

## 🔑 API密钥申请

### 1. 阿里云DashScope（必需）

**申请地址**: https://dashscope.aliyun.com/

**免费额度**: 新用户赠送100万tokens

**用途**:
- 通义千问LLM（对话生成）
- text-embedding-v2（知识库向量化）

### 2. 科大讯飞（可选，阶段2）

**申请地址**: https://www.xfyun.cn/

**免费额度**: 500万字符/年

**用途**: 语音识别（ASR）

### 3. 阿里云智能语音（可选，阶段2）

**申请地址**: https://nls.aliyun.com/

**免费额度**: 100万字符

**用途**: 语音合成（TTS）

---

## 🤝 贡献指南

欢迎贡献！请遵循以下流程：

1. Fork 本项目
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启一个Pull Request

### 开发规范

- **代码风格**: 遵循 PEP 8 (Python) / StandardJS (JavaScript)
- **提交信息**: 使用语义化提交（Conventional Commits）
- **分支策略**: Git Flow
- **测试**: 所有新功能必须包含测试用例

---

## 🐛 问题反馈

遇到问题？请在 [GitHub Issues](https://github.com/licong-git-dev/MindPal/issues) 提交

提交前请确认：
- 搜索已有Issue，避免重复
- 提供详细的复现步骤
- 附上错误日志和截图

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 👥 团队

**MindPal开发团队**

- 产品负责人: Licong
- 技术负责人: Licong
- AI顾问: Claude (Anthropic)

---

## 🙏 致谢

感谢以下开源项目和服务：

- [Flask](https://flask.palletsprojects.com/) - Python Web框架
- [阿里云DashScope](https://dashscope.aliyun.com/) - 大语言模型API
- [科大讯飞](https://www.xfyun.cn/) - 语音识别技术
- [Milvus](https://milvus.io/) - 向量数据库

---

## 📞 联系我们

- **项目主页**: https://github.com/licong-git-dev/MindPal
- **在线演示**: http://43.98.170.184
- **技术博客**: (待补充)
- **微信公众号**: (待补充)

---

<div align="center">

**用AI重新定义陪伴，用技术连接未来世界**

Made with ❤️ by MindPal Team

⭐ 如果这个项目对你有帮助，请给我们一个Star！

</div>
