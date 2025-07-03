#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError, URLError

class SimpleProxyHandler(BaseHTTPRequestHandler):
    """简单HTTP代理处理器"""
    
    def log_message(self, format, *args):
        """记录请求日志"""
        sys.stdout.write("[%s] %s - %s\n" % (
            self.log_date_time_string(),
            self.address_string(),
            format % args
        ))
        sys.stdout.flush()
    
    def do_GET(self):
        """处理GET请求"""
        self.log_message("GET %s", self.path)
        self.handle_request('GET')
    
    def do_POST(self):
        """处理POST请求"""
        self.log_message("POST %s", self.path)
        self.handle_request('POST')
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.log_message("OPTIONS %s", self.path)
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def handle_request(self, method):
        """处理所有类型的请求"""
        try:
            if self.path.startswith('/api/'):
                # API请求转发到后端
                self.proxy_to_backend(method)
            else:
                # 其他请求转发到前端
                self.proxy_to_frontend(method)
        except Exception as e:
            self.log_message("Error handling request: %s", str(e))
            self.send_error(500, "Internal server error")
    
    def proxy_to_backend(self, method):
        """转发API请求到后端服务"""
        backend_url = f"http://localhost:8001{self.path}"
        self.log_message("Proxying to backend: %s", backend_url)
        
        try:
            # 准备请求数据
            data = None
            if method == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    data = self.rfile.read(content_length)
            
            # 创建请求
            req = urllib.request.Request(backend_url, data=data, method=method)
            
            # 添加必要的请求头
            req.add_header('Content-Type', self.headers.get('Content-Type', 'application/json'))
            if data:
                req.add_header('Content-Length', str(len(data)))
            
            # 发送请求
            with urllib.request.urlopen(req, timeout=10) as response:
                # 读取响应
                response_data = response.read()
                
                # 发送响应状态
                self.send_response(response.status)
                
                # 添加CORS头
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                
                # 添加响应头
                content_type = response.headers.get('Content-Type', 'application/json')
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(len(response_data)))
                
                self.end_headers()
                
                # 发送响应内容
                self.wfile.write(response_data)
                
                self.log_message("Backend response: %d bytes, status: %d", 
                                len(response_data), response.status)
                
        except HTTPError as e:
            self.log_message("Backend HTTP error: %d %s", e.code, e.reason)
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                "error": f"Backend error: {e.code} {e.reason}",
                "url": backend_url
            }
            self.wfile.write(json.dumps(error_response).encode())
            
        except URLError as e:
            self.log_message("Backend connection error: %s", str(e))
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                "error": f"Backend connection failed: {str(e)}",
                "url": backend_url
            }
            self.wfile.write(json.dumps(error_response).encode())
    
    def proxy_to_frontend(self, method):
        """转发非API请求到前端服务"""
        frontend_url = f"http://localhost:3000{self.path}"
        self.log_message("Proxying to frontend: %s", frontend_url)
        
        try:
            # 创建请求
            req = urllib.request.Request(frontend_url, method=method)
            
            # 发送请求
            with urllib.request.urlopen(req, timeout=10) as response:
                # 读取响应
                response_data = response.read()
                
                # 发送响应状态
                self.send_response(response.status)
                
                # 复制响应头（过滤一些不需要的）
                for header, value in response.headers.items():
                    if header.lower() not in ['transfer-encoding', 'connection']:
                        self.send_header(header, value)
                
                self.end_headers()
                
                # 发送响应内容
                self.wfile.write(response_data)
                
                self.log_message("Frontend response: %d bytes, status: %d", 
                                len(response_data), response.status)
                
        except Exception as e:
            self.log_message("Frontend error: %s", str(e))
            self.send_response(502)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>AI课堂助手 - 服务不可用</title>
                <meta charset="utf-8">
            </head>
            <body>
                <h1>AI课堂助手</h1>
                <h2>前端服务暂时不可用</h2>
                <p>错误: {str(e)}</p>
                <p>请稍后重试...</p>
            </body>
            </html>
            """
            self.wfile.write(error_html.encode())

def main():
    """启动代理服务器"""
    server_address = ('0.0.0.0', 80)
    
    try:
        httpd = HTTPServer(server_address, SimpleProxyHandler)
        print("🔗 AI课堂助手简单代理服务启动")
        print(f"📍 监听地址: {server_address[0]}:{server_address[1]}")
        print("🎯 前端代理: localhost:3000")
        print("🎯 API代理: localhost:8001")
        print("🚀 服务器已启动，按 Ctrl+C 停止")
        print("=" * 50)
        
        httpd.serve_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号，正在关闭代理服务...")
        httpd.shutdown()
        print("✅ 代理服务已关闭")
    except Exception as e:
        print(f"❌ 启动代理服务失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 