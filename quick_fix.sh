#!/bin/bash

echo "🔧 AI课堂助手 - 一键修复脚本"
echo "================================"

# 检查基本环境
if [ ! -f "package.json" ]; then
    echo "❌ 当前目录没有 package.json，请确保在项目根目录运行"
    echo "正确的目录应该包含: package.json, backend/, requirements.txt"
    exit 1
fi

echo "✅ 项目目录检查通过"

# 创建必要目录
echo "📁 创建必要目录..."
mkdir -p logs backend/data backend/uploads uploads

# 安装依赖
echo "📦 安装 Python 依赖..."
python3 -m pip install --user -r requirements.txt

echo "📦 安装 Node.js 依赖..."
npm install

# 停止已有服务
echo "⏹️ 停止已有服务..."
pkill -f "working_server.py" 2>/dev/null || true
pkill -f "node.*dev" 2>/dev/null || true
pkill -f "run.py" 2>/dev/null || true
sleep 2

# 启动后端服务
echo "🚀 启动后端服务..."
if [ -f "backend/working_server.py" ]; then
    echo "使用 backend/working_server.py"
    nohup python3 backend/working_server.py > logs/backend.log 2>&1 &
    BACKEND_PID=$!
elif [ -f "backend/run.py" ]; then
    echo "使用 backend/run.py"
    nohup python3 backend/run.py > logs/backend.log 2>&1 &
    BACKEND_PID=$!
elif [ -f "run.py" ]; then
    echo "使用 run.py"
    nohup python3 run.py > logs/backend.log 2>&1 &
    BACKEND_PID=$!
else
    echo "❌ 找不到后端启动脚本"
    echo "请检查是否存在以下文件之一："
    echo "  - backend/working_server.py"
    echo "  - backend/run.py"
    echo "  - run.py"
    exit 1
fi

echo "后端 PID: $BACKEND_PID"
sleep 3

# 检查后端是否启动成功
if ps -p $BACKEND_PID > /dev/null 2>&1; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败，查看日志:"
    tail -5 logs/backend.log
fi

# 启动前端服务
echo "🌐 启动前端服务..."
nohup npm run dev > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端 PID: $FRONTEND_PID"
sleep 5

# 检查前端是否启动成功
if ps -p $FRONTEND_PID > /dev/null 2>&1; then
    echo "✅ 前端服务启动成功"
else
    echo "❌ 前端服务启动失败，查看日志:"
    tail -5 logs/frontend.log
fi

# 显示服务状态
echo ""
echo "📊 服务状态检查..."
echo "运行中的进程:"
ps aux | grep -E "(node|python3)" | grep -v grep | head -5

echo ""
echo "端口占用情况:"
if command -v netstat &> /dev/null; then
    netstat -tlnp 2>/dev/null | grep -E ":3000|:8001" || echo "未检测到端口占用"
elif command -v ss &> /dev/null; then
    ss -tlnp 2>/dev/null | grep -E ":3000|:8001" || echo "未检测到端口占用"
fi

# 获取服务器IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "YOUR_SERVER_IP")

echo ""
echo "🎉 部署完成！"
echo "================================"
echo "🌐 前端访问: http://$SERVER_IP:3000"
echo "🔧 后端API: http://$SERVER_IP:8001"
echo ""
echo "📋 管理命令:"
echo "  查看后端日志: tail -f logs/backend.log"
echo "  查看前端日志: tail -f logs/frontend.log"
echo "  停止所有服务: pkill -f 'working_server.py|node.*dev|run.py'"
echo ""

# 保存PID
echo $BACKEND_PID > logs/backend.pid 2>/dev/null || true
echo $FRONTEND_PID > logs/frontend.pid 2>/dev/null || true

echo "💡 如果无法访问，请检查:"
echo "  1. 防火墙是否开放端口 3000 和 8001"
echo "  2. 服务器安全组是否允许这些端口"
echo "  3. 查看日志文件确认服务正常运行" 