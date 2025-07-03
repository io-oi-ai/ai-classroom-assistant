#!/bin/bash

echo "🚀 AI课堂助手后端启动脚本"
echo "=================================="

# 进入后端目录
cd /opt/ai-classroom/backend

# 停止现有的Python进程
echo "🛑 停止现有服务..."
pkill -f 'python.*backend' 2>/dev/null || true
pkill -f 'python.*run.py' 2>/dev/null || true
sleep 2

# 检查端口
if lsof -i:8001 >/dev/null 2>&1; then
    echo "🚫 端口8001被占用，强制停止..."
    fuser -k 8001/tcp 2>/dev/null || true
    sleep 2
fi

# 创建logs目录
mkdir -p ../logs

# 启动后端服务
echo "🚀 启动后端服务..."
nohup python simple_backend.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
if ps -p $BACKEND_PID > /dev/null; then
    echo "✅ 后端服务启动成功！"
    echo "📍 PID: $BACKEND_PID"
    echo "🔗 健康检查: http://47.112.185.79:8001/api/health"
    
    # 测试健康检查
    echo "🧪 测试健康检查..."
    sleep 2
    curl -s http://localhost:8001/api/health || echo "健康检查失败"
else
    echo "❌ 后端服务启动失败"
    echo "📋 查看错误日志:"
    tail -20 ../logs/backend.log
fi

echo "🏁 启动脚本完成" 