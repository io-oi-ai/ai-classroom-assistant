#!/bin/bash

# =================================================================
# AI课堂助手 - 服务器端重建脚本
# 在阿里云服务器上直接重建项目，无需上传
# =================================================================

set -e

echo "🚀 开始在服务器上重建AI课堂助手项目..."

# 创建项目目录
sudo mkdir -p /opt/ai-classroom
sudo chown -R admin:admin /opt/ai-classroom
cd /opt/ai-classroom

# 创建后端目录结构
mkdir -p backend/{app/{api,core,models,services,utils},data,uploads,templates}
mkdir -p frontend/src/{components,pages,services,utils}
mkdir -p components/ui
mkdir -p data

# 创建环境变量文件
cat > .env << 'EOF'
GOOGLE_AI_API_KEY=AIzaSyCbJ8PlTK7UTCkKwCv1uVyM5RXnsMv4qLM
PORT=8001
HOST=0.0.0.0
DEBUG=false
NEXT_PUBLIC_API_URL=http://47.112.185.79:3000
EOF

# 创建后端主服务文件
cat > backend/working_server.py << 'EOF'
import os
import json
import time
import uuid
import mimetypes
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import threading
import traceback

# 设置上传目录
UPLOAD_DIR = "uploads"
DATA_DIR = "data"

# 确保目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# 数据文件路径
COURSES_FILE = os.path.join(DATA_DIR, "courses.json")
FILES_FILE = os.path.join(DATA_DIR, "files.json")
CARDS_FILE = os.path.join(DATA_DIR, "note_cards.json")

def init_data_files():
    """初始化数据文件"""
    if not os.path.exists(COURSES_FILE):
        with open(COURSES_FILE, 'w', encoding='utf-8') as f:
            json.dump({"courses": []}, f, ensure_ascii=False, indent=2)
    
    if not os.path.exists(FILES_FILE):
        with open(FILES_FILE, 'w', encoding='utf-8') as f:
            json.dump({"files": []}, f, ensure_ascii=False, indent=2)
    
    if not os.path.exists(CARDS_FILE):
        with open(CARDS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"cards": []}, f, ensure_ascii=False, indent=2)

def get_courses():
    """获取所有课程"""
    try:
        with open(COURSES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"courses": []}

def save_courses(data):
    """保存课程数据"""
    with open(COURSES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class SimpleAIHandler(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/courses':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            courses_data = get_courses()
            self.wfile.write(json.dumps(courses_data).encode('utf-8'))
            return
        
        # 处理静态文件
        return super().do_GET()

    def do_POST(self):
        if self.path == '/api/courses':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                course_name = data.get('name', '').strip()
                if not course_name:
                    self.wfile.write(json.dumps({"error": "课程名称不能为空"}).encode('utf-8'))
                    return
                
                # 创建新课程
                course_id = str(uuid.uuid4())
                new_course = {
                    "id": course_id,
                    "name": course_name,
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                
                courses_data = get_courses()
                courses_data["courses"].append(new_course)
                save_courses(courses_data)
                
                # 创建课程目录
                course_dir = os.path.join(UPLOAD_DIR, course_id)
                os.makedirs(course_dir, exist_ok=True)
                
                self.wfile.write(json.dumps({
                    "success": True,
                    "course": new_course
                }).encode('utf-8'))
                
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return

if __name__ == "__main__":
    init_data_files()
    
    server_address = ('0.0.0.0', 8001)
    httpd = HTTPServer(server_address, SimpleAIHandler)
    
    print("🚀 AI课堂助手后端服务启动成功")
    print(f"📍 服务地址: http://47.112.185.79:8001")
    print("✅ 基础功能已启用")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
        httpd.shutdown()
EOF

# 创建package.json for frontend
cat > package.json << 'EOF'
{
  "name": "ai-classroom-assistant",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "next dev -p 3000",
    "build": "next build",
    "start": "next start -p 3000",
    "lint": "next lint"
  },
  "dependencies": {
    "next": "14.0.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "@types/node": "20.8.0",
    "@types/react": "18.2.0",
    "@types/react-dom": "18.2.0",
    "typescript": "5.2.0"
  }
}
EOF

# 创建简单的前端页面
mkdir -p app pages
cat > app/page.tsx << 'EOF'
export default function Home() {
  return (
    <div style={{ padding: '50px', textAlign: 'center' }}>
      <h1>🎓 AI课堂助手</h1>
      <p>服务器部署成功！</p>
      <p>后端API: http://47.112.185.79:8001</p>
      <p>前端界面: http://47.112.185.79:3000</p>
    </div>
  )
}
EOF

cat > app/layout.tsx << 'EOF'
export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh">
      <body>{children}</body>
    </html>
  )
}
EOF

# 创建next.config.js
cat > next.config.mjs << 'EOF'
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8001/api/:path*',
      },
    ]
  },
}

export default nextConfig
EOF

# 创建tsconfig.json
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "es6"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}
EOF

echo "✅ 项目结构创建完成"
echo "📦 开始安装依赖..."

# 安装Node.js (如果还没安装)
if ! command -v node &> /dev/null; then
    echo "📥 安装Node.js..."
    curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
    sudo dnf install -y nodejs
fi

# 安装前端依赖
npm install

echo "🎯 启动服务..."

# 启动后端服务
cd backend
nohup python3 working_server.py > ../server.log 2>&1 &

# 等待后端启动
sleep 3

# 启动前端服务
cd ..
nohup npm run dev > frontend.log 2>&1 &

# 检查服务状态
sleep 5
ps aux | grep -E "(node|python3.*working_server)"

echo "🎉 部署完成！"
echo "🌐 前端访问地址: http://47.112.185.79:3000"
echo "🔧 后端API地址: http://47.112.185.79:8001"

# 保存进程ID到文件
echo $! > /tmp/ai-backend.pid
echo $! > /tmp/ai-frontend.pid

echo "⏳ 服务正在后台运行..."
echo "🔍 查看服务状态: ps aux | grep -E '(node|python3.*working_server)'"
echo "🛑 停止服务: kill \$(cat /tmp/ai-backend.pid) \$(cat /tmp/ai-frontend.pid)"

echo "🔧 AI课堂助手 - 服务器重建修复脚本"
echo "==============================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 错误处理函数
handle_error() {
    echo -e "${RED}❌ 错误: $1${NC}"
    exit 1
}

# 成功信息函数
success_msg() {
    echo -e "${GREEN}✅ $1${NC}"
}

# 警告信息函数
warn_msg() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# 信息函数
info_msg() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# 1. 检查当前目录和文件
echo "🔍 检查当前环境..."
pwd
ls -la

# 2. 检查是否在正确的目录
if [ ! -f "package.json" ] || [ ! -d "backend" ]; then
    handle_error "请确保在项目根目录运行此脚本，且包含 package.json 和 backend 目录"
fi

# 3. 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p logs
mkdir -p backend/data
mkdir -p backend/uploads
mkdir -p uploads
success_msg "目录创建完成"

# 4. 检查 Python 和 Node.js
echo "🔧 检查运行环境..."
if ! command -v python3 &> /dev/null; then
    handle_error "Python3 未安装，请先安装 Python3"
fi

if ! command -v node &> /dev/null; then
    handle_error "Node.js 未安装，请先安装 Node.js"
fi

if ! command -v npm &> /dev/null; then
    handle_error "npm 未安装，请先安装 npm"
fi

success_msg "运行环境检查通过"

# 5. 安装 Python 依赖
echo "🐍 安装 Python 依赖..."
if [ -f "requirements.txt" ]; then
    python3 -m pip install --user -r requirements.txt || handle_error "Python 依赖安装失败"
    success_msg "Python 依赖安装完成"
else
    warn_msg "requirements.txt 不存在，跳过 Python 依赖安装"
fi

# 6. 安装 Node.js 依赖
echo "📦 安装 Node.js 依赖..."
if [ -f "package.json" ]; then
    npm install || handle_error "Node.js 依赖安装失败"
    success_msg "Node.js 依赖安装完成"
else
    warn_msg "package.json 不存在，跳过 Node.js 依赖安装"
fi

# 7. 检查防火墙权限并尝试配置
echo "🔥 配置防火墙..."
if command -v firewall-cmd &> /dev/null; then
    if sudo -n true 2>/dev/null; then
        echo "配置防火墙规则..."
        sudo firewall-cmd --permanent --add-port=3000/tcp
        sudo firewall-cmd --permanent --add-port=8001/tcp
        sudo firewall-cmd --reload
        success_msg "防火墙配置完成"
    else
        warn_msg "需要 sudo 权限配置防火墙，请手动运行："
        echo "sudo firewall-cmd --permanent --add-port=3000/tcp"
        echo "sudo firewall-cmd --permanent --add-port=8001/tcp"
        echo "sudo firewall-cmd --reload"
    fi
else
    warn_msg "firewall-cmd 不可用，请手动配置防火墙开放端口 3000 和 8001"
fi

# 8. 停止已有服务
echo "⏹️ 停止已有服务..."
pkill -f "working_server.py" 2>/dev/null || true
pkill -f "node.*dev" 2>/dev/null || true
pkill -f "run.py" 2>/dev/null || true
sleep 2
success_msg "已有服务已停止"

# 9. 启动后端服务
echo "🚀 启动后端服务..."

# 检查后端脚本文件
if [ -f "backend/working_server.py" ]; then
    BACKEND_SCRIPT="backend/working_server.py"
elif [ -f "backend/run.py" ]; then
    BACKEND_SCRIPT="backend/run.py"
elif [ -f "run.py" ]; then
    BACKEND_SCRIPT="run.py"
else
    handle_error "找不到后端启动脚本"
fi

echo "使用后端脚本: $BACKEND_SCRIPT"

# 启动后端服务，输出到日志文件
nohup python3 $BACKEND_SCRIPT > logs/backend.log 2>&1 &
BACKEND_PID=$!

echo "后端服务PID: $BACKEND_PID"
sleep 3

# 检查后端是否启动成功
if ps -p $BACKEND_PID > /dev/null; then
    success_msg "后端服务启动成功 (PID: $BACKEND_PID)"
else
    warn_msg "后端服务可能启动失败，检查日志: logs/backend.log"
    if [ -f "logs/backend.log" ]; then
        echo "最近的后端日志:"
        tail -10 logs/backend.log
    fi
fi

# 10. 启动前端服务
echo "🌐 启动前端服务..."

# 启动前端服务，输出到日志文件
nohup npm run dev > logs/frontend.log 2>&1 &
FRONTEND_PID=$!

echo "前端服务PID: $FRONTEND_PID"
sleep 5

# 检查前端是否启动成功
if ps -p $FRONTEND_PID > /dev/null; then
    success_msg "前端服务启动成功 (PID: $FRONTEND_PID)"
else
    warn_msg "前端服务可能启动失败，检查日志: logs/frontend.log"
    if [ -f "logs/frontend.log" ]; then
        echo "最近的前端日志:"
        tail -10 logs/frontend.log
    fi
fi

# 11. 检查服务状态
echo "📊 检查服务状态..."
sleep 3

# 检查端口占用
if command -v netstat &> /dev/null; then
    echo "端口占用情况:"
    netstat -tlnp | grep -E ":3000|:8001" || warn_msg "未检测到服务端口"
elif command -v ss &> /dev/null; then
    echo "端口占用情况:"
    ss -tlnp | grep -E ":3000|:8001" || warn_msg "未检测到服务端口"
fi

# 检查进程
echo "服务进程:"
ps aux | grep -E "(node|python3)" | grep -v grep || warn_msg "未检测到服务进程"

# 12. 测试服务连接
echo "🔗 测试服务连接..."

# 测试后端
if command -v curl &> /dev/null; then
    echo "测试后端服务..."
    if curl -s http://localhost:8001/api/courses > /dev/null; then
        success_msg "后端服务响应正常"
    else
        warn_msg "后端服务连接失败"
    fi
    
    echo "测试前端服务..."
    if curl -s http://localhost:3000 > /dev/null; then
        success_msg "前端服务响应正常"
    else
        warn_msg "前端服务连接失败"
    fi
else
    warn_msg "curl 不可用，无法测试服务连接"
fi

# 13. 显示完成信息
echo ""
echo "==============================================="
echo -e "${GREEN}🎉 部署修复完成！${NC}"
echo "==============================================="

# 获取服务器IP
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "YOUR_SERVER_IP")

echo ""
echo "📱 访问地址:"
echo -e "${BLUE}🌐 前端: http://$SERVER_IP:3000${NC}"
echo -e "${BLUE}🔧 后端: http://$SERVER_IP:8001${NC}"
echo ""

echo "📋 服务管理命令:"
echo "• 查看后端日志: tail -f logs/backend.log"
echo "• 查看前端日志: tail -f logs/frontend.log"
echo "• 停止所有服务: pkill -f 'working_server.py|node.*dev'"
echo "• 重启服务: ./server_rebuild.sh"
echo ""

echo "🔍 故障排除:"
echo "• 如果服务无法访问，检查防火墙设置"
echo "• 如果端口被占用，使用: lsof -i :3000,8001"
echo "• 如果依赖缺失，重新运行: npm install 和 pip install -r requirements.txt"
echo ""

# 保存PID到文件，方便后续管理
echo $BACKEND_PID > logs/backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo -e "${GREEN}✨ 脚本执行完成！${NC}" 