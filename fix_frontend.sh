#!/bin/bash

# 创建前端修复脚本
cat > frontend_fix.sh << 'EOF'
#!/bin/bash

cd /root
echo "🔧 修复前端网络绑定问题..."

echo "⏹️ 停止当前前端服务..."
pkill -f "next dev"
sleep 3

echo "🚀 使用网络模式启动前端..."
nohup npm run dev:network > logs/frontend.log 2>&1 &
sleep 8

echo "🔍 检查服务状态..."
netstat -tlnp | grep ":3000"

echo ""
echo "📋 检查前端日志..."
tail -15 logs/frontend.log

echo ""
echo "🌐 测试前端访问..."
curl -I http://localhost:3000 2>/dev/null | head -2 || echo "本地测试失败"

echo ""
echo "✅ 前端修复完成！"
echo "🌐 请尝试访问: http://47.112.185.79:3000"

EOF

echo "📤 上传前端修复脚本..."
scp frontend_fix.sh root@47.112.185.79:~/

echo "🚀 执行前端修复..."
ssh root@47.112.185.79 'chmod +x frontend_fix.sh && ./frontend_fix.sh'

echo "🧹 清理..."
rm frontend_fix.sh

echo "✅ 前端修复完成！" 