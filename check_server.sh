#!/bin/bash

echo "正在连接服务器检查状态..."

# 检查tar文件是否存在
echo "=== 检查压缩文件 ==="
ssh root@47.112.185.79 'ls -la ai-classroom-fixed.tar.gz'

echo ""
echo "=== 检查当前目录内容 ==="
ssh root@47.112.185.79 'pwd && ls -la'

echo ""
echo "=== 检查是否有项目目录 ==="
ssh root@47.112.185.79 'find . -name "package.json" -o -name "requirements.txt" -o -name "backend" -type d 2>/dev/null | head -10'

echo ""
echo "=== 解压项目文件到当前目录 ==="
ssh root@47.112.185.79 'if [ -f ai-classroom-fixed.tar.gz ]; then echo "找到压缩文件，开始解压..."; tar -xzf ai-classroom-fixed.tar.gz; echo "解压完成"; else echo "未找到压缩文件"; fi'

echo ""
echo "=== 解压后检查文件 ==="
ssh root@47.112.185.79 'ls -la package.json requirements.txt backend/ 2>/dev/null || echo "文件仍然不存在"' 