#!/bin/bash

echo "🏥 AI课堂助手服务器全面诊断..."

# 创建诊断脚本
cat > diagnosis.sh << 'EOF'
#!/bin/bash

echo "=== AI课堂助手服务器诊断报告 ==="
echo "时间: $(date)"
echo ""

echo "🔍 1. 进程状态检查"
echo "Next.js 进程:"
ps aux | grep next | grep -v grep || echo "❌ Next.js 未运行"

echo ""
echo "Python 进程:"
ps aux | grep python3 | grep -v grep || echo "❌ Python 服务未运行"

echo ""
echo "🌐 2. 端口监听状态"
echo "端口 80 (HTTP代理):"
netstat -tlnp | grep :80 || echo "❌ 端口 80 未监听"

echo ""
echo "端口 3000 (前端):"
netstat -tlnp | grep :3000 || echo "❌ 端口 3000 未监听"

echo ""
echo "端口 8001 (后端API):"
netstat -tlnp | grep :8001 || echo "❌ 端口 8001 未监听"

echo ""
echo "🧪 3. 本地连接测试"
echo "测试 HTTP 代理 (端口 80):"
timeout 5 curl -s -I http://127.0.0.1/ | head -2 || echo "❌ HTTP代理无响应"

echo ""
echo "测试前端 (端口 3000):"
timeout 5 curl -s -I http://127.0.0.1:3000/ | head -2 || echo "❌ 前端无响应"

echo ""
echo "测试后端 API (端口 8001):"
timeout 5 curl -s -I http://127.0.0.1:8001/ | head -2 || echo "❌ 后端API无响应"

echo ""
echo "🔥 4. 防火墙状态"
echo "防火墙状态: $(firewall-cmd --state 2>/dev/null || echo '未知')"
echo "开放端口: $(firewall-cmd --list-ports 2>/dev/null || echo '无法获取')"

echo ""
echo "📁 5. 关键文件检查"
echo "项目目录:"
ls -la /root/ | grep -E "(package\.json|app|node_modules)" | head -3

echo ""
echo "日志文件:"
ls -la /root/logs/ 2>/dev/null || echo "日志目录不存在"

echo ""
echo "🚀 6. 重启服务建议"
echo "如果服务异常，执行以下命令重启:"
echo "# 停止所有服务"
echo "pkill -f next"
echo "pkill -f python3"
echo ""
echo "# 重新启动"
echo "cd /root"
echo "nohup npm run dev:network > logs/frontend.log 2>&1 &"
echo "nohup python3 backend/run.py > logs/backend.log 2>&1 &"
echo "# 启动代理(如果需要)"
echo "nohup python3 -c \"..." # 代理脚本

echo ""
echo "=== 诊断完成 ==="

EOF

echo "📤 上传诊断脚本..."
scp diagnosis.sh root@47.112.185.79:~/

echo "🔍 执行诊断..."
ssh root@47.112.185.79 'chmod +x diagnosis.sh && ./diagnosis.sh'

echo "🧹 清理..."
rm diagnosis.sh

echo "✅ 诊断完成！" 