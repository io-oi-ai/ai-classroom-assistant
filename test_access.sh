#!/bin/bash

echo "🔍 测试前端访问..."

# 创建测试脚本
cat > access_test.sh << 'EOF'
#!/bin/bash

echo "📋 服务状态检查..."
echo "Next.js 进程:"
ps aux | grep next | grep -v grep

echo ""
echo "端口监听状态:"
netstat -tlnp | grep :3000

echo ""
echo "🧪 本地访问测试..."
echo "HTTP响应头:"
curl -I http://localhost:3000 2>/dev/null | head -5

echo ""
echo "🌐 外部访问测试..."
echo "从外部IP测试:"
curl -I http://47.112.185.79:3000 2>/dev/null | head -5

echo ""
echo "🔧 防火墙状态..."
firewall-cmd --list-ports 2>/dev/null | grep 3000 || echo "防火墙端口未开放"

echo ""
echo "📁 检查项目文件..."
ls -la app/page.tsx 2>/dev/null || echo "页面文件不存在"

echo ""
echo "🚀 如果访问失败，尝试重新构建..."
if ! curl -s http://localhost:3000 > /dev/null; then
    echo "本地访问失败，可能需要重新构建"
    npm run build
    echo "构建完成，重新启动..."
    pkill -f next
    nohup npm run start:network > logs/frontend.log 2>&1 &
    sleep 5
    echo "生产模式已启动"
fi

EOF

echo "📤 上传测试脚本..."
scp access_test.sh root@47.112.185.79:~/

echo "🧪 执行访问测试..."
ssh root@47.112.185.79 'chmod +x access_test.sh && ./access_test.sh'

echo "🧹 清理..."
rm access_test.sh

echo "✅ 测试完成！" 