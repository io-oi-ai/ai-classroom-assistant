#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产环境启动脚本
专为部署设计，支持环境变量配置和多进程运行
"""

import uvicorn
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def main():
    """主启动函数"""
    
    # 环境配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))
    workers = int(os.getenv("WORKERS", "4"))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    api_key = os.getenv("GOOGLE_AI_API_KEY")
    
    # 检查必要的环境变量
    if not api_key:
        print("❌ 错误：未找到 GOOGLE_AI_API_KEY 环境变量")
        print("请在 .env 文件中设置 GOOGLE_AI_API_KEY=你的API密钥")
        sys.exit(1)
    
    print("🚀 AI课堂助手 - 生产环境启动")
    print("=" * 50)
    print(f"📍 服务地址: http://{host}:{port}")
    print(f"👥 工作进程: {workers}")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    print(f"🔑 API密钥: 已配置")
    print(f"🌍 环境: {'开发' if debug else '生产'}")
    print("=" * 50)
    
    try:
        if debug:
            # 开发模式：单进程，自动重载
            uvicorn.run(
                "app.main:app",
                host=host,
                port=port,
                reload=True,
                reload_dirs=["app"],
                log_level="debug"
            )
        else:
            # 生产模式：多进程，优化性能
            uvicorn.run(
                "app.main:app",
                host=host,
                port=port,
                workers=workers,
                access_log=True,
                log_level="info",
                reload=False
            )
    except KeyboardInterrupt:
        print("\n📴 服务器关闭")
    except Exception as e:
        print(f"❌ 启动失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 