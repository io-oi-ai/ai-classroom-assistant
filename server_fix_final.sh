#!/bin/bash

echo "🔧 AI课堂助手 - 最终修复脚本"
echo "==============================="

# 检查当前位置
echo "📍 当前位置: $(pwd)"

# 检查项目文件
if [ ! -f "package.json" ] || [ ! -d "backend" ]; then
    echo "❌ 项目文件不完整！"
    echo "需要的文件/目录："
    echo "  ✓ package.json"
    echo "  ✓ backend/"
    echo "  ✓ requirements.txt"
    echo ""
    echo "请重新上传完整的项目文件到当前目录"
    exit 1
fi

echo "✅ 项目文件检查通过"

# 创建必要目录
echo "📁 创建必要目录..."
mkdir -p logs
mkdir -p backend/data
mkdir -p backend/uploads
mkdir -p uploads

# 设置权限
chmod 755 logs
chmod 755 backend/data
chmod 755 backend/uploads
chmod 755 uploads

# 安装Python依赖
echo "🐍 安装Python依赖..."
if [ -f "requirements.txt" ]; then
    python3 -m pip install --user -r requirements.txt
    if [ $? -eq 0 ]; then
        echo "✅ Python依赖安装成功"
    else
        echo "❌ Python依赖安装失败"
        exit 1
    fi
else
    echo "❌ requirements.txt 不存在"
    exit 1
fi

# 安装Node.js依赖
echo "📦 安装Node.js依赖..."
if [ -f "package.json" ]; then
    npm install --production
    if [ $? -eq 0 ]; then
        echo "✅ Node.js依赖安装成功"
    else
        echo "❌ Node.js依赖安装失败"
        exit 1
    fi
else
    echo "❌ package.json 不存在"
    exit 1
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
cd $(dirname $BACKEND_SCRIPT)
nohup python3 $(basename $BACKEND_SCRIPT) > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd - > /dev/null

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
    echo "请检查 logs/backend.log 获取详细错误信息"
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
    echo "请检查 logs/frontend.log 获取详细错误信息"
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
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "YOUR_SERVER_IP")

echo ""
echo "🎉 部署完成！"
echo "==============================="
echo "🌐 前端访问: http://$SERVER_IP:3000"
echo "🔧 后端API: http://$SERVER_IP:8001"
echo ""
echo "📋 管理命令:"
echo "  查看后端日志: tail -f logs/backend.log"
echo "  查看前端日志: tail -f logs/frontend.log"
echo "  停止所有服务: kill \$(cat logs/backend.pid) \$(cat logs/frontend.pid)"
echo "  重启服务: ./server_fix_final.sh"
echo ""
echo "🔍 故障排除:"
echo "  • 如果无法访问，检查防火墙和安全组设置"
echo "  • 如果服务异常，查看对应的日志文件"
echo "  • 确保端口3000和8001在防火墙中开放"
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