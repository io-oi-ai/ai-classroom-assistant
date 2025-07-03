#!/bin/bash

# 创建依赖修复脚本
cat > fix_deps.sh << 'EOF'
#!/bin/bash

cd /root
echo "🔧 修复依赖问题..."

echo "📝 创建正确的requirements.txt..."
cat > requirements.txt << 'PYTHON_DEPS'
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
python-dotenv==1.0.0
pillow==10.1.0
PyPDF2==3.0.1
opencv-python-headless==4.8.1.78
PyMuPDF==1.23.8
requests==2.31.0
numpy==1.24.3
PYTHON_DEPS

echo "✅ requirements.txt已更新"

echo "📦 安装Python依赖..."
python3 -m pip install --user --upgrade pip
python3 -m pip install --user -r requirements.txt

echo "📝 修复Node.js依赖冲突..."
npm install --legacy-peer-deps

echo "🔧 检查安装结果..."
python3 -c "import PIL; print('PIL安装成功')" || echo "PIL安装失败"
npm list next || echo "Next.js检查"

echo "🚀 重新启动后端..."
pkill -f "working_server.py" || echo "没有运行的后端进程"
nohup python3 backend/working_server.py > logs/backend.log 2>&1 &
echo "后端已启动，PID: $!"

sleep 5

echo "🚀 重新启动前端..."
pkill -f "next" || echo "没有运行的前端进程"
nohup npm run dev > logs/frontend.log 2>&1 &
echo "前端已启动，PID: $!"

sleep 10

echo "🔍 检查服务状态..."
ps aux | grep -E "(node|python3)" | grep -v grep | grep -v BT-

echo ""
echo "🌐 检查端口状态..."
netstat -tlnp | grep -E ":3000|:8001"

echo ""
echo "📋 最新日志..."
echo "=== 后端日志 ==="
tail -10 logs/backend.log

echo ""
echo "=== 前端日志 ==="
tail -10 logs/frontend.log

EOF

echo "📤 上传修复脚本..."
scp fix_deps.sh root@47.112.185.79:~/

echo "🚀 执行修复..."
ssh root@47.112.185.79 'chmod +x fix_deps.sh && ./fix_deps.sh'

echo "🧹 清理..."
rm fix_deps.sh

echo "✅ 修复完成！"

EOF 