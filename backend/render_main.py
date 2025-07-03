#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# 环境变量
PORT = int(os.environ.get("PORT", 10000))
HOST = os.environ.get("HOST", "0.0.0.0")

# 创建FastAPI应用
app = FastAPI(
    title="AI课堂助手后端", 
    version="1.0.0",
    description="AI课堂助手后端API服务"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模拟数据
COURSES_DATA = {
    "courses": [
        {
            "id": "course_001",
            "name": "数学基础",
            "description": "数学基础知识学习",
            "created_at": "2024-01-01T00:00:00Z",
            "file_count": 0
        },
        {
            "id": "course_002",
            "name": "物理原理", 
            "description": "物理原理知识学习",
            "created_at": "2024-01-01T00:00:00Z",
            "file_count": 0
        },
        {
            "id": "course_003",
            "name": "化学基础",
            "description": "化学基础知识学习", 
            "created_at": "2024-01-01T00:00:00Z",
            "file_count": 0
        }
    ]
}

FILES_DATA = {"files": []}
CARDS_DATA = {"cards": []}

# 根路径
@app.get("/")
def read_root():
    return {
        "name": "AI课堂助手后端",
        "version": "1.0.0",
        "status": "运行中",
        "timestamp": time.time(),
        "message": "欢迎使用AI课堂助手！",
        "endpoints": {
            "health": "/health",
            "courses": "/api/courses",
            "chat": "/api/chat"
        }
    }

# 健康检查
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI课堂助手后端",
        "timestamp": time.time(),
        "message": "服务正常运行"
    }

# 获取所有课程
@app.get("/api/courses")
def get_courses():
    return COURSES_DATA

# 获取课程文件
@app.get("/api/courses/{course_id}/files")
def get_course_files(course_id: str):
    course_files = [f for f in FILES_DATA["files"] if f.get("course_id") == course_id]
    return {"files": course_files}

# 获取课程卡片
@app.get("/api/courses/{course_id}/cards")
def get_course_cards(course_id: str):
    course_cards = [c for c in CARDS_DATA["cards"] if c.get("course_id") == course_id]
    return {"cards": course_cards}

# 聊天接口
@app.post("/api/chat")
def chat_endpoint(request: dict):
    try:
        message = request.get('message', '')
        course_id = request.get('courseId', '')
        
        # 简单的AI回复
        responses = [
            f"您好！我是AI学习助手，很高兴为您服务！",
            f"关于您的问题「{message}」，我正在思考中...",
            f"这是一个很好的问题！让我来帮您分析一下。",
            f"基于您的描述，我建议您可以从以下几个角度思考：",
            f"1. 首先理解基本概念和原理",
            f"2. 然后通过实例加深理解", 
            f"3. 最后进行练习和应用",
            f"如果您需要更详细的解答，请提供更多上下文信息。"
        ]
        
        ai_response = "\n".join(responses)
        if course_id:
            ai_response += f"\n\n💡 这个问题与课程《{course_id}》相关，建议您查阅相关课程资料。"
        
        return {
            "response": ai_response,
            "timestamp": time.time(),
            "course_id": course_id,
            "message_length": len(message),
            "status": "success"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"聊天处理失败: {str(e)}")

# 文件上传接口
@app.post("/api/upload")
def upload_endpoint(request: dict):
    try:
        file_name = request.get('fileName', f'upload_{int(time.time())}.txt')
        course_id = request.get('courseId', 'course_001')
        content = request.get('content', '')
        
        # 模拟文件处理
        processed_content = f"文件已处理：{file_name}\n内容长度：{len(content)} 字符\n处理时间：{time.time()}"
        
        return {
            "success": True,
            "message": "文件上传处理成功",
            "file_name": file_name,
            "course_id": course_id,
            "processed_content": processed_content,
            "timestamp": time.time()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

# 启动消息
@app.on_event("startup")
def startup_event():
    print("🚀 AI课堂助手后端启动成功!")
    print(f"📍 运行地址: http://{HOST}:{PORT}")
    print(f"📖 API文档: http://{HOST}:{PORT}/docs")
    print(f"🔍 交互式API: http://{HOST}:{PORT}/redoc")

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="info") 