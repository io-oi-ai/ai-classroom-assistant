#!/bin/bash

# =================================================================
# AI课堂助手 - 轻量服务器专用部署脚本
# 适用于: 1核2G-4核8G 的轻量应用服务器
# 支持: 阿里云、腾讯云、华为云等轻量服务器
# =================================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "请使用 sudo 运行此脚本"
        exit 1
    fi
}

# 检测系统信息
detect_system() {
    log_step "检测系统信息..."
    
    # 获取系统信息
    OS=$(lsb_release -si 2>/dev/null || echo "Unknown")
    VERSION=$(lsb_release -sr 2>/dev/null || echo "Unknown")
    ARCH=$(uname -m)
    MEMORY=$(free -m | awk 'NR==2{printf "%.0f", $2/1024}')
    CPU_CORES=$(nproc)
    DISK_SPACE=$(df -h / | awk 'NR==2{print $4}')
    
    log_info "操作系统: $OS $VERSION"
    log_info "架构: $ARCH"
    log_info "内存: ${MEMORY}GB"
    log_info "CPU核心: $CPU_CORES"
    log_info "可用磁盘空间: $DISK_SPACE"
    
    # 检查最低要求
    if (( MEMORY < 2 )); then
        log_warning "内存少于2GB，建议增加交换空间"
        NEED_SWAP=true
    fi
    
    if (( CPU_CORES < 1 )); then
        log_error "CPU核心数不足，至少需要1核"
        exit 1
    fi
}

# 优化系统设置
optimize_system() {
    log_step "优化系统设置..."
    
    # 更新系统
    log_info "更新系统包..."
    apt update && apt upgrade -y
    
    # 安装基础工具
    log_info "安装基础工具..."
    apt install -y curl wget git unzip htop iotop net-tools \
        software-properties-common apt-transport-https ca-certificates \
        gnupg lsb-release
    
    # 配置交换空间（如果需要）
    if [[ "$NEED_SWAP" == "true" ]]; then
        create_swap_space
    fi
    
    # 优化内核参数
    log_info "优化内核参数..."
    cat > /etc/sysctl.d/99-ai-classroom.conf << EOF
# 网络优化
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# 内存优化
vm.swappiness = 10
vm.vfs_cache_pressure = 50

# 文件句柄限制
fs.file-max = 65536
EOF
    sysctl -p /etc/sysctl.d/99-ai-classroom.conf
}

# 创建交换空间
create_swap_space() {
    log_info "创建2GB交换空间..."
    
    # 检查是否已有交换空间
    if [[ $(swapon --show | wc -l) -gt 0 ]]; then
        log_warning "已存在交换空间，跳过创建"
        return
    fi
    
    # 创建交换文件
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    
    # 永久启用
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    
    log_info "交换空间创建完成"
}

# 安装Node.js
install_nodejs() {
    log_step "安装Node.js 18..."
    
    # 检查是否已安装
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_info "Node.js已安装: $NODE_VERSION"
        return
    fi
    
    # 安装Node.js 18
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt install -y nodejs
    
    # 验证安装
    node --version
    npm --version
    
    log_info "Node.js安装完成"
}

# 安装Python 3
install_python() {
    log_step "安装Python 3..."
    
    # 安装Python和相关工具
    apt install -y python3 python3-pip python3-venv python3-dev \
        build-essential libssl-dev libffi-dev
    
    # 升级pip
    python3 -m pip install --upgrade pip
    
    # 验证安装
    python3 --version
    pip3 --version
    
    log_info "Python 3安装完成"
}

# 安装轻量化Docker（可选）
install_docker_lite() {
    log_step "安装轻量化Docker（可选）..."
    
    read -p "是否安装Docker？(y/N): " install_docker
    if [[ $install_docker =~ ^[Yy]$ ]]; then
        # 安装Docker
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        
        # 启动Docker
        systemctl start docker
        systemctl enable docker
        
        # 添加用户到docker组
        usermod -aG docker ubuntu 2>/dev/null || true
        
        log_info "Docker安装完成"
    fi
}

# 克隆项目
clone_project() {
    log_step "克隆AI课堂助手项目..."
    
    PROJECT_DIR="/opt/ai-classroom"
    
    # 删除旧目录（如果存在）
    if [[ -d "$PROJECT_DIR" ]]; then
        rm -rf "$PROJECT_DIR"
    fi
    
    # 克隆项目
    git clone https://github.com/io-oi-ai/Classroom-learning-assistant.git "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    
    # 设置权限
    chown -R ubuntu:ubuntu "$PROJECT_DIR" 2>/dev/null || \
    chown -R $(logname):$(logname) "$PROJECT_DIR" 2>/dev/null || \
    chmod -R 755 "$PROJECT_DIR"
    
    log_info "项目克隆完成: $PROJECT_DIR"
}

# 配置环境变量
configure_environment() {
    log_step "配置环境变量..."
    
    # 获取服务器IP
    SERVER_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip || echo "localhost")
    
    # 提示用户输入API密钥
    echo
    echo "请访问 https://aistudio.google.com/app/apikey 获取Google AI API密钥"
    echo
    read -p "请输入Google AI API密钥: " GOOGLE_API_KEY
    
    if [[ -z "$GOOGLE_API_KEY" ]]; then
        log_error "API密钥不能为空"
        exit 1
    fi
    
    # 创建环境变量文件
    cat > "$PROJECT_DIR/.env" << EOF
GOOGLE_AI_API_KEY=$GOOGLE_API_KEY
PORT=8001
HOST=0.0.0.0
DEBUG=false
NEXT_PUBLIC_API_URL=http://$SERVER_IP:3000
EOF
    
    log_info "环境变量配置完成"
    log_info "服务器IP: $SERVER_IP"
}

# 安装项目依赖
install_dependencies() {
    log_step "安装项目依赖..."
    
    cd "$PROJECT_DIR"
    
    # 安装前端依赖
    log_info "安装前端依赖..."
    npm install --production
    
    # 安装后端依赖
    log_info "安装后端依赖..."
    cd backend
    pip3 install -r requirements.txt
    cd ..
    
    log_info "依赖安装完成"
}

# 构建前端
build_frontend() {
    log_step "构建前端..."
    
    cd "$PROJECT_DIR"
    
    # 构建生产版本
    npm run build
    
    log_info "前端构建完成"
}

# 配置防火墙
configure_firewall() {
    log_step "配置防火墙..."
    
    # 检查防火墙状态
    if command -v ufw &> /dev/null; then
        # 使用ufw
        ufw --force enable
        ufw allow ssh
        ufw allow 22/tcp
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 3000/tcp
        ufw allow 8001/tcp
        
        log_info "UFW防火墙配置完成"
    elif command -v firewall-cmd &> /dev/null; then
        # 使用firewalld
        systemctl start firewalld
        systemctl enable firewalld
        
        firewall-cmd --permanent --add-port=22/tcp
        firewall-cmd --permanent --add-port=80/tcp
        firewall-cmd --permanent --add-port=443/tcp
        firewall-cmd --permanent --add-port=3000/tcp
        firewall-cmd --permanent --add-port=8001/tcp
        firewall-cmd --reload
        
        log_info "Firewalld防火墙配置完成"
    else
        log_warning "未找到防火墙工具，请手动配置端口"
    fi
}

# 创建系统服务
create_systemd_services() {
    log_step "创建系统服务..."
    
    # 后端服务
    cat > /etc/systemd/system/ai-classroom-backend.service << EOF
[Unit]
Description=AI Classroom Backend Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$PROJECT_DIR/backend
Environment=PATH=/usr/bin:/usr/local/bin
ExecStart=/usr/bin/python3 working_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 前端服务
    cat > /etc/systemd/system/ai-classroom-frontend.service << EOF
[Unit]
Description=AI Classroom Frontend Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$PROJECT_DIR
Environment=PATH=/usr/bin:/usr/local/bin
Environment=NODE_ENV=production
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 重新加载systemd
    systemctl daemon-reload
    
    # 启用服务
    systemctl enable ai-classroom-backend
    systemctl enable ai-classroom-frontend
    
    log_info "系统服务创建完成"
}

