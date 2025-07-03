#!/bin/bash

# AI课堂助手快速部署脚本 (简化版)
# 适合初学者和快速测试

set -e

# 配置
PROJECT_NAME="ai-classroom"
REPO_URL="https://github.com/io-oi-ai/Classroom-learning-assistant.git"

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
echo_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo "🚀 AI课堂助手快速部署"
echo "============================"

# 1. 安装Docker
echo_info "安装Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
fi

# 2. 安装Docker Compose
echo_info "安装Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# 3. 克隆代码
echo_info "下载项目代码..."
if [ -d "$PROJECT_NAME" ]; then
    cd "$PROJECT_NAME"
    git pull origin main
else
    git clone "$REPO_URL" "$PROJECT_NAME"
    cd "$PROJECT_NAME"
fi

# 4. 配置环境变量
echo_info "配置环境变量..."
echo "请输入Google AI API密钥："
read -r API_KEY

cat > .env << EOF
GOOGLE_AI_API_KEY=$API_KEY
PORT=8001
HOST=0.0.0.0
DEBUG=false
NEXT_PUBLIC_API_URL=http://$(curl -s ifconfig.me):3000
EOF

# 5. 启动服务
echo_info "启动服务..."
docker-compose down || true
docker-compose up -d --build

# 6. 等待服务启动
echo_info "等待服务启动..."
sleep 30

# 7. 检查状态
if docker-compose ps | grep -q "Up"; then
    echo_success "部署成功！"
    echo ""
    echo "🌐 访问地址："
    echo "   前端: http://$(curl -s ifconfig.me):3000"
    echo "   后端: http://$(curl -s ifconfig.me):8001"
    echo ""
    echo "📋 管理命令："
    echo "   查看状态: docker-compose ps"
    echo "   查看日志: docker-compose logs -f"
    echo "   重启服务: docker-compose restart"
    echo "   停止服务: docker-compose down"
else
    echo_error "部署失败，请查看日志："
    docker-compose logs
fi 