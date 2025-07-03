#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import urllib.request
import urllib.parse
import urllib.error
from http.server import SimpleHTTPRequestHandler, HTTPServer
from threading import Thread

class APIProxyHandler(SimpleHTTPRequestHandler):
    """API代理处理器，将API请求转发到后端服务"""
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        if self.path.startswith('/api/'):
            self.proxy_to_backend('GET')
        else:
            # 非API请求，转发到前端服务器
            self.proxy_to_frontend()
    
    def do_POST(self):
        """处理POST请求"""
        if self.path.startswith('/api/'):
            self.proxy_to_backend('POST')
        else:
            self.proxy_to_frontend()
    
    def proxy_to_backend(self, method):
        """将API请求代理到后端服务"""
        try:
            backend_url = f"http://localhost:8001{self.path}"
            
            # 准备请求数据
            request_data = None
            if method == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    request_data = self.rfile.read(content_length)
            
            # 创建请求
            req = urllib.request.Request(backend_url, data=request_data, method=method)
            
            # 复制请求头
            for header_name, header_value in self.headers.items():
                if header_name.lower() not in ['host', 'content-length']:
                    req.add_header(header_name, header_value)
            
            # 发送请求到后端
            with urllib.request.urlopen(req, timeout=30) as response:
                # 发送响应状态
                self.send_response(response.status)
                
                # 添加CORS头和其他响应头
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                
                # 复制其他响应头
                for header_name, header_value in response.headers.items():
                    if header_name.lower() not in ['transfer-encoding', 'connection']:
                        self.send_header(header_name, header_value)
                
                self.end_headers()
                
                # 转发响应内容
                self.wfile.write(response.read())
                
        except urllib.error.HTTPError as e:
            # 后端返回错误
            self.send_response(e.code)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                "error": f"后端服务错误: {e.code} {e.reason}",
                "backend_url": backend_url
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
            
        except Exception as e:
            # 连接错误或其他错误
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                "error": f"代理错误: {str(e)}",
                "backend_url": backend_url
            }
            self.wfile.write(json.dumps(error_response).encode('utf-8'))
    
    def proxy_to_frontend(self):
        """将非API请求代理到前端服务器"""
        try:
            frontend_url = f"http://localhost:3000{self.path}"
            
            # 创建请求
            req = urllib.request.Request(frontend_url)
            
            # 复制请求头
            for header_name, header_value in self.headers.items():
                if header_name.lower() not in ['host']:
                    req.add_header(header_name, header_value)
            
            # 发送请求到前端
            with urllib.request.urlopen(req, timeout=30) as response:
                # 发送响应状态
                self.send_response(response.status)
                
                # 复制响应头
                for header_name, header_value in response.headers.items():
                    if header_name.lower() not in ['transfer-encoding', 'connection']:
                        self.send_header(header_name, header_value)
                
                self.end_headers()
                
                # 转发响应内容
                self.wfile.write(response.read())
                
        except Exception as e:
            # 前端服务器错误
            self.send_response(502)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            error_html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>代理错误</title></head>
            <body>
                <h1>AI课堂助手</h1>
                <h2>前端服务不可用</h2>
                <p>错误信息: {str(e)}</p>
                <p>请稍后重试...</p>
            </body>
            </html>
            """
            self.wfile.write(error_html.encode('utf-8'))

def start_proxy_server():
    """启动代理服务器"""
    server_address = ('0.0.0.0', 80)
    httpd = HTTPServer(server_address, APIProxyHandler)
    
    print("🔗 AI课堂助手代理服务启动")
    print("📍 代理地址: http://0.0.0.0:80")
    print("🎯 前端代理: localhost:3000")
    print("🎯 API代理: localhost:8001")
    print("=" * 50)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 代理服务器正在关闭...")
        httpd.shutdown()
        print("✅ 代理服务器已关闭")

if __name__ == '__main__':
    start_proxy_server() 