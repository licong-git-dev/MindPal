#!/bin/bash

# MindPal 一键部署脚本
# 适用于 Ubuntu 20.04/22.04 LTS
# 使用方法：sudo bash deploy.sh

set -e  # 遇到错误立即退出

echo "========================================="
echo "  MindPal 部署脚本 v1.0"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}请使用 root 用户或 sudo 执行此脚本${NC}"
  exit 1
fi

# 获取服务器公网IP
SERVER_IP=$(curl -s ifconfig.me)
echo -e "${GREEN}检测到服务器公网IP: ${SERVER_IP}${NC}"
echo ""

# 1. 更新系统
echo -e "${YELLOW}[1/10] 更新系统软件包...${NC}"
apt update -y
apt upgrade -y

# 2. 安装基础软件
echo -e "${YELLOW}[2/10] 安装基础软件 (Git, Python3, Nginx, etc.)...${NC}"
apt install -y git python3 python3-pip python3-venv nginx curl wget software-properties-common

# 3. 安装 PostgreSQL (可选，先用SQLite)
# echo -e "${YELLOW}安装 PostgreSQL...${NC}"
# apt install -y postgresql postgresql-contrib

# 4. 创建项目目录
echo -e "${YELLOW}[3/10] 创建项目目录...${NC}"
PROJECT_DIR="/var/www/mindpal"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 5. 克隆GitHub代码
echo -e "${YELLOW}[4/10] 克隆 GitHub 代码仓库...${NC}"
if [ -d "$PROJECT_DIR/.git" ]; then
  echo "代码仓库已存在，执行 git pull 更新..."
  git pull
else
  git clone https://github.com/licong-git-dev/MindPal.git .
fi

# 6. 配置后端环境
echo -e "${YELLOW}[5/10] 配置 Python 虚拟环境...${NC}"
cd $PROJECT_DIR/backend

# 创建虚拟环境
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 7. 安装Python依赖
echo -e "${YELLOW}[6/10] 安装 Python 依赖包...${NC}"

# 创建 requirements.txt（如果不存在）
cat > requirements.txt <<EOF
Flask==3.0.0
Flask-CORS==4.0.0
flask-sqlalchemy==3.1.1
python-dotenv==1.0.0
dashscope==1.14.1
gunicorn==21.2.0
PyPDF2==3.0.1
python-docx==1.1.0
faiss-cpu==1.7.4
langchain==0.1.0
psycopg2-binary==2.9.9
bcrypt==4.1.2
PyJWT==2.8.0
EOF

pip install --upgrade pip
pip install -r requirements.txt

# 8. 创建环境变量配置文件
echo -e "${YELLOW}[7/10] 创建环境变量配置...${NC}"
cat > .env <<EOF
# 阿里云配置
DASHSCOPE_API_KEY=sk-71bb10435f134dfdab3a4b684e57b640

# 模型配置
LLM_MODEL=qwen-turbo
EMBEDDING_MODEL=text-embedding-v2

# 应用配置
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite:///mindpal.db

# CORS配置
ALLOWED_ORIGINS=http://${SERVER_IP},https://${SERVER_IP}
EOF

echo -e "${GREEN}环境变量配置文件已创建: $PROJECT_DIR/backend/.env${NC}"

# 9. 初始化数据库
echo -e "${YELLOW}[8/10] 初始化数据库...${NC}"
python3 -c "from app import db; db.create_all()" 2>/dev/null || echo "数据库初始化将在首次运行时自动完成"

# 10. 配置 Gunicorn systemd 服务
echo -e "${YELLOW}[9/10] 配置后端服务 (Gunicorn)...${NC}"
cat > /etc/systemd/system/mindpal-backend.service <<EOF
[Unit]
Description=MindPal Backend Service
After=network.target

[Service]
Type=notify
User=root
WorkingDirectory=$PROJECT_DIR/backend
Environment="PATH=$PROJECT_DIR/backend/venv/bin"
ExecStart=$PROJECT_DIR/backend/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 重新加载 systemd
systemctl daemon-reload
systemctl enable mindpal-backend
systemctl restart mindpal-backend

echo -e "${GREEN}后端服务已启动！${NC}"
systemctl status mindpal-backend --no-pager

# 11. 配置 Nginx
echo -e "${YELLOW}[10/10] 配置 Nginx 反向代理...${NC}"

# 备份原有配置
if [ -f /etc/nginx/sites-available/default ]; then
  cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup
fi

cat > /etc/nginx/sites-available/mindpal <<EOF
server {
    listen 80;
    server_name ${SERVER_IP};

    # 前端静态文件
    location / {
        root $PROJECT_DIR/frontend;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # 日志
    access_log /var/log/nginx/mindpal_access.log;
    error_log /var/log/nginx/mindpal_error.log;
}
EOF

# 启用站点配置
ln -sf /etc/nginx/sites-available/mindpal /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 测试Nginx配置
nginx -t

# 重启Nginx
systemctl restart nginx
systemctl enable nginx

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}  🎉 MindPal 部署成功！${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo -e "${GREEN}访问地址：${NC}"
echo -e "  HTTP:  http://${SERVER_IP}"
echo ""
echo -e "${YELLOW}后续操作：${NC}"
echo "1. 修改 root 密码（安全建议）："
echo "   passwd"
echo ""
echo "2. 查看后端服务状态："
echo "   systemctl status mindpal-backend"
echo ""
echo "3. 查看后端日志："
echo "   journalctl -u mindpal-backend -f"
echo ""
echo "4. 查看Nginx日志："
echo "   tail -f /var/log/nginx/mindpal_error.log"
echo ""
echo "5. 更新代码："
echo "   cd $PROJECT_DIR && git pull && systemctl restart mindpal-backend"
echo ""
echo -e "${RED}⚠️  重要安全提醒：${NC}"
echo "1. 立即修改 root 密码！"
echo "2. 配置防火墙（ufw）只开放必要端口"
echo "3. 考虑配置 HTTPS（Let's Encrypt免费证书）"
echo ""
echo -e "${GREEN}部署完成时间: $(date)${NC}"