# 创建管理脚本
create_management_scripts() {
    log_step "创建管理脚本..."
    
    # 启动脚本
    cat > "$PROJECT_DIR/start.sh" << 'EOF'
#!/bin/bash
echo "启动AI课堂助手服务..."
sudo systemctl start ai-classroom-backend
sudo systemctl start ai-classroom-frontend
echo "服务启动完成"
echo "前端地址: http://$(curl -s ifconfig.me):3000"
echo "后端地址: http://$(curl -s ifconfig.me):8001"
EOF

    # 停止脚本
    cat > "$PROJECT_DIR/stop.sh" << 'EOF'
#!/bin/bash
echo "停止AI课堂助手服务..."
sudo systemctl stop ai-classroom-backend
sudo systemctl stop ai-classroom-frontend
echo "服务已停止"
EOF

    # 重启脚本
    cat > "$PROJECT_DIR/restart.sh" << 'EOF'
#!/bin/bash
echo "重启AI课堂助手服务..."
sudo systemctl restart ai-classroom-backend
sudo systemctl restart ai-classroom-frontend
echo "服务重启完成"
echo "前端地址: http://$(curl -s ifconfig.me):3000"
echo "后端地址: http://$(curl -s ifconfig.me):8001"
EOF

    # 状态检查脚本
    cat > "$PROJECT_DIR/status.sh" << 'EOF'
#!/bin/bash
echo "=== AI课堂助手服务状态 ==="
echo
echo "后端服务状态:"
sudo systemctl status ai-classroom-backend --no-pager -l
echo
echo "前端服务状态:"
sudo systemctl status ai-classroom-frontend --no-pager -l
echo
echo "端口占用情况:"
sudo netstat -tlnp | grep -E ":(3000|8001)"
echo
echo "系统资源使用:"
echo "内存使用: $(free -h | awk 'NR==2{printf "已使用 %s / 总计 %s (%.2f%%)\n", $3,$2,$3*100/$2 }')"
echo "磁盘使用: $(df -h / | awk 'NR==2{printf "已使用 %s / 总计 %s (%s)\n", $3,$2,$5}')"
echo "CPU负载: $(uptime | awk -F'load average:' '{print $2}')"
EOF

    # 清理脚本
    cat > "$PROJECT_DIR/cleanup.sh" << 'EOF'
#!/bin/bash
echo "清理AI课堂助手临时文件..."

# 清理临时文件
find /tmp -name "*ai-classroom*" -type f -delete 2>/dev/null || true

# 清理日志文件（保留最近7天）
find . -name "*.log" -type f -mtime +7 -delete 2>/dev/null || true

# 清理上传文件（保留最近30天）
find uploads/ -type f -mtime +30 -delete 2>/dev/null || true

# 清理npm缓存
npm cache clean --force 2>/dev/null || true

echo "清理完成"
EOF

    # 设置执行权限
    chmod +x "$PROJECT_DIR"/*.sh
    
    log_info "管理脚本创建完成"
}

# 创建定时任务
create_cron_jobs() {
    log_step "创建定时任务..."
    
    # 创建定时清理任务
    cat > /etc/cron.d/ai-classroom << EOF
# AI课堂助手定时任务
# 每天凌晨3点清理临时文件
0 3 * * * ubuntu cd $PROJECT_DIR && ./cleanup.sh > /dev/null 2>&1

# 每5分钟检查服务状态
*/5 * * * * root systemctl is-active --quiet ai-classroom-backend || systemctl restart ai-classroom-backend
*/5 * * * * root systemctl is-active --quiet ai-classroom-frontend || systemctl restart ai-classroom-frontend
EOF
    
    log_info "定时任务创建完成"
}

# 启动服务
start_services() {
    log_step "启动服务..."
    
    # 启动后端服务
    systemctl start ai-classroom-backend
    sleep 5
    
    # 启动前端服务
    systemctl start ai-classroom-frontend
    sleep 5
    
    # 检查服务状态
    if systemctl is-active --quiet ai-classroom-backend && \
       systemctl is-active --quiet ai-classroom-frontend; then
        log_info "所有服务启动成功"
    else
        log_error "服务启动失败，请检查日志"
        systemctl status ai-classroom-backend --no-pager
        systemctl status ai-classroom-frontend --no-pager
        exit 1
    fi
}

# 显示部署结果
show_deployment_result() {
    local SERVER_IP=$(curl -s ifconfig.me || echo "your-server-ip")
    
    echo
    echo "=================================="
    echo "🎉 AI课堂助手部署完成！"
    echo "=================================="
    echo
    echo "📱 访问地址:"
    echo "   前端界面: http://$SERVER_IP:3000"
    echo "   后端API:  http://$SERVER_IP:8001"
    echo
    echo "🔧 管理命令:"
    echo "   启动服务: cd $PROJECT_DIR && ./start.sh"
    echo "   停止服务: cd $PROJECT_DIR && ./stop.sh"
    echo "   重启服务: cd $PROJECT_DIR && ./restart.sh"
    echo "   查看状态: cd $PROJECT_DIR && ./status.sh"
    echo "   清理文件: cd $PROJECT_DIR && ./cleanup.sh"
    echo
    echo "📊 系统服务:"
    echo "   sudo systemctl status ai-classroom-backend"
    echo "   sudo systemctl status ai-classroom-frontend"
    echo
    echo "📝 日志查看:"
    echo "   sudo journalctl -u ai-classroom-backend -f"
    echo "   sudo journalctl -u ai-classroom-frontend -f"
    echo
    echo "🔔 重要提醒:"
    echo "   1. 请在云服务器安全组中开放端口: 3000, 8001"
    echo "   2. 定期备份项目目录: $PROJECT_DIR"
    echo "   3. 定期更新系统和依赖包"
    echo
    echo "=================================="
    
    # 显示服务状态
    echo "当前服务状态:"
    systemctl status ai-classroom-backend --no-pager -l | head -5
    systemctl status ai-classroom-frontend --no-pager -l | head -5
}

# 主函数
main() {
    log_info "🚀 开始部署AI课堂助手到轻量服务器..."
    
    check_root
    detect_system
    optimize_system
    install_nodejs
    install_python
    install_docker_lite
    clone_project
    configure_environment
    install_dependencies
    build_frontend
    configure_firewall
    create_systemd_services
    create_management_scripts
    create_cron_jobs
    start_services
    show_deployment_result
    
    log_info "🎉 部署完成！AI课堂助手现在运行在轻量服务器上了！"
}

# 执行主函数
main "$@"

# 检查进程
ps aux | grep -E "(node|python3)" | grep -v grep

# 检查端口
netstat -tlnp | grep -E ":3000|:8001"

# 查看日志
tail -f logs/backend.log
tail -f logs/frontend.log 