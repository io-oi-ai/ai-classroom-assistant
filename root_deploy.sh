#!/bin/bash

echo "🔧 AI课堂助手 - Root用户部署脚本"
echo "================================="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用root用户运行此脚本"
    echo "当前用户: $(whoami)"
    exit 1
fi

echo "✅ Root用户确认"

# 设置项目目录
PROJECT_DIR="/opt/ai-classroom"
ARCHIVE_FILE="/opt/ai-classroom-fixed.tar.gz"

echo "📍 项目目录: $PROJECT_DIR"

# 检查压缩包是否存在
if [ ! -f "$ARCHIVE_FILE" ]; then
    echo "❌ 压缩包不存在: $ARCHIVE_FILE"
    echo "请先上传 ai-classroom-fixed.tar.gz 到 /opt/ 目录"
    exit 1
fi

echo "✅ 压缩包文件存在"

# 清理旧目录
echo "🧹 清理旧项目目录..."
rm -rf "$PROJECT_DIR"

# 创建项目目录
echo "📁 创建项目目录..."
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# 解压文件
echo "📦 解压项目文件..."
tar -xzf "$ARCHIVE_FILE"

if [ $? -ne 0 ]; then
    echo "❌ 文件解压失败"
    exit 1
fi

echo "✅ 文件解压成功"

# 检查关键文件
if [ ! -f "package.json" ] || [ ! -d "backend" ] || [ ! -f "requirements.txt" ]; then
    echo "❌ 项目文件不完整！"
    echo "当前目录内容："
    ls -la
    exit 1
fi

echo "✅ 项目文件检查通过"

# 创建必要目录
echo "📁 创建必要目录..."
mkdir -p logs
mkdir -p backend/data
mkdir -p backend/uploads
mkdir -p uploads

# 设置目录权限
chmod 755 logs backend/data backend/uploads uploads

# 检查Python和Node.js
echo "🔧 检查运行环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装"
    exit 1
fi

echo "✅ 运行环境检查通过"

# 安装Python依赖
echo "🐍 安装Python依赖..."
python3 -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Python依赖安装失败"
    exit 1
fi

echo "✅ Python依赖安装成功"

# 安装Node.js依赖
echo "📦 安装Node.js依赖..."
npm install

if [ $? -ne 0 ]; then
    echo "❌ Node.js依赖安装失败"
    exit 1
fi

echo "✅ Node.js依赖安装成功"

# 配置防火墙
echo "🔥 配置防火墙..."
if command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=3000/tcp 2>/dev/null || true
    firewall-cmd --permanent --add-port=8001/tcp 2>/dev/null || true
    firewall-cmd --reload 2>/dev/null || true
    echo "✅ 防火墙配置完成"
else
    echo "⚠️ firewall-cmd 不可用，请手动配置防火墙"
fi

# 停止已有服务
echo "⏹️ 停止已有服务..."
pkill -f "working_server.py" 2>/dev/null || true
pkill -f "run.py" 2>/dev/null || true
pkill -f "node.*dev" 2>/dev/null || true
pkill -f "npm.*dev" 2>/dev/null || true
sleep 3

echo "✅ 已有服务已停止"

# 启动后端服务
echo "🚀 启动后端服务..."

# 查找后端启动脚本
BACKEND_SCRIPT=""
if [ -f "backend/working_server.py" ]; then
    BACKEND_SCRIPT="backend/working_server.py"
    echo "使用: backend/working_server.py"
elif [ -f "backend/run.py" ]; then
    BACKEND_SCRIPT="backend/run.py"
    echo "使用: backend/run.py"
elif [ -f "run.py" ]; then
    BACKEND_SCRIPT="run.py"
    echo "使用: run.py"
else
    echo "❌ 找不到后端启动脚本"
    echo "查找的文件："
    echo "  - backend/working_server.py"
    echo "  - backend/run.py"
    echo "  - run.py"
    exit 1
fi

# 启动后端
nohup python3 "$BACKEND_SCRIPT" > logs/backend.log 2>&1 &
BACKEND_PID=$!

echo "后端服务PID: $BACKEND_PID"

# 等待后端启动
echo "⏳ 等待后端启动..."
sleep 5

# 检查后端是否启动成功
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败"
    echo "查看后端日志:"
    if [ -f "logs/backend.log" ]; then
        tail -10 logs/backend.log
    fi
    exit 1
fi

# 启动前端服务
echo "🌐 启动前端服务..."
nohup npm run dev > logs/frontend.log 2>&1 &
FRONTEND_PID=$!

echo "前端服务PID: $FRONTEND_PID"

# 等待前端启动
echo "⏳ 等待前端启动..."
sleep 8

# 检查前端是否启动成功
if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo "✅ 前端服务启动成功"
else
    echo "❌ 前端服务启动失败"
    echo "查看前端日志:"
    if [ -f "logs/frontend.log" ]; then
        tail -10 logs/frontend.log
    fi
    exit 1
fi

# 保存PID
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

# 检查服务状态
echo ""
echo "📊 服务状态检查..."
echo "运行中的进程:"
ps aux | grep -E "(node|python3)" | grep -v grep | grep -E "(dev|working_server|run\.py)"

echo ""
echo "端口占用情况:"
if command -v netstat &> /dev/null; then
    netstat -tlnp 2>/dev/null | grep -E ":3000|:8001"
elif command -v ss &> /dev/null; then
    ss -tlnp 2>/dev/null | grep -E ":3000|:8001"
fi

# 获取服务器IP
SERVER_IP="47.112.185.79"

echo ""
echo "🎉 部署完成！"
echo "==============================="
echo "🌐 前端访问: http://$SERVER_IP:3000"
echo "🔧 后端API: http://$SERVER_IP:8001"
echo ""
echo "📋 管理命令:"
echo "  查看后端日志: tail -f $PROJECT_DIR/logs/backend.log"
echo "  查看前端日志: tail -f $PROJECT_DIR/logs/frontend.log"
echo "  停止所有服务: kill \$(cat $PROJECT_DIR/logs/backend.pid) \$(cat $PROJECT_DIR/logs/frontend.pid)"
echo "  重启服务: $PROJECT_DIR/root_deploy.sh"
echo ""
echo "🔍 故障排除:"
echo "  • 如果无法访问，检查阿里云安全组设置"
echo "  • 如果服务异常，查看对应的日志文件"
echo "  • 确保端口3000和8001在安全组中开放"
echo ""

# 测试服务连接
echo "🔗 测试服务连接..."
sleep 2

if command -v curl &> /dev/null; then
    echo "测试后端API..."
    if curl -s --connect-timeout 5 http://localhost:8001 > /dev/null 2>&1; then
        echo "✅ 后端服务响应正常"
    else
        echo "⚠️ 后端服务连接测试失败，可能还在启动中"
    fi
    
    echo "测试前端服务..."
    if curl -s --connect-timeout 5 http://localhost:3000 > /dev/null 2>&1; then
        echo "✅ 前端服务响应正常"
    else
        echo "⚠️ 前端服务连接测试失败，可能还在启动中"
    fi
else
    echo "⚠️ curl不可用，无法测试服务连接"
fi

echo ""
echo "✨ 脚本执行完成！"
echo "如有问题，请查看日志文件获取详细信息。"

# 显示访问提示
echo ""
echo "🎯 接下来的步骤:"
echo "1. 在浏览器中访问: http://47.112.185.79:3000"
echo "2. 如果无法访问，请检查阿里云安全组是否开放了3000和8001端口"
echo "3. 查看服务日志确认服务正常运行" 