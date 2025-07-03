#!/bin/bash

# AI课堂助手自动化部署脚本
# 版本: v1.0.0

set -e  # 出现错误时退出

# 配置变量
PROJECT_DIR="/root/ai-classroom-assistant"
SERVICE_NAME="ai-classroom"
PORT=8001
BACKUP_DIR="/root/backups"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 创建备份
create_backup() {
    if [ -d "$PROJECT_DIR" ]; then
        log_info "创建备份..."
        mkdir -p "$BACKUP_DIR"
        BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
        cp -r "$PROJECT_DIR" "$BACKUP_DIR/$BACKUP_NAME"
        log_success "备份创建完成: $BACKUP_DIR/$BACKUP_NAME"
    fi
}

# 停止服务
stop_service() {
    log_info "停止现有服务..."
    pkill -f "python.*simple_server.py" || true
    pkill -f "python.*app.py" || true
    log_success "服务已停止"
}

# 部署代码
deploy_code() {
    log_info "部署最新代码..."
    
    if [ -d "$PROJECT_DIR" ]; then
        cd "$PROJECT_DIR"
        git pull origin main
    else
        log_info "首次部署，克隆仓库..."
        git clone <YOUR_REPO_URL> "$PROJECT_DIR"
        cd "$PROJECT_DIR"
    fi
    
    log_success "代码部署完成"
}

# 安装依赖
install_dependencies() {
    log_info "检查并安装依赖..."
    cd "$PROJECT_DIR"
    
    # Python依赖
    if [ -f "requirements.txt" ]; then
        pip3 install -r requirements.txt
    fi
    
    # Node.js依赖
    if [ -f "package.json" ]; then
        npm install
    fi
    
    log_success "依赖安装完成"
}

# 启动服务
start_service() {
    log_info "启动服务..."
    cd "$PROJECT_DIR"
    
    # 后台启动服务
    nohup python3 simple_server.py > /tmp/ai-classroom.log 2>&1 &
    
    # 等待服务启动
    sleep 3
    
    # 检查服务状态
    if curl -s http://localhost:$PORT > /dev/null; then
        log_success "服务启动成功！"
        log_info "访问地址: http://47.112.185.79:$PORT"
    else
        log_error "服务启动失败，请检查日志: /tmp/ai-classroom.log"
        return 1
    fi
}

# 主流程
main() {
    log_info "开始部署 AI课堂助手..."
    echo "======================================"
    
    create_backup
    stop_service
    deploy_code
    install_dependencies
    start_service
    
    echo "======================================"
    log_success "部署完成！"
    log_info "服务状态: 运行中"
    log_info "访问地址: http://47.112.185.79:$PORT"
    log_info "日志文件: /tmp/ai-classroom.log"
}

# 执行主流程
main 