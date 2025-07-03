#!/bin/bash

echo "🔧 设置nginx反向代理解决访问问题..."

# 创建nginx设置脚本
cat > nginx_setup.sh << 'EOF'
#!/bin/bash

echo "📦 安装nginx..."
yum install -y nginx

echo "🔧 配置nginx反向代理..."
cat > /etc/nginx/conf.d/ai-classroom.conf << 'NGINX_CONF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX_CONF

echo "🚀 启动nginx..."
systemctl enable nginx
systemctl start nginx

echo "🔍 检查nginx状态..."
systemctl status nginx --no-pager -l

echo "🌐 检查端口80..."
netstat -tlnp | grep :80

echo "🧪 测试nginx代理..."
curl -I http://localhost/ 2>/dev/null | head -5

echo "✅ nginx设置完成！"
echo "🌐 现在可以通过 http://47.112.185.79 访问"

EOF

echo "📤 上传nginx设置脚本..."
scp nginx_setup.sh root@47.112.185.79:~/

echo "🚀 执行nginx设置..."
ssh root@47.112.185.79 'chmod +x nginx_setup.sh && ./nginx_setup.sh'

echo "🧹 清理..."
rm nginx_setup.sh

echo "✅ nginx代理设置完成！"
echo "🌐 请尝试访问: http://47.112.185.79" 