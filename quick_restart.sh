#!/bin/bash

echo "🔄 快速重启AI课堂助手服务..."

# 创建重启脚本
cat > restart.sh << 'EOF'
#!/bin/bash

echo "🛑 停止所有服务..."
pkill -f next 2>/dev/null
pkill -f python3 2>/dev/null
sleep 3

echo "📁 进入项目目录..."
cd /root

echo "🧹 清理缓存..."
rm -rf .next 2>/dev/null

echo "📋 创建日志目录..."
mkdir -p logs

echo "🚀 启动前端服务..."
nohup npm run dev:network > logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "前端PID: $FRONTEND_PID"

echo "⏳ 等待前端启动..."
sleep 10

echo "🚀 启动后端服务..."
nohup python3 backend/run.py > logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "后端PID: $BACKEND_PID"

echo "⏳ 等待后端启动..."
sleep 5

echo "🚀 启动HTTP代理服务..."
cat > proxy.py << 'PROXY'
import http.server
import socketserver
import urllib.request
import urllib.error

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            if self.path.startswith("/api/"):
                url = "http://127.0.0.1:8001" + self.path
            else:
                url = "http://127.0.0.1:3000" + self.path
            
            req = urllib.request.Request(url)
            response = urllib.request.urlopen(req, timeout=10)
            
            self.send_response(200)
            for header, value in response.headers.items():
                if header.lower() not in ['server', 'date']:
                    self.send_header(header, value)
            self.end_headers()
            self.wfile.write(response.read())
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            error_msg = f"<h1>代理错误</h1><p>{str(e)}</p><p>请检查前后端服务是否正常运行</p>"
            self.wfile.write(error_msg.encode())

print("启动代理服务器在端口80...")
with socketserver.TCPServer(("0.0.0.0", 80), ProxyHandler) as httpd:
    httpd.serve_forever()
PROXY

nohup python3 proxy.py > logs/proxy.log 2>&1 &
PROXY_PID=$!
echo "代理PID: $PROXY_PID"

echo "⏳ 等待所有服务启动..."
sleep 10

echo "🔍 检查服务状态..."
echo "进程状态:"
ps aux | grep -E "(next|python3)" | grep -v grep

echo ""
echo "端口状态:"
netstat -tlnp | grep -E ":(80|3000|8001)"

echo ""
echo "🧪 测试本地访问..."
curl -I http://127.0.0.1/ 2>/dev/null | head -2 || echo "代理测试失败"

echo ""
echo "✅ 重启完成！"
echo "🌐 请尝试访问: http://47.112.185.79"

EOF

echo "📤 上传重启脚本..."
scp restart.sh root@47.112.185.79:~/

echo "🚀 执行重启..."
ssh root@47.112.185.79 'chmod +x restart.sh && ./restart.sh'

echo "🧹 清理..."
rm restart.sh

echo "✅ 重启完成！请尝试访问: http://47.112.185.79" 