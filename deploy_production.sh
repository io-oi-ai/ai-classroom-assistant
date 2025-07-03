#!/bin/bash

# AI课堂助手生产环境部署脚本
# 支持阿里云、腾讯云、AWS等主流云平台

set -e

# 配置变量
PROJECT_NAME="ai-classroom-assistant"
GITHUB_REPO="https://github.com/io-oi-ai/Classroom-learning-assistant.git"
DOMAIN_NAME="your-domain.com"  # 替换为你的域名
EMAIL="your-email@example.com"  # 替换为你的邮箱

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 检查系统环境
check_system() {
    log_info "检查系统环境..."
    
    # 检查是否为root用户
    if [ "$EUID" -ne 0 ]; then
        log_error "请使用root用户运行此脚本"
        exit 1
    fi
    
    # 检查操作系统
    if [[ -f /etc/redhat-release ]]; then
        OS="centos"
        INSTALL_CMD="yum install -y"
        UPDATE_CMD="yum update -y"
    elif [[ -f /etc/debian_version ]]; then
        OS="ubuntu"
        INSTALL_CMD="apt-get install -y"
        UPDATE_CMD="apt-get update && apt-get upgrade -y"
    else
        log_error "不支持的操作系统"
        exit 1
    fi
    
    log_success "系统检查完成: $OS"
}

# 安装必要软件
install_dependencies() {
    log_info "安装系统依赖..."
    
    # 更新系统
    $UPDATE_CMD
    
    # 安装基础软件
    if [ "$OS" = "ubuntu" ]; then
        $INSTALL_CMD curl wget git unzip software-properties-common
        
        # 安装Docker
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        
        # 安装Docker Compose
        curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        
        # 安装Nginx
        $INSTALL_CMD nginx
        
        # 安装Certbot (SSL证书)
        $INSTALL_CMD snapd
        snap install core; snap refresh core
        snap install --classic certbot
        ln -s /snap/bin/certbot /usr/bin/certbot
        
    elif [ "$OS" = "centos" ]; then
        $INSTALL_CMD curl wget git unzip
        
        # 安装Docker
        yum install -y yum-utils
        yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
        yum install -y docker-ce docker-ce-cli containerd.io
        systemctl start docker
        systemctl enable docker
        
        # 安装Docker Compose
        curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        
        # 安装Nginx
        $INSTALL_CMD nginx
        systemctl start nginx
        systemctl enable nginx
        
        # 安装Certbot
        $INSTALL_CMD epel-release
        $INSTALL_CMD certbot python3-certbot-nginx
    fi
    
    log_success "依赖安装完成"
}

# 配置防火墙
configure_firewall() {
    log_info "配置防火墙..."
    
    if [ "$OS" = "ubuntu" ]; then
        ufw allow 22/tcp
        ufw allow 80/tcp
        ufw allow 443/tcp
        ufw allow 3000/tcp
        ufw allow 8001/tcp
        ufw --force enable
    elif [ "$OS" = "centos" ]; then
        firewall-cmd --permanent --add-port=22/tcp
        firewall-cmd --permanent --add-port=80/tcp
        firewall-cmd --permanent --add-port=443/tcp
        firewall-cmd --permanent --add-port=3000/tcp
        firewall-cmd --permanent --add-port=8001/tcp
        firewall-cmd --reload
    fi
    
    log_success "防火墙配置完成"
}

# 克隆代码
clone_project() {
    log_info "克隆项目代码..."
    
    PROJECT_DIR="/root/$PROJECT_NAME"
    
    if [ -d "$PROJECT_DIR" ]; then
        log_warning "项目目录已存在，执行更新..."
        cd "$PROJECT_DIR"
        git pull origin main
    else
        git clone "$GITHUB_REPO" "$PROJECT_DIR"
        cd "$PROJECT_DIR"
    fi
    
    log_success "代码获取完成"
}

# 配置环境变量
setup_environment() {
    log_info "配置环境变量..."
    
    cd "/root/$PROJECT_NAME"
    
    # 提示用户输入API密钥
    echo ""
    echo "请输入Google AI API密钥 (获取地址: https://aistudio.google.com/app/apikey):"
    read -r GOOGLE_AI_API_KEY
    
    # 创建.env文件
    cat > .env << EOF
# AI课堂助手生产环境配置
GOOGLE_AI_API_KEY=$GOOGLE_AI_API_KEY

# 服务器配置
PORT=8001
HOST=0.0.0.0
DEBUG=false

# 数据库配置 (如需要)
DATABASE_URL=sqlite:///./data/app.db

# 安全配置
SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_HOSTS=localhost,127.0.0.1,$DOMAIN_NAME

# 文件上传限制 (MB)
MAX_FILE_SIZE_VIDEO=100
MAX_FILE_SIZE_AUDIO=50
MAX_FILE_SIZE_IMAGE=20
MAX_FILE_SIZE_DOCUMENT=10

# 前端配置
NEXT_PUBLIC_API_URL=https://$DOMAIN_NAME/api
EOF
    
    log_success "环境变量配置完成"
}

# 配置Nginx
setup_nginx() {
    log_info "配置Nginx反向代理..."
    
    # 备份原配置
    cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.backup
    
    # 创建站点配置
    cat > "/etc/nginx/sites-available/$PROJECT_NAME" << EOF
server {
    listen 80;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;
    
    # 重定向到HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN_NAME www.$DOMAIN_NAME;
    
    # SSL证书配置 (certbot会自动填充)
    
    # 静态文件
    location /uploads/ {
        alias /root/$PROJECT_NAME/uploads/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API代理
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 前端代理
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # WebSocket支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
EOF
    
    # 启用站点
    if [ "$OS" = "ubuntu" ]; then
        ln -sf "/etc/nginx/sites-available/$PROJECT_NAME" "/etc/nginx/sites-enabled/"
        rm -f /etc/nginx/sites-enabled/default
    elif [ "$OS" = "centos" ]; then
        cp "/etc/nginx/sites-available/$PROJECT_NAME" "/etc/nginx/conf.d/$PROJECT_NAME.conf"
    fi
    
    # 测试配置
    nginx -t
    systemctl reload nginx
    
    log_success "Nginx配置完成"
}

# 申请SSL证书
setup_ssl() {
    log_info "申请SSL证书..."
    
    # 使用Certbot自动申请证书
    certbot --nginx -d "$DOMAIN_NAME" -d "www.$DOMAIN_NAME" --email "$EMAIL" --agree-tos --non-interactive
    
    # 设置自动续期
    echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
    
    log_success "SSL证书配置完成"
}

# 构建和启动Docker容器
deploy_containers() {
    log_info "构建和启动Docker容器..."
    
    cd "/root/$PROJECT_NAME"
    
    # 停止现有容器
    docker-compose down || true
    
    # 构建新镜像
    docker-compose build --no-cache
    
    # 启动容器
    docker-compose up -d
    
    # 等待服务启动
    sleep 10
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        log_success "Docker容器启动成功"
    else
        log_error "Docker容器启动失败"
        docker-compose logs
        exit 1
    fi
}

# 设置监控和日志
setup_monitoring() {
    log_info "设置服务监控..."
    
    # 创建服务监控脚本
    cat > "/root/monitor_$PROJECT_NAME.sh" << EOF
#!/bin/bash
cd "/root/$PROJECT_NAME"

# 检查Docker容器状态
if ! docker-compose ps | grep -q "Up"; then
    echo "\$(date): Services are down, restarting..." >> /var/log/$PROJECT_NAME-monitor.log
    docker-compose up -d
fi

# 检查磁盘空间
DISK_USAGE=\$(df / | awk 'NR==2{print \$5}' | sed 's/%//')
if [ "\$DISK_USAGE" -gt 85 ]; then
    echo "\$(date): Disk usage is \${DISK_USAGE}%" >> /var/log/$PROJECT_NAME-monitor.log
fi
EOF
    
    chmod +x "/root/monitor_$PROJECT_NAME.sh"
    
    # 设置定时任务
    echo "*/5 * * * * /root/monitor_$PROJECT_NAME.sh" | crontab -
    
    log_success "监控设置完成"
}

# 显示部署信息
show_deployment_info() {
    echo ""
    echo "======================================"
    log_success "🎉 AI课堂助手部署完成！"
    echo "======================================"
    echo ""
    echo "🌐 访问地址:"
    echo "   • HTTPS: https://$DOMAIN_NAME"
    echo "   • HTTP:  http://$DOMAIN_NAME (自动跳转HTTPS)"
    echo ""
    echo "🔧 管理命令:"
    echo "   • 查看状态: cd /root/$PROJECT_NAME && docker-compose ps"
    echo "   • 查看日志: cd /root/$PROJECT_NAME && docker-compose logs -f"
    echo "   • 重启服务: cd /root/$PROJECT_NAME && docker-compose restart"
    echo "   • 停止服务: cd /root/$PROJECT_NAME && docker-compose down"
    echo ""
    echo "📁 重要目录:"
    echo "   • 项目目录: /root/$PROJECT_NAME"
    echo "   • 上传文件: /root/$PROJECT_NAME/uploads"
    echo "   • 数据文件: /root/$PROJECT_NAME/backend/data"
    echo "   • 日志文件: /var/log/$PROJECT_NAME-monitor.log"
    echo ""
    echo "🔐 安全提醒:"
    echo "   • 请定期备份数据"
    echo "   • 监控服务器资源使用情况"
    echo "   • 及时更新系统安全补丁"
    echo ""
    echo "======================================"
}

# 主函数
main() {
    echo "🚀 AI课堂助手自动化部署脚本"
    echo "支持Ubuntu/CentOS系统"
    echo ""
    
    # 获取用户输入
    echo "请输入你的域名 (例如: classroom.example.com):"
    read -r DOMAIN_NAME
    
    echo "请输入你的邮箱 (用于SSL证书):"
    read -r EMAIL
    
    echo ""
    echo "即将开始部署，按Enter继续..."
    read -r
    
    # 执行部署步骤
    check_system
    install_dependencies
    configure_firewall
    clone_project
    setup_environment
    setup_nginx
    setup_ssl
    deploy_containers
    setup_monitoring
    show_deployment_info
}

# 执行主函数
main "$@" 