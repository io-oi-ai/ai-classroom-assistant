#!/bin/bash

echo "🚀 开始为root用户部署AI课堂助手..."

# 服务器信息
SERVER_IP="47.112.185.79"
USER="root"
PASSWORD="Wxc7758258"

echo "📋 服务器信息："
echo "  IP: $SERVER_IP"
echo "  用户: $USER"
echo ""

# 创建临时脚本文件
cat > temp_deploy_script.sh << 'EOF'
#!/bin/bash

echo "🔍 检查当前目录..."
pwd
echo ""

echo "📁 当前目录内容："
ls -la
echo ""

echo "🔍 查找项目文件..."
find . -name "ai-classroom-fixed.tar.gz" -o -name "package.json" -o -name "requirements.txt" 2>/dev/null
echo ""

# 检查是否在正确目录
if [ -f "ai-classroom-fixed.tar.gz" ]; then
    echo "✅ 找到压缩文件，开始解压..."
    tar -xzf ai-classroom-fixed.tar.gz
    echo "✅ 解压完成"
else
    echo "❌ 未找到ai-classroom-fixed.tar.gz文件"
    echo "🔍 搜索整个系统中的文件..."
    find / -name "ai-classroom-fixed.tar.gz" 2>/dev/null | head -5
fi

echo ""
echo "📁 解压后检查关键文件..."
ls -la package.json requirements.txt backend/ 2>/dev/null || echo "⚠️ 关键文件不存在"

echo ""
echo "🔧 创建必要目录..."
mkdir -p logs backend/data backend/uploads uploads

echo ""
echo "📦 检查Python和Node.js..."
python3 --version
node --version
npm --version

EOF

echo "📤 上传并执行部署脚本..."
scp temp_deploy_script.sh root@$SERVER_IP:~/
ssh root@$SERVER_IP 'chmod +x temp_deploy_script.sh && ./temp_deploy_script.sh'

echo ""
echo "🧹 清理临时文件..."
rm temp_deploy_script.sh

echo "✅ 检查完成！" 