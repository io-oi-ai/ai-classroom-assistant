#!/bin/bash

# 创建服务启动脚本
cat > remote_start.sh << 'EOF'
#!/bin/bash

cd /root
echo "📂 当前目录: $(pwd)"

echo "🔧 创建日志目录..."
mkdir -p logs

echo "📦 安装Python依赖..."
python3 -m pip install --user -r requirements.txt

echo "📦 安装Node.js依赖..."
npm install

echo "🚀 启动后端服务..."
nohup python3 backend/working_server.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "后端PID: $BACKEND_PID"

echo "⏳ 等待后端启动..."
sleep 5

echo "🚀 启动前端服务..."
nohup npm run dev > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端PID: $FRONTEND_PID"

echo "⏳ 等待前端启动..."
sleep 10

echo "🔍 检查服务状态..."
ps aux | grep -E "(node|python3)" | grep -v grep | grep -v BT-

echo ""
echo "🌐 检查端口状态..."
netstat -tlnp | grep -E ":3000|:8001"

echo ""
echo "📋 查看后端日志..."
tail -20 logs/backend.log

echo ""
echo "📋 查看前端日志..."
tail -20 logs/frontend.log

echo ""
echo "✅ 服务启动完成！"
echo "🌐 访问地址: http://47.112.185.79:3000"

EOF

echo "📤 上传启动脚本..."
scp remote_start.sh root@47.112.185.79:~/

echo "🚀 执行启动脚本..."
ssh root@47.112.185.79 'chmod +x remote_start.sh && ./remote_start.sh'

echo "🧹 清理..."
rm remote_start.sh

echo "✅ 完成！" 