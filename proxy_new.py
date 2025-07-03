#!/usr/bin/env python3
import sys
import json
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError, URLError

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request('GET')
    
    def do_POST(self):
        self.handle_request('POST')
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_request(self, method):
        print(f"[PROXY] {method} {self.path}")
        
        if self.path.startswith('/api/'):
            # API请求转发到后端
            url = f"http://localhost:8001{self.path}"
        else:
            # 其他请求转发到前端
            url = f"http://localhost:3000{self.path}"
        
        try:
            data = None
            if method == 'POST':
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    data = self.rfile.read(content_length)
            
            req = urllib.request.Request(url, data=data, method=method)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                response_data = response.read()
                
                self.send_response(response.status)
                self.send_header('Access-Control-Allow-Origin', '*')
                
                for header, value in response.headers.items():
                    if header.lower() not in ['transfer-encoding', 'connection']:
                        self.send_header(header, value)
                
                self.end_headers()
                self.wfile.write(response_data)
                
                print(f"[PROXY] Success: {len(response_data)} bytes from {url}")
                
        except Exception as e:
            print(f"[PROXY] Error: {e}")
            self.send_response(502)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(f"Proxy Error: {e}".encode())

if __name__ == '__main__':
    httpd = HTTPServer(('0.0.0.0', 80), ProxyHandler)
    print("Proxy server starting on port 80...")
    httpd.serve_forever() 