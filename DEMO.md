# 🎉 AI课堂助手在线演示

## 🌟 产品特色

### 🤖 智能AI助手
- **多模态分析**: 支持图片、音频、视频、PDF等格式
- **智能对话**: 基于Gemini 2.0 Flash模型的AI聊天
- **个性化学习**: 根据学习内容智能生成知识点

### 📚 笔记卡片生成
- **自动生成**: 一键生成精美的学习笔记卡片
- **数学可视化**: 自动生成函数图形、几何图形
- **多学科支持**: 数学、物理、化学、生物等
- **清晰设计**: 简洁明了的卡片布局

### 🎯 核心功能

| 功能 | 描述 | 示例 |
|------|------|------|
| **课程管理** | 创建和管理不同课程 | 高数一、工业设计史 |
| **文件上传** | 支持多种格式上传 | PDF、图片、音频、视频 |
| **AI分析** | 智能内容分析和总结 | 自动提取关键知识点 |
| **笔记生成** | 生成带图形的学习卡片 | 函数图像、化学结构式 |
| **聊天对话** | 实时AI学习助手 | 答疑解惑、学习指导 |

## 🚀 快速部署

### 方案1：云服务器一键部署

```bash
# 下载并运行部署脚本
wget https://raw.githubusercontent.com/io-oi-ai/Classroom-learning-assistant/main/quick_deploy.sh
chmod +x quick_deploy.sh
sudo ./quick_deploy.sh
```

**结果**: 
- 前端: `http://你的服务器IP:3000`
- 后端: `http://你的服务器IP:8001`

### 方案2：本地快速体验

```bash
# 克隆项目
git clone https://github.com/io-oi-ai/Classroom-learning-assistant.git
cd Classroom-learning-assistant

# 配置API密钥
echo "GOOGLE_AI_API_KEY=你的密钥" > .env

# Docker启动
docker-compose up -d
```

**结果**: 
- 访问: `http://localhost:3000`

## 📱 使用演示

### 1️⃣ 创建课程
![课程管理](https://via.placeholder.com/600x300/2196F3/white?text=课程管理界面)

**操作步骤**:
1. 点击"创建课程"
2. 输入课程名称（如：高等数学）
3. 开始上传学习材料

### 2️⃣ 上传学习材料
![文件上传](https://via.placeholder.com/600x300/4CAF50/white?text=文件上传界面)

**支持格式**:
- 📄 PDF文档
- 🖼️ 图片文件
- 🎵 音频录音
- 📹 视频课程

### 3️⃣ 生成智能笔记
![笔记生成](https://via.placeholder.com/600x300/FF9800/white?text=智能笔记卡片)

**特色功能**:
- ✅ 自动提取关键概念
- ✅ 生成数学函数图形
- ✅ 智能学科分类
- ✅ 精美卡片设计

### 4️⃣ AI学习助手
![AI对话](https://via.placeholder.com/600x300/9C27B0/white?text=AI学习助手)

**对话示例**:
```
用户: 请解释一下什么是极限
AI: 极限是微积分的基础概念，表示函数值在自变量趋向某一值时的趋势...
```

## 🎯 实际效果展示

### 数学笔记卡片示例
```
标题: 极限计算方法总结
内容: 
- 基本极限定理
- 洛必达法则
- 夹逼定理
- 等价无穷小替换

[函数图形: y=1/x 在 x→0 时的行为]
```

### 物理笔记卡片示例
```
标题: 牛顿第二定律
内容:
- F = ma
- 力与加速度的关系
- 质量的作用

[示意图: 力的分析图]
```

## 🌐 在线访问

### 演示地址
- **完整版**: `https://classroom.your-domain.com`
- **API文档**: `https://classroom.your-domain.com/api/docs`

### 测试账号
- 用户名: `demo@example.com`
- 密码: `demo123`

## 📊 技术架构

```
前端 (Next.js) → 后端 (Python) → AI模型 (Gemini)
     ↓              ↓              ↓
  用户界面     ←   API服务     ←   智能分析
     ↓              ↓              ↓
  文件管理     ←   数据存储     ←   内容生成
```

## 🔧 部署配置

### 最低配置要求
- **CPU**: 2核
- **内存**: 4GB
- **存储**: 40GB
- **带宽**: 5Mbps

### 推荐配置
- **CPU**: 4核
- **内存**: 8GB
- **存储**: 100GB SSD
- **带宽**: 100Mbps

## 📞 获取支持

### 常见问题
1. **Q: 如何获取Google AI API密钥？**
   A: 访问 [Google AI Studio](https://aistudio.google.com/app/apikey) 注册并创建密钥

2. **Q: 支持哪些文件格式？**
   A: PDF、图片(JPG/PNG)、音频(MP3/WAV)、视频(MP4/AVI)

3. **Q: 生成的笔记卡片可以导出吗？**
   A: 是的，支持PNG图片格式导出

### 技术支持
- 🐛 [报告问题](https://github.com/io-oi-ai/Classroom-learning-assistant/issues)
- 📖 [查看文档](https://github.com/io-oi-ai/Classroom-learning-assistant/blob/main/部署指南.md)
- 💬 [在线讨论](https://github.com/io-oi-ai/Classroom-learning-assistant/discussions)

---

🎓 **立即体验AI驱动的智能学习助手，让学习更高效！** 