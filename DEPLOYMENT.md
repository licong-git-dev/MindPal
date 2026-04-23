# MindPal 部署指南

## 📋 快速开始

### 方式一: Docker部署 (推荐)

#### 1. 前置要求
- Docker 20.10+
- Docker Compose 2.0+
- 阿里云DashScope API Key

#### 2. 克隆项目
```bash
git clone <your-repo-url>
cd MindPal
```

#### 3. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件,填入你的DASHSCOPE_API_KEY
```

#### 4. 一键部署
```bash
chmod +x deploy.sh
./deploy.sh
```

#### 5. 访问应用
- 前端: http://localhost
- 后端API: http://localhost:8000
- 健康检查: http://localhost:8000/health

#### 6. 预设测试账号
- 手机号: `13800138000`
- 密码: `123456`

---

### 方式二: 本地开发部署

#### 1. 后端部署

```bash
cd backend_v2

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入本地配置

# 启动后端
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端将运行在 http://localhost:8000

#### 2. 前端部署

```bash
cd frontend

# 启动简单HTTP服务器
python -m http.server 8000

# 或使用Node.js
npx http-server -p 8000
```

前端将运行在 http://localhost:8000

---

## 🛠️ 常用Docker命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
docker-compose logs -f backend   # 仅查看后端日志
docker-compose logs -f frontend  # 仅查看前端日志

# 重启服务
docker-compose restart
docker-compose restart backend   # 仅重启后端

# 停止服务
docker-compose down

# 重新构建并启动
docker-compose up --build -d

# 清理所有数据(谨慎使用)
docker-compose down -v
```

---

## 📊 项目结构

```
MindPal/
├── backend_v2/               # 主线后端（FastAPI）
│   ├── app/
│   │   ├── api/v1/          # API路由
│   │   ├── models/          # 数据模型
│   │   ├── schemas/         # Pydantic模式
│   │   ├── services/        # 业务逻辑
│   │   ├── core/            # 安全/WebSocket等核心能力
│   │   ├── config.py        # 配置管理
│   │   └── main.py          # 启动入口
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── requirements.txt
│
├── backend/                  # 历史/MVP 参考实现（Flask）
├── frontend/                 # 前端应用
├── Dockerfile.frontend       # 前端 Dockerfile
├── docker-compose.yml        # 根编排（默认接 backend_v2）
├── nginx.conf                # Nginx配置
└── deploy.sh                 # 一键部署脚本
```

---

## 🔑 核心功能

### 1. 用户认证
- JWT Token认证
- 手机号 + 密码登录
- 预设测试账号: 13800138000 / 123456

### 2. 数字人管理
- 创建自定义数字人(5步流程)
  - 选择形象(emoji头像)
  - 设置性格(6种预设 + 自定义)
  - 选择声音(6种预设声音)
  - 设置知识库
  - 确认创建
- 数字人列表查看
- 删除数字人

### 3. AI对话
- 流式SSE对话
- 阿里云通义千问LLM
- 个性化回复(基于数字人性格)
- 情绪分析
- RAG知识增强

### 4. 知识库管理
- 文档上传(PDF/DOCX/TXT/MD)
- 自动文本提取和分块
- FAISS向量化存储
- RAG检索增强对话
- 文档列表和删除

---

## 🧪 测试流程

### 1. 完整用户流程测试

```bash
# 1. 启动服务
./deploy.sh

# 2. 访问 http://localhost

# 3. 登录
手机号: 13800138000
密码: 123456

# 4. 创建数字人
按5步流程创建

# 5. 开始对话
与数字人对话

# 6. 上传知识库
上传PDF/DOCX文档

# 7. 测试RAG
问与文档相关的问题
```

### 2. API测试

```bash
# 进入backend目录
cd backend

# 运行测试脚本
python test_api.py
```

---

## 🔧 故障排查

### 1. 后端无法启动
```bash
# 查看后端日志
docker-compose logs backend

# 常见问题:
# - 缺少DASHSCOPE_API_KEY: 检查.env文件
# - 端口5000被占用: 修改docker-compose.yml
# - 数据库初始化失败: 删除backend/data目录重试
```

### 2. 前端无法访问
```bash
# 查看前端日志
docker-compose logs frontend

# 常见问题:
# - 端口80被占用: 修改docker-compose.yml
# - Nginx配置错误: 检查nginx.conf
```

### 3. 对话无响应
```bash
# 检查API Key是否有效
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"dhId": 1, "message": "你好"}'

# 检查阿里云API调用
docker-compose logs backend | grep "DashScope"
```

### 4. RAG检索不生效
```bash
# 检查向量数据库
ls -la backend/data/vectors/

# 检查文档上传记录
docker-compose exec backend python -c "
from app.models import db, KnowledgeDoc
from app import app
with app.app_context():
    docs = KnowledgeDoc.query.all()
    for doc in docs:
        print(f'{doc.id}: {doc.filename} - {doc.status}')
"
```

---

## 📈 性能优化

### 1. 后端优化
- 增加Gunicorn workers: 修改Dockerfile.backend中的`--workers`参数
- 启用Redis缓存(可选)
- 使用PostgreSQL替代SQLite(生产环境)

### 2. 前端优化
- 启用Nginx Gzip压缩(已配置)
- CDN加速静态资源
- 图片懒加载

### 3. RAG优化
- 调整chunk_size和chunk_overlap: 修改chunking_service.py
- 增加top_k检索数量: 修改chat.py中的`top_k`参数
- 使用更大的向量维度(如果API支持)

---

## 🚀 生产环境部署

### 1. 使用HTTPS
```bash
# 修改nginx.conf,添加SSL配置
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ...
}
```

### 2. 数据库迁移到PostgreSQL
```bash
# 修改.env
DATABASE_URL=postgresql://user:pass@localhost:5432/mindpal

# 更新requirements.txt
pip install psycopg2-binary
```

### 3. 使用云服务
- 阿里云ECS: 部署应用
- 阿里云OSS: 存储上传文件
- 阿里云RDS: PostgreSQL数据库
- 阿里云VPC: 网络隔离

---

## 📞 技术支持

- 文档: https://github.com/your-repo/MindPal
- Issues: https://github.com/your-repo/MindPal/issues
- Email: support@mindpal.ai

---

## 📄 License

MIT License

Copyright (c) 2025 MindPal Team
