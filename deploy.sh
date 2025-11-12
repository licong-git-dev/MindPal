#!/bin/bash

###############################################################################
# MindPal 一键部署脚本
# 用途: 快速部署MindPal数字人平台到Docker环境
# 作者: MindPal Team
# 版本: v1.0
###############################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 打印Banner
print_banner() {
    echo -e "${BLUE}"
    cat << "EOF"
    ███╗   ███╗██╗███╗   ██╗██████╗ ██████╗  █████╗ ██╗
    ████╗ ████║██║████╗  ██║██╔══██╗██╔══██╗██╔══██╗██║
    ██╔████╔██║██║██╔██╗ ██║██║  ██║██████╔╝███████║██║
    ██║╚██╔╝██║██║██║╚██╗██║██║  ██║██╔═══╝ ██╔══██║██║
    ██║ ╚═╝ ██║██║██║ ╚████║██████╔╝██║     ██║  ██║███████╗
    ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═════╝ ╚═╝     ╚═╝  ╚═╝╚══════╝

            AI数字人伴侣平台 - 一键部署脚本
EOF
    echo -e "${NC}"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        exit 1
    fi
    log_success "Docker已安装"
}

# 检查环境变量
check_env() {
    log_info "检查环境配置..."
    if [ ! -f ".env" ]; then
        log_warning ".env文件不存在"
        exit 1
    fi
    log_success "环境配置检查通过"
}

# 主函数
main() {
    print_banner
    log_info "开始部署MindPal..."
    check_dependencies
    check_env
    
    log_info "停止旧容器..."
    docker-compose down 2>/dev/null || true
    
    log_info "构建镜像..."
    docker-compose build --no-cache
    
    log_info "启动服务..."
    docker-compose up -d
    
    log_success "部署完成! 访问 http://localhost"
}

main
