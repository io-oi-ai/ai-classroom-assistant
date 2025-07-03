#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import urllib.parse
from http.server import SimpleHTTPRequestHandler, HTTPServer
from threading import Thread

# 全局配置
UPLOAD_DIR = "uploads"
DATA_DIR = "data"
PORT = 8001

# 确保目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

def init_data_files():
    """初始化数据文件"""
    
    # 初始化courses.json
    courses_file = os.path.join(DATA_DIR, "courses.json")
    if not os.path.exists(courses_file):
        courses_data = {
            "courses": [
                {
                    "id": "course_001",
                    "name": "数学基础",
                    "created_at": "2024-01-01T00:00:00Z",
                    "file_count": 0
                },
                {
                    "id": "course_002", 
                    "name": "物理原理",
                    "created_at": "2024-01-01T00:00:00Z",
                    "file_count": 0
                }
            ]
        }
        with open(courses_file, 'w', encoding='utf-8') as f:
            json.dump(courses_data, f, ensure_ascii=False, indent=2)
    
    # 初始化files.json
    files_file = os.path.join(DATA_DIR, "files.json")
    if not os.path.exists(files_file):
        files_data = {"files": []}
        with open(files_file, 'w', encoding='utf-8') as f:
            json.dump(files_data, f, ensure_ascii=False, indent=2)
    
    # 初始化note_cards.json
    cards_file = os.path.join(DATA_DIR, "note_cards.json")
    if not os.path.exists(cards_file):
        cards_data = {"cards": []}
        with open(cards_file, 'w', encoding='utf-8') as f:
            json.dump(cards_data, f, ensure_ascii=False, indent=2)

def load_json_file(filename):
    """加载JSON文件"""
    try:
        filepath = os.path.join(DATA_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"加载文件失败 {filename}: {str(e)}")
        return {}

def save_json_file(filename, data):
    """保存JSON文件"""
    try:
        filepath = os.path.join(DATA_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存文件失败 {filename}: {str(e)}")
        return False

class SimpleAIHandler(SimpleHTTPRequestHandler):
    """简化的AI课堂助手HTTP处理器"""
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        # 添加CORS头
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        try:
            if self.path == '/api/courses':
                # 获取所有课程
                courses_data = load_json_file("courses.json")
                self.wfile.write(json.dumps(courses_data).encode('utf-8'))
                
            elif self.path.startswith('/api/courses/') and self.path.endswith('/files'):
                # 获取课程文件
                course_id = self.path.split('/')[-2]
                files_data = load_json_file("files.json")
                course_files = [f for f in files_data.get("files", []) if f.get("course_id") == course_id]
                self.wfile.write(json.dumps({"files": course_files}).encode('utf-8'))
                
            elif self.path.startswith('/api/courses/') and self.path.endswith('/cards'):
                # 获取课程笔记卡片
                course_id = self.path.split('/')[-2]
                cards_data = load_json_file("note_cards.json")
                course_cards = [c for c in cards_data.get("cards", []) if c.get("course_id") == course_id]
                self.wfile.write(json.dumps({"cards": course_cards}).encode('utf-8'))
                
            elif self.path == '/api/health':
                # 健康检查
                self.wfile.write(json.dumps({
                    "status": "healthy",
                    "timestamp": time.time(),
                    "message": "AI课堂助手后端服务正常运行"
                }).encode('utf-8'))
                
            else:
                # 默认返回API信息
                self.wfile.write(json.dumps({
                    "name": "AI课堂助手",
                    "version": "1.0.0",
                    "status": "running",
                    "endpoints": [
                        "/api/courses",
                        "/api/courses/{id}/files", 
                        "/api/courses/{id}/cards",
                        "/api/chat",
                        "/api/upload",
                        "/api/health"
                    ]
                }).encode('utf-8'))
                
        except Exception as e:
            print(f"GET请求处理错误: {str(e)}")
            self.wfile.write(json.dumps({
                "error": f"服务器错误: {str(e)}"
            }).encode('utf-8'))
    
    def do_POST(self):
        """处理POST请求"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        try:
            # 解析请求数据
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
            else:
                data = {}
            
            if self.path == '/api/chat':
                # 聊天功能
                message = data.get('message', '')
                course_id = data.get('courseId', '')
                
                # 简单的AI回复（可以后续接入真正的AI API）
                ai_response = f"您好！我收到了您关于'{message}'的问题。"
                if course_id:
                    ai_response += f"\n这个问题与课程 {course_id} 相关。"
                ai_response += "\n\n我是AI学习助手，很高兴为您服务！如需更智能的对话，请配置AI API。"
                
                response = {
                    "response": ai_response,
                    "timestamp": time.time(),
                    "course_id": course_id
                }
                
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            elif self.path == '/api/upload':
                # 文件上传功能
                file_name = data.get('fileName', f'upload_{int(time.time())}.txt')
                course_id = data.get('courseId', 'course_001')
                content = data.get('content', '')
                
                # 保存文件
                file_path = os.path.join(UPLOAD_DIR, course_id, file_name)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # 记录文件信息
                files_data = load_json_file("files.json")
                if "files" not in files_data:
                    files_data["files"] = []
                
                new_file = {
                    "id": f"file_{int(time.time())}",
                    "name": file_name,
                    "type": "document",
                    "path": file_path,
                    "course_id": course_id,
                    "created_at": time.time(),
                    "summary": content[:100] + "..." if len(content) > 100 else content
                }
                
                files_data["files"].append(new_file)
                save_json_file("files.json", files_data)
                
                response = {
                    "success": True,
                    "file": new_file,
                    "message": "文件上传成功"
                }
                
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            elif self.path == '/api/generate-handwritten-note':
                # 生成手写笔记功能
                title = data.get('title', '学习笔记')
                content = data.get('content', '')
                
                # 简化的笔记生成（返回成功信息）
                response = {
                    "success": True,
                    "note_id": f"note_{int(time.time())}",
                    "title": title,
                    "message": "手写笔记生成功能暂未实现，但系统正常工作",
                    "image_url": "/placeholder.png"
                }
                
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
            else:
                # 未知的POST请求
                self.wfile.write(json.dumps({
                    "error": f"未知的API端点: {self.path}"
                }).encode('utf-8'))
                
        except Exception as e:
            print(f"POST请求处理错误: {str(e)}")
            self.wfile.write(json.dumps({
                "error": f"服务器错误: {str(e)}"
            }).encode('utf-8'))

def start_server():
    """启动HTTP服务器"""
    init_data_files()
    
    server_address = ('0.0.0.0', PORT)
    httpd = HTTPServer(server_address, SimpleAIHandler)
    
    print(f"🚀 AI课堂助手后端服务启动")
    print(f"📍 服务地址: http://0.0.0.0:{PORT}")
    print(f"🔗 API根地址: http://0.0.0.0:{PORT}/api/")
    print(f"💡 健康检查: http://0.0.0.0:{PORT}/api/health")
    print("=" * 50)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 服务器正在关闭...")
        httpd.shutdown()
        print("✅ 服务器已关闭")

if __name__ == '__main__':
    start_server() 