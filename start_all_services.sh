#!/bin/bash

echo "🚀 AI课堂助手完整服务启动"
echo "========================================"

cd /opt/ai-classroom

# 停止现有服务
echo "🛑 停止所有现有服务..."
pkill -f 'python.*proxy' 2>/dev/null || true
pkill -f 'python.*backend' 2>/dev/null || true
pkill -f 'python.*run.py' 2>/dev/null || true
pkill -f 'next dev' 2>/dev/null || true
sleep 3

# 清理端口
for port in 80 3000 8001; do
    if lsof -i:$port >/dev/null 2>&1; then
        echo "🚫 清理端口 $port..."
        fuser -k $port/tcp 2>/dev/null || true
    fi
done
sleep 2

# 创建必要目录
mkdir -p logs
mkdir -p backend/data

echo "🔧 启动服务..."

# 1. 启动后端服务
echo "📡 启动后端服务 (端口8001)..."
cd backend
nohup python simple_backend.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# 2. 启动前端服务
echo "🌐 启动前端服务 (端口3000)..."
nohup npm run dev:network > logs/frontend.log 2>&1 &
FRONTEND_PID=$!

# 3. 启动代理服务
echo "🔗 启动代理服务 (端口80)..."
nohup python api_proxy.py > logs/proxy.log 2>&1 &
PROXY_PID=$!

# 等待服务启动
echo "⏳ 等待所有服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."

backend_status="❌"
frontend_status="❌"
proxy_status="❌"

if ps -p $BACKEND_PID > /dev/null; then
    backend_status="✅"
fi

if ps -p $FRONTEND_PID > /dev/null; then
    frontend_status="✅"
fi

if ps -p $PROXY_PID > /dev/null; then
    proxy_status="✅"
fi

echo "📊 服务状态报告:"
echo "   后端服务 (8001): $backend_status"
echo "   前端服务 (3000): $frontend_status"
echo "   代理服务 (80):   $proxy_status"

# 测试健康检查
echo "🧪 服务测试..."
sleep 2

echo "🔍 本地后端健康检查:"
curl -s http://localhost:8001/api/health || echo "后端服务测试失败"

echo -e "\n🔍 本地前端测试:"
curl -s -I http://localhost:3000 | head -1 || echo "前端服务测试失败"

echo -e "\n🔍 代理服务测试:"
curl -s -I http://localhost:80 | head -1 || echo "代理服务测试失败"

echo ""
echo "🎯 访问地址:"
echo "   主站点: http://47.112.185.79"
echo "   API测试: http://47.112.185.79/api/health"
echo ""
echo "🏁 所有服务启动完成！" 