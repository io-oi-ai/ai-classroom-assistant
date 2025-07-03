#!/bin/bash

echo "🔄 正在重启前端服务..."

# 停止现有的前端服务
echo "⏹️ 停止现有前端服务..."
pkill -f 'next dev' 2>/dev/null || echo "没有发现正在运行的前端服务"

# 等待进程完全停止
sleep 3

# 检查端口3000是否被占用，如果是则强制停止
if lsof -i:3000 >/dev/null 2>&1; then
    echo "🚫 端口3000被占用，正在强制停止..."
    fuser -k 3000/tcp 2>/dev/null || true
    sleep 2
fi

# 确保logs目录存在
mkdir -p logs

# 启动前端服务
echo "🚀 启动前端服务（网络模式）..."
cd /opt/ai-classroom
nohup npm run dev:network > logs/frontend.log 2>&1 & 

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
if ps aux | grep 'next dev' | grep -v grep >/dev/null; then
    echo "✅ 前端服务启动成功！"
    echo "📍 访问地址: http://47.112.185.79:3000"
    echo "📋 服务状态:"
    ps aux | grep 'next dev' | grep -v grep
else
    echo "❌ 前端服务启动失败"
    echo "📋 查看错误日志:"
    tail -20 logs/frontend.log 2>/dev/null || echo "无法读取日志文件"
fi

echo "🏁 前端重启完成" 