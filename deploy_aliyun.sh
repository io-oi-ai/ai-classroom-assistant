#!/bin/bash
# AI课堂助手 - 阿里云自动部署脚本
# 适用于阿里云ECS Ubuntu 20.04+

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 显示欢迎信息
show_welcome() {
    clear
    echo "========================================"
    echo "🚀 AI课堂助手 - 阿里云部署脚本"
    echo "========================================"
    echo "系统要求："
    echo "- 阿里云ECS (Ubuntu 20.04+)"
    echo "- 2核4GB内存（最低）"
    echo "- 50GB存储空间"
    echo "- 已开放80、443端口"
    echo "========================================"
}

# 检查系统信息
check_system() {
    print_info "检查系统环境..."
    
    # 检查是否为 Ubuntu
    if ! grep -q "Ubuntu" /etc/os-release; then
        print_error "此脚本仅支持 Ubuntu 系统"
        exit 1
    fi
    
    # 检查系统版本
    VERSION=$(lsb_release -rs | cut -d'.' -f1)
    if [ "$VERSION" -lt 20 ]; then
        print_error "Ubuntu 版本过低，需要 20.04+，当前版本: $(lsb_release -rs)"
        exit 1
    fi
    
    # 检查内存
    MEMORY=$(free -m | awk 'NR==2{printf "%.0f", $2/1024}')
    if [ "$MEMORY" -lt 3 ]; then
        print_warning "内存不足4GB，建议升级配置，当前: ${MEMORY}GB"
    fi
    
    print_success "系统检查通过 - Ubuntu $(lsb_release -rs)"
}

# 更新系统
update_system() {
    print_info "更新系统包..."
    export DEBIAN_FRONTEND=noninteractive
    apt update -y
    apt upgrade -y
    apt install -y curl wget git unzip software-properties-common
    print_success "系统更新完成"
}

# 安装 Node.js 18
install_nodejs() {
    print_info "安装 Node.js 18..."
    
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -ge 18 ]; then
            print_info "Node.js 已安装，版本: $(node -v)"
            return
        fi
    fi
    
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    apt-get install -y nodejs
    
    # 验证安装
    if command -v node &> /dev/null; then
        print_success "Node.js 安装成功，版本: $(node -v)"
    else
        print_error "Node.js 安装失败"
        exit 1
    fi
}

# 安装 Python 3.9+
install_python() {
    print_info "安装 Python 3.9+..."
    
    apt install -y python3.9 python3.9-venv python3-pip python3.9-dev
    
    # 创建 python3 软链接
    if [ ! -L "/usr/bin/python3" ]; then
        ln -sf /usr/bin/python3.9 /usr/bin/python3
    fi
    
    python3 --version
    print_success "Python 安装成功，版本: $(python3 --version)"
}

# 安装 Nginx
install_nginx() {
    print_info "安装 Nginx..."
    
    apt install -y nginx
    systemctl enable nginx
    systemctl start nginx
    
    # 检查 Nginx 状态
    if systemctl is-active --quiet nginx; then
        print_success "Nginx 安装并启动成功"
    else
        print_error "Nginx 启动失败"
        exit 1
    fi
}

# 安装 PM2
install_pm2() {
    print_info "安装 PM2 进程管理器..."
    
    npm install -g pm2
    
    if command -v pm2 &> /dev/null; then
        print_success "PM2 安装成功"
    else
        print_error "PM2 安装失败"
        exit 1
    fi
}

# 配置防火墙
setup_firewall() {
    print_info "配置防火墙..."
    
    # 安装 ufw
    apt install -y ufw
    
    # 配置防火墙规则
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow 22/tcp    # SSH
    ufw allow 80/tcp    # HTTP
    ufw allow 443/tcp   # HTTPS
    ufw --force enable
    
    print_success "防火墙配置完成"
}

# 部署项目
deploy_project() {
    print_info "部署 AI课堂助手项目..."
    
    # 设置项目目录
    PROJECT_DIR="/var/www/ai-classroom"
    
    # 如果是从当前目录部署
    if [ -f "package.json" ] && [ -d "backend" ]; then
        print_info "从当前目录复制项目..."
        mkdir -p /var/www
        cp -r . $PROJECT_DIR
    else
        print_error "未找到项目文件，请确保在项目根目录运行此脚本"
        exit 1
    fi
    
    cd $PROJECT_DIR
    
    # 设置权限
    chown -R www-data:www-data $PROJECT_DIR
    chmod -R 755 $PROJECT_DIR
    
    print_success "项目文件复制完成"
}

# 配置前端
setup_frontend() {
    print_info "配置前端应用..."
    
    cd /var/www/ai-classroom
    
    # 安装依赖
    npm install
    
    # 构建生产版本
    npm run build
    
    print_success "前端构建完成"
}

# 配置后端
setup_backend() {
    print_info "配置后端应用..."
    
    cd /var/www/ai-classroom/backend
    
    # 创建虚拟环境
    python3 -m venv venv
    source venv/bin/activate
    
    # 安装依赖
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # 配置环境变量
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# AI课堂助手生产环境配置
GOOGLE_AI_API_KEY=请填入你的Google_AI_API密钥
HOST=0.0.0.0
PORT=8001
DEBUG=False
WORKERS=4
ENVIRONMENT=production
EOF
        print_warning "请编辑 /var/www/ai-classroom/backend/.env 文件，填入你的 Google AI API 密钥"
    fi
    
    print_success "后端配置完成"
}

# 配置 Nginx
setup_nginx() {
    print_info "配置 Nginx 反向代理..."
    
    # 获取服务器公网IP
    PUBLIC_IP=$(curl -s http://checkip.amazonaws.com/ || curl -s http://ipv4.icanhazip.com/ || echo "your-server-ip")
    
    cat > /etc/nginx/sites-available/ai-classroom << EOF
server {
    listen 80;
    server_name $PUBLIC_IP _;
    client_max_body_size 50M;
    
    # 安全头部
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # 前端应用
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }
    
    # 后端API
    location /api/ {
        proxy_pass http://localhost:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
    }
    
    # 静态文件
    location /uploads/ {
        alias /var/www/ai-classroom/backend/uploads/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # 健康检查
    location /health {
        access_log off;
        return 200 "healthy\\n";
        add_header Content-Type text/plain;
    }
}
EOF
    
    # 启用站点
    ln -sf /etc/nginx/sites-available/ai-classroom /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # 测试配置
    nginx -t
    if [ $? -eq 0 ]; then
        systemctl reload nginx
        print_success "Nginx 配置完成"
    else
        print_error "Nginx 配置错误"
        exit 1
    fi
}

# 配置 PM2
setup_pm2() {
    print_info "配置 PM2 进程管理..."
    
    cd /var/www/ai-classroom
    
    cat > ecosystem.config.js << EOF
module.exports = {
  apps: [
    {
      name: 'ai-classroom-frontend',
      script: 'npm',
      args: 'start',
      cwd: '/var/www/ai-classroom',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        NODE_ENV: 'production',
        PORT: 3000
      },
      log_file: '/var/log/pm2/ai-classroom-frontend.log',
      out_file: '/var/log/pm2/ai-classroom-frontend-out.log',
      error_file: '/var/log/pm2/ai-classroom-frontend-error.log',
      time: true
    },
    {
      name: 'ai-classroom-backend',
      script: '/var/www/ai-classroom/backend/venv/bin/python',
      args: 'production_run.py',
      cwd: '/var/www/ai-classroom/backend',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '2G',
      env: {
        PYTHONPATH: '/var/www/ai-classroom/backend'
      },
      log_file: '/var/log/pm2/ai-classroom-backend.log',
      out_file: '/var/log/pm2/ai-classroom-backend-out.log',
      error_file: '/var/log/pm2/ai-classroom-backend-error.log',
      time: true
    }
  ]
};
EOF
    
    # 创建日志目录
    mkdir -p /var/log/pm2
    chown -R www-data:www-data /var/log/pm2
    
    # 启动应用
    pm2 start ecosystem.config.js
    pm2 startup
    pm2 save
    
    print_success "PM2 配置完成"
}

# 创建管理脚本
create_management_scripts() {
    print_info "创建管理脚本..."
    
    # 创建启动脚本
    cat > /usr/local/bin/ai-classroom-start << 'EOF'
#!/bin/bash
echo "启动 AI课堂助手..."
pm2 start /var/www/ai-classroom/ecosystem.config.js
systemctl start nginx
echo "服务启动完成"
EOF
    
    # 创建停止脚本
    cat > /usr/local/bin/ai-classroom-stop << 'EOF'
#!/bin/bash
echo "停止 AI课堂助手..."
pm2 stop all
echo "服务停止完成"
EOF
    
    # 创建重启脚本
    cat > /usr/local/bin/ai-classroom-restart << 'EOF'
#!/bin/bash
echo "重启 AI课堂助手..."
pm2 restart all
systemctl restart nginx
echo "服务重启完成"
EOF
    
    # 创建状态检查脚本
    cat > /usr/local/bin/ai-classroom-status << 'EOF'
#!/bin/bash
echo "=== AI课堂助手服务状态 ==="
echo "PM2 进程状态:"
pm2 status
echo ""
echo "Nginx 状态:"
systemctl status nginx --no-pager -l
echo ""
echo "磁盘使用情况:"
df -h
echo ""
echo "内存使用情况:"
free -h
EOF
    
    # 设置执行权限
    chmod +x /usr/local/bin/ai-classroom-*
    
    print_success "管理脚本创建完成"
}

# 配置 SSL (可选)
setup_ssl() {
    read -p "是否配置免费SSL证书？(y/n): " setup_ssl_choice
    if [[ $setup_ssl_choice =~ ^[Yy]$ ]]; then
        print_info "配置 Let's Encrypt SSL证书..."
        
        # 安装 certbot
        apt install -y certbot python3-certbot-nginx
        
        read -p "请输入你的域名 (例: example.com): " domain_name
        if [ ! -z "$domain_name" ]; then
            # 更新 Nginx 配置为域名
            sed -i "s/server_name .*/server_name $domain_name;/" /etc/nginx/sites-available/ai-classroom
            systemctl reload nginx
            
            # 获取SSL证书
            certbot --nginx -d $domain_name --non-interactive --agree-tos --email admin@$domain_name
            
            # 设置自动续期
            echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
            
            print_success "SSL证书配置完成"
        else
            print_warning "跳过SSL配置"
        fi
    fi
}

# 显示部署结果
show_results() {
    clear
    PUBLIC_IP=$(curl -s http://checkip.amazonaws.com/ || curl -s http://ipv4.icanhazip.com/ || echo "your-server-ip")
    
    echo "========================================"
    echo "🎉 AI课堂助手部署完成！"
    echo "========================================"
    echo "访问地址: http://$PUBLIC_IP"
    echo "管理界面: 前端界面"
    echo ""
    echo "📋 管理命令:"
    echo "启动服务: ai-classroom-start"
    echo "停止服务: ai-classroom-stop"
    echo "重启服务: ai-classroom-restart"
    echo "查看状态: ai-classroom-status"
    echo ""
    echo "📝 重要提醒:"
    echo "1. 请编辑 /var/www/ai-classroom/backend/.env"
    echo "   填入你的 Google AI API 密钥"
    echo "2. 确保阿里云安全组已开放 80、443 端口"
    echo "3. 如有域名，建议配置SSL证书"
    echo ""
    echo "📊 查看日志:"
    echo "pm2 logs"
    echo "tail -f /var/log/nginx/access.log"
    echo ""
    echo "🔧 配置API密钥后重启："
    echo "ai-classroom-restart"
    echo "========================================"
}

# 主函数
main() {
    show_welcome
    
    # 检查是否为 root
    if [ "$EUID" -ne 0 ]; then
        print_error "请使用 root 权限运行此脚本"
        echo "使用命令: sudo bash deploy_aliyun.sh"
        exit 1
    fi
    
    read -p "按回车键开始安装，或 Ctrl+C 取消..."
    
    check_system
    update_system
    install_nodejs
    install_python
    install_nginx
    install_pm2
    setup_firewall
    deploy_project
    setup_frontend
    setup_backend
    setup_nginx
    setup_pm2
    create_management_scripts
    setup_ssl
    
    show_results
}

# 运行主函数
main "$@" 