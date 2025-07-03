"use client"

import { DialogFooter } from "../components/ui/dialog"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { useChat } from "@ai-sdk/react"
import { Button } from "../components/ui/button"
import { Textarea } from "../components/ui/textarea"
import { Avatar, AvatarFallback } from "../components/ui/avatar"
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "../components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "../components/ui/tabs"
import { ScrollArea } from "../components/ui/scroll-area"
import {
  FileText,
  Send,
  Upload,
  Globe,
  MessageSquare,
  Clock,
  Search,
  PlusCircle,
  ChevronDown,
  Paperclip,
  ImageIcon,
  File,
  BookOpen,
  GraduationCap,
  Music,
  Video,
  Database,
  ArrowRight,
  Plus,
  Trash2,
  Edit3,
  Edit2,
  Save,
  FolderOpen,
  ChevronRight,
  X
} from "lucide-react"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "../components/ui/dialog"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { v4 as uuidv4 } from "uuid"
import { Progress } from "../components/ui/progress"
import { API_CONFIG, getApiUrl, getCourseUrl } from './config'

interface Course {
  id: string
  name: string
  createTime: number
}

interface FileItem {
  id: string
  name: string
  type: string
  path: string
  courseId: string
  uploadTime: number
  summary: string
}

interface Note {
  id: string
  content: string
  courseId: string
  messageId: string
  createdAt: number
}

export default function LearningAssistant() {
  const [subjects, setSubjects] = useState([
    {
      name: "自动控制原理",
      color: "blue",
      teacher: "李教授",
      chats: [
        "自动控制系统的稳定性分析",
        "PID控制器的参数调整方法",
        "频率响应分析与波特图",
        "状态空间表示法的优势",
        "根轨迹法设计控制系统",
      ],
    },
    {
      name: "数据结构",
      color: "green",
      teacher: "王教授",
      chats: [
        "二叉树的遍历算法比较",
        "红黑树与AVL树的区别",
        "图的最短路径算法",
        "哈希表的冲突解决策略",
        "排序算法的时间复杂度分析",
      ],
    },
    {
      name: "计算机网络",
      color: "purple",
      teacher: "张教授",
      chats: [
        "TCP/IP协议栈的层次结构",
        "HTTP与HTTPS的区别",
        "网络安全中的加密技术",
        "DNS解析过程详解",
        "IPv4向IPv6过渡的挑战",
      ],
    },
    {
      name: "高等数学",
      color: "yellow",
      teacher: "陈教授",
      chats: [
        "多元函数微分学应用",
        "级数收敛性判别方法",
        "拉普拉斯变换的性质",
        "傅里叶级数展开技巧",
        "偏微分方程求解方法",
      ],
    },
    {
      name: "机器学习",
      color: "red",
      teacher: "刘教授",
      chats: [
        "神经网络的反向传播算法",
        "支持向量机的核函数选择",
        "决策树与随机森林比较",
        "无监督学习中的聚类方法",
        "过拟合问题的解决方案",
      ],
    },
  ])
  const [activeSubject, setActiveSubject] = useState<number>(0)
  const { messages, input, handleInputChange, handleSubmit, isLoading, setMessages, setInput } = useChat({
    api: "/api/chat",
    initialMessages: [
      {
        id: "welcome-message",
        role: "assistant",
        content: `您好！我是您的AI学习助手。很高兴能帮助您解答问题。请问您想了解什么内容呢？`,
      },
    ],
    onResponse: (response) => {
      console.log("收到AI响应:", response)
      setTimeout(() => {
        if (messagesEndRef.current) {
          messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
        }
      }, 100)
    },
    onError: (error) => {
      console.error("AI响应错误:", error)
      setMessages((messages) => [
        ...messages,
        {
          id: uuidv4(),
          role: "assistant",
          content: "抱歉，我遇到了一些问题。请稍后再试。",
        },
      ])
    },
  })

  const [files, setFiles] = useState<FileList | undefined>(undefined)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const knowledgeFileInputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [activeChat, setActiveChat] = useState<number>(0)
  const [isAddCourseOpen, setIsAddCourseOpen] = useState(false)
  const [isNewChatOpen, setIsNewChatOpen] = useState(false)
  const [newChatMessage, setNewChatMessage] = useState("")
  const [newCourseName, setNewCourseName] = useState("")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [isKnowledgeUploadOpen, setIsKnowledgeUploadOpen] = useState(false)
  const [knowledgeFiles, setKnowledgeFiles] = useState<File[]>([])
  const [uploadProgress, setUploadProgress] = useState<{ [key: string]: number }>({})
  const [isUploading, setIsUploading] = useState(false)
  
  // 课程和文件管理相关状态
  const [courses, setCourses] = useState<Course[]>([])
  const [expandedCourses, setExpandedCourses] = useState<Set<string>>(new Set())
  const [courseFiles, setCourseFiles] = useState<{ [courseId: string]: FileItem[] }>({})
  const [selectedFiles, setSelectedFiles] = useState<string[]>([])
  const [currentCourseId, setCurrentCourseId] = useState<string | null>(null)
  
  // 笔记编辑相关状态
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null)
  const [editingContent, setEditingContent] = useState("")
  const [notes, setNotes] = useState<Note[]>([])
  
  // 笔记卡片相关状态
  const [isGeneratingCards, setIsGeneratingCards] = useState(false)
  
  // 课程编辑相关状态
  const [editingCourseId, setEditingCourseId] = useState<string | null>(null)
  const [editingCourseName, setEditingCourseName] = useState("")
  
  // URL导入相关状态
  const [isUrlImportOpen, setIsUrlImportOpen] = useState(false)
  const [importUrl, setImportUrl] = useState("")
  const [isImporting, setIsImporting] = useState(false)

  const colors = ["blue", "green", "purple", "yellow", "red", "pink", "indigo", "orange", "teal"]

  // 获取课程列表
  const fetchCourses = async () => {
    try {
      const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.COURSES))
      const data = await response.json()
      setCourses(data.courses || [])
      if (data.courses && data.courses.length > 0 && !currentCourseId) {
        setCurrentCourseId(data.courses[0].id)
      }
    } catch (error) {
      console.error('获取课程列表失败:', error)
    }
  }

  // 获取课程文件
  const fetchCourseFiles = async (courseId: string) => {
    try {
      const response = await fetch(getCourseUrl(courseId, '/files'))
      const data = await response.json()
      setCourseFiles(prev => ({
        ...prev,
        [courseId]: data.files || []
      }))
    } catch (error) {
      console.error('获取课程文件失败:', error)
      setCourseFiles(prev => ({
        ...prev,
        [courseId]: []
      }))
    }
  }

  // 切换课程展开状态
  const toggleCourseExpansion = (courseId: string) => {
    const newExpanded = new Set(expandedCourses)
    if (newExpanded.has(courseId)) {
      newExpanded.delete(courseId)
    } else {
      newExpanded.add(courseId)
      // 如果还没有加载过这个课程的文件，则加载
      if (!courseFiles[courseId]) {
        fetchCourseFiles(courseId)
      }
    }
    setExpandedCourses(newExpanded)
  }

  // 处理文件选择
  const handleFileSelection = (fileId: string, courseId: string) => {
    setSelectedFiles(prev => {
      const newSelection = prev.includes(fileId) 
        ? prev.filter(id => id !== fileId)
        : [...prev, fileId]
      
      // 如果有文件被选择，自动设置当前课程ID
      if (newSelection.length > 0) {
        setCurrentCourseId(courseId)
      }
      
      return newSelection
    })
  }

  // 清空文件选择
  const clearFileSelection = () => {
    setSelectedFiles([])
  }

  // 上传文件到指定课程
  const uploadFilesToCourse = async (courseId: string, uploadFiles: FileList) => {
    if (uploadFiles.length === 0) return

    setIsUploading(true)
    let successCount = 0
    let failCount = 0

    for (let i = 0; i < uploadFiles.length; i++) {
      const file = uploadFiles[i]
      const formData = new FormData()
      formData.append('file', file)
      formData.append('courseId', courseId)

      try {
        // 真实上传进度模拟
        setUploadProgress(prev => ({
          ...prev,
          [file.name]: 0
        }))

        const xhr = new XMLHttpRequest()
        
        // 监听上传进度
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            const percentComplete = Math.round((e.loaded / e.total) * 100)
            setUploadProgress(prev => ({
              ...prev,
              [file.name]: percentComplete
            }))
          }
        })

        // 创建Promise来处理XMLHttpRequest
        const uploadPromise = new Promise((resolve, reject) => {
          xhr.onload = () => {
            if (xhr.status === 200) {
              resolve(xhr.response)
            } else {
              reject(new Error(`HTTP ${xhr.status}`))
            }
          }
          xhr.onerror = () => reject(new Error('网络错误'))
        })

        xhr.open('POST', getApiUrl(API_CONFIG.ENDPOINTS.UPLOAD))
        xhr.send(formData)

        await uploadPromise
        successCount++
        
        // 标记为完成
        setUploadProgress(prev => ({
          ...prev,
          [file.name]: 100
        }))

      } catch (error) {
        console.error(`上传文件 ${file.name} 失败:`, error)
        failCount++
        setUploadProgress(prev => ({
          ...prev,
          [file.name]: -1 // 标记为失败
        }))
      }
    }

    // 显示上传结果消息
    const resultMessage = successCount > 0 
      ? `✅ 成功上传 ${successCount} 个文件${failCount > 0 ? `，${failCount} 个文件上传失败` : ''}！`
      : `❌ 所有文件上传失败，请检查网络连接或文件格式。`

    setMessages((prev) => [
      ...prev,
      {
        id: uuidv4(),
        role: "assistant",
        content: resultMessage,
      },
    ])

    // 重新加载该课程的文件列表
    if (successCount > 0) {
      await fetchCourseFiles(courseId)
    }

    setIsUploading(false)
    // 延迟清除进度，让用户看到完成状态
    setTimeout(() => {
      setUploadProgress({})
    }, 2000)
  }

  // 删除文件
  const deleteFile = async (courseId: string, fileId: string) => {
    try {
      const response = await fetch(getCourseUrl(courseId, `/files/${fileId}`), {
        method: 'DELETE',
      })

      if (response.ok) {
        await fetchCourseFiles(courseId)
        setSelectedFiles(prev => prev.filter(id => id !== fileId))
      }
    } catch (error) {
      console.error('删除文件失败:', error)
    }
  }

  // 开始编辑消息
  const startEditingMessage = (messageId: string, content: string) => {
    setEditingMessageId(messageId)
    setEditingContent(content)
  }

  // 保存编辑的消息为笔记
  const saveMessageAsNote = async () => {
    if (!editingMessageId || !editingContent.trim() || !currentCourseId) return

    const newNote: Note = {
      id: uuidv4(),
      content: editingContent.trim(),
      courseId: currentCourseId,
      messageId: editingMessageId,
      createdAt: Date.now()
    }

    setNotes(prev => [...prev, newNote])
    setEditingMessageId(null)
    setEditingContent("")

    // 这里可以添加保存到后端的逻辑
    try {
      // await saveNoteToBackend(newNote)
      console.log('笔记已保存:', newNote)
    } catch (error) {
      console.error('保存笔记失败:', error)
    }
  }

  // 取消编辑
  const cancelEditing = () => {
    setEditingMessageId(null)
    setEditingContent("")
  }

  // 生成笔记卡片
  const generateNoteCards = async (courseId: string, fileIds: string[]) => {
    setIsGeneratingCards(true)
    try {
      const response = await fetch(getCourseUrl(courseId, '/generate-single-card'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          fileIds: fileIds,
          cardIndex: 0  // 总是生成第一张（唯一的）卡片
        }),
      })

      const data = await response.json()
      
      if (data.success) {
        // 显示成功消息
        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            role: "assistant",
            content: `✨ 成功生成了一张智能笔记卡片！这张卡片包含了从您的文件中提取的关键知识点，并配有丰富的图形化内容，帮助您更好地理解和记忆内容。`,
          },
        ])
        
        // 清空文件选择
        clearFileSelection()
      } else {
        throw new Error(data.error || '生成笔记卡片失败')
      }
    } catch (error) {
      console.error('生成笔记卡片失败:', error)
      const errorMessage = error instanceof Error ? error.message : '未知错误'
      setMessages((prev) => [
        ...prev,
        {
          id: uuidv4(),
          role: "assistant",
          content: `抱歉，生成笔记卡片时遇到了问题：${errorMessage}。请稍后重试。`,
        },
      ])
    } finally {
      setIsGeneratingCards(false)
    }
  }

  // 开始编辑课程名称
  const startEditingCourse = (courseId: string, currentName: string) => {
    setEditingCourseId(courseId)
    setEditingCourseName(currentName)
  }

  // 保存课程名称
  const saveCourseEdit = async (courseId: string) => {
    if (!editingCourseName.trim()) {
      alert('课程名称不能为空')
      return
    }

    try {
      const response = await fetch(getCourseUrl(courseId, '/update'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: editingCourseName.trim() })
      })

      const data = await response.json()
      
      if (data.success) {
        // 更新本地课程列表
        setCourses(courses.map(course => 
          course.id === courseId 
            ? { ...course, name: editingCourseName.trim() }
            : course
        ))
        setEditingCourseId(null)
        setEditingCourseName("")
        
        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            role: "assistant",
            content: `✅ 课程名称已成功更新为"${editingCourseName.trim()}"！`,
          },
        ])
      } else {
        alert(`更新失败: ${data.error}`)
      }
    } catch (error) {
      console.error('更新课程名称失败:', error)
      alert('更新失败，请重试')
    }
  }

  // 取消编辑课程名称
  const cancelCourseEdit = () => {
    setEditingCourseId(null)
    setEditingCourseName("")
  }

  // 删除课程
  const deleteCourse = async (courseId: string, courseName: string) => {
    if (!confirm(`确定要删除课程"${courseName}"吗？\n\n此操作将同时删除：\n- 课程下的所有文件\n- 课程相关的所有笔记卡片\n- 课程目录和数据\n\n此操作不可恢复！`)) {
      return
    }

    try {
      const response = await fetch(getCourseUrl(courseId, ''), {
        method: 'DELETE'
      })

      const data = await response.json()
      
      if (data.success) {
        // 从本地课程列表中移除
        setCourses(courses.filter(course => course.id !== courseId))
        
        // 如果删除的是当前选中的课程，清除选中状态
        if (currentCourseId === courseId) {
          setCurrentCourseId(null)
        }
        
        // 清除相关的文件数据
        const newCourseFiles = { ...courseFiles }
        delete newCourseFiles[courseId]
        setCourseFiles(newCourseFiles)
        
        // 清除文件选择
        setSelectedFiles([])
        
        setMessages((prev) => [
          ...prev,
          {
            id: uuidv4(),
            role: "assistant",
            content: `✅ 课程"${courseName}"及其所有相关数据已成功删除！`,
          },
        ])
      } else {
        alert(`删除失败: ${data.error}`)
      }
    } catch (error) {
      console.error('删除课程失败:', error)
      alert('删除失败，请重试')
    }
  }

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split(".").pop()?.toLowerCase()

    if (["pdf"].includes(extension || "")) {
      return <File className="h-4 w-4 text-red-500" />
    } else if (["jpg", "jpeg", "png", "gif", "webp"].includes(extension || "")) {
      return <ImageIcon className="h-4 w-4 text-blue-500" />
    } else if (["mp3", "wav", "ogg"].includes(extension || "")) {
      return <Music className="h-4 w-4 text-purple-500" />
    } else if (["mp4", "webm", "avi", "mov"].includes(extension || "")) {
      return <Video className="h-4 w-4 text-green-500" />
    } else {
      return <FileText className="h-4 w-4 text-gray-500" />
    }
  }

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString('zh-CN')
  }

  // 滚动到最新消息
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
    }
  }, [messages])

  // 初始化时获取课程列表
  useEffect(() => {
    fetchCourses()
  }, [])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFiles(e.dataTransfer.files)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFiles(e.target.files)
    }
  }

  const handleKnowledgeFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files)
      setKnowledgeFiles((prev) => [...prev, ...newFiles])

      const newProgress = { ...uploadProgress }
      newFiles.forEach((file) => {
        newProgress[file.name] = 0
      })
      setUploadProgress(newProgress)
    }
  }

  const handleKnowledgeFileDrop = (e: React.DragEvent) => {
    e.preventDefault()
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files)
      setKnowledgeFiles((prev) => [...prev, ...newFiles])

      const newProgress = { ...uploadProgress }
      newFiles.forEach((file) => {
        newProgress[file.name] = 0
      })
      setUploadProgress(newProgress)
    }
  }

  const removeKnowledgeFile = (fileName: string) => {
    setKnowledgeFiles((prev) => prev.filter((file) => file.name !== fileName))

    const newProgress = { ...uploadProgress }
    delete newProgress[fileName]
    setUploadProgress(newProgress)
  }

  const uploadKnowledgeFiles = async () => {
    if (knowledgeFiles.length === 0) return

    setIsUploading(true)

    for (const file of knowledgeFiles) {
      for (let progress = 0; progress <= 100; progress += 5) {
        setUploadProgress((prev) => ({
          ...prev,
          [file.name]: progress,
        }))
        await new Promise((resolve) => setTimeout(resolve, 100))
      }

      await new Promise((resolve) => setTimeout(resolve, 500))
    }

    setMessages((prev) => [
      ...prev,
      {
        id: uuidv4(),
        role: "assistant",
        content: `我已经学习了您上传的${knowledgeFiles.length}个文件，并将其添加到我的知识库中。现在您可以向我提问相关内容了！`,
      },
    ])

    setKnowledgeFiles([])
    setUploadProgress({})
    setIsUploading(false)
  }

  const handleFormSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()

    if (!input.trim() && (!files || files.length === 0) && selectedFiles.length === 0) {
      return
    }

    if (input.trim()) {
      const updatedSubjects = [...subjects]
      if (messages.length === 0) {
        updatedSubjects[activeSubject].chats.unshift(input.trim())
      } else if (activeChat === 0) {
        updatedSubjects[activeSubject].chats[activeChat] = input.trim()
      }
      setSubjects(updatedSubjects)
    }

    const userMessage = {
      id: uuidv4(),
      role: "user" as const,
      content: input,
    }
    setMessages((prev) => [...prev, userMessage])

    const loadingId = uuidv4()
    setMessages((prev) => [
      ...prev,
      {
        id: loadingId,
        role: "assistant" as const,
        content: selectedFiles.length > 0 ? "正在分析您选择的文件并思考回答..." : "正在思考...",
      },
    ])

    try {
      if (selectedFiles.length > 0 && currentCourseId) {
        const requestData = {
          message: input,
          courseId: currentCourseId,
          isNewChat: false,
          selectedFiles: selectedFiles
        }

        const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.CHAT), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(requestData)
        })

        const data = await response.json()

        setMessages((prev) =>
          prev
            .filter((msg) => msg.id !== loadingId)
            .concat({
              id: uuidv4(),
              role: "assistant" as const,
              content: data.response || "抱歉，我无法理解您的问题。请尝试重新表述。",
            }),
        )
      } else {
        handleSubmit(e, {
          experimental_attachments: files,
        })
        
        setMessages((prev) => prev.filter((msg) => msg.id !== loadingId))
      }

      setInput("")
      setFiles(undefined)
      if (fileInputRef.current) {
        fileInputRef.current.value = ""
      }

      setTimeout(() => {
        if (messagesEndRef.current) {
          messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
        }
      }, 100)
    } catch (error) {
      console.error("发送消息失败:", error)
      setMessages((prev) =>
        prev
          .filter((msg) => msg.id !== loadingId)
          .concat({
            id: uuidv4(),
            role: "assistant" as const,
            content: "抱歉，我遇到了一些问题。请稍后再试。",
          }),
      )
    }
  }

  const handleAddCourse = async () => {
    if (!newCourseName.trim()) return

    try {
      const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.COURSES), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name: newCourseName.trim() }),
      })

      if (response.ok) {
        const result = await response.json()
        const newCourse = result.course
        
        setCourses(prev => [...prev, newCourse])
        
        const randomColor = colors[Math.floor(Math.random() * colors.length)]

        const newSubjectItem = {
          name: newCourseName,
          teacher: "AI助教",
          color: randomColor,
          chats: [],
        }

        setSubjects([...subjects, newSubjectItem])

        setNewCourseName("")
        setIsAddCourseOpen(false)

        setActiveSubject(subjects.length)
        setActiveChat(0)
      }
    } catch (error) {
      console.error('创建课程失败:', error)
    }
  }

  const handleStartNewChat = async () => {
    if (newChatMessage.trim()) {
      const updatedSubjects = [...subjects]
      updatedSubjects[activeSubject].chats.unshift(newChatMessage.trim())
      setSubjects(updatedSubjects)

      setIsNewChatOpen(false)

      const welcomeMessage = {
        id: "welcome-message",
        role: "assistant",
        content: `您好！我是您的AI学习助手。很高兴能帮助您解答问题。`,
      }

      const userMessage = {
        id: uuidv4(),
        role: "user",
        content: newChatMessage.trim(),
      }

      setMessages([welcomeMessage, userMessage] as any)

      setActiveChat(0)

      try {
        const loadingId = uuidv4()
        setMessages((prev) => [...prev, { id: loadingId, role: "assistant", content: "正在思考...", isLoading: true }])

        const response = await fetch("/api/chat", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            messages: [
              {
                role: "system",
                content: `你是一位AI学习助手。请用专业且易懂的方式回答问题。`,
              },
              {
                role: "user",
                content: newChatMessage.trim(),
              },
            ],
          }),
        })

        if (!response.ok) {
          throw new Error("AI响应出错")
        }

        const data = await response.json()

        setMessages((prev) =>
          prev
            .filter((msg) => msg.id !== loadingId)
            .concat({
              id: uuidv4(),
              role: "assistant",
              content: data.text || "抱歉，我无法理解您的问题。请尝试重新表述。",
            }),
        )

        setInput("")
        setNewChatMessage("")

        setTimeout(() => {
          if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: "smooth" })
          }
        }, 100)
      } catch (error) {
        console.error("发送消息失败:", error)
        setMessages((prev) =>
          prev
            .filter((msg) => !(msg as any).isLoading)
            .concat({
              id: uuidv4(),
              role: "assistant",
              content: "抱歉，我遇到了一些问题。请稍后再试。",
            }),
        )
      }
    }
  }

  // URL导入功能
  const handleUrlImport = async () => {
    if (!importUrl.trim()) {
      alert('请输入有效的URL')
      return
    }

    if (!currentCourseId) {
      alert('请先选择一个课程')
      return
    }

    setIsImporting(true)
    
    try {
      const response = await fetch(getApiUrl('/api/upload-by-url'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: importUrl.trim(),
          courseId: currentCourseId
        })
      })

      const data = await response.json()

      if (data.success) {
        // 刷新文件列表
        await fetchCourseFiles(currentCourseId)
        
        // 关闭对话框并清空输入
        setIsUrlImportOpen(false)
        setImportUrl('')
        
        alert(data.message || '文件导入成功！')
      } else {
        alert(data.error || '导入失败，请检查URL是否有效')
      }
    } catch (error) {
      console.error('URL导入失败:', error)
      alert('导入失败，请检查网络连接和URL是否有效')
    } finally {
      setIsImporting(false)
    }
  }

  useEffect(() => {
    setActiveChat(0)
    console.log(`切换到学科: ${subjects[activeSubject].name}`)
  }, [activeSubject])

  const currentSubjectChats = subjects[activeSubject].chats || []

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-80 border-r bg-white flex flex-col overflow-hidden">
        <div className="p-4 flex items-center gap-2 border-b">
          <div className="h-8 w-8 rounded-full bg-purple-600 flex items-center justify-center">
            <span className="text-white font-bold">AI</span>
          </div>
          <span className="font-semibold">学习助手</span>
        </div>

        <div className="p-3">
          <Button variant="outline" className="w-full justify-start gap-2 mb-2 text-sm" onClick={() => setIsNewChatOpen(true)}>
            <PlusCircle className="h-4 w-4 flex-shrink-0" />
            <span className="truncate">新对话</span>
          </Button>
          <Button variant="outline" className="w-full justify-start gap-2 mb-2 text-sm" onClick={() => setIsAddCourseOpen(true)}>
            <Plus className="h-4 w-4 flex-shrink-0" />
            <span className="truncate">新建课程</span>
          </Button>
          <Button 
            variant="outline" 
            className="w-full justify-start gap-2 mb-2 text-sm" 
            onClick={() => window.open('/cards', '_blank')}
          >
            <ImageIcon className="h-4 w-4 flex-shrink-0" />
            <span className="truncate">查看笔记卡片</span>
          </Button>
          <Button 
            variant="outline" 
            className="w-full justify-start gap-2 mb-4 text-sm" 
            onClick={() => window.open('/handwritten', '_blank')}
          >
            <Edit3 className="h-4 w-4 flex-shrink-0" />
            <span className="truncate">手写笔记生成</span>
          </Button>
        </div>

        <div className="flex items-center px-4 py-2">
          <div className="flex items-center gap-2 text-sm font-medium">
            <BookOpen className="h-4 w-4" />
            <span>我的课程</span>
          </div>
        </div>

        <ScrollArea className="flex-1">
          {courses.map((course) => (
            <div key={course.id} className="border-b border-gray-100">
              {/* 课程标题 */}
              <div 
                className="px-4 py-3 hover:bg-gray-50 cursor-pointer flex items-center justify-between group"
                onClick={() => toggleCourseExpansion(course.id)}
              >
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <GraduationCap className="h-4 w-4 text-blue-500 flex-shrink-0" />
                  {editingCourseId === course.id ? (
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <Input
                        value={editingCourseName}
                        onChange={(e) => setEditingCourseName(e.target.value)}
                        className="h-6 text-sm flex-1 min-w-0"
                        onKeyDown={(e) => {
                          e.stopPropagation()
                          if (e.key === 'Enter') {
                            saveCourseEdit(course.id)
                          } else if (e.key === 'Escape') {
                            cancelCourseEdit()
                          }
                        }}
                        autoFocus
                        onClick={(e) => e.stopPropagation()}
                      />
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0 flex-shrink-0"
                        onClick={(e) => {
                          e.stopPropagation()
                          saveCourseEdit(course.id)
                        }}
                        title="保存"
                      >
                        <Save className="h-3 w-3 text-green-600" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0 flex-shrink-0"
                        onClick={(e) => {
                          e.stopPropagation()
                          cancelCourseEdit()
                        }}
                        title="取消"
                      >
                        <X className="h-3 w-3 text-gray-500" />
                      </Button>
                    </div>
                  ) : (
                    <span className="font-medium truncate min-w-0" title={course.name}>{course.name}</span>
                  )}
                </div>
                <div className="flex items-center gap-1 flex-shrink-0">
                  {/* 编辑按钮 */}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => {
                      e.stopPropagation()
                      startEditingCourse(course.id, course.name)
                    }}
                    title="编辑课程名"
                  >
                    <Edit2 className="h-3 w-3 text-gray-500 hover:text-blue-600" />
                  </Button>
                  
                  {/* 删除按钮 */}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => {
                      e.stopPropagation()
                      deleteCourse(course.id, course.name)
                    }}
                    title="删除课程"
                  >
                    <Trash2 className="h-3 w-3 text-red-500 hover:text-red-700" />
                  </Button>
                  
                  <ChevronRight 
                    className={`h-4 w-4 text-gray-400 transition-transform flex-shrink-0 ${
                      expandedCourses.has(course.id) ? 'rotate-90' : ''
                    }`} 
                  />
                </div>
              </div>

              {/* 展开的文件列表 */}
              {expandedCourses.has(course.id) && (
                <div className="px-4 pb-3 bg-gray-50">
                  {/* 文件上传区域 */}
                  <div className="mb-3">
                    <input
                      type="file"
                      multiple
                      className="hidden"
                      id={`file-upload-${course.id}`}
                      onChange={(e) => {
                        if (e.target.files) {
                          uploadFilesToCourse(course.id, e.target.files)
                        }
                      }}
                    />
                    <div className="space-y-2">
                      {/* 上传文件按钮 */}
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full text-xs flex items-center justify-center gap-2 h-8"
                        onClick={() => document.getElementById(`file-upload-${course.id}`)?.click()}
                        disabled={isUploading}
                      >
                        {isUploading ? (
                          <>
                            <div className="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin flex-shrink-0"></div>
                            <span className="truncate">上传文件中...</span>
                          </>
                        ) : (
                          <>
                            <Upload className="h-3 w-3 flex-shrink-0" />
                            <span className="truncate">上传文件</span>
                          </>
                        )}
                      </Button>
                      
                      {/* 导入链接按钮 */}
                      <Button
                        variant="outline"
                        size="sm"
                        className="w-full text-xs flex items-center justify-center gap-2 h-8 border-green-300 text-green-700 hover:bg-green-50"
                        onClick={() => {
                          setCurrentCourseId(course.id)
                          setIsUrlImportOpen(true)
                        }}
                        disabled={isImporting}
                      >
                        {isImporting ? (
                          <>
                            <div className="w-3 h-3 border border-green-400 border-t-transparent rounded-full animate-spin flex-shrink-0"></div>
                            <span className="truncate">导入链接中...</span>
                          </>
                        ) : (
                          <>
                            <Globe className="h-3 w-3 flex-shrink-0" />
                            <span className="truncate">导入链接</span>
                          </>
                        )}
                      </Button>
                    </div>
                    
                    {/* 上传进度显示 */}
                    {Object.keys(uploadProgress).length > 0 && (
                      <div className="mt-2 space-y-1">
                        {Object.entries(uploadProgress).map(([fileName, progress]) => (
                          <div key={fileName} className="text-xs">
                            <div className="flex items-center justify-between mb-1">
                              <span className="truncate flex-1 min-w-0" title={fileName}>{fileName}</span>
                              <span className={`ml-2 flex-shrink-0 ${
                                progress === -1 ? 'text-red-500' : 
                                progress === 100 ? 'text-green-500' : 'text-blue-500'
                              }`}>
                                {progress === -1 ? '失败' : progress === 100 ? '完成' : `${progress}%`}
                              </span>
                            </div>
                            {progress >= 0 && progress < 100 && (
                              <Progress value={progress} className="h-1" />
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* 文件列表 */}
                  <div className="space-y-1 max-h-40 overflow-y-auto scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
                    {courseFiles[course.id]?.map((file) => (
                      <div
                        key={file.id}
                        className={`group flex items-center gap-2 p-2 text-xs rounded transition-colors ${
                          selectedFiles.includes(file.id) 
                            ? 'bg-blue-100 border border-blue-300' 
                            : 'hover:bg-gray-100 border border-transparent'
                        }`}
                      >
                        <input
                          type="checkbox"
                          checked={selectedFiles.includes(file.id)}
                          onChange={() => handleFileSelection(file.id, course.id)}
                          className="w-3 h-3 flex-shrink-0"
                          onClick={(e) => e.stopPropagation()}
                        />
                        <div className="flex-shrink-0">
                          {getFileIcon(file.name)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="truncate font-medium text-xs" title={file.name}>{file.name}</div>
                          <div className="text-gray-500 text-xs truncate leading-tight" title={file.summary || '无摘要'}>
                            {file.summary ? (file.summary.length > 25 ? file.summary.substring(0, 25) + '...' : file.summary) : '无摘要'}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteFile(course.id, file.id)
                          }}
                          title="删除文件"
                        >
                          <Trash2 className="h-3 w-3 text-red-500 hover:text-red-700" />
                        </Button>
                      </div>
                    )) || (
                      <div className="text-xs text-gray-500 text-center py-2">
                        暂无文件
                      </div>
                    )}
                  </div>

                  {/* 选择文件操作 */}
                  {selectedFiles.length > 0 && (
                    <div className="mt-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => generateNoteCards(course.id, selectedFiles)}
                        disabled={isGeneratingCards}
                        className="w-full text-xs flex items-center justify-center gap-1"
                      >
                        {isGeneratingCards ? (
                          <>
                            <div className="w-3 h-3 border border-gray-400 border-t-transparent rounded-full animate-spin flex-shrink-0"></div>
                            <span className="truncate">生成中...</span>
                          </>
                        ) : (
                          <>
                            <ImageIcon className="h-3 w-3 flex-shrink-0" />
                            <span className="truncate">生成图片笔记卡片</span>
                          </>
                        )}
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
          
          {courses.length === 0 && (
            <div className="px-4 py-6 text-center text-sm text-gray-500">
              <BookOpen className="h-8 w-8 mx-auto mb-2 text-gray-300" />
              <p>还没有课程</p>
              <p className="text-xs mt-1">点击上方"新建课程"开始</p>
            </div>
          )}
        </ScrollArea>

        <div className="flex items-center px-4 py-2 border-t">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Clock className="h-4 w-4" />
            <span>最近对话</span>
          </div>
          <Button variant="ghost" size="icon" className="ml-auto">
            <ChevronDown className="h-4 w-4" />
          </Button>
        </div>

        <ScrollArea className="max-h-32 scrollbar-thin scrollbar-thumb-gray-300 scrollbar-track-gray-100">
          {currentSubjectChats.length > 0 ? (
            currentSubjectChats.map((chat, index) => (
              <div
                key={index}
                className={`px-4 py-2 text-sm hover:bg-gray-100 cursor-pointer ${activeChat === index ? "bg-blue-50 border-l-2 border-blue-500" : ""}`}
                onClick={() => setActiveChat(index)}
                title={chat}
              >
                <div className="truncate">{chat}</div>
              </div>
            ))
          ) : (
            <div className="px-4 py-6 text-center text-sm text-gray-500">暂无对话记录</div>
          )}
        </ScrollArea>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <div className="p-4 border-b bg-white flex justify-between items-center">
          <Tabs defaultValue="chat">
            <TabsList>
              <TabsTrigger value="chat">聊天</TabsTrigger>
              <TabsTrigger value="search">搜索</TabsTrigger>
            </TabsList>
          </Tabs>

          <div className="flex items-center gap-2">
            <GraduationCap className="h-5 w-5 text-blue-500" />
            <span className="font-medium">
              AI学习助手
              {selectedFiles.length > 0 && (
                <span className="ml-2 text-sm text-blue-600">
                  (基于 {selectedFiles.length} 个文件)
                </span>
              )}
            </span>
          </div>
        </div>

        <ScrollArea className="flex-1 p-4 relative">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center mb-4">
                <MessageSquare className="h-8 w-8 text-blue-500" />
              </div>
              <h2 className="text-2xl font-bold mb-2">我是您的AI学习助手</h2>
              <p className="text-gray-500 mb-6">
                上传文件并提问，我将帮助你理解内容
              </p>

              <div className="grid grid-cols-4 gap-4 max-w-2xl">
                <Button variant="outline" className="flex flex-col h-24 p-3">
                  <FileText className="h-6 w-6 mb-2" />
                  <span className="text-xs">文档分析</span>
                </Button>
                <Button variant="outline" className="flex flex-col h-24 p-3">
                  <Search className="h-6 w-6 mb-2" />
                  <span className="text-xs">AI搜索</span>
                </Button>
                <Button variant="outline" className="flex flex-col h-24 p-3">
                  <BookOpen className="h-6 w-6 mb-2" />
                  <span className="text-xs">课程资料</span>
                </Button>
                <Button variant="outline" className="flex flex-col h-24 p-3">
                  <ImageIcon className="h-6 w-6 mb-2" />
                  <span className="text-xs">图像生成</span>
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {messages.map((message) => (
                <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`flex gap-3 max-w-3xl ${message.role === "user" ? "flex-row-reverse" : ""}`}>
                    <Avatar>
                      <AvatarFallback>
                        {message.role === "user" ? "用户" : "AI"}
                      </AvatarFallback>
                    </Avatar>
                    <Card className={message.role === "assistant" ? "bg-blue-50" : ""}>
                      <CardContent className="p-4">
                        {editingMessageId === message.id ? (
                          <div className="space-y-3">
                            <Textarea
                              value={editingContent}
                              onChange={(e) => setEditingContent(e.target.value)}
                              className="min-h-[100px]"
                              placeholder="编辑您的笔记内容..."
                            />
                            <div className="flex gap-2">
                              <Button size="sm" onClick={saveMessageAsNote}>
                                <Save className="h-4 w-4 mr-1" />
                                保存笔记
                              </Button>
                              <Button size="sm" variant="outline" onClick={cancelEditing}>
                                取消
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <div className="group relative">
                            <div className="whitespace-pre-wrap">{message.content}</div>
                            {message.role === "assistant" && (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="absolute top-0 right-0 opacity-0 group-hover:opacity-100 transition-opacity"
                                onClick={() => startEditingMessage(message.id, message.content)}
                              >
                                <Edit3 className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        )}
                        {message.experimental_attachments?.map((attachment, index) => (
                          <div key={index} className="mt-2">
                            {attachment.contentType?.startsWith("image/") ? (
                              <img
                                src={attachment.url || "/placeholder.svg"}
                                alt={attachment.name || `Attachment ${index}`}
                                className="max-w-full rounded-md border"
                              />
                            ) : attachment.contentType?.startsWith("application/pdf") ? (
                              <div className="flex items-center gap-2 p-2 border rounded-md bg-gray-50">
                                <File className="h-5 w-5 text-red-500" />
                                <span>{attachment.name || `PDF ${index}`}</span>
                              </div>
                            ) : (
                              <div className="flex items-center gap-2 p-2 border rounded-md bg-gray-50">
                                <FileText className="h-5 w-5" />
                                <span>{attachment.name || `File ${index}`}</span>
                              </div>
                            )}
                          </div>
                        ))}
                      </CardContent>
                    </Card>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="flex gap-3 max-w-3xl">
                    <Avatar>
                      <AvatarFallback>AI</AvatarFallback>
                    </Avatar>
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center space-x-2">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                          <div
                            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                            style={{ animationDelay: "0.2s" }}
                          ></div>
                          <div
                            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                            style={{ animationDelay: "0.4s" }}
                          ></div>
                          <span className="text-sm text-gray-500 ml-1">正在思考...</span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}

          {/* 固定在ScrollArea右下角的文件上传窗口 */}
          <div className={`absolute bottom-4 right-4 z-50 ${isKnowledgeUploadOpen ? "w-80" : "w-14"}`}>
            <Card className="shadow-lg border-blue-200 transition-all duration-300">
              <CardHeader
                className={`p-3 bg-blue-500 text-white rounded-t-lg flex ${isKnowledgeUploadOpen ? "justify-between" : "justify-center"} items-center cursor-pointer`}
                onClick={() => setIsKnowledgeUploadOpen(!isKnowledgeUploadOpen)}
              >
                {isKnowledgeUploadOpen ? (
                  <>
                    <CardTitle className="text-sm flex items-center">
                      <Database className="h-4 w-4 mr-2" />
                      添加到知识库
                    </CardTitle>
                    <X className="h-4 w-4 cursor-pointer" />
                  </>
                ) : (
                  <Database className="h-6 w-6" />
                )}
              </CardHeader>

              {isKnowledgeUploadOpen && (
                <>
                  <CardContent className="p-3 space-y-3">
                    <div className="grid grid-cols-2 gap-2">
                      <div
                        className="border-2 border-dashed border-blue-300 rounded-md p-3 text-center cursor-pointer hover:bg-blue-50 transition-colors"
                        onClick={() => knowledgeFileInputRef.current?.click()}
                        onDragOver={(e) => e.preventDefault()}
                        onDrop={handleKnowledgeFileDrop}
                      >
                        <Upload className="h-6 w-6 text-blue-500 mx-auto mb-1" />
                        <p className="text-xs text-blue-700">上传文件</p>
                        <input
                          type="file"
                          ref={knowledgeFileInputRef}
                          onChange={handleKnowledgeFileChange}
                          className="hidden"
                          multiple
                          accept=".pdf,.doc,.docx,.txt,.mp3,.wav,.mp4,.avi,.jpg,.jpeg,.png"
                        />
                      </div>
                      
                      <div
                        className="border-2 border-dashed border-green-300 rounded-md p-3 text-center cursor-pointer hover:bg-green-50 transition-colors"
                        onClick={() => setIsUrlImportOpen(true)}
                      >
                        <Globe className="h-6 w-6 text-green-500 mx-auto mb-1" />
                        <p className="text-xs text-green-700">导入链接</p>
                      </div>
                    </div>
                    
                    <p className="text-xs text-gray-500 text-center">支持PDF、Word、PPT、图片、音频、视频等格式</p>

                    {knowledgeFiles.length > 0 && (
                      <div className="space-y-2 max-h-40 overflow-y-auto">
                        {knowledgeFiles.map((file, index) => (
                          <div key={index} className="flex items-center justify-between bg-gray-50 p-2 rounded-md">
                            <div className="flex items-center gap-2 text-sm overflow-hidden">
                              {getFileIcon(file.name)}
                              <span className="truncate">{file.name}</span>
                            </div>
                            <div className="flex items-center">
                              {uploadProgress[file.name] > 0 && uploadProgress[file.name] < 100 ? (
                                <div className="w-16">
                                  <Progress value={uploadProgress[file.name]} className="h-1" />
                                </div>
                              ) : uploadProgress[file.name] === 100 ? (
                                <div className="text-green-500 text-xs">完成</div>
                              ) : (
                                <X
                                  className="h-4 w-4 text-gray-500 hover:text-red-500 cursor-pointer"
                                  onClick={() => removeKnowledgeFile(file.name)}
                                />
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>

                  <CardFooter className="p-3 pt-0">
                    <Button
                      className="w-full bg-blue-500 hover:bg-blue-600 text-white flex items-center justify-center gap-2"
                      onClick={uploadKnowledgeFiles}
                      disabled={knowledgeFiles.length === 0 || isUploading}
                    >
                      {isUploading ? (
                        <div className="flex items-center">
                          <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                          处理中...
                        </div>
                      ) : (
                        <>
                          <ArrowRight className="h-4 w-4" />
                          <span>上传到知识库</span>
                        </>
                      )}
                    </Button>
                  </CardFooter>
                </>
              )}
            </Card>
          </div>
        </ScrollArea>

        {/* Message Input Area */}
        <div className="p-4 border-t bg-white">
          {/* 选择文件提示 */}
          {selectedFiles.length > 0 && (
            <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center justify-between text-sm text-blue-700 mb-2">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  <span>已选择 {selectedFiles.length} 个文件，AI将基于这些文件回答您的问题</span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearFileSelection}
                  className="h-6 px-2 text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-100"
                >
                  清空选择
                </Button>
              </div>
              <div className="flex flex-wrap gap-1">
                {selectedFiles.map((fileId) => {
                  // 查找文件信息
                  let file = null
                  for (const courseId in courseFiles) {
                    file = courseFiles[courseId].find(f => f.id === fileId)
                    if (file) break
                  }
                  return file ? (
                    <span key={fileId} className="inline-flex items-center gap-1 px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                      {getFileIcon(file.name)}
                      {file.name}
                      <button
                        type="button"
                        onClick={() => {
                          // 找到文件对应的课程ID
                          let fileCourseId = null
                          for (const courseId in courseFiles) {
                            const foundFile = courseFiles[courseId].find(f => f.id === fileId)
                            if (foundFile) {
                              fileCourseId = courseId
                              break
                            }
                          }
                          if (fileCourseId) {
                            handleFileSelection(fileId, fileCourseId)
                          }
                        }}
                        className="ml-1 hover:bg-blue-200 rounded"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </span>
                  ) : null
                })}
              </div>
            </div>
          )}

          <form onSubmit={handleFormSubmit} className="relative">
            <Textarea
              value={input}
              onChange={handleInputChange}
              placeholder={
                selectedFiles.length > 0 
                  ? `基于选择的文件向AI提问...`
                  : `向AI学习助手提问...`
              }
              className={`min-h-[80px] resize-none ${selectedFiles.length > 0 ? 'pr-40' : 'pr-24'}`}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  const form = e.currentTarget.form
                  if (form) form.requestSubmit()
                }
              }}
              disabled={isLoading}
            />

            <div className="absolute bottom-3 right-3 flex items-center gap-2">
              {/* 基于文件回复按钮 */}
              {selectedFiles.length > 0 && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    if (input.trim()) {
                      const form = document.querySelector('form') as HTMLFormElement
                      if (form) form.requestSubmit()
                    }
                  }}
                  disabled={isLoading || !input.trim()}
                  className="h-8 px-3 text-xs bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100"
                >
                  基于文件回复
                </Button>
              )}
              
              <div
                className={`relative p-2 rounded-md cursor-pointer ${isDragging ? "bg-blue-100" : "hover:bg-gray-100"} ${isLoading ? "opacity-50 cursor-not-allowed" : ""}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => !isLoading && fileInputRef.current?.click()}
              >
                <Paperclip className="h-5 w-5 text-gray-500" />
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileChange}
                  className="hidden"
                  multiple
                  disabled={isLoading}
                />
                {files && files.length > 0 && (
                  <div className="absolute -top-1 -right-1 bg-blue-500 text-white rounded-full w-4 h-4 flex items-center justify-center text-xs">
                    {files.length}
                  </div>
                )}
              </div>

              <Button type="submit" size="icon" disabled={isLoading || (!input && (!files || files.length === 0))}>
                {isLoading ? (
                  <div className="h-5 w-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                ) : (
                  <Send className="h-5 w-5" />
                )}
              </Button>
            </div>

            {/* File Upload Area */}
            {isDragging && !isLoading && (
              <div className="absolute inset-0 bg-blue-50 bg-opacity-90 border-2 border-dashed border-blue-300 rounded-md flex items-center justify-center">
                <div className="text-center">
                  <Upload className="h-10 w-10 text-blue-500 mx-auto mb-2" />
                  <p className="text-blue-700">拖放文件到这里上传</p>
                </div>
              </div>
            )}

            {/* File Preview */}
            {files && files.length > 0 && (
              <div className="mt-2 p-2 bg-gray-50 rounded-md">
                <div className="text-sm font-medium mb-1">已选择的文件：</div>
                <div className="space-y-1">
                  {Array.from(files).map((file, index) => (
                    <div key={index} className="flex items-center gap-2 text-sm">
                      <FileText className="h-4 w-4" />
                      <span>{file.name}</span>
                      <span className="text-gray-500 text-xs">({(file.size / 1024).toFixed(1)} KB)</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </form>
        </div>
      </div>

      {/* 新建课程对话框 */}
      <Dialog open={isAddCourseOpen} onOpenChange={setIsAddCourseOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>新建课程</DialogTitle>
            <DialogDescription>创建一个新的课程来管理您的学习资料和进行智能对话。</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="course-name" className="text-right">
                课程名称
              </Label>
              <Input
                id="course-name"
                value={newCourseName}
                onChange={(e) => setNewCourseName(e.target.value)}
                className="col-span-3"
                placeholder="例如：高等数学、机器学习"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddCourseOpen(false)}>
              取消
            </Button>
            <Button onClick={handleAddCourse} disabled={!newCourseName.trim()}>
              创建课程
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 新对话对话框 */}
      <Dialog open={isNewChatOpen} onOpenChange={setIsNewChatOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>开始新对话</DialogTitle>
            <DialogDescription>输入您的问题，开始一个新的对话。</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="chat-message" className="text-right">
                问题
              </Label>
              <Textarea
                id="chat-message"
                value={newChatMessage}
                onChange={(e) => setNewChatMessage(e.target.value)}
                className="col-span-3 min-h-[100px]"
                placeholder={`向AI学习助手提问...`}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsNewChatOpen(false)}>
              取消
            </Button>
            <Button
              onClick={handleStartNewChat}
              disabled={!newChatMessage.trim() || isLoading}
              className="relative bg-blue-600 hover:bg-blue-700 text-white"
            >
              {isLoading ? (
                <div className="flex items-center">
                  <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  处理中...
                </div>
              ) : (
                "开始对话"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* URL导入对话框 */}
      <Dialog open={isUrlImportOpen} onOpenChange={setIsUrlImportOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>通过链接导入文件</DialogTitle>
            <DialogDescription>
              输入文件的URL地址，系统将自动下载并添加到当前课程的知识库中。
              <br />
              支持PDF、Word、PPT、图片、音频、视频等多种格式。
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="import-url" className="text-right">
                文件URL
              </Label>
              <Input
                id="import-url"
                value={importUrl}
                onChange={(e) => setImportUrl(e.target.value)}
                className="col-span-3"
                placeholder="https://example.com/file.pdf"
                disabled={isImporting}
              />
            </div>
            {currentCourseId && (
              <div className="grid grid-cols-4 items-center gap-4">
                <Label className="text-right text-sm text-gray-600">
                  目标课程
                </Label>
                <div className="col-span-3 text-sm text-gray-800">
                  {courses.find(c => c.id === currentCourseId)?.name || '未选择课程'}
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => {
                setIsUrlImportOpen(false)
                setImportUrl('')
              }}
              disabled={isImporting}
            >
              取消
            </Button>
            <Button 
              onClick={handleUrlImport} 
              disabled={!importUrl.trim() || !currentCourseId || isImporting}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              {isImporting ? (
                <div className="flex items-center">
                  <div className="animate-spin mr-2 h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                  导入中...
                </div>
              ) : (
                <>
                  <Globe className="h-4 w-4 mr-2" />
                  导入文件
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

