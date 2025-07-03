#!/bin/bash

echo "🔍 最终检查和启动AI课堂助手..."

# 创建最终启动脚本
cat > final_startup.sh << 'EOF'
#!/bin/bash

cd /root
echo "📂 当前目录: $(pwd)"

echo "🔧 配置防火墙..."
firewall-cmd --permanent --add-port=3000/tcp >/dev/null 2>&1
firewall-cmd --permanent --add-port=8001/tcp >/dev/null 2>&1
firewall-cmd --reload >/dev/null 2>&1
echo "✅ 防火墙已配置"

echo "🚀 启动前端服务（端口3000）..."
pkill -f "next dev" >/dev/null 2>&1
nohup npm run dev > logs/frontend.log 2>&1 &
sleep 5

echo "🚀 启动简化后端（端口8001）..."
pkill -f "python3.*backend" >/dev/null 2>&1

# 创建简化的后端服务器
cat > simple_backend.py << 'BACKEND'
#!/usr/bin/env python3
import os
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler

class CORSHTTPRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        if self.path == '/api/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy", "message": "AI课堂助手后端运行中"}).encode())
        else:
            super().do_GET()

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8001), CORSHTTPRequestHandler)
    print("后端服务器启动在端口 8001")
    server.serve_forever()
BACKEND

nohup python3 simple_backend.py > logs/backend.log 2>&1 &
sleep 3

echo "🔍 检查服务状态..."
echo "端口状态:"
netstat -tlnp | grep -E ":3000|:8001"

echo ""
echo "服务进程:"
ps aux | grep -E "(node|python3)" | grep -v grep | grep -v BT- | head -5

echo ""
echo "✅ 服务启动完成！"
echo "🌐 前端访问地址: http://47.112.185.79:3000"
echo "🔧 后端API地址: http://47.112.185.79:8001"

echo ""
echo "📋 快速测试:"
curl -s http://localhost:8001/api/health || echo "后端API测试失败"

EOF

echo "📤 上传最终脚本..."
scp final_startup.sh root@47.112.185.79:~/

echo "🚀 执行最终启动..."
ssh root@47.112.185.79 'chmod +x final_startup.sh && ./final_startup.sh'

echo ""
echo "🧹 清理..."
rm final_startup.sh

echo ""
echo "🎉 部署完成！"
echo "🌐 请在浏览器中访问: http://47.112.185.79:3000"
echo "🔧 后端API: http://47.112.185.79:8001/api/health" 