#!/bin/bash

echo "🔧 修复并部署AI课堂助手..."

# 创建修复脚本
cat > fix_deployment.sh << 'EOF'
#!/bin/bash

echo "🔍 当前位置: $(pwd)"
echo ""

echo "📁 检查压缩文件位置..."
ls -la /opt/ai-classroom-fixed.tar.gz

echo ""
echo "📦 移动并解压项目文件..."
cd /root
cp /opt/ai-classroom-fixed.tar.gz ./
echo "✅ 文件已复制到root目录"

echo ""
echo "🎁 开始解压..."
tar -xzf ai-classroom-fixed.tar.gz
echo "✅ 解压完成"

echo ""
echo "📁 检查解压结果..."
ls -la package.json requirements.txt backend/ 2>/dev/null || echo "⚠️ 检查解压内容..."
ls -la | head -20

echo ""
echo "🔧 创建必要目录..."
mkdir -p logs backend/data backend/uploads uploads

echo ""
echo "📦 安装Python依赖..."
if [ -f requirements.txt ]; then
    python3 -m pip install --user -r requirements.txt
    echo "✅ Python依赖安装完成"
else
    echo "❌ requirements.txt不存在"
fi

echo ""
echo "📦 安装Node.js依赖..."
if [ -f package.json ]; then
    npm install
    echo "✅ Node.js依赖安装完成"
else
    echo "❌ package.json不存在"
fi

echo ""
echo "🚀 启动后端服务..."
if [ -f backend/working_server.py ]; then
    nohup python3 backend/working_server.py > logs/backend.log 2>&1 &
    echo "✅ 后端服务已启动"
    sleep 3
else
    echo "❌ backend/working_server.py不存在"
fi

echo ""
echo "🚀 启动前端服务..."
if [ -f package.json ]; then
    nohup npm run dev > logs/frontend.log 2>&1 &
    echo "✅ 前端服务已启动"
    sleep 5
else
    echo "❌ 无法启动前端，package.json不存在"
fi

echo ""
echo "🔍 检查服务状态..."
ps aux | grep -E "(node|python3)" | grep -v grep | grep -v BT-

echo ""
echo "🌐 检查端口状态..."
netstat -tlnp | grep -E ":3000|:8001"

echo ""
echo "📋 查看日志..."
echo "=== 后端日志 ==="
if [ -f logs/backend.log ]; then
    tail -10 logs/backend.log
else
    echo "后端日志文件不存在"
fi

echo ""
echo "=== 前端日志 ==="
if [ -f logs/frontend.log ]; then
    tail -10 logs/frontend.log
else
    echo "前端日志文件不存在"
fi

EOF

echo "📤 上传修复脚本到服务器..."
scp fix_deployment.sh root@47.112.185.79:~/

echo ""
echo "🚀 执行修复和部署..."
ssh root@47.112.185.79 'chmod +x fix_deployment.sh && ./fix_deployment.sh'

echo ""
echo "🧹 清理临时文件..."
rm fix_deployment.sh

echo ""
echo "✅ 部署完成！请检查 http://47.112.185.79:3000" 