#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import uuid
import time
import base64
import cgi
import requests
import PyPDF2
import cv2
import fitz  # PyMuPDF
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from PIL import Image, ImageDraw, ImageFont
import math
import re
import uvicorn
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置上传目录
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads')
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

# 确保目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

# 数据文件路径
COURSES_FILE = os.path.join(DATA_DIR, 'courses.json')
FILES_FILE = os.path.join(DATA_DIR, 'files.json')
NOTE_CARDS_FILE = os.path.join(DATA_DIR, 'note_cards.json')

def init_data_files():
    """初始化数据文件"""
    if not os.path.exists(COURSES_FILE):
        with open(COURSES_FILE, 'w', encoding='utf-8') as f:
            json.dump({"courses": []}, f, ensure_ascii=False, indent=2)
    
    if not os.path.exists(FILES_FILE):
        with open(FILES_FILE, 'w', encoding='utf-8') as f:
            json.dump({"files": []}, f, ensure_ascii=False, indent=2)

    if not os.path.exists(NOTE_CARDS_FILE):
        with open(NOTE_CARDS_FILE, 'w', encoding='utf-8') as f:
            json.dump({"cards": []}, f, ensure_ascii=False, indent=2)

def get_courses():
    """获取课程列表"""
    with open(COURSES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_courses(data):
    """保存课程数据"""
    with open(COURSES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_files():
    """获取文件列表"""
    with open(FILES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_files(data):
    """保存文件数据"""
    with open(FILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_note_cards(course_id=None):
    """获取笔记卡片"""
    with open(NOTE_CARDS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        cards = data.get("cards", [])
        if course_id:
            cards = [card for card in cards if card.get("course_id") == course_id]
        return cards

def save_note_cards(cards):
    """保存笔记卡片"""
    with open(NOTE_CARDS_FILE, 'w', encoding='utf-8') as f:
        json.dump({"cards": cards}, f, ensure_ascii=False, indent=2)

def delete_note_card(card_id):
    """删除笔记卡片"""
    try:
        cards = get_note_cards()
        card_to_delete = None
        
        # 找到要删除的卡片
        for card in cards:
            if card["id"] == card_id:
                card_to_delete = card
                break
        
        if not card_to_delete:
            return {"success": False, "error": "卡片不存在"}
        
        # 删除关联的图片文件
        if card_to_delete.get("image"):
            image_path = os.path.join(UPLOAD_DIR, card_to_delete["image"].lstrip('/uploads/'))
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception as e:
                    print(f"删除图片文件失败: {str(e)}")
        
        # 从列表中移除卡片
        cards = [card for card in cards if card["id"] != card_id]
        save_note_cards(cards)
        
        return {"success": True, "message": "卡片删除成功"}
        
    except Exception as e:
        return {"success": False, "error": f"删除卡片失败: {str(e)}"}

def update_note_card(card_id, title, content):
    """更新笔记卡片"""
    try:
        cards = get_note_cards()
        
        # 找到要更新的卡片
        for card in cards:
            if card["id"] == card_id:
                card["title"] = title
                card["content"] = content
                break
        else:
            return {"success": False, "error": "卡片不存在"}
        
        save_note_cards(cards)
        return {"success": True, "message": "卡片更新成功"}
        
    except Exception as e:
        return {"success": False, "error": f"更新卡片失败: {str(e)}"}

def get_course(course_id):
    """根据ID获取课程"""
    courses_data = get_courses()
    for course in courses_data["courses"]:
        if course["id"] == course_id:
            return course
    return None

def create_course(name):
    """创建新课程"""
    courses_data = get_courses()
    new_course = {
        "id": str(uuid.uuid4()),
        "name": name,
        "created_at": time.time()
    }
    courses_data["courses"].append(new_course)
    save_courses(courses_data)
    return new_course

def delete_course(course_id):
    """删除课程及其所有相关文件"""
    try:
        courses_data = get_courses()
        course_to_delete = None
        
        # 找到要删除的课程
        for course in courses_data["courses"]:
            if course["id"] == course_id:
                course_to_delete = course
                break
        
        if not course_to_delete:
            return {"success": False, "error": "课程不存在"}
        
        # 删除课程相关的所有文件
        course_files = get_course_files(course_id)
        for file in course_files:
            delete_file(file["id"], course_id)
        
        # 删除课程相关的所有笔记卡片
        cards = get_note_cards(course_id)
        for card in cards:
            delete_note_card(card["id"])
        
        # 删除课程目录
        course_dir = os.path.join(UPLOAD_DIR, course_id)
        if os.path.exists(course_dir):
            import shutil
            try:
                shutil.rmtree(course_dir)
            except Exception as e:
                print(f"删除课程目录失败: {str(e)}")
        
        # 从课程列表中移除
        courses_data["courses"] = [c for c in courses_data["courses"] if c["id"] != course_id]
        save_courses(courses_data)
        
        return {"success": True, "message": "课程删除成功"}
        
    except Exception as e:
        return {"success": False, "error": f"删除课程失败: {str(e)}"}

def update_course(course_id, name):
    """更新课程名称"""
    try:
        courses_data = get_courses()
        
        # 找到要更新的课程
        for course in courses_data["courses"]:
            if course["id"] == course_id:
                course["name"] = name.strip()
                save_courses(courses_data)
                return {"success": True, "course": course, "message": "课程名称更新成功"}
        
        return {"success": False, "error": "课程不存在"}
        
    except Exception as e:
        return {"success": False, "error": f"更新课程失败: {str(e)}"}

def get_course_files(course_id):
    """获取课程的所有文件"""
    files_data = get_files()
    result = []
    for file in files_data["files"]:
        # 支持两种字段名格式：courseId (旧格式) 和 course_id (新格式)
        file_course_id = file.get("course_id") or file.get("courseId")
        if file_course_id == course_id:
            result.append(file)
    return result

def add_file_record(file_name, file_type, file_path, course_id, summary="", screenshots=None):
    """添加文件记录"""
    files_data = get_files()
    new_file = {
        "id": str(uuid.uuid4()),
        "name": file_name,
        "type": file_type,
        "path": file_path,
        "course_id": course_id,
        "summary": summary,
        "uploaded_at": time.time(),
        "screenshots": screenshots or []
    }
    files_data["files"].append(new_file)
    save_files(files_data)
    return new_file

def delete_file(file_id, course_id):
    """删除文件"""
    try:
        files_data = get_files()
        file_to_delete = None
        
        # 找到要删除的文件
        for file in files_data["files"]:
            # 支持两种字段名格式：courseId (旧格式) 和 course_id (新格式)
            file_course_id = file.get("course_id") or file.get("courseId")
            if file["id"] == file_id and file_course_id == course_id:
                file_to_delete = file
                break
        
        if not file_to_delete:
            return {"success": False, "error": "文件不存在"}
        
        # 删除物理文件
        file_path = os.path.join(UPLOAD_DIR, file_to_delete["path"])
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"删除物理文件失败: {str(e)}")
        
        # 删除截图文件
        if file_to_delete.get("screenshots"):
            for screenshot in file_to_delete["screenshots"]:
                screenshot_path = os.path.join(UPLOAD_DIR, screenshot.lstrip('/uploads/'))
                if os.path.exists(screenshot_path):
                    try:
                        os.remove(screenshot_path)
                    except Exception as e:
                        print(f"删除截图文件失败: {str(e)}")
        
        # 从列表中移除文件记录
        files_data["files"] = [file for file in files_data["files"] if file["id"] != file_id]
        save_files(files_data)
        
        return {"success": True, "message": "文件删除成功"}
        
    except Exception as e:
        return {"success": False, "error": f"删除文件失败: {str(e)}"}

# 笔记卡片生成相关功能

def detect_subject_and_visualization(content):
    """使用AI智能检测学科类型并确定可视化方案"""
    try:
        # 使用AI分析内容并确定学科和可视化方案
        analysis_prompt = f"""
        请分析以下学习内容，确定学科类型并建议最佳的可视化方案：

        内容：{content}

        请以JSON格式返回分析结果：
        {{
            "subject": "学科类型(math/physics/chemistry/biology/history/language/general)",
            "subject_confidence": "置信度(0-1)",
            "visualization_type": "可视化类型",
            "visualization_description": "图片内容描述，说明应该画什么来帮助理解这个知识点",
            "key_elements": ["关键元素1", "关键元素2", "关键元素3"]
        }}

        学科分类标准：
        - math: 数学相关（函数、几何、代数、微积分等）
        - physics: 物理相关（力学、电磁学、热学、光学等）
        - chemistry: 化学相关（分子、反应、元素、化学键等）
        - biology: 生物相关（细胞、基因、生态、生理等）
        - history: 历史相关（事件、人物、朝代、社会发展等）
        - language: 语言文学相关（语法、文学、写作、语言学等）
        - general: 通用或其他学科

        可视化建议：根据具体内容提出有助于理解的图片描述
        """
        
        ai_response = call_google_ai_api_direct(analysis_prompt)
        
        # 尝试解析AI响应
        import json
        import re
        
        json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
        if json_match:
            try:
                analysis = json.loads(json_match.group())
                return {
                    'subject': analysis.get('subject', 'general'),
                    'confidence': float(analysis.get('subject_confidence', 0.5)),
                    'visualization_type': analysis.get('visualization_type', '文本展示'),
                    'visualization_description': analysis.get('visualization_description', '显示文本内容'),
                    'key_elements': analysis.get('key_elements', [])
                }
            except:
                pass
        
        # 如果AI分析失败，使用简化的启发式方法
        return analyze_content_heuristic(content)
        
    except Exception as e:
        print(f"AI分析失败: {str(e)}")
        return analyze_content_heuristic(content)

def analyze_content_heuristic(content):
    """启发式内容分析作为备用方案"""
    content_lower = content.lower()
    
    # 简单的关键词检测作为备用
    if any(word in content_lower for word in ['函数', '导数', '积分', '极限', '方程', '几何']):
        return {
            'subject': 'math',
            'confidence': 0.8,
            'visualization_type': '数学图形',
            'visualization_description': '绘制函数图像、几何图形或数学公式示意图',
            'key_elements': ['坐标系', '函数曲线', '数学符号']
        }
    elif any(word in content_lower for word in ['力', '能量', '电', '磁', '光', '热']):
        return {
            'subject': 'physics',
            'confidence': 0.8,
            'visualization_type': '物理现象图',
            'visualization_description': '绘制物理现象、力的作用或能量转换示意图',
            'key_elements': ['物理图形', '力的方向', '能量流动']
        }
    else:
        return {
            'subject': 'general',
            'confidence': 0.6,
            'visualization_type': '概念图',
            'visualization_description': '绘制概念关系图或重点内容框架',
            'key_elements': ['关键概念', '连接线', '层次结构']
        }

def load_chinese_fonts():
    """加载中文字体"""
    font_paths = [
        # macOS 中文字体 (更新实际存在的路径)
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/System/Library/Fonts/Hiragino Sans GB.ttc',
        '/System/Library/Fonts/Helvetica.ttc',
        '/System/Library/Fonts/Times.ttc',
        # Windows 中文字体
        'C:/Windows/Fonts/msyh.ttc',
        'C:/Windows/Fonts/simsun.ttc',
        'C:/Windows/Fonts/simhei.ttf',
        # Linux 中文字体
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/opentype/noto/NotoCJK-Regular.ttc',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
    ]
    
    print("🔍 正在加载中文字体...")
    for font_path in font_paths:
        if os.path.exists(font_path):
            print(f"✅ 找到字体: {font_path}")
            return font_path
        else:
            print(f"❌ 字体不存在: {font_path}")
    
    print("⚠️ 未找到合适的中文字体，将使用默认字体")
    return None

def safe_draw_text(draw, position, text, font, fill, shadow=False, shadow_offset=(2, 2), shadow_color=(0, 0, 0)):
    """安全绘制文本，简洁清爽的设计风格"""
    try:
        # 确保文本是字符串格式
        if not isinstance(text, str):
            text = str(text)
        
        # 简洁设计：不使用阴影效果，保持清爽
        # 直接绘制主文字
        draw.text(position, text, font=font, fill=fill, encoding='utf-8')
        
    except Exception as e:
        print(f"🚨 文本绘制错误: {str(e)}")
        print(f"📝 问题文本: {repr(text)}")
        
        try:
            # 尝试不指定编码，简洁绘制
            draw.text(position, text, font=font, fill=fill)
        except Exception as e2:
            print(f"🚨 第二次绘制也失败: {str(e2)}")
            try:
                # 最后的备用方案：只保留ASCII字符
                safe_text = ''.join(c for c in text if ord(c) < 128)
                if safe_text.strip():
                    draw.text(position, safe_text, font=font, fill=fill)
                else:
                    draw.text(position, "[中文显示异常]", font=font, fill=fill)
            except Exception as e3:
                print(f"🚨 所有文本绘制方法都失败: {str(e3)}")
                # 绘制一个简单的占位符
                draw.rectangle([position[0], position[1], position[0]+100, position[1]+20], fill=fill)

def safe_draw_text_with_background(draw, position, text, font, text_color, bg_color, padding=4):
    """绘制简洁的文字，不使用背景框，改为下划线"""
    try:
        # 确保文本是字符串格式
        if not isinstance(text, str):
            text = str(text)
        
        # 计算文字尺寸
        try:
            bbox = font.getbbox(text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            # 如果getbbox不可用，使用估算
            text_width = len(text) * 15
            text_height = 20
        
        # 简洁设计：直接绘制文字，不使用背景框
        draw.text(position, text, font=font, fill=text_color, encoding='utf-8')
        
        # 添加下划线突出重点
        line_y = position[1] + text_height + 2
        draw.line([(position[0], line_y), (position[0] + text_width, line_y)], 
                 fill=text_color, width=1)
        
    except Exception as e:
        print(f"🚨 带背景文本绘制错误: {str(e)}")
        # 回退到普通文字绘制
        safe_draw_text(draw, position, text, font, text_color)

def smart_text_wrap(text, font, max_width):
    """智能文本换行，支持中文"""
    lines = []
    current_line = ""
    
    for char in text:
        test_line = current_line + char
        try:
            bbox = font.getbbox(test_line)
            text_width = bbox[2] - bbox[0]
        except:
            # 如果getbbox不可用，使用简单的字符计数
            text_width = len(test_line) * 20
            
        if text_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                current_line = char
            else:
                lines.append(char)
    
    if current_line:
        lines.append(current_line)
    
    return lines

class HandwrittenNoteGenerator:
    def __init__(self):
        # 笔记本尺寸（更接近真实笔记本比例）
        self.width = 1200
        self.height = 1600
        self.margin = 80
        self.content_width = self.width - 2 * self.margin
        
        # 加载字体
        print("🎨 初始化手写风格笔记生成器...")
        self.font_path = load_chinese_fonts()
        
        # Gemini图像生成配置
        self.enable_ai_images = True  # 是否启用AI图像生成
        self.api_key = os.getenv('GOOGLE_AI_API_KEY', 'AIzaSyCbJ8PlTK7UTCkKwCv1uVyM5RXnsMv4qLM')
        
        try:
            if self.font_path:
                print(f"📝 使用字体: {self.font_path}")
                # 优化的手写风格字体尺寸 - 增大字体差异，提高层次感
                self.font_title = ImageFont.truetype(self.font_path, 64)     # 主标题更大
                self.font_subtitle = ImageFont.truetype(self.font_path, 48)  # 副标题中等
                self.font_content = ImageFont.truetype(self.font_path, 36)   # 正文适中
                self.font_small = ImageFont.truetype(self.font_path, 30)     # 小字更清晰
                self.font_formula = ImageFont.truetype(self.font_path, 40)   # 公式稍大
                print("✅ 字体加载成功!")
            else:
                print("⚠️ 使用默认字体")
                self.font_title = ImageFont.load_default()
                self.font_subtitle = ImageFont.load_default()
                self.font_content = ImageFont.load_default() 
                self.font_small = ImageFont.load_default()
                self.font_formula = ImageFont.load_default()
        except Exception as e:
            print(f"❌ 字体加载失败: {str(e)}")
            print("🔄 回退到默认字体")
            self.font_title = ImageFont.load_default()
            self.font_subtitle = ImageFont.load_default()
            self.font_content = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_formula = ImageFont.load_default()
        
        # 优化的高对比度配色方案
        self.colors = {
            'background': (45, 52, 65),      # 深蓝灰背景
            'paper': (250, 248, 240),        # 米白色纸张
            'title': (25, 25, 25),           # 深黑色标题（高对比度）
            'subtitle': (60, 80, 120),       # 深蓝色副标题
            'text': (40, 40, 40),            # 深灰色正文（高对比度）
            'formula': (180, 60, 20),        # 深橙色公式
            'highlight': (200, 20, 20),      # 深红色重点
            'note': (20, 120, 20),           # 深绿色注释
            'border': (100, 120, 140),       # 边框颜色
            'decoration': (120, 80, 140),    # 深紫色装饰元素
            # 新增高对比度颜色
            'text_shadow': (200, 200, 200),  # 文字阴影色
            'bg_highlight': (255, 255, 180), # 高亮背景色
            'bg_formula': (255, 240, 220),   # 公式背景色
            'bg_note': (240, 255, 240)       # 注释背景色
        }
    
    def draw_content_with_visualization(self, draw, content, analysis, x, y, width, font_content, font_small):
        """根据AI分析结果绘制内容和相应的可视化图形"""
        visualization_desc = analysis.get('visualization_description', '')
        key_elements = analysis.get('key_elements', [])
        subject = analysis.get('subject', 'general')
        
        # 为可视化区域预留空间
        visual_area_width = 280
        text_area_width = width - visual_area_width - 20
        visual_x = x + text_area_width + 20
        visual_y = y + 50
        
        # 绘制文本内容
        lines = smart_text_wrap(content, font_content, text_area_width)
        current_y = y
        line_height = 45
        
        # 限制文本行数，为可视化留出空间
        max_lines = min(10, len(lines))
        for line in lines[:max_lines]:
            safe_draw_text(draw, (x, current_y), line, font_content, self.colors['text'])
            current_y += line_height
        
        # 根据分析结果绘制相应的可视化内容
        if subject == 'math' or '函数' in visualization_desc or '图像' in visualization_desc:
            self.draw_mathematical_visualization(draw, content, visual_x, visual_y, visual_area_width, font_small)
        elif subject == 'physics' or '力' in visualization_desc or '能量' in visualization_desc:
            self.draw_physics_visualization(draw, content, visual_x, visual_y, visual_area_width, font_small)
        elif subject == 'chemistry' or '分子' in visualization_desc or '反应' in visualization_desc:
            self.draw_chemistry_visualization(draw, content, visual_x, visual_y, visual_area_width, font_small)
        elif subject == 'biology' or '细胞' in visualization_desc or '生物' in visualization_desc:
            self.draw_biology_visualization(draw, content, visual_x, visual_y, visual_area_width, font_small)
        elif subject == 'history' or '时间' in visualization_desc or '事件' in visualization_desc:
            self.draw_history_visualization(draw, content, visual_x, visual_y, visual_area_width, font_small)
        else:
            self.draw_concept_map(draw, content, key_elements, visual_x, visual_y, visual_area_width, font_small)
    
    def draw_mathematical_visualization(self, draw, content, x, y, width, font_small):
        """绘制数学相关的可视化图形"""
        # 绘制坐标系
        coord_size = min(width - 40, 200)
        center_x = x + width // 2
        center_y = y + coord_size // 2 + 50
        
        # 坐标轴
        draw.line([center_x - coord_size//2, center_y, center_x + coord_size//2, center_y], fill=(100, 100, 100), width=2)
        draw.line([center_x, center_y - coord_size//2, center_x, center_y + coord_size//2], fill=(100, 100, 100), width=2)
        
        # 添加箭头和标签
        draw.polygon([(center_x + coord_size//2 - 5, center_y - 3), (center_x + coord_size//2, center_y), (center_x + coord_size//2 - 5, center_y + 3)], fill=(100, 100, 100))
        draw.polygon([(center_x - 3, center_y - coord_size//2 + 5), (center_x, center_y - coord_size//2), (center_x + 3, center_y - coord_size//2 + 5)], fill=(100, 100, 100))
        
        # 根据内容绘制不同的数学图形
        if '导数' in content or '切线' in content:
            # 绘制函数和切线
            for i in range(-coord_size//2, coord_size//2, 2):
                plot_x = center_x + i
                plot_y = center_y - int(i * i * 0.005)  # 抛物线
                if y <= plot_y <= y + 300:
                    draw.point([plot_x, plot_y], fill=(255, 0, 0))
            # 添加切线
            draw.line([center_x - 50, center_y + 25, center_x + 50, center_y - 75], fill=(0, 150, 0), width=2)
            safe_draw_text_with_background(draw, (x + 5, y + 10), "f(x)", font_small, (255, 0, 0), (255, 255, 255))
            safe_draw_text_with_background(draw, (x + 5, y + 30), "切线", font_small, (0, 150, 0), (255, 255, 255))
            
        elif '极限' in content:
            # 绘制极限趋近过程
            points = [(center_x - 60, center_y + 30), (center_x - 30, center_y + 15), (center_x - 15, center_y + 8), (center_x, center_y)]
            for i, (px, py) in enumerate(points):
                draw.ellipse([px-3, py-3, px+3, py+3], fill=(255-i*50, 0+i*50, 0), outline=(200, 0, 0))
                if i < len(points) - 1:
                    draw.line([px, py, points[i+1][0], points[i+1][1]], fill=(150, 150, 150), width=1)
            safe_draw_text_with_background(draw, (x + 5, y + 10), "lim x→a", font_small, (100, 100, 100), (255, 255, 255))
            
        else:
            # 默认函数图像
            for i in range(-coord_size//2, coord_size//2, 2):
                plot_x = center_x + i
                plot_y = center_y - int(30 * math.sin(i * 0.05))
                if y <= plot_y <= y + 300:
                    draw.point([plot_x, plot_y], fill=(255, 0, 0))
    
    def draw_physics_visualization(self, draw, content, x, y, width, font_small):
        """绘制物理相关的可视化图形"""
        center_x = x + width // 2
        center_y = y + 100
        
        if '力' in content or '矢量' in content:
            # 绘制力矢量图
            vectors = [
                (center_x, center_y, center_x + 60, center_y - 40, (255, 0, 0), "F1"),
                (center_x, center_y, center_x - 30, center_y - 60, (0, 255, 0), "F2"),
                (center_x, center_y, center_x + 30, center_y + 50, (0, 0, 255), "F3")
            ]
            
            for x1, y1, x2, y2, color, label in vectors:
                draw.line([x1, y1, x2, y2], fill=color, width=3)
                # 绘制箭头
                dx, dy = x2 - x1, y2 - y1
                length = math.sqrt(dx*dx + dy*dy)
                if length > 0:
                    dx, dy = dx/length, dy/length
                    arrow_x = x2 - 8*dx + 4*dy
                    arrow_y = y2 - 8*dy - 4*dx
                    draw.polygon([(x2, y2), (arrow_x, arrow_y), (x2 - 8*dx - 4*dy, y2 - 8*dy + 4*dx)], fill=color)
                safe_draw_text(draw, (x2 + 5, y2 - 10), label, font_small, color)
                
        elif '波' in content or '振动' in content:
            # 绘制波形
            for i in range(width - 40):
                wave_x = x + 20 + i
                wave_y = center_y + int(30 * math.sin(i * 0.1))
                draw.point([wave_x, wave_y], fill=(0, 100, 255))
            safe_draw_text(draw, (x + 5, y + 10), "波形", font_small, (0, 100, 255))
            
        else:
            # 默认能量图
            draw.rectangle([center_x - 40, center_y - 20, center_x + 40, center_y + 20], outline=(255, 100, 0), width=2)
            safe_draw_text(draw, (center_x - 15, center_y - 8), "能量", font_small, (255, 100, 0))
    
    def draw_chemistry_visualization(self, draw, content, x, y, width, font_small):
        """绘制化学相关的可视化图形"""
        center_x = x + width // 2
        center_y = y + 100
        
        # 绘制分子结构
        atoms = [
            (center_x, center_y, 'C', (50, 50, 50)),
            (center_x - 40, center_y - 30, 'H', (200, 200, 200)),
            (center_x + 40, center_y - 30, 'H', (200, 200, 200)),
            (center_x, center_y + 40, 'O', (255, 0, 0))
        ]
        
        # 绘制化学键
        bonds = [
            (center_x, center_y, center_x - 40, center_y - 30),
            (center_x, center_y, center_x + 40, center_y - 30),
            (center_x, center_y, center_x, center_y + 40)
        ]
        
        for x1, y1, x2, y2 in bonds:
            draw.line([x1, y1, x2, y2], fill=(100, 100, 100), width=2)
        
        for ax, ay, symbol, color in atoms:
            draw.ellipse([ax-15, ay-15, ax+15, ay+15], outline=color, fill=(240, 240, 240), width=2)
            safe_draw_text(draw, (ax-8, ay-8), symbol, font_small, color)
    
    def draw_biology_visualization(self, draw, content, x, y, width, font_small):
        """绘制生物相关的可视化图形"""
        center_x = x + width // 2
        center_y = y + 100
        
        # 绘制细胞结构
        # 细胞膜
        draw.ellipse([center_x - 60, center_y - 50, center_x + 60, center_y + 50], outline=(0, 150, 0), width=3)
        
        # 细胞核
        draw.ellipse([center_x - 25, center_y - 20, center_x + 25, center_y + 20], outline=(0, 0, 150), fill=(200, 200, 255), width=2)
        safe_draw_text(draw, (center_x - 10, center_y - 5), "核", font_small, (0, 0, 150))
        
        # 线粒体
        draw.ellipse([center_x - 50, center_y + 20, center_x - 30, center_y + 35], outline=(150, 0, 0), fill=(255, 200, 200), width=2)
        draw.ellipse([center_x + 30, center_y - 40, center_x + 50, center_y - 25], outline=(150, 0, 0), fill=(255, 200, 200), width=2)
    
    def draw_history_visualization(self, draw, content, x, y, width, font_small):
        """绘制历史相关的可视化图形"""
        # 绘制时间轴
        timeline_y = y + 100
        start_x = x + 20
        end_x = x + width - 20
        
        draw.line([start_x, timeline_y, end_x, timeline_y], fill=(100, 100, 100), width=3)
        
        # 时间点标记
        num_events = 3
        for i in range(num_events):
            event_x = start_x + (end_x - start_x) * i / (num_events - 1)
            draw.line([event_x, timeline_y - 20, event_x, timeline_y + 20], fill=(150, 0, 0), width=2)
            safe_draw_text(draw, (event_x - 15, timeline_y + 25), f"事件{i+1}", font_small, (100, 0, 0))
    
    def draw_concept_map(self, draw, content, key_elements, x, y, width, font_small):
        """绘制概念图"""
        center_x = x + width // 2
        center_y = y + 100
        
        # 主概念
        draw.ellipse([center_x - 40, center_y - 20, center_x + 40, center_y + 20], outline=(0, 100, 200), fill=(220, 240, 255), width=2)
        safe_draw_text(draw, (center_x - 20, center_y - 8), "主概念", font_small, (0, 100, 200))
        
        # 子概念
        angles = [0, 2*math.pi/3, 4*math.pi/3]
        for i, angle in enumerate(angles):
            sub_x = center_x + int(80 * math.cos(angle))
            sub_y = center_y + int(60 * math.sin(angle))
            
            # 连接线
            draw.line([center_x, center_y, sub_x, sub_y], fill=(150, 150, 150), width=2)
            
            # 子概念框
            draw.rectangle([sub_x - 25, sub_y - 15, sub_x + 25, sub_y + 15], outline=(200, 100, 0), fill=(255, 240, 220), width=1)
            safe_draw_text(draw, (sub_x - 15, sub_y - 8), f"概念{i+1}", font_small, (200, 100, 0))
    
    def generate_card(self, title, content, analysis=None):
        """生成笔记卡片"""
        if analysis is None:
            analysis = {'subject': 'general', 'confidence': 0.5}
            
        subject_type = analysis.get('subject', 'general')
        
        # 根据学科选择背景色
        subject_colors = {
            'math': (240, 248, 255),      # 浅蓝色
            'physics': (255, 248, 240),   # 浅橙色
            'chemistry': (248, 255, 240), # 浅绿色
            'biology': (255, 240, 248),   # 浅粉色
            'history': (255, 255, 240),   # 浅黄色
            'language': (248, 240, 255),  # 浅紫色
            'general': (248, 248, 248)    # 浅灰色
        }
        
        bg_color = subject_colors.get(subject_type, (248, 248, 248))
        
        # 创建图像
        image = Image.new('RGB', (self.width, self.height), bg_color)
        draw = ImageDraw.Draw(image)
        
        # 绘制边框
        draw.rectangle([10, 10, self.width-10, self.height-10], outline=(200, 200, 200), width=3)
        
        # 绘制标题
        title_y = self.margin
        safe_draw_text(draw, (self.margin, title_y), title, self.font_title, (30, 30, 30))
        
        # 绘制学科标签和置信度
        subject_names = {
            'math': '数学',
            'physics': '物理',
            'chemistry': '化学',
            'biology': '生物',
            'history': '历史',
            'language': '语言',
            'general': '通用'
        }
        
        subject_label = subject_names.get(subject_type, '通用')
        confidence = analysis.get('confidence', 0.5)
        
        label_x = self.width - self.margin - 120
        # 根据置信度选择标签颜色
        if confidence > 0.8:
            label_color = (0, 150, 0)  # 高置信度 - 绿色
        elif confidence > 0.6:
            label_color = (200, 100, 0)  # 中等置信度 - 橙色
        else:
            label_color = (100, 100, 100)  # 低置信度 - 灰色
            
        draw.rectangle([label_x, self.margin, label_x + 100, self.margin + 40], 
                      fill=label_color, outline=(50, 50, 50))
        safe_draw_text(draw, (label_x + 10, self.margin + 8), subject_label, self.font_small, (255, 255, 255))
        
        # 显示可视化类型
        viz_type = analysis.get('visualization_type', '文本展示')
        safe_draw_text(draw, (self.margin, title_y + 50), f"图示: {viz_type}", self.font_small, (100, 100, 100))
        
        # 绘制内容和智能可视化
        content_y = title_y + 100
        content_x = self.margin
        
        self.draw_content_with_visualization(draw, content, analysis, content_x, content_y, 
                                           self.content_width, self.font_content, self.font_small)
        
        # 绘制时间戳
        timestamp = time.strftime("%Y/%m/%d %H:%M:%S")
        safe_draw_text(draw, (self.margin, self.height - 40), timestamp, self.font_small, (150, 150, 150))
        
        return image
    
    def generate_handwritten_note(self, title, note_data, analysis, page_index=0):
        """生成手写风格的知识卡片 - 单页包含完整内容，集成AI图像生成"""
        # 创建纯白色背景，不使用横线样式
        image = Image.new('RGB', (self.width, self.height), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        
        # 简洁的边框设计
        paper_margin = 30
        paper_rect = [paper_margin, paper_margin, self.width - paper_margin, self.height - paper_margin]
        draw.rectangle(paper_rect, fill=(255, 255, 255), outline=(220, 220, 220), width=2)
        
        # 移除笔记本线条和装饰边框，保持简洁的白色背景
        
        current_y = paper_margin + 60
        
        # 绘制主标题
        current_y = self.draw_main_title(draw, title, current_y)
        current_y += 20
        
        # 尝试为内容生成AI插图
        detailed_content = note_data.get('detailed_content', '')
        subject = analysis.get('subject', 'general')
        visualization_desc = analysis.get('visualization_description', '')
        
        # 生成AI插图（如果启用）
        ai_image = None
        if self.enable_ai_images and detailed_content:
            ai_image = self.generate_ai_illustration(detailed_content, subject, visualization_desc)
        
        # 绘制完整的知识卡片内容（紧凑版）
        if ai_image:
            # 有AI插图时的布局
            current_y = self.draw_compact_knowledge_card_with_ai(draw, image, note_data, current_y, ai_image)
        else:
            # 传统布局
            current_y = self.draw_compact_knowledge_card(draw, note_data, current_y)
        
        # 绘制页脚装饰
        self.draw_footer_decoration(draw, analysis)
        
        return image
    
    def draw_compact_knowledge_card(self, draw, note_data, start_y):
        """绘制知识卡片 - 全新的清晰美观布局"""
        current_y = start_y
        
        # 获取数据
        concepts = note_data.get('concepts', [])
        content = note_data.get('content', '')
        steps = note_data.get('steps', [])
        formulas = note_data.get('formulas', [])
        notes = note_data.get('notes', [])
        examples = note_data.get('examples', '')
        
        # 绘制主要内容区域背景
        content_area = [self.margin + 50, current_y, 
                       self.width - self.margin - 50, self.height - 150]
        # 绘制带圆角的内容背景
        draw.rectangle(content_area, fill=(248, 250, 252), outline=(200, 210, 220), width=2)
        
        current_y += 30
        
        # 1. 核心概念区域 - 最重要，放在顶部
        if concepts:
            current_y = self.draw_clean_concepts_section(draw, concepts, current_y)
            current_y += 25
        
        # 2. 重要公式区域 - 突出显示
        if formulas:
            current_y = self.draw_clean_formula_section(draw, formulas, current_y)
            current_y += 25
        
        # 3. 核心要点区域 - 主要内容
        if content:
            current_y = self.draw_clean_content_section(draw, content, current_y)
            current_y += 20
        
        # 4. 关键步骤区域 - 实操指导
        if steps:
            current_y = self.draw_clean_steps_section(draw, steps, current_y)
            current_y += 20
        
        # 5. 注意事项 - 警示信息
        if notes:
            current_y = self.draw_clean_notes_section(draw, notes, current_y)
        
        return current_y

    def draw_clean_concepts_section(self, draw, concepts, start_y):
        """绘制简洁的概念区域"""
        current_y = start_y
        
        # 区域标题 - 简洁下划线样式
        title_text = "💡 核心概念"
        safe_draw_text(draw, (self.margin + 80, current_y + 8), title_text, 
                      self.font_subtitle, (59, 130, 246))
        # 添加下划线突出重点
        title_width = len(title_text) * 24  # 估算标题宽度
        line_y = current_y + 50
        draw.line([(self.margin + 80, line_y), (self.margin + 80 + title_width, line_y)], 
                 fill=(59, 130, 246), width=3)
        current_y += 70
        
        # 概念卡片
        for i, concept in enumerate(concepts[:2]):
            term = concept.get('term', '')
            definition = concept.get('definition', '')
            
            # 简洁的概念项目 - 无背景框设计
            # 概念编号 - 简洁圆点设计
            dot_center = (self.margin + 95, current_y + 15)
            draw.ellipse([dot_center[0] - 8, dot_center[1] - 8, 
                         dot_center[0] + 8, dot_center[1] + 8], 
                        fill=(59, 130, 246))
            
            # 概念标题 - 突出显示
            safe_draw_text(draw, (self.margin + 115, current_y + 8), term, 
                         self.font_content, (30, 41, 59))
            
            # 添加标题下划线
            title_width = len(term) * 18
            line_y = current_y + 35
            draw.line([(self.margin + 115, line_y), (self.margin + 115 + title_width, line_y)], 
                     fill=(59, 130, 246), width=2)
            
            # 概念定义 - 分行显示，更简洁
            def_lines = smart_text_wrap(definition, self.font_small, 580)
            def_y = current_y + 45
            for line in def_lines[:2]:  # 只显示2行
                safe_draw_text(draw, (self.margin + 115, def_y), line, 
                             self.font_small, (71, 85, 105))
                def_y += 22
            
            current_y += 100
        
        return current_y

    def draw_clean_formula_section(self, draw, formulas, start_y):
        """绘制简洁的公式区域"""
        current_y = start_y
        formula = formulas[0]  # 只显示第一个公式
        
        # 公式区域标题 - 简洁下划线样式
        title_text = "⚡ 重要公式"
        safe_draw_text(draw, (self.margin + 80, current_y + 8), title_text, 
                      self.font_subtitle, (168, 85, 247))
        # 添加下划线突出重点
        title_width = len(title_text) * 24
        line_y = current_y + 50
        draw.line([(self.margin + 80, line_y), (self.margin + 80 + title_width, line_y)], 
                 fill=(168, 85, 247), width=3)
        current_y += 70
        
        # 公式名称 - 简洁显示
        name = formula.get('name', '')
        if name:
            safe_draw_text(draw, (self.margin + 100, current_y + 8), name, 
                         self.font_content, (88, 28, 135))
            # 添加名称下划线
            name_width = len(name) * 18
            name_line_y = current_y + 35
            draw.line([(self.margin + 100, name_line_y), (self.margin + 100 + name_width, name_line_y)], 
                     fill=(168, 85, 247), width=2)
            current_y += 50
        
        # 公式内容 - 居中显示，无边框
        formula_text = formula.get('formula', '')
        if formula_text:
            # 计算公式宽度，居中显示
            formula_bbox = draw.textbbox((0, 0), formula_text, font=self.font_formula)
            formula_width = formula_bbox[2] - formula_bbox[0]
            formula_x = (self.width - formula_width) // 2
            
            # 简洁显示公式，无背景框
            safe_draw_text(draw, (formula_x, current_y + 8), formula_text, 
                         self.font_formula, (88, 28, 135))
            
            # 添加公式下的装饰线
            formula_line_y = current_y + 45
            line_start_x = formula_x - 20
            line_end_x = formula_x + formula_width + 20
            draw.line([(line_start_x, formula_line_y), (line_end_x, formula_line_y)], 
                     fill=(168, 85, 247), width=1)
            current_y += 55
        
        return current_y

    def draw_clean_content_section(self, draw, content, start_y):
        """绘制简洁的内容区域"""
        current_y = start_y
        
        # 内容区域标题 - 简洁下划线样式
        title_text = "📝 核心要点"
        safe_draw_text(draw, (self.margin + 80, current_y + 8), title_text, 
                      self.font_subtitle, (34, 197, 94))
        # 添加下划线突出重点
        title_width = len(title_text) * 24
        line_y = current_y + 50
        draw.line([(self.margin + 80, line_y), (self.margin + 80 + title_width, line_y)], 
                 fill=(34, 197, 94), width=3)
        current_y += 70
        
        # 内容文本 - 分段显示，简洁无边框
        content_lines = smart_text_wrap(content[:300], self.font_small, 680)
        text_y = current_y + 12
        for line in content_lines[:4]:  # 只显示4行
            # 添加简洁的圆点符号
            if line.strip():
                # 绘制圆点
                dot_x = self.margin + 90
                dot_y = text_y + 8
                draw.ellipse([dot_x - 3, dot_y - 3, dot_x + 3, dot_y + 3], 
                           fill=(34, 197, 94))
                
                safe_draw_text(draw, (self.margin + 105, text_y), line, 
                             self.font_small, (22, 101, 52))
                text_y += 22
        
        return current_y + 110

    def draw_clean_steps_section(self, draw, steps, start_y):
        """绘制简洁的步骤区域"""
        current_y = start_y
        
        # 步骤区域标题 - 简洁下划线样式
        title_text = "📋 关键步骤"
        safe_draw_text(draw, (self.margin + 80, current_y + 8), title_text, 
                      self.font_subtitle, (249, 115, 22))
        # 添加下划线突出重点
        title_width = len(title_text) * 24
        line_y = current_y + 50
        draw.line([(self.margin + 80, line_y), (self.margin + 80 + title_width, line_y)], 
                 fill=(249, 115, 22), width=3)
        current_y += 70
        
        # 步骤列表 - 简洁无边框设计
        for i, step in enumerate(steps[:3]):
            # 步骤编号 - 简洁圆圈设计
            num_center = (self.margin + 95, current_y + 15)
            draw.ellipse([num_center[0] - 12, num_center[1] - 12, 
                         num_center[0] + 12, num_center[1] + 12], 
                        fill=(249, 115, 22))
            safe_draw_text(draw, (num_center[0] - 6, num_center[1] - 8), str(i+1), 
                         self.font_small, (255, 255, 255))
            
            # 步骤内容 - 简洁显示
            step_lines = smart_text_wrap(step, self.font_small, 600)
            safe_draw_text(draw, (self.margin + 120, current_y + 8), step_lines[0], 
                         self.font_small, (154, 52, 18))
            
            # 添加步骤下划线
            step_line_y = current_y + 32
            draw.line([(self.margin + 120, step_line_y), (self.margin + 600, step_line_y)], 
                     fill=(249, 115, 22), width=1)
            
            current_y += 45
        
        return current_y

    def draw_clean_notes_section(self, draw, notes, start_y):
        """绘制简洁的注意事项区域"""
        current_y = start_y
        
        # 注意事项标题 - 简洁下划线样式
        title_text = "⚠️ 重要提醒"
        safe_draw_text(draw, (self.margin + 80, current_y + 8), title_text, 
                      self.font_subtitle, (239, 68, 68))
        # 添加下划线突出重点
        title_width = len(title_text) * 24
        line_y = current_y + 50
        draw.line([(self.margin + 80, line_y), (self.margin + 80 + title_width, line_y)], 
                 fill=(239, 68, 68), width=3)
        current_y += 70
        
        # 注意事项列表 - 简洁无边框设计
        for note in notes[:2]:
            # 警告图标 - 简洁显示
            icon_x = self.margin + 90
            safe_draw_text(draw, (icon_x, current_y + 8), "⚠️", 
                         self.font_content, (239, 68, 68))
            
            # 注意事项内容 - 简洁显示
            note_lines = smart_text_wrap(note, self.font_small, 650)
            safe_draw_text(draw, (self.margin + 120, current_y + 12), note_lines[0], 
                         self.font_small, (127, 29, 29))
            
            # 添加注意事项下划线
            note_line_y = current_y + 35
            draw.line([(self.margin + 120, note_line_y), (self.margin + 650, note_line_y)], 
                     fill=(239, 68, 68), width=1)
            
            current_y += 45
        
        return current_y
    
    def draw_notebook_lines(self, draw, left, right):
        """绘制笔记本横线"""
        line_spacing = 45
        start_y = 120
        for y in range(start_y, self.height - 100, line_spacing):
            # 绘制浅色横线
            draw.line([left, y, right, y], fill=(200, 200, 200, 100), width=1)
    
    def draw_decorative_border(self, draw, left, right, top, bottom):
        """绘制装饰性边框"""
        # 左侧红线（模仿笔记本红线）
        margin_line_x = left + 80
        draw.line([margin_line_x, top + 40, margin_line_x, bottom - 40], 
                 fill=self.colors['highlight'], width=2)
    
    def draw_knowledge_structure_icons(self, draw, start_y):
        """绘制知识结构的图标标记"""
        # 在右上角绘制知识地图小图标
        icon_x = self.width - 120
        icon_y = start_y + 10
        
        # 绘制思维导图样式的小图标
        center_x, center_y = icon_x + 25, icon_y + 25
        
        # 中心圆点
        draw.ellipse([center_x - 8, center_y - 8, center_x + 8, center_y + 8], 
                    fill=self.colors['highlight'])
        
        # 四个分支
        branch_positions = [
            (center_x - 20, center_y - 15),  # 左上
            (center_x + 20, center_y - 15),  # 右上
            (center_x - 20, center_y + 15),  # 左下
            (center_x + 20, center_y + 15)   # 右下
        ]
        
        for branch_x, branch_y in branch_positions:
            # 连接线
            draw.line([center_x, center_y, branch_x, branch_y], 
                     fill=self.colors['subtitle'], width=2)
            # 分支圆点
            draw.ellipse([branch_x - 4, branch_y - 4, branch_x + 4, branch_y + 4], 
                        fill=self.colors['subtitle'])
        
        # 在左上角绘制学习进度标记
        progress_x = self.margin + 20
        progress_y = start_y + 10
        
        # 绘制进度条样式
        progress_width = 60
        progress_height = 8
        
        # 背景条
        draw.rectangle([progress_x, progress_y, progress_x + progress_width, progress_y + progress_height],
                      fill=(200, 200, 200))
        
        # 进度条（75%完成度）
        filled_width = int(progress_width * 0.75)
        draw.rectangle([progress_x, progress_y, progress_x + filled_width, progress_y + progress_height],
                      fill=self.colors['formula'])
        
        # 进度文字
        safe_draw_text_with_background(draw, (progress_x, progress_y + 15), "学习进度", 
                      self.font_small, self.colors['text'], (255, 255, 255), padding=2)
    
    def draw_structure_connections(self, draw, start_y):
        """绘制连接线条帮助理解知识结构"""
        # 左侧垂直连接线
        line_x = self.margin + 60
        line_start_y = start_y + 80
        line_end_y = self.height - 150
        
        # 主连接线
        draw.line([line_x, line_start_y, line_x, line_end_y], 
                 fill=self.colors['subtitle'], width=3)
        
        # 分支连接点
        section_positions = [
            line_start_y + 80,   # 概念部分
            line_start_y + 200,  # 内容部分
            line_start_y + 320,  # 方法部分
            line_start_y + 440   # 应用部分
        ]
        
        for y_pos in section_positions:
            if y_pos < line_end_y:
                # 水平分支线
                draw.line([line_x, y_pos, line_x + 30, y_pos], 
                         fill=self.colors['subtitle'], width=2)
                # 分支点圆圈
                draw.ellipse([line_x - 5, y_pos - 5, line_x + 5, y_pos + 5], 
                            fill=self.colors['highlight'])
        
        # 在右下角添加完成度标记
        completion_x = self.width - 100
        completion_y = self.height - 80
        
        # 完成度圆环
        ring_radius = 25
        draw.ellipse([completion_x - ring_radius, completion_y - ring_radius, 
                     completion_x + ring_radius, completion_y + ring_radius],
                    outline=self.colors['formula'], width=3)
        
        # 完成度文字
        safe_draw_text_with_background(draw, (completion_x - 15, completion_y - 8), "✓", 
                      self.font_content, self.colors['formula'], (255, 255, 255), padding=2)
        
        # 角落装饰（使用正确的坐标）
        corner_size = 20
        left = self.margin
        right = self.width - self.margin
        top = start_y
        
        # 左上角
        draw.arc([left + 10, top + 10, left + 10 + corner_size, top + 10 + corner_size], 
                0, 90, fill=self.colors['decoration'], width=3)
        # 右上角
        draw.arc([right - 10 - corner_size, top + 10, right - 10, top + 10 + corner_size], 
                90, 180, fill=self.colors['decoration'], width=3)
    
    def draw_main_title(self, draw, title, start_y):
        """绘制主标题 - 优化排版版本"""
        # 标题背景高亮 - 增加字体和间距
        title_bbox = draw.textbbox((0, 0), title, font=self.font_title)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]
        title_x = (self.width - title_width) // 2
        
        # 绘制标题背景 - 增加大小
        highlight_rect = [title_x - 30, start_y - 15, title_x + title_width + 30, start_y + title_height + 25]
        draw.rectangle(highlight_rect, fill=(self.colors['title'][0], self.colors['title'][1], self.colors['title'][2], 50))
        
        # 绘制标题文字 - 简洁清爽设计
        safe_draw_text(draw, (title_x, start_y), title, self.font_title, self.colors['title'])
        
        # 标题下划线装饰 - 调整位置
        underline_y = start_y + title_height + 15
        draw.line([title_x, underline_y, title_x + title_width, underline_y], 
                 fill=self.colors['title'], width=4)
        
        # 添加小装饰元素 - 调整位置
        for i in range(3):
            circle_x = title_x + title_width + 40 + i * 15
            circle_y = start_y + title_height // 2
            draw.ellipse([circle_x - 4, circle_y - 4, circle_x + 4, circle_y + 4], 
                        fill=self.colors['decoration'])
        
        return start_y + title_height + 50  # 增加标题后的间距
    
    def draw_concepts_page(self, draw, note_data, start_y):
        """绘制概念与原理页面"""
        current_y = start_y
        
        # 绘制概念部分
        concepts = note_data.get('concepts', [])
        if concepts:
            current_y = self.draw_section_title(draw, "核心概念", current_y)
            
            for i, concept in enumerate(concepts):
                current_y = self.draw_concept_block(draw, concept, current_y, i)
        
        # 绘制公式部分
        formulas = note_data.get('formulas', [])
        if formulas:
            current_y = self.draw_section_title(draw, "重要公式", current_y + 30)
            
            for formula in formulas:
                current_y = self.draw_formula_block(draw, formula, current_y)
        
        # 绘制详细内容
        detailed_content = note_data.get('detailed_content', '')
        if detailed_content:
            current_y = self.draw_section_title(draw, "详细解释", current_y + 30)
            current_y = self.draw_content_block(draw, detailed_content, current_y)
        
        return current_y
    
    def draw_methods_page(self, draw, note_data, start_y):
        """绘制步骤与方法页面"""
        current_y = start_y
        
        # 绘制步骤
        steps = note_data.get('steps', [])
        if steps:
            current_y = self.draw_section_title(draw, "关键步骤", current_y)
            
            for i, step in enumerate(steps):
                current_y = self.draw_step_block(draw, step, i + 1, current_y)
        
        # 绘制注意事项
        notes = note_data.get('notes', [])
        if notes:
            current_y = self.draw_section_title(draw, "注意事项", current_y + 30)
            
            for note in notes:
                current_y = self.draw_note_block(draw, note, current_y)
        
        return current_y
    
    def draw_examples_page(self, draw, note_data, start_y):
        """绘制应用与实例页面"""
        current_y = start_y
        
        # 绘制应用实例
        examples = note_data.get('examples', '')
        if examples:
            current_y = self.draw_section_title(draw, "实际应用", current_y)
            current_y = self.draw_content_block(draw, examples, current_y)
        
        return current_y
    
    def draw_section_title(self, draw, title, y):
        """绘制章节标题"""
        # 章节标题图标
        icon_x = self.margin + 100
        draw.rectangle([icon_x - 15, y, icon_x + 15, y + 30], 
                      fill=self.colors['subtitle'])
        
        # 标题文字
        title_x = icon_x + 25
        safe_draw_text(draw, (title_x, y), title, self.font_subtitle, self.colors['subtitle'])
        
        # 装饰线
        title_bbox = draw.textbbox((0, 0), title, font=self.font_subtitle)
        title_width = title_bbox[2] - title_bbox[0]
        line_end_x = title_x + title_width + 20
        draw.line([line_end_x, y + 15, self.width - self.margin - 50, y + 15], 
                 fill=self.colors['subtitle'], width=2)
        
        return y + 50
    
    def draw_concept_block(self, draw, concept, y, index):
        """绘制概念块"""
        term = concept.get('term', '')
        definition = concept.get('definition', '')
        
        # 概念编号圆圈
        circle_x = self.margin + 120
        circle_y = y + 10
        draw.ellipse([circle_x - 15, circle_y - 15, circle_x + 15, circle_y + 15], 
                    fill=self.colors['highlight'], outline=self.colors['text'])
        safe_draw_text(draw, (circle_x - 8, circle_y - 10), str(index + 1), self.font_small, (255, 255, 255))
        
        # 概念名称
        term_x = circle_x + 30
        safe_draw_text(draw, (term_x, y), term, self.font_content, self.colors['highlight'])
        
        # 概念定义
        definition_y = y + 35
        definition_lines = smart_text_wrap(definition, self.font_small, self.content_width - 100)
        for line in definition_lines[:3]:  # 最多3行
            safe_draw_text(draw, (term_x + 20, definition_y), line, self.font_small, self.colors['text'])
            definition_y += 30
        
        return definition_y + 20
    
    def draw_formula_block(self, draw, formula, y):
        """绘制公式块"""
        name = formula.get('name', '')
        formula_text = formula.get('formula', '')
        description = formula.get('description', '')
        
        # 公式背景框
        formula_box = [self.margin + 100, y, self.width - self.margin - 50, y + 120]
        draw.rectangle(formula_box, fill=(80, 90, 110), outline=self.colors['formula'], width=2)
        
        # 公式名称
        name_y = y + 10
        safe_draw_text(draw, (self.margin + 120, name_y), name, self.font_content, self.colors['formula'])
        
        # 公式内容（居中）
        formula_y = y + 50
        try:
            formula_bbox = draw.textbbox((0, 0), formula_text, font=self.font_formula)
            formula_width = formula_bbox[2] - formula_bbox[0]
        except:
            formula_width = len(formula_text) * 20
        
        formula_x = (self.width - formula_width) // 2
        safe_draw_text(draw, (formula_x, formula_y), formula_text, self.font_formula, self.colors['formula'])
        
        # 公式说明
        if description:
            desc_y = y + 90
            safe_draw_text(draw, (self.margin + 120, desc_y), description, self.font_small, self.colors['text'])
        
        return y + 140
    
    def draw_content_block(self, draw, content, y):
        """绘制内容块"""
        lines = smart_text_wrap(content, self.font_content, self.content_width - 60)
        line_height = 38
        
        for i, line in enumerate(lines[:8]):  # 最多8行
            # 添加随机的手写效果偏移
            offset_x = (i % 3) * 2 - 2  # 轻微的左右偏移
            text_x = self.margin + 120 + offset_x
            safe_draw_text(draw, (text_x, y), line, self.font_content, self.colors['text'])
            y += line_height
        
        return y + 20
    
    def draw_step_block(self, draw, step, step_num, y):
        """绘制步骤块"""
        # 步骤编号
        step_circle_x = self.margin + 120
        step_circle_y = y + 15
        draw.ellipse([step_circle_x - 20, step_circle_y - 20, step_circle_x + 20, step_circle_y + 20], 
                    fill=self.colors['note'], outline=self.colors['border'], width=2)
        safe_draw_text(draw, (step_circle_x - 10, step_circle_y - 12), str(step_num), self.font_content, (50, 50, 50))
        
        # 步骤内容
        step_x = step_circle_x + 40
        step_lines = smart_text_wrap(step, self.font_content, self.content_width - 160)
        current_y = y
        
        for line in step_lines[:2]:  # 最多2行
            safe_draw_text(draw, (step_x, current_y), line, self.font_content, self.colors['text'])
            current_y += 35
        
        # 连接线到下一步
        if step_num < 5:  # 假设最多5步
            draw.line([step_circle_x, step_circle_y + 20, step_circle_x, step_circle_y + 50], 
                     fill=self.colors['note'], width=3)
        
        return current_y + 25
    
    def draw_note_block(self, draw, note, y):
        """绘制注意事项块"""
        # 注意图标
        icon_x = self.margin + 120
        icon_y = y + 10
        # 绘制感叹号图标
        draw.ellipse([icon_x - 12, icon_y - 12, icon_x + 12, icon_y + 12], 
                    fill=self.colors['highlight'], outline=self.colors['border'])
        safe_draw_text(draw, (icon_x - 5, icon_y - 10), "!", self.font_content, (255, 255, 255))
        
        # 注意内容
        note_x = icon_x + 30
        note_lines = smart_text_wrap(note, self.font_small, self.content_width - 120)
        
        for line in note_lines[:2]:  # 最多2行
            safe_draw_text(draw, (note_x, y), line, self.font_small, self.colors['note'])
            y += 30
        
        return y + 15
    
    def draw_footer_decoration(self, draw, analysis):
        """绘制页脚装饰"""
        footer_y = self.height - 80
        
        # 学科标识
        subject = analysis.get('subject', 'general')
        subject_names = {
            'math': '数学', 'physics': '物理', 'chemistry': '化学',
            'biology': '生物', 'history': '历史', 'language': '语言', 'general': '通用'
        }
        subject_name = subject_names.get(subject, '通用')
        
        # 绘制学科标签
        label_x = self.width - 150
        draw.rectangle([label_x, footer_y, label_x + 80, footer_y + 30], 
                      fill=self.colors['decoration'], outline=self.colors['border'])
        safe_draw_text(draw, (label_x + 10, footer_y + 5), subject_name, self.font_small, (255, 255, 255))
        
        # 绘制装饰性元素
        for i in range(5):
            deco_x = self.margin + 50 + i * 40
            draw.ellipse([deco_x, footer_y + 10, deco_x + 8, footer_y + 18], 
                        fill=self.colors['decoration'])
        
        # 时间戳
        timestamp = time.strftime("%Y.%m.%d")
        safe_draw_text(draw, (self.margin + 50, footer_y + 5), timestamp, self.font_small, self.colors['border'])

    def generate_ai_illustration(self, content, subject, visualization_desc):
        """使用Gemini 2.0生成AI插图"""
        try:
            if not self.enable_ai_images:
                return None
                
            print("🤖 正在使用Gemini 2.0生成AI插图...")
            
            # 构建图像生成提示
            subject_prompts = {
                'math': '数学图表，坐标系，函数图像，几何图形',
                'physics': '物理实验装置，力学图示，波形图，能量转换',
                'chemistry': '分子结构，化学反应，实验器材，周期表',
                'biology': '细胞结构，生物体系统，生态关系，进化过程',
                'history': '历史时间线，地图，历史人物，重要事件',
                'general': '学习概念图，知识结构，思维导图'
            }
            
            base_prompt = subject_prompts.get(subject, subject_prompts['general'])
            
            image_prompt = f"""
            创建一个教育性的插图，用于学习笔记卡片。
            
            主题：{content[:100]}...
            学科：{subject}
            风格要求：简洁明了的教育插图，适合学习材料
            元素：{base_prompt}
            视觉描述：{visualization_desc}
            
            要求：
            - 清晰易懂的教育插图
            - 适合作为学习辅助材料
            - 简洁的线条和配色
            - 突出重点概念
            """
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-preview-image-generation:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            
            data = {
                "contents": [{"parts": [{"text": image_prompt}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "responseModalities": ["TEXT", "IMAGE"]
                }
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                # 查找图像数据
                if "candidates" in result and len(result["candidates"]) > 0:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "inlineData" in part and "data" in part["inlineData"]:
                                # 解码base64图像数据
                                import base64
                                from io import BytesIO
                                
                                image_data = base64.b64decode(part["inlineData"]["data"])
                                ai_image = Image.open(BytesIO(image_data))
                                
                                print("✅ AI插图生成成功!")
                                return ai_image
                                
            print("⚠️ AI插图生成失败，使用传统绘制方法")
            return None
            
        except Exception as e:
            print(f"❌ AI插图生成错误: {str(e)}")
            return None

    def combine_ai_and_manual_graphics(self, draw, content, analysis, x, y, width, font_content, font_small):
        """结合AI生成的插图和手动绘制的图形"""
        try:
            subject = analysis.get('subject', 'general')
            visualization_desc = analysis.get('visualization_description', '')
            
            # 尝试生成AI插图
            ai_image = self.generate_ai_illustration(content, subject, visualization_desc)
            
            if ai_image:
                # AI插图成功生成，整合到卡片中
                ai_width = min(300, width // 2)
                ai_height = min(200, ai_width * 2 // 3)
                
                # 调整AI图像尺寸
                ai_image_resized = ai_image.resize((ai_width, ai_height), Image.Resampling.LANCZOS)
                
                # 在卡片右上角放置AI插图
                ai_x = x + width - ai_width - 20
                ai_y = y + 20
                
                # 创建一个临时图像来获取当前绘制内容
                temp_img = Image.new('RGB', (self.width, self.height), self.colors['paper'])
                temp_draw = ImageDraw.Draw(temp_img)
                
                # 将AI图像粘贴到临时图像上
                temp_img.paste(ai_image_resized, (ai_x, ai_y))
                
                # 在AI图像周围添加装饰边框
                border_color = self.colors['subtitle']
                temp_draw.rectangle([ai_x-2, ai_y-2, ai_x+ai_width+2, ai_y+ai_height+2], 
                                  outline=border_color, width=2)
                
                # 添加标签
                safe_draw_text(temp_draw, (ai_x, ai_y + ai_height + 5), "AI生成插图", 
                             self.font_small, self.colors['decoration'])
                
                # 文本区域调整为左侧
                text_width = width - ai_width - 40
                
                # 绘制文本内容
                lines = smart_text_wrap(content, font_content, text_width)
                current_y = y
                line_height = 45
                
                max_lines = min(8, len(lines))
                for line in lines[:max_lines]:
                    safe_draw_text(temp_draw, (x, current_y), line, font_content, self.colors['text'])
                    current_y += line_height
                
                return temp_img
            else:
                # AI插图生成失败，使用原有的可视化方法
                return self.draw_content_with_visualization(draw, content, analysis, x, y, width, font_content, font_small)
                
        except Exception as e:
            print(f"❌ 图像结合过程出错: {str(e)}")
            # 回退到原有方法
            return self.draw_content_with_visualization(draw, content, analysis, x, y, width, font_content, font_small)

    def draw_compact_knowledge_card_with_ai(self, draw, base_image, note_data, start_y, ai_image):
        """绘制带AI插图的紧凑知识卡片"""
        try:
            # AI插图区域设置 - 增加白色背景区域
            ai_width = min(380, self.content_width // 2)
            ai_height = min(280, ai_width * 3 // 4)
            ai_x = self.width - self.margin - ai_width - 30
            ai_y = start_y + 30
            
            # 为AI图像创建白色背景区域
            background_padding = 15
            bg_rect = [ai_x - background_padding, ai_y - background_padding, 
                      ai_x + ai_width + background_padding, ai_y + ai_height + background_padding]
            draw.rectangle(bg_rect, fill=(255, 255, 255), outline=(200, 200, 200), width=1)
            
            # 调整AI图像尺寸并粘贴到白色背景上
            ai_image_resized = ai_image.resize((ai_width, ai_height), Image.Resampling.LANCZOS)
            base_image.paste(ai_image_resized, (ai_x, ai_y))
            
            # 简洁的边框设计
            border_color = (150, 150, 150)
            draw.rectangle([ai_x-2, ai_y-2, ai_x+ai_width+2, ai_y+ai_height+2], 
                          outline=border_color, width=2)
            
            # 添加AI标签
            label_y = ai_y + ai_height + 8
            safe_draw_text(draw, (ai_x, label_y), "🤖 AI生成插图", 
                         self.font_small, self.colors['decoration'])
            
            # 调整内容区域（左侧布局）
            content_width = self.content_width - ai_width - 60
            
            current_y = start_y
            available_height = self.height - start_y - 120
            section_height = available_height // 4
            
            # 绘制知识结构图标记（左侧）
            left_icon_area = 60
            self.draw_knowledge_structure_icons(draw, start_y)
            
            # 左侧内容区域调整
            content_x = self.margin + left_icon_area + 20
            
            # 1. 核心概念部分（左侧，紧凑版）
            concepts = note_data.get('concepts', [])
            if concepts and current_y < start_y + section_height:
                current_y = self.draw_mini_section_title(draw, "💡 核心概念", current_y)
                
                for i, concept in enumerate(concepts[:2]):  # 限制2个概念
                    if current_y > start_y + section_height - 50:
                        break
                        
                    term = concept.get('term', '')
                    definition = concept.get('definition', '')
                    
                    # 概念卡片（调整宽度）
                    card_width = content_width - 20
                    card_height = 60
                    
                    # 概念编号和内容
                    circle_x = content_x + 15
                    circle_y = current_y + 8
                    draw.ellipse([circle_x - 10, circle_y - 10, circle_x + 10, circle_y + 10],
                                fill=self.colors['highlight'])
                    safe_draw_text(draw, (circle_x - 4, circle_y - 6), str(i+1), 
                                 self.font_small, self.colors['paper'])
                    
                    # 概念名称
                    safe_draw_text(draw, (content_x + 35, current_y), term, 
                                 self.font_content, self.colors['highlight'])
                    
                    # 定义（简化版）
                    def_lines = smart_text_wrap(definition, self.font_small, card_width - 50)
                    def_y = current_y + 22
                    for line in def_lines[:1]:  # 只显示第一行
                        safe_draw_text(draw, (content_x + 35, def_y), line, 
                                     self.font_small, self.colors['text'])
                    
                    current_y += card_height
            
            # 2. 详细内容（左侧下方）
            current_y += 20
            detailed_content = note_data.get('detailed_content', '')
            if detailed_content and current_y < start_y + section_height * 2:
                current_y = self.draw_mini_section_title(draw, "📝 核心要点", current_y)
                
                # 内容文本（调整宽度和长度）
                content_lines = smart_text_wrap(detailed_content[:300], self.font_small, content_width - 20)
                max_lines = min(6, (section_height - 60) // 22)
                
                for line in content_lines[:max_lines]:
                    if current_y > start_y + section_height * 2 - 30:
                        break
                    safe_draw_text(draw, (content_x, current_y), line, 
                                 self.font_small, self.colors['text'])
                    current_y += 22
            
            # 3. 关键步骤/公式（左侧，如果空间允许）
            current_y += 15
            steps = note_data.get('steps', [])
            formulas = note_data.get('formulas', [])
            if (steps or formulas) and current_y < start_y + section_height * 3:
                if formulas:
                    current_y = self.draw_mini_section_title(draw, "⚡ 公式", current_y)
                    formula = formulas[0]  # 只显示第一个公式
                    formula_text = formula.get('formula', '')
                    if formula_text:
                        # 简化的公式显示
                        formula_bg_width = min(len(formula_text) * 12, content_width - 20)
                        draw.rectangle([content_x, current_y - 5, 
                                       content_x + formula_bg_width, current_y + 25],
                                      fill=self.colors['formula'], outline=self.colors['formula'])
                        safe_draw_text(draw, (content_x + 5, current_y), formula_text, 
                                     self.font_content, self.colors['paper'])
                        current_y += 35
                
                elif steps:
                    current_y = self.draw_mini_section_title(draw, "⚡ 步骤", current_y)
                    for i, step in enumerate(steps[:3]):  # 最多3个步骤
                        if current_y > start_y + section_height * 3 - 30:
                            break
                        step_text = f"{i+1}. {step}"
                        step_lines = smart_text_wrap(step_text, self.font_small, content_width - 20)
                        for line in step_lines[:1]:  # 每个步骤只显示一行
                            safe_draw_text(draw, (content_x, current_y), line, 
                                         self.font_small, self.colors['text'])
                            current_y += 25
                        current_y += 5
            
            # 移除复杂的连接线条，保持简洁设计
            
            return current_y
            
        except Exception as e:
            print(f"❌ 绘制AI增强卡片时出错: {str(e)}")
            # 回退到传统方法
            return self.draw_compact_knowledge_card(draw, note_data, start_y)

class NoteCardGenerator:
    """保持向后兼容的原始卡片生成器"""
    def __init__(self):
        self.width = 900
        self.height = 1200
        self.margin = 60
        self.content_width = self.width - 2 * self.margin
        
        # 加载字体
        print("🎨 初始化笔记卡片生成器...")
        self.font_path = load_chinese_fonts()
        
        try:
            if self.font_path:
                print(f"📝 使用字体: {self.font_path}")
                self.font_title = ImageFont.truetype(self.font_path, 48)
                self.font_content = ImageFont.truetype(self.font_path, 32)
                self.font_small = ImageFont.truetype(self.font_path, 24)
                print("✅ 字体加载成功!")
            else:
                print("⚠️ 使用默认字体")
                self.font_title = ImageFont.load_default()
                self.font_content = ImageFont.load_default() 
                self.font_small = ImageFont.load_default()
        except Exception as e:
            print(f"❌ 字体加载失败: {str(e)}")
            print("🔄 回退到默认字体")
            self.font_title = ImageFont.load_default()
            self.font_content = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
    
    def generate_card(self, title, content, analysis=None):
        """生成传统样式的笔记卡片"""
        if analysis is None:
            analysis = {'subject': 'general', 'confidence': 0.5}
            
        subject_type = analysis.get('subject', 'general')
        
        # 根据学科选择背景色
        subject_colors = {
            'math': (240, 248, 255),      # 浅蓝色
            'physics': (255, 248, 240),   # 浅橙色
            'chemistry': (248, 255, 240), # 浅绿色
            'biology': (255, 240, 248),   # 浅粉色
            'history': (255, 255, 240),   # 浅黄色
            'language': (248, 240, 255),  # 浅紫色
            'general': (248, 248, 248)    # 浅灰色
        }
        
        bg_color = subject_colors.get(subject_type, (248, 248, 248))
        
        # 创建图像
        image = Image.new('RGB', (self.width, self.height), bg_color)
        draw = ImageDraw.Draw(image)
        
        # 绘制边框
        draw.rectangle([10, 10, self.width-10, self.height-10], outline=(200, 200, 200), width=3)
        
        # 绘制标题
        title_y = self.margin
        safe_draw_text(draw, (self.margin, title_y), title, self.font_title, (30, 30, 30))
        
        # 绘制内容
        content_y = title_y + 100
        lines = smart_text_wrap(content, self.font_content, self.content_width)
        for line in lines[:15]:  # 最多15行
            safe_draw_text(draw, (self.margin, content_y), line, self.font_content, (50, 50, 50))
            content_y += 40
        
        # 绘制时间戳
        timestamp = time.strftime("%Y/%m/%d %H:%M:%S")
        safe_draw_text(draw, (self.margin, self.height - 40), timestamp, self.font_small, (150, 150, 150))
        
        return image

def call_google_ai_api_direct(prompt):
    """直接调用Google AI API的简化版本"""
    try:
        api_key = os.getenv('GOOGLE_AI_API_KEY', 'AIzaSyCbJ8PlTK7UTCkKwCv1uVyM5RXnsMv4qLM')
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.4,
                "topK": 32,
                "topP": 1,
                "maxOutputTokens": 2048
            }
        }
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and len(result["candidates"]) > 0:
                if "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"]:
                    return result["candidates"][0]["content"]["parts"][0]["text"]
        
        return "AI生成的学习内容..."
        
    except Exception as e:
        return f"基于提供的材料生成的学习要点..."

def generate_single_note_card(course_id, file_ids, card_index=0):
    """生成单张知识卡片 - 每次生成一个完整的独立知识点"""
    try:
        print(f"🃏 开始生成第 {card_index + 1} 张卡片...")
        
        # 获取文件内容
        files_data = get_files()
        selected_files = []
        
        for file in files_data["files"]:
            if file["id"] in file_ids:
                selected_files.append(file)
        
        if not selected_files:
            return {"success": False, "error": "未找到指定的文件"}
        
        # 使用AI分析文件内容
        file_contents = []
        for file in selected_files:
            summary = file.get("summary", "")
            
            # 检查文件摘要是否有效
            if not summary or summary.strip() == "" or "无法获取" in summary or "错误" in summary:
                # 使用文件基本信息作为内容
                file_type = file.get("type", "unknown")
                file_name = file.get("name", "unknown")
                
                if file_type == "video":
                    content = f"视频文件：{file_name}。这是一个教学视频，请基于视频文件名和类型生成相关的学习要点。"
                elif file_type == "audio":
                    content = f"音频文件：{file_name}。这是一个教学音频，请基于音频文件名和类型生成相关的学习要点。"
                elif file_type == "pdf":
                    content = f"PDF文档：{file_name}。这是一个学习文档，请基于文档名称生成相关的学习要点。"
                elif file_type == "image":
                    content = f"图片文件：{file_name}。这是一个教学图片，请基于图片名称生成相关的学习要点。"
                else:
                    content = f"学习材料：{file_name}。请基于文件名称和类型({file_type})生成相关的学习知识点。"
            else:
                content = summary
            
            file_contents.append(content)
        
        combined_content = "\n\n".join(file_contents)
        
        # 根据文件内容生成一个独立的知识点卡片
        prompt = f"""
        请基于以下学习材料，生成**一个核心知识点**的学习卡片。

        📋 **生成指南**：
        - 如果有具体内容，提取最重要的核心知识点
        - 如果只有文件名信息，请智能推断并生成相关的学科知识点
        - 内容要简洁明了，适合快速学习记忆
        - 重点突出核心概念和实际应用

        🎯 **内容要求**：
        - 标题：简洁明确（6-10字）
        - 概念定义：准确精练（15-25字）
        - 核心内容：重点突出（80-120字）
        - 实用性：突出应用价值和关键要点

        学习材料：
        {combined_content}

        请以以下JSON格式返回：
        {{
            "title": "核心知识点标题（6-10字）",
            "concepts": [
                {{"term": "核心概念", "definition": "简洁定义（15-25字）"}},
                {{"term": "关键要点", "definition": "重要特征（15-25字）"}}
            ],
            "formulas": [
                {{"name": "重要公式", "formula": "数学表达式", "description": "应用说明（10-15字）"}}
            ],
            "detailed_content": "核心要点总结：原理机制+应用价值（80-120字）",
            "steps": [
                "第1步：关键操作（15-20字）",
                "第2步：重要步骤（15-20字）",
                "第3步：最终结果（15-20字）"
            ],
            "notes": [
                "⚠️ 重要注意（20-30字）",
                "💡 关键技巧（20-30字）"
            ],
            "examples": "典型应用：具体场景+结果（30-50字）"
        }}
        
        ⚡ **重要**：如果材料信息有限，请基于文件名和类型智能生成相关学科的核心知识点！
        """
        
        # 调用AI API
        ai_response = call_google_ai_api_direct(prompt)
        
        # 解析AI响应
        try:
            import json
            import re
            
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                note_data = json.loads(json_match.group())
            else:
                # 备用方案：创建简化的笔记结构
                lines = ai_response.split('\n')
                title = "知识要点"
                content = ai_response[:300] + "..." if len(ai_response) > 300 else ai_response
                
                # 尝试从响应中提取标题
                for line in lines[:5]:
                    if line.strip() and len(line.strip()) <= 20:
                        title = line.strip()
                        break
                
                note_data = {
                    "title": title,
                    "concepts": [{"term": "核心概念", "definition": "重要知识点"}],
                    "formulas": [],
                    "detailed_content": content,
                    "steps": ["理解概念", "掌握方法", "实际应用"],
                    "notes": ["注意理论联系实际"],
                    "examples": "具体应用案例"
                }
        except Exception as e:
            print(f"解析AI响应失败: {e}")
            # 解析失败的备用方案
            note_data = {
                "title": f"学习笔记-{card_index + 1}", 
                "concepts": [{"term": "重要概念", "definition": "核心知识点"}],
                "formulas": [],
                "detailed_content": ai_response[:300] + "..." if len(ai_response) > 300 else ai_response,
                "steps": ["学习理解", "练习应用", "总结提升"],
                "notes": ["认真学习，反复练习"],
                "examples": "实际应用场景"
            }
        
        # 确保标题简洁
        title = note_data.get('title', '学习笔记')
        if len(title) > 20:
            title = title[:20] + "..."
        
        print(f"📝 生成卡片: {title}")
        
        # 使用AI智能分析内容
        content_text = note_data.get("detailed_content", "")
        analysis = detect_subject_and_visualization(content_text)
        
        # 生成手写风格的笔记卡片图像
        generator = HandwrittenNoteGenerator()
        # 生成单页完整笔记，不分页
        card_image = generator.generate_handwritten_note(title, note_data, analysis, page_index=0)
        
        # 保存图像
        card_id = str(uuid.uuid4())
        image_filename = f"card_{card_id}.png"
        image_path = os.path.join(UPLOAD_DIR, image_filename)
        card_image.save(image_path)
        
        print(f"💾 卡片图片已保存: {image_filename}")
        
        # 创建卡片记录
        card_record = {
            "id": card_id,
            "title": title,
            "content": content_text,
            "note_data": note_data,  # 保存完整的笔记结构
            "subject": analysis.get('subject', 'general'),
            "confidence": analysis.get('confidence', 0.5),
            "visualization_type": analysis.get('visualization_type', '手写笔记'),
            "image": f"/uploads/{image_filename}",
            "course_id": course_id,
            "created_at": time.time(),
            "file_ids": file_ids,
            "image_source": "generated"
        }
        
        # 保存到数据库
        existing_cards = get_note_cards()
        existing_cards.append(card_record)
        save_note_cards(existing_cards)
        
        return {
            "success": True,
            "card": card_record,
            "message": f"成功生成知识卡片: {title}"
        }
        
    except Exception as e:
        print(f"❌ 生成卡片失败: {str(e)}")
        return {"success": False, "error": f"生成笔记卡片失败: {str(e)}"}

def generate_note_cards_from_files(course_id, file_ids):
    """根据文件生成笔记卡片（批量生成，保持向后兼容）"""
    try:
        # 获取文件内容
        files_data = get_files()
        selected_files = []
        
        for file in files_data["files"]:
            if file["id"] in file_ids:
                selected_files.append(file)
        
        if not selected_files:
            return {"success": False, "error": "未找到指定的文件"}
        
        # 使用AI分析文件内容
        file_contents = []
        for file in selected_files:
            summary = file.get("summary", "")
            
            # 检查文件摘要是否有效
            if not summary or summary.strip() == "" or "无法获取" in summary or "错误" in summary:
                # 使用文件基本信息作为内容
                file_type = file.get("type", "unknown")
                file_name = file.get("name", "unknown")
                
                if file_type == "video":
                    content = f"视频文件：{file_name}。这是一个教学视频，请基于视频文件名和类型生成相关的学习要点。"
                elif file_type == "audio":
                    content = f"音频文件：{file_name}。这是一个教学音频，请基于音频文件名和类型生成相关的学习要点。"
                elif file_type == "pdf":
                    content = f"PDF文档：{file_name}。这是一个学习文档，请基于文档名称生成相关的学习要点。"
                elif file_type == "image":
                    content = f"图片文件：{file_name}。这是一个教学图片，请基于图片名称生成相关的学习要点。"
                else:
                    content = f"学习材料：{file_name}。请基于文件名称和类型({file_type})生成相关的学习知识点。"
            else:
                content = summary
            
            file_contents.append(content)
        
        combined_content = "\n\n".join(file_contents)
        
        # 使用AI生成结构化的知识点
        prompt = f"""
        请分析以下学习材料，精选3-5个**最核心**的知识点，生成简洁高效学习卡片。

        🎯 **简洁标准**：
        - 选择最重要的核心概念
        - 每个知识点简明扼要，便于快速掌握
        - 突出关键信息，避免冗长描述
        - 标题精准（6-8字），内容简洁实用

        📋 **内容要求**：
        - 重点突出核心概念和关键应用
        - 包含必要的公式、步骤、要点
        - 内容简洁明了，一目了然
        - 便于理解和记忆

        学习材料：
        {combined_content}
        
        请以以下JSON格式返回：
        {{
            "cards": [
                {{
                    "title": "核心知识点（6-8字）",
                    "content": "要点总结：定义+要点+应用（60-100字，简洁明了）"
                }},
                {{
                    "title": "关键概念（6-8字）", 
                    "content": "核心内容：原理+方法+注意事项（60-100字，重点突出）"
                }}
            ]
        }}
        
        ⚡ **严格要求**：简洁明了，重点突出，便于快速学习！
        """
        
        # 调用AI API
        ai_response = call_google_ai_api_direct(prompt)
        
        # 解析AI响应
        try:
            # 尝试提取JSON部分
            import json
            import re
            
            # 查找JSON部分
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if json_match:
                cards_data = json.loads(json_match.group())
                knowledge_points = cards_data.get("cards", [])
            else:
                # 如果没有找到JSON，则创建默认卡片
                knowledge_points = [
                    {
                        "title": "核心知识点",
                        "content": ai_response[:500] + "..." if len(ai_response) > 500 else ai_response
                    }
                ]
        except:
            # 解析失败时的备用方案
            knowledge_points = [
                {
                    "title": "学习要点",
                    "content": ai_response[:500] + "..." if len(ai_response) > 500 else ai_response
                }
            ]
        
        # 生成笔记卡片
        generator = NoteCardGenerator()
        generated_cards = []
        
        for i, point in enumerate(knowledge_points[:5]):  # 最多生成5张卡片
            title = point.get("title", f"知识点 {i+1}")
            content = point.get("content", "内容生成中...")
            
            # 使用AI智能分析内容
            analysis = detect_subject_and_visualization(content)
            
            # 生成卡片图像
            card_image = generator.generate_card(title, content, analysis)
            
            # 保存图像
            card_id = str(uuid.uuid4())
            image_filename = f"card_{card_id}.png"
            image_path = os.path.join(UPLOAD_DIR, image_filename)
            card_image.save(image_path)
            
            # 创建卡片记录
            card_record = {
                "id": card_id,
                "title": title,
                "content": content,
                "subject": analysis.get('subject', 'general'),
                "confidence": analysis.get('confidence', 0.5),
                "visualization_type": analysis.get('visualization_type', '文本展示'),
                "image": f"/uploads/{image_filename}",
                "course_id": course_id,
                "created_at": time.time(),
                "file_ids": file_ids
            }
            
            generated_cards.append(card_record)
        
        # 保存到数据库
        existing_cards = get_note_cards()
        existing_cards.extend(generated_cards)
        save_note_cards(existing_cards)
        
        return {
            "success": True,
            "cards": generated_cards,
            "message": f"成功生成{len(generated_cards)}张笔记卡片"
        }
        
    except Exception as e:
        return {"success": False, "error": f"生成笔记卡片失败: {str(e)}"}

class SimpleHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        # 处理静态文件请求（图片等）
        if self.path.startswith('/uploads/'):
            try:
                # 构建文件路径
                file_path = os.path.join(UPLOAD_DIR, self.path[9:])  # 去掉 '/uploads/' 前缀
                
                if os.path.exists(file_path) and os.path.isfile(file_path):
                    # 确定文件类型
                    if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                        content_type = 'image/png' if file_path.lower().endswith('.png') else 'image/jpeg'
                    else:
                        content_type = 'application/octet-stream'
                    
                    # 发送文件
                    self.send_response(200)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-type', content_type)
                    self.end_headers()
                    
                    with open(file_path, 'rb') as f:
                        self.wfile.write(f.read())
                    return
                else:
                    self.send_response(404)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    self.wfile.write(b'File Not Found')
                    return
            except Exception as e:
                print(f"静态文件服务错误: {str(e)}")
                self.send_response(500)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(b'Internal Server Error')
                return
        
        # API请求处理
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # 获取课程列表
        if self.path == '/api/courses':
            self.wfile.write(json.dumps(get_courses()).encode('utf-8'))
            
        # 获取课程文件
        elif self.path.startswith('/api/courses/') and '/files' in self.path:
            parts = self.path.split('/')
            course_id = parts[3]  # /api/courses/{course_id}/files
            course_files = get_course_files(course_id)
            self.wfile.write(json.dumps({"files": course_files}).encode('utf-8'))
            
        # 获取课程笔记卡片
        elif self.path.startswith('/api/courses/') and '/cards' in self.path:
            parts = self.path.split('/')
            course_id = parts[3]  # /api/courses/{course_id}/cards
            cards = get_note_cards(course_id)
            self.wfile.write(json.dumps({"cards": cards}).encode('utf-8'))
        
        else:
            self.wfile.write(json.dumps({
                "error": "路径不存在"
            }).encode('utf-8'))
    
    def call_google_ai_api(self, prompt):
        """调用Google AI API处理文本请求"""
        try:
            # 获取API密钥
            api_key = os.getenv('GOOGLE_AI_API_KEY', 'AIzaSyCbJ8PlTK7UTCkKwCv1uVyM5RXnsMv4qLM')
            
            if not api_key:
                return "错误: 未设置Google AI API密钥。请在.env文件中配置GOOGLE_AI_API_KEY。"
            
            # 使用gemini-2.0-flash模型（2024年最新）
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            headers = {
                "Content-Type": "application/json"
            }
            
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.4,
                    "topK": 32,
                    "topP": 1,
                    "maxOutputTokens": 2048
                }
            }
            
            # 发送请求
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    if "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"]:
                        return result["candidates"][0]["content"]["parts"][0]["text"]
                
                return "AI未能生成有效回复"
            else:
                error_details = response.text
                try:
                    error_json = response.json()
                    if "error" in error_json:
                        error_details = error_json["error"]["message"]
                except:
                    pass
                
                return f"API调用失败: HTTP {response.status_code}\n{error_details}"
            
        except Exception as e:
            return f"处理请求时出错: {str(e)}"
    
    def call_gemini_multimodal_api(self, file_path, file_type, prompt):
        """调用Gemini多模态API处理图片、音频或视频文件"""
        try:
            # 获取API密钥
            api_key = os.getenv('GOOGLE_AI_API_KEY', 'AIzaSyCbJ8PlTK7UTCkKwCv1uVyM5RXnsMv4qLM')
            
            if not api_key:
                return "错误: 未设置Google AI API密钥。请在.env文件中配置GOOGLE_AI_API_KEY。"
            
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            
            # 根据文件类型设置不同的大小限制
            if file_type == 'video':
                max_size = 100 * 1024 * 1024  # 视频文件限制100MB
            elif file_type == 'audio':
                max_size = 20 * 1024 * 1024   # 音频文件限制20MB
            else:
                max_size = 10 * 1024 * 1024   # PDF等其他文件限制10MB
            
            if file_size > max_size:
                size_mb = file_size/1024/1024
                limit_mb = max_size/1024/1024
                return f"文件大小({size_mb:.2f}MB)超过限制({limit_mb:.0f}MB)。请上传更小的文件。"
            
            # 读取文件数据
            with open(file_path, 'rb') as file:
                file_bytes = file.read()
            
            # 确定MIME类型
            mime_type = ""
            if file_type == "audio":
                if file_path.endswith('.mp3'):
                    mime_type = "audio/mpeg"
                elif file_path.endswith('.wav'):
                    mime_type = "audio/wav"
                elif file_path.endswith('.m4a'):
                    mime_type = "audio/mp4"
                else:
                    mime_type = "audio/mpeg"  # 默认
            elif file_type == "video":
                if file_path.endswith('.mp4'):
                    mime_type = "video/mp4"
                elif file_path.endswith('.avi'):
                    mime_type = "video/x-msvideo"
                elif file_path.endswith('.mov'):
                    mime_type = "video/quicktime"
                else:
                    mime_type = "video/mp4"  # 默认
            elif file_type == "image":
                if file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                    mime_type = "image/jpeg"
                elif file_path.endswith('.png'):
                    mime_type = "image/png"
                elif file_path.endswith('.gif'):
                    mime_type = "image/gif"
                elif file_path.endswith('.webp'):
                    mime_type = "image/webp"
                else:
                    mime_type = "image/jpeg"  # 默认
            elif file_type == "pdf":
                mime_type = "application/pdf"
            
            # 使用最新的gemini-2.0-flash模型
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            headers = {
                "Content-Type": "application/json"
            }
            
            # 将文件编码为Base64
            file_base64 = base64.b64encode(file_bytes).decode('utf-8')
            
            # 构建请求体
            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"请用中文回答：{prompt}"
                            },
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": file_base64
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.4,
                    "topK": 32,
                    "topP": 1,
                    "maxOutputTokens": 2048
                }
            }
            
            # 发送请求
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    if "content" in result["candidates"][0] and "parts" in result["candidates"][0]["content"]:
                        return result["candidates"][0]["content"]["parts"][0]["text"]
                
                return "AI未能生成有效回复。这可能是因为文件过大或格式不受支持。"
            else:
                error_details = response.text
                try:
                    error_json = response.json()
                    if "error" in error_json:
                        error_details = error_json["error"]["message"]
                except:
                    pass
                
                return f"API调用失败: HTTP {response.status_code}\n{error_details}\n\n这可能是因为文件太大或格式不受支持。"
        
        except Exception as e:
            return f"处理{file_type}文件时出错: {str(e)}"
    
    def process_pdf(self, file_path):
        """处理PDF文件并提取文本内容"""
        try:
            # 直接调用多模态API处理PDF文件
            return self.call_gemini_multimodal_api(file_path, "pdf", "请分析这个PDF文件并提供详细信息和内容摘要。如果内容中包含问题，请回答这些问题。")
        except Exception as e:
            # 如果多模态API处理失败，回退到传统提取方法
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    total_pages = len(pdf_reader.pages)
                    
                    # 添加PDF的基本信息
                    text += f"PDF文件包含 {total_pages} 页\n\n"
                    
                    # 提取文本内容
                    for i, page in enumerate(pdf_reader.pages):
                        page_content = page.extract_text() or "【此页无文本内容】"
                        text += f"--- 第 {i+1} 页 ---\n{page_content}\n\n"
                    
                    # 处理提取的文本
                    prompt = f"""
                    我上传了一个PDF文件，其内容如下:
                    
                    {text}
                    
                    请根据文件内容进行分析并给出专业的回复。如果内容中包含问题，请回答这些问题。
                    如果是一般内容，请总结主要观点并提出建议。
                    """
                    
                    return self.call_google_ai_api(prompt)
            except Exception as e2:
                raise Exception(f"PDF处理错误: {str(e)}, 备用处理也失败: {str(e2)}")
    
    def do_POST(self):
        # URL导入功能
        if self.path == '/api/upload-by-url':
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
            
            try:
                # 解析POST请求中的JSON数据
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                url = data.get('url', '').strip()
                course_id = data.get('courseId', '').strip()
                
                if not url:
                    self.wfile.write(json.dumps({
                        "error": "URL不能为空"
                    }).encode('utf-8'))
                    return
                
                if not course_id:
                    self.wfile.write(json.dumps({
                        "error": "未指定课程ID"
                    }).encode('utf-8'))
                    return
                
                # 验证URL格式
                import urllib.parse
                parsed_url = urllib.parse.urlparse(url)
                if not parsed_url.scheme or not parsed_url.netloc:
                    self.wfile.write(json.dumps({
                        "error": "无效的URL格式"
                    }).encode('utf-8'))
                    return
                
                # 检查课程是否存在
                courses_data = get_courses()
                course_exists = any(course["id"] == course_id for course in courses_data["courses"])
                if not course_exists:
                    self.wfile.write(json.dumps({
                        "error": f"课程ID不存在: {course_id}"
                    }).encode('utf-8'))
                    return
                
                # 下载文件
                import urllib.request
                import tempfile
                import mimetypes
                
                try:
                    # 创建请求，设置User-Agent避免被拒绝
                    req = urllib.request.Request(url)
                    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                    
                    # 下载文件
                    with urllib.request.urlopen(req, timeout=30) as response:
                        # 检查响应状态
                        if response.status != 200:
                            self.wfile.write(json.dumps({
                                "error": f"无法下载文件，HTTP状态码: {response.status}"
                            }).encode('utf-8'))
                            return
                        
                        # 获取文件内容
                        file_content = response.read()
                        
                        # 获取文件名和类型
                        content_disposition = response.headers.get('Content-Disposition', '')
                        if 'filename=' in content_disposition:
                            filename = content_disposition.split('filename=')[1].strip('"\'')
                        else:
                            # 从URL中提取文件名
                            filename = os.path.basename(parsed_url.path)
                            if not filename or '.' not in filename:
                                # 根据Content-Type推断文件扩展名
                                content_type = response.headers.get('Content-Type', '')
                                ext = mimetypes.guess_extension(content_type.split(';')[0])
                                filename = f"downloaded_file_{int(time.time())}{ext or '.txt'}"
                        
                        # 确保文件名安全
                        filename = os.path.basename(filename)  # 防止路径遍历
                        if not filename:
                            filename = f"downloaded_file_{int(time.time())}.txt"
                
                except urllib.error.HTTPError as e:
                    self.wfile.write(json.dumps({
                        "error": f"下载失败，HTTP错误: {e.code} {e.reason}"
                    }).encode('utf-8'))
                    return
                except urllib.error.URLError as e:
                    self.wfile.write(json.dumps({
                        "error": f"下载失败，网络错误: {str(e.reason)}"
                    }).encode('utf-8'))
                    return
                except Exception as e:
                    self.wfile.write(json.dumps({
                        "error": f"下载失败: {str(e)}"
                    }).encode('utf-8'))
                    return
                
                # 检查文件大小
                file_size = len(file_content)
                max_size = 100 * 1024 * 1024  # 100MB限制
                
                if file_size > max_size:
                    size_mb = file_size/1024/1024
                    self.wfile.write(json.dumps({
                        "error": f"文件大小({size_mb:.2f}MB)超过限制(100MB)。请选择更小的文件。"
                    }).encode('utf-8'))
                    return
                
                # 根据文件扩展名确定文件类型
                file_extension = filename.split('.')[-1].lower() if '.' in filename else ''
                
                if file_extension == 'pdf':
                    file_type = 'pdf'
                elif file_extension in ['mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac']:
                    file_type = 'audio'
                elif file_extension in ['mp4', 'avi', 'mov', 'webm', 'mkv', 'flv']:
                    file_type = 'video'
                elif file_extension in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
                    file_type = 'image'
                elif file_extension in ['doc', 'docx', 'txt', 'rtf']:
                    file_type = 'document'
                elif file_extension in ['ppt', 'pptx']:
                    file_type = 'presentation'
                else:
                    file_type = 'document'
                
                # 创建课程文件目录
                course_dir = os.path.join(UPLOAD_DIR, course_id)
                if not os.path.exists(course_dir):
                    os.makedirs(course_dir)
                
                # 创建临时文件
                temp_file_path = os.path.join(course_dir, f"{int(time.time())}_{filename}")
                
                # 保存下载的文件
                with open(temp_file_path, 'wb') as f:
                    f.write(file_content)
                
                try:
                    # 根据文件类型处理
                    if file_type == 'pdf':
                        ai_response = self.process_pdf(temp_file_path)
                    elif file_type == 'audio':
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "audio", "请分析这个音频文件并提供详细内容描述、转录和总结")
                    elif file_type == 'video':
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "video", "请分析这个视频并提供详细内容描述、场景分析、转录和总结")
                    elif file_type == 'image':
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "image", "请分析这张图片并提供详细描述、内容分析和总结")
                    elif file_type in ['document', 'presentation']:
                        # 对于文档类型，尝试作为文本处理
                        ai_response = f"已通过URL导入文件：{filename}。文件类型：{file_type}。文件来源：{url}。请在聊天中询问相关问题以获取更多信息。"
                    else:
                        ai_response = f"已通过URL导入文件：{filename}。文件类型：{file_type}。文件来源：{url}。"
                    
                    # 记录文件信息
                    summary = ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
                    new_file = add_file_record(
                        file_name=filename,
                        file_type=file_type,
                        file_path=os.path.relpath(temp_file_path, UPLOAD_DIR),
                        course_id=course_id,
                        summary=summary,
                        screenshots=None
                    )
                    
                    self.wfile.write(json.dumps({
                        "success": True,
                        "file": new_file,
                        "content": ai_response,
                        "message": f"成功从URL导入文件: {filename}"
                    }).encode('utf-8'))
                    
                except Exception as e:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    raise e
                
            except Exception as e:
                self.wfile.write(json.dumps({
                    "error": f"处理URL导入时出错: {str(e)}"
                }).encode('utf-8'))
            return
        
        # 文件上传功能
        elif self.path == '/api/upload':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            try:
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )
                
                # 检查是否有文件上传
                if 'file' not in form:
                    self.wfile.write(json.dumps({
                        "error": "没有找到上传的文件"
                    }).encode('utf-8'))
                    return
                
                # 检查是否提供了课程ID
                if 'courseId' not in form:
                    self.wfile.write(json.dumps({
                        "error": "未指定课程ID"
                    }).encode('utf-8'))
                    return
                
                # 获取上传的文件和课程ID
                file_item = form['file']
                course_id = form['courseId'].value
                
                # 根据文件扩展名确定文件类型
                filename = file_item.filename
                file_extension = filename.split('.')[-1].lower() if '.' in filename else ''
                
                if file_extension == 'pdf':
                    file_type = 'pdf'
                elif file_extension in ['mp3', 'wav', 'ogg', 'm4a']:
                    file_type = 'audio'
                elif file_extension in ['mp4', 'avi', 'mov', 'webm']:
                    file_type = 'video'
                elif file_extension in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                    file_type = 'image'
                else:
                    file_type = 'document'
                
                # 检查文件大小
                file_content = file_item.file.read()
                file_size = len(file_content)
                
                # 根据文件类型设置不同的大小限制
                if file_type == 'video':
                    max_size = 100 * 1024 * 1024  # 视频文件限制100MB
                elif file_type == 'audio':
                    max_size = 20 * 1024 * 1024   # 音频文件限制20MB
                else:
                    max_size = 10 * 1024 * 1024   # PDF等其他文件限制10MB
                
                if file_size > max_size:
                    size_mb = file_size/1024/1024
                    limit_mb = max_size/1024/1024
                    self.wfile.write(json.dumps({
                        "error": f"文件大小({size_mb:.2f}MB)超过限制({limit_mb:.0f}MB)。请上传更小的文件。"
                    }).encode('utf-8'))
                    return
                
                # 检查课程是否存在
                courses_data = get_courses()
                course_exists = any(course["id"] == course_id for course in courses_data["courses"])
                if not course_exists:
                    self.wfile.write(json.dumps({
                        "error": f"课程ID不存在: {course_id}"
                    }).encode('utf-8'))
                    return
                
                # 创建课程文件目录
                course_dir = os.path.join(UPLOAD_DIR, course_id)
                if not os.path.exists(course_dir):
                    os.makedirs(course_dir)
                
                # 创建临时文件
                temp_file_path = os.path.join(course_dir, f"{int(time.time())}_{file_item.filename}")
                
                # 保存上传的文件
                with open(temp_file_path, 'wb') as f:
                    f.write(file_content)
                
                try:
                    # 根据文件类型处理
                    if file_type == 'pdf':
                        ai_response = self.process_pdf(temp_file_path)
                    elif file_type == 'audio':
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "audio", "请分析这个音频文件并提供详细内容描述、转录和总结")
                    elif file_type == 'video':
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "video", "请分析这个视频并提供详细内容描述、场景分析、转录和总结")
                    elif file_type == 'image':
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "image", "请分析这张图片并提供详细描述、内容分析和总结")
                    elif file_type == 'document':
                        # 对于其他文档类型，尝试作为文本处理
                        ai_response = f"已上传文档文件：{filename}。文件类型：{file_type}。请在聊天中询问相关问题以获取更多信息。"
                    else:
                        raise Exception("不支持的文件类型")
                    
                    # 记录文件信息
                    summary = ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
                    new_file = add_file_record(
                        file_name=file_item.filename,
                        file_type=file_type,
                        file_path=os.path.relpath(temp_file_path, UPLOAD_DIR),
                        course_id=course_id,
                        summary=summary,
                        screenshots=None
                    )
                    
                    self.wfile.write(json.dumps({
                        "success": True,
                        "file": new_file,
                        "content": ai_response
                    }).encode('utf-8'))
                    
                except Exception as e:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    raise e
                
            except Exception as e:
                self.wfile.write(json.dumps({
                    "error": f"处理文件时出错: {str(e)}"
                }).encode('utf-8'))
            return
        
        # 其他POST请求的通用响应头设置
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        # 更新课程名称
        if self.path.startswith('/api/courses/') and '/update' in self.path:
            try:
                # 解析URL: /api/courses/{course_id}/update
                parts = self.path.split('/')
                course_id = parts[3]
                
                # 解析POST请求中的JSON数据
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                name = data.get('name', '').strip()
                
                if not name:
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": "课程名称不能为空"
                    }).encode('utf-8'))
                    return
                
                result = update_course(course_id, name)
                self.wfile.write(json.dumps(result).encode('utf-8'))
                
            except Exception as e:
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": str(e)
                }).encode('utf-8'))
        
        # 创建新课程
        elif self.path == '/api/courses':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                name = data.get('name', '').strip()
                
                if not name:
                    self.wfile.write(json.dumps({
                        "error": "课程名称不能为空"
                    }).encode('utf-8'))
                    return
                
                new_course = create_course(name)
                self.wfile.write(json.dumps({
                    "course": new_course
                }).encode('utf-8'))
                
            except Exception as e:
                self.wfile.write(json.dumps({
                    "error": f"创建课程失败: {str(e)}"
                }).encode('utf-8'))
        
        # 生成笔记卡片（批量，保持向后兼容）
        elif self.path.startswith('/api/courses/') and '/generate-cards' in self.path:
            # 解析URL: /api/courses/{course_id}/generate-cards
            parts = self.path.split('/')
            if len(parts) >= 4:
                course_id = parts[3]
                
                try:
                    # 读取请求数据
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                    file_ids = data.get('fileIds', [])
                    
                    if not file_ids:
                        # 如果没有指定文件，使用课程下的所有文件
                        course_files = get_course_files(course_id)
                        file_ids = [file["id"] for file in course_files]
                    
                    if not file_ids:
                self.wfile.write(json.dumps({
                            "success": False,
                            "error": "没有找到文件，请先上传学习材料"
                    }).encode('utf-8'))
                    return
                
                    # 生成笔记卡片
                    result = generate_note_cards_from_files(course_id, file_ids)
                    self.wfile.write(json.dumps(result).encode('utf-8'))
                
                except Exception as e:
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": f"生成笔记卡片失败: {str(e)}"
                    }).encode('utf-8'))
                    else:
                    self.wfile.write(json.dumps({
                        "success": False,
                    "error": "无效的请求路径"
                    }).encode('utf-8'))
        
        # 生成单张笔记卡片（分页）
        elif self.path.startswith('/api/courses/') and self.path.endswith('/generate-single-card'):
            # 解析URL: /api/courses/{course_id}/generate-single-card
            parts = self.path.split('/')
            if len(parts) >= 4:
                course_id = parts[3]
                
                try:
                    # 读取请求数据
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    file_ids = data.get('fileIds', [])
                    card_index = data.get('cardIndex', 0)  # 卡片索引，从0开始
                    
                    if not file_ids:
                        # 如果没有指定文件，使用课程下的所有文件
                        course_files = get_course_files(course_id)
                        file_ids = [file["id"] for file in course_files]
                    
                    if not file_ids:
                        self.wfile.write(json.dumps({
                            "success": False,
                            "error": "没有找到文件，请先上传学习材料"
                        }).encode('utf-8'))
                        return
                    
                    # 生成单张笔记卡片
                    result = generate_single_note_card(course_id, file_ids, card_index)
                    self.wfile.write(json.dumps(result).encode('utf-8'))
                
            except Exception as e:
                self.wfile.write(json.dumps({
                    "success": False,
                        "error": f"生成笔记卡片失败: {str(e)}"
                    }).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": "无效的请求路径"
                }).encode('utf-8'))
        
        # 聊天功能
        elif self.path == '/api/chat':
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                message = data.get('message', '')
                course_id = data.get('courseId')
                
                if not message.strip():
                    self.wfile.write(json.dumps({
                        "error": "消息不能为空"
                    }).encode('utf-8'))
                    return
                
                # 构建上下文
                context = ""
                
                # 如果指定了课程ID，使用课程文件作为上下文
                if course_id:
                    course_files = get_course_files(course_id)
                    if course_files:
                        context = "基于以下课程材料回答问题：\n\n"
                        for file in course_files:
                            context += f"文件：{file['name']}\n摘要：{file.get('summary', '无摘要')}\n\n"
                        message = context + "\n用户问题：" + message
                
                # 调用AI接口
                ai_response = self.call_google_ai_api(message)
                
                self.wfile.write(json.dumps({
                    "response": ai_response
            }).encode('utf-8'))

            except Exception as e:
                self.wfile.write(json.dumps({
                    "error": str(e)
                }).encode('utf-8'))
        
        # URL导入功能
        elif self.path == '/api/upload-by-url':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
            
            try:
                # 解析POST请求中的JSON数据
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                url = data.get('url', '').strip()
                course_id = data.get('courseId', '').strip()
                
                if not url:
                    self.wfile.write(json.dumps({
                        "error": "URL不能为空"
                    }).encode('utf-8'))
                    return
                
                if not course_id:
                    self.wfile.write(json.dumps({
                        "error": "未指定课程ID"
                    }).encode('utf-8'))
                    return
                
                # 验证URL格式
                import urllib.parse
                parsed_url = urllib.parse.urlparse(url)
                if not parsed_url.scheme or not parsed_url.netloc:
                    self.wfile.write(json.dumps({
                        "error": "无效的URL格式"
                    }).encode('utf-8'))
                    return
                
                # 检查课程是否存在
                courses_data = get_courses()
                course_exists = any(course["id"] == course_id for course in courses_data["courses"])
                if not course_exists:
                    self.wfile.write(json.dumps({
                        "error": f"课程ID不存在: {course_id}"
                    }).encode('utf-8'))
                    return
                
                # 下载文件
                import urllib.request
                import tempfile
                import mimetypes
                
                try:
                    # 创建请求，设置User-Agent避免被拒绝
                    req = urllib.request.Request(url)
                    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
                    
                    # 下载文件
                    with urllib.request.urlopen(req, timeout=30) as response:
                        # 检查响应状态
                        if response.status != 200:
                            self.wfile.write(json.dumps({
                                "error": f"无法下载文件，HTTP状态码: {response.status}"
                            }).encode('utf-8'))
                            return
                        
                        # 获取文件内容
                        file_content = response.read()
                        
                        # 获取文件名和类型
                        content_disposition = response.headers.get('Content-Disposition', '')
                        if 'filename=' in content_disposition:
                            filename = content_disposition.split('filename=')[1].strip('"\'')
                else:
                            # 从URL中提取文件名
                            filename = os.path.basename(parsed_url.path)
                            if not filename or '.' not in filename:
                                # 根据Content-Type推断文件扩展名
                                content_type = response.headers.get('Content-Type', '')
                                ext = mimetypes.guess_extension(content_type.split(';')[0])
                                filename = f"downloaded_file_{int(time.time())}{ext or '.txt'}"
                        
                        # 确保文件名安全
                        filename = os.path.basename(filename)  # 防止路径遍历
                        if not filename:
                            filename = f"downloaded_file_{int(time.time())}.txt"
                
                except urllib.error.HTTPError as e:
                    self.wfile.write(json.dumps({
                        "error": f"下载失败，HTTP错误: {e.code} {e.reason}"
                    }).encode('utf-8'))
                    return
                except urllib.error.URLError as e:
                    self.wfile.write(json.dumps({
                        "error": f"下载失败，网络错误: {str(e.reason)}"
                    }).encode('utf-8'))
                    return
                except Exception as e:
                    self.wfile.write(json.dumps({
                        "error": f"下载失败: {str(e)}"
                    }).encode('utf-8'))
                    return
                
                # 检查文件大小
                file_size = len(file_content)
                max_size = 100 * 1024 * 1024  # 100MB限制
                
                if file_size > max_size:
                    size_mb = file_size/1024/1024
                    self.wfile.write(json.dumps({
                        "error": f"文件大小({size_mb:.2f}MB)超过限制(100MB)。请选择更小的文件。"
                    }).encode('utf-8'))
                    return
                
                # 根据文件扩展名确定文件类型
                file_extension = filename.split('.')[-1].lower() if '.' in filename else ''
                
                if file_extension == 'pdf':
                    file_type = 'pdf'
                elif file_extension in ['mp3', 'wav', 'ogg', 'm4a', 'flac', 'aac']:
                    file_type = 'audio'
                elif file_extension in ['mp4', 'avi', 'mov', 'webm', 'mkv', 'flv']:
                    file_type = 'video'
                elif file_extension in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']:
                    file_type = 'image'
                elif file_extension in ['doc', 'docx', 'txt', 'rtf']:
                    file_type = 'document'
                elif file_extension in ['ppt', 'pptx']:
                    file_type = 'presentation'
                else:
                    file_type = 'document'
                
                # 创建课程文件目录
                course_dir = os.path.join(UPLOAD_DIR, course_id)
                if not os.path.exists(course_dir):
                    os.makedirs(course_dir)
                
                # 创建临时文件
                temp_file_path = os.path.join(course_dir, f"{int(time.time())}_{filename}")
                
                # 保存下载的文件
                with open(temp_file_path, 'wb') as f:
                    f.write(file_content)
                
                try:
                    # 根据文件类型处理
                    if file_type == 'pdf':
                        ai_response = self.process_pdf(temp_file_path)
                    elif file_type == 'audio':
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "audio", "请分析这个音频文件并提供详细内容描述、转录和总结")
                    elif file_type == 'video':
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "video", "请分析这个视频并提供详细内容描述、场景分析、转录和总结")
                    elif file_type == 'image':
                        ai_response = self.call_gemini_multimodal_api(temp_file_path, "image", "请分析这张图片并提供详细描述、内容分析和总结")
                    elif file_type in ['document', 'presentation']:
                        # 对于文档类型，尝试作为文本处理
                        ai_response = f"已通过URL导入文件：{filename}。文件类型：{file_type}。文件来源：{url}。请在聊天中询问相关问题以获取更多信息。"
                    else:
                        ai_response = f"已通过URL导入文件：{filename}。文件类型：{file_type}。文件来源：{url}。"
                    
                    # 记录文件信息
                    summary = ai_response[:200] + "..." if len(ai_response) > 200 else ai_response
                    new_file = add_file_record(
                        file_name=filename,
                        file_type=file_type,
                        file_path=os.path.relpath(temp_file_path, UPLOAD_DIR),
                        course_id=course_id,
                        summary=summary,
                        screenshots=None
                    )
                    
                    self.wfile.write(json.dumps({
                        "success": True,
                        "file": new_file,
                        "content": ai_response,
                        "message": f"成功从URL导入文件: {filename}"
                    }).encode('utf-8'))
                    
                except Exception as e:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    raise e
                
            except Exception as e:
                self.wfile.write(json.dumps({
                    "error": f"处理URL导入时出错: {str(e)}"
                }).encode('utf-8'))
            return
        
        else:
            self.wfile.write(json.dumps({
                "error": "路径不存在"
            }).encode('utf-8'))
    
    def do_DELETE(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # 删除课程
        if self.path.startswith('/api/courses/') and not '/files/' in self.path and not '/cards' in self.path:
            # 解析URL: /api/courses/{course_id}
            parts = self.path.split('/')
            if len(parts) >= 4:
                course_id = parts[3]
                
                try:
                    result = delete_course(course_id)
                    self.wfile.write(json.dumps(result).encode('utf-8'))
                except Exception as e:
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": str(e)
                    }).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": "无效的删除请求路径"
                }).encode('utf-8'))
        
        # 删除文件
        elif self.path.startswith('/api/courses/') and '/files/' in self.path:
            # 解析URL: /api/courses/{course_id}/files/{file_id}
            parts = self.path.split('/')
            if len(parts) >= 6:
                course_id = parts[3]
                file_id = parts[5]
                
                try:
                    result = delete_file(file_id, course_id)
                    self.wfile.write(json.dumps(result).encode('utf-8'))
        except Exception as e:
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": str(e)
                    }).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": "无效的删除请求路径"
                }).encode('utf-8'))
        
        # 删除笔记卡片
        elif self.path.startswith('/api/cards/'):
            # 解析URL: /api/cards/{card_id}
            parts = self.path.split('/')
            if len(parts) >= 3:
                card_id = parts[3]
                
                try:
                    result = delete_note_card(card_id)
                    self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
                    self.wfile.write(json.dumps({
                        "error": str(e)
                    }).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({
                    "error": "无效的删除请求路径"
                }).encode('utf-8'))
        
        else:
            self.wfile.write(json.dumps({
                "error": "不支持的请求地址"
            }).encode('utf-8'))
    
    def do_PUT(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        
        # 更新课程名称
        if self.path.startswith('/api/courses/') and not '/files/' in self.path and not '/cards' in self.path:
            # 解析URL: /api/courses/{course_id}
            parts = self.path.split('/')
            if len(parts) >= 4:
                course_id = parts[3]
                
                try:
                    # 读取请求数据
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    name = data.get('name', '').strip()
                    
                    if not name:
                        self.wfile.write(json.dumps({
                            "success": False,
                            "error": "课程名称不能为空"
                        }).encode('utf-8'))
                        return
                    
                    result = update_course(course_id, name)
                    self.wfile.write(json.dumps(result).encode('utf-8'))
                    
                except Exception as e:
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": str(e)
                    }).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": "无效的更新请求路径"
                }).encode('utf-8'))
        
        # 更新笔记卡片
        elif self.path.startswith('/api/cards/'):
            # 解析URL: /api/cards/{card_id}
            parts = self.path.split('/')
            if len(parts) >= 3:
                card_id = parts[3]
                
                try:
                    # 读取请求数据
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    data = json.loads(post_data.decode('utf-8'))
                    title = data.get('title', '').strip()
                    content = data.get('content', '').strip()
                    
                    if not title or not content:
                        self.wfile.write(json.dumps({
                            "success": False,
                            "error": "标题和内容不能为空"
                        }).encode('utf-8'))
                        return
                    
                    result = update_note_card(card_id, title, content)
                    self.wfile.write(json.dumps(result).encode('utf-8'))
            
        except Exception as e:
                    self.wfile.write(json.dumps({
                        "success": False,
                        "error": str(e)
                    }).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({
                    "success": False,
                    "error": "无效的更新请求路径"
                }).encode('utf-8'))
        
        else:
            self.wfile.write(json.dumps({
                "error": "不支持的请求地址"
            }).encode('utf-8'))

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8001):
    init_data_files()
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'启动服务器在端口 {port}')
    httpd.serve_forever()

if __name__ == '__main__':
    # 获取环境变量
    host = os.getenv("HOST", "0.0.0.0")  # 默认允许网络访问
    port = int(os.getenv("PORT", "8001"))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print(f"🚀 启动AI课堂助手后端服务...")
    print(f"📍 服务地址: http://{host}:{port}")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    print(f"🔑 API密钥状态: {'已配置' if os.getenv('GOOGLE_AI_API_KEY') else '未配置'}")
    
    uvicorn.run(
        "app.main:app", 
        host=host,
        port=port, 
        reload=debug,
        workers=1 if debug else 4,  # 生产环境使用多个工作进程
        access_log=True,
        log_level="info"
    ) 