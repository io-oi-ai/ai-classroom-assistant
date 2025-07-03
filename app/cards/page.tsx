"use client"

import { useState, useEffect } from "react"
import { Button } from "../components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card"
import { ScrollArea } from "../components/ui/scroll-area"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "../components/ui/dialog"
import { Textarea } from "../components/ui/textarea"
import { Input } from "../components/ui/input"
import { Label } from "../components/ui/label"
import { Checkbox } from "../components/ui/checkbox"
import { ArrowLeft, BookOpen, ImageIcon, Calendar, FileText, Edit3, Trash2, Save, X, Download, CheckSquare, Square, Plus } from "lucide-react"
import { useRouter } from "next/navigation"
import { API_CONFIG, getApiUrl, getCourseUrl, getCardUrl } from '../config'

interface NoteCard {
  id: string
  title: string
  content: string
  image: string | null
  course_id: string
  file_ids: string[]
  created_at: number
  image_source?: "extracted" | "generated" | "none"
}

interface Course {
  id: string
  name: string
  createTime: number
}

export default function NotesCardsPage() {
  const router = useRouter()
  const [cards, setCards] = useState<NoteCard[]>([])
  const [courses, setCourses] = useState<Course[]>([])
  const [selectedCourseId, setSelectedCourseId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  
  // 多选相关状态
  const [selectedCards, setSelectedCards] = useState<Set<string>>(new Set())
  const [isSelectMode, setIsSelectMode] = useState(false)
  
  // 编辑相关状态
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false)
  const [editingCard, setEditingCard] = useState<NoteCard | null>(null)
  const [editTitle, setEditTitle] = useState("")
  const [editContent, setEditContent] = useState("")
  const [isUpdating, setIsUpdating] = useState(false)
  
  // 删除确认相关状态
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false)
  const [cardToDelete, setCardToDelete] = useState<NoteCard | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)
  
  // 批量删除确认相关状态
  const [isBatchDeleteDialogOpen, setIsBatchDeleteDialogOpen] = useState(false)
  const [isBatchDeleting, setIsBatchDeleting] = useState(false)
  
  // 展开全文相关状态
  const [expandedCards, setExpandedCards] = useState<Set<string>>(new Set())
  
  // 图片预览相关状态
  const [isImagePreviewOpen, setIsImagePreviewOpen] = useState(false)
  const [previewImageUrl, setPreviewImageUrl] = useState<string>("")
  const [previewImageTitle, setPreviewImageTitle] = useState<string>("")
  
  // 生成单张卡片相关状态
  const [isGenerating, setIsGenerating] = useState(false)

  // 获取课程列表
  const fetchCourses = async () => {
    try {
      const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.COURSES))
      const data = await response.json()
      setCourses(data.courses || [])
      if (data.courses && data.courses.length > 0) {
        setSelectedCourseId(data.courses[0].id)
      }
    } catch (error) {
      console.error('获取课程列表失败:', error)
    }
  }

  // 获取笔记卡片
  const fetchCards = async (courseId?: string) => {
    try {
      setLoading(true)
      const url = courseId 
        ? getCourseUrl(courseId, '/cards')
        : getApiUrl(API_CONFIG.ENDPOINTS.CARDS)
      
      const response = await fetch(url)
      const data = await response.json()
      setCards(data.cards || [])
    } catch (error) {
      console.error('获取笔记卡片失败:', error)
      setCards([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCourses()
  }, [])

  useEffect(() => {
    if (selectedCourseId) {
      fetchCards(selectedCourseId)
    }
  }, [selectedCourseId])

  useEffect(() => {
    // 当退出选择模式时，清空选中的卡片
    if (!isSelectMode) {
      setSelectedCards(new Set())
    }
  }, [isSelectMode])

  const formatDate = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString('zh-CN')
  }

  const getCourseName = (courseId: string) => {
    const course = courses.find(c => c.id === courseId)
    return course?.name || '未知课程'
  }

  // 多选功能
  const toggleSelectMode = () => {
    setIsSelectMode(!isSelectMode)
  }

  const toggleCardSelection = (cardId: string) => {
    const newSelectedCards = new Set(selectedCards)
    if (newSelectedCards.has(cardId)) {
      newSelectedCards.delete(cardId)
    } else {
      newSelectedCards.add(cardId)
    }
    setSelectedCards(newSelectedCards)
  }

  const selectAllCards = () => {
    if (selectedCards.size === cards.length) {
      setSelectedCards(new Set())
    } else {
      setSelectedCards(new Set(cards.map(card => card.id)))
    }
  }

  // 开始编辑卡片
  const startEditCard = (card: NoteCard) => {
    setEditingCard(card)
    setEditTitle(card.title)
    setEditContent(card.content)
    setIsEditDialogOpen(true)
  }

  // 保存编辑
  const saveEdit = async () => {
    if (!editingCard || !editTitle.trim() || !editContent.trim()) return

    setIsUpdating(true)
    try {
      const response = await fetch(getCardUrl(editingCard.id, '/edit'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: editTitle.trim(),
          content: editContent.trim(),
        }),
      })

      const result = await response.json()
      
      if (result.success) {
        // 更新本地状态
        setCards(prev => prev.map(card => 
          card.id === editingCard.id 
            ? { ...card, title: editTitle.trim(), content: editContent.trim() }
            : card
        ))
        setIsEditDialogOpen(false)
        setEditingCard(null)
        setEditTitle("")
        setEditContent("")
      } else {
        alert(result.error || '编辑失败')
      }
    } catch (error) {
      console.error('编辑卡片失败:', error)
      alert('编辑失败，请稍后重试')
    } finally {
      setIsUpdating(false)
    }
  }

  // 取消编辑
  const cancelEdit = () => {
    setIsEditDialogOpen(false)
    setEditingCard(null)
    setEditTitle("")
    setEditContent("")
  }

  // 开始删除单个卡片
  const startDeleteCard = (card: NoteCard) => {
    setCardToDelete(card)
    setIsDeleteDialogOpen(true)
  }

  // 确认删除单个卡片
  const confirmDelete = async () => {
    if (!cardToDelete) return

    setIsDeleting(true)
    try {
      const response = await fetch(getCardUrl(cardToDelete.id), {
        method: 'DELETE',
      })

      const result = await response.json()
      
      if (result.success) {
        // 从本地状态中移除卡片
        setCards(prev => prev.filter(card => card.id !== cardToDelete.id))
        setIsDeleteDialogOpen(false)
        setCardToDelete(null)
      } else {
        alert(result.error || '删除失败')
      }
    } catch (error) {
      console.error('删除卡片失败:', error)
      alert('删除失败，请稍后重试')
    } finally {
      setIsDeleting(false)
    }
  }

  // 取消删除
  const cancelDelete = () => {
    setIsDeleteDialogOpen(false)
    setCardToDelete(null)
  }

  // 开始批量删除
  const startBatchDelete = () => {
    if (selectedCards.size === 0) {
      alert('请先选择要删除的卡片')
      return
    }
    setIsBatchDeleteDialogOpen(true)
  }

  // 确认批量删除
  const confirmBatchDelete = async () => {
    if (selectedCards.size === 0) return

    setIsBatchDeleting(true)
    try {
      let successCount = 0
      let failCount = 0

      for (const cardId of selectedCards) {
        try {
          const response = await fetch(getCardUrl(cardId), {
            method: 'DELETE',
          })
          const result = await response.json()
          if (result.success) {
            successCount++
          } else {
            failCount++
          }
        } catch (error) {
          failCount++
        }
      }

      // 更新本地状态
      setCards(prev => prev.filter(card => !selectedCards.has(card.id)))
      setSelectedCards(new Set())
      setIsBatchDeleteDialogOpen(false)
      setIsSelectMode(false)
      
      alert(`批量删除完成！成功：${successCount} 张，失败：${failCount} 张`)
    } catch (error) {
      console.error('批量删除失败:', error)
      alert('批量删除失败，请稍后重试')
    } finally {
      setIsBatchDeleting(false)
    }
  }

  // 取消批量删除
  const cancelBatchDelete = () => {
    setIsBatchDeleteDialogOpen(false)
  }

  const toggleCardExpansion = (cardId: string) => {
    setExpandedCards(prev => {
      const newSet = new Set(prev)
      if (newSet.has(cardId)) {
        newSet.delete(cardId)
      } else {
        newSet.add(cardId)
      }
      return newSet
    })
  }

  const previewImage = (imageUrl: string, title: string) => {
    setPreviewImageUrl(`${API_CONFIG.BASE_URL}${imageUrl}`)
    setPreviewImageTitle(title)
    setIsImagePreviewOpen(true)
  }

  const closeImagePreview = () => {
    setIsImagePreviewOpen(false)
    setPreviewImageUrl("")
    setPreviewImageTitle("")
  }

  // 下载单个卡片图片
  const downloadCardImage = async (card: NoteCard) => {
    if (!card.image) {
      alert('该卡片没有图片')
      return
    }

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}${card.image}`)
      const blob = await response.blob()
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      
      // 生成文件名
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
      const filename = `${card.title.replace(/[^\w\u4e00-\u9fa5]/g, '_')}_${timestamp}.png`
      link.download = filename
      
      // 触发下载
      document.body.appendChild(link)
      link.click()
      
      // 清理
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
    } catch (error) {
      console.error('下载图片失败:', error)
      alert('下载失败，请稍后重试')
    }
  }

  // 批量下载选中卡片的图片
  const batchDownloadImages = async () => {
    if (selectedCards.size === 0) {
      alert('请先选择要下载的卡片')
      return
    }

    const selectedCardObjects = cards.filter(card => selectedCards.has(card.id))
    const cardsWithImages = selectedCardObjects.filter(card => card.image)

    if (cardsWithImages.length === 0) {
      alert('选中的卡片中没有图片')
      return
    }

    if (cardsWithImages.length > 10) {
      if (!confirm(`您将下载 ${cardsWithImages.length} 张图片，这可能需要一些时间。是否继续？`)) {
        return
      }
    }

    let successCount = 0
    let failCount = 0

    for (const card of cardsWithImages) {
      try {
        await new Promise(resolve => setTimeout(resolve, 200)) // 延迟200ms避免并发过多
        await downloadCardImage(card)
        successCount++
      } catch (error) {
        console.error(`下载卡片 ${card.title} 的图片失败:`, error)
        failCount++
      }
    }

    alert(`批量下载完成！成功：${successCount} 张，失败：${failCount} 张`)
  }

  // 下载所有图片
  const downloadAllImages = async () => {
    const cardsWithImages = cards.filter(card => card.image)

    if (cardsWithImages.length === 0) {
      alert('当前没有可下载的图片')
      return
    }

    if (cardsWithImages.length > 10) {
      if (!confirm(`您将下载 ${cardsWithImages.length} 张图片，这可能需要一些时间。是否继续？`)) {
        return
      }
    }

    let successCount = 0
    let failCount = 0

    for (const card of cardsWithImages) {
      try {
        await new Promise(resolve => setTimeout(resolve, 200)) // 延迟200ms避免并发过多
        await downloadCardImage(card)
        successCount++
      } catch (error) {
        console.error(`下载卡片 ${card.title} 的图片失败:`, error)
        failCount++
      }
    }

    alert(`批量下载完成！成功：${successCount} 张，失败：${failCount} 张`)
  }

  // 生成单张卡片
  const generateSingleCard = async () => {
    if (!selectedCourseId) {
      alert('请先选择一个课程')
      return
    }

    // 获取课程文件
    try {
      const filesResponse = await fetch(getCourseUrl(selectedCourseId, '/files'))
      const filesData = await filesResponse.json()
      
      if (!filesData.files || filesData.files.length === 0) {
        alert('该课程暂无文件，无法生成卡片')
        return
      }

      setIsGenerating(true)
      
      const response = await fetch(getCourseUrl(selectedCourseId, '/generate-single-card'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          fileIds: filesData.files.map((f: any) => f.id),
          cardIndex: 0  // 总是生成第一张（唯一的）卡片
        }),
      })

      const result = await response.json()
      
      if (result.success) {
        // 重新获取卡片列表以显示新生成的卡片
        await fetchCards(selectedCourseId)
        alert('卡片生成成功！')
      } else {
        alert(result.error || '生成失败')
      }
    } catch (error) {
      console.error('生成卡片失败:', error)
      alert('生成失败，请稍后重试')
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 头部导航 */}
      <div className="bg-white border-b px-6 py-4">
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => router.push('/')}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            返回主页
          </Button>
          <div className="flex items-center gap-2">
            <BookOpen className="h-6 w-6 text-blue-500" />
            <h1 className="text-2xl font-bold">智能笔记卡片</h1>
          </div>
        </div>
      </div>

      {/* 主要内容区域 - 统一滚动 */}
      <div className="flex max-h-[calc(100vh-80px)] overflow-hidden">
        {/* 左侧课程选择 */}
        <div className="w-80 bg-white border-r flex-shrink-0">
          <div className="p-4 border-b bg-white sticky top-0 z-10">
            <h2 className="font-semibold text-lg">选择课程</h2>
          </div>
          <div className="p-2 overflow-y-auto max-h-[calc(100vh-140px)]">
            {courses.map((course) => (
              <Button
                key={course.id}
                variant={selectedCourseId === course.id ? "default" : "ghost"}
                className="w-full justify-start mb-2"
                onClick={() => setSelectedCourseId(course.id)}
              >
                <BookOpen className="h-4 w-4 mr-2" />
                {course.name}
              </Button>
            ))}
            {courses.length === 0 && (
              <div className="text-center text-gray-500 py-8">
                暂无课程
              </div>
            )}
          </div>
        </div>

        {/* 右侧卡片展示 */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
                <p className="text-gray-500">加载中...</p>
              </div>
            </div>
          ) : cards.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <ImageIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-gray-600 mb-2">暂无笔记卡片</h3>
                <p className="text-gray-500 mb-4">
                  {selectedCourseId ? '该课程还没有生成笔记卡片' : '请先选择一个课程'}
                </p>
                <Button onClick={() => router.push('/')}>
                  去生成笔记卡片
                </Button>
              </div>
            </div>
          ) : (
            <div>
              <div className="mb-6">
                <div className="flex justify-between items-center">
                  <div>
                    <h2 className="text-xl font-semibold mb-2">
                      {selectedCourseId ? getCourseName(selectedCourseId) : '所有课程'} 的笔记卡片
                    </h2>
                    <p className="text-gray-600">
                      共 {cards.length} 张卡片
                      {isSelectMode && selectedCards.size > 0 && (
                        <span className="ml-2 text-blue-600">
                          - 已选择 {selectedCards.size} 张
                        </span>
                      )}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    {!isSelectMode ? (
                      <>
                        <Button
                          variant="default"
                          size="sm"
                          onClick={generateSingleCard}
                          disabled={isGenerating || !selectedCourseId}
                          className="flex items-center gap-2"
                        >
                          <Plus className="h-4 w-4" />
                          {isGenerating ? '生成中...' : '生成知识卡片'}
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={toggleSelectMode}
                          className="flex items-center gap-2"
                        >
                          <CheckSquare className="h-4 w-4" />
                          多选管理
                        </Button>
                        {cards.length > 0 && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={downloadAllImages}
                            className="flex items-center gap-2"
                          >
                            <Download className="h-4 w-4" />
                            下载全部图片
                          </Button>
                        )}
                      </>
                    ) : (
                      <>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={selectAllCards}
                          className="flex items-center gap-2"
                        >
                          {selectedCards.size === cards.length ? (
                            <Square className="h-4 w-4" />
                          ) : (
                            <CheckSquare className="h-4 w-4" />
                          )}
                          {selectedCards.size === cards.length ? '取消全选' : '全选'}
                        </Button>
                        {selectedCards.size > 0 && (
                          <>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={batchDownloadImages}
                              className="flex items-center gap-2"
                            >
                              <Download className="h-4 w-4" />
                              下载选中 ({selectedCards.size})
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={startBatchDelete}
                              className="flex items-center gap-2 text-red-600 hover:text-red-700"
                            >
                              <Trash2 className="h-4 w-4" />
                              删除选中 ({selectedCards.size})
                            </Button>
                          </>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={toggleSelectMode}
                          className="flex items-center gap-2"
                        >
                          <X className="h-4 w-4" />
                          退出选择
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {cards.map((card) => (
                  <Card 
                    key={card.id} 
                    className={`overflow-hidden hover:shadow-lg transition-shadow group relative ${
                      isSelectMode 
                        ? 'cursor-default' 
                        : 'cursor-default'
                    }`}
                    onClick={isSelectMode ? (e) => {
                      // 在多选模式下，只有点击复选框才能选中，阻止卡片点击事件
                      e.preventDefault()
                      e.stopPropagation()
                    } : undefined}
                  >
                    {/* 多选模式下的选择框 */}
                    {isSelectMode && (
                      <div className="absolute top-3 left-3 z-10">
                        <Checkbox
                          checked={selectedCards.has(card.id)}
                          onCheckedChange={() => toggleCardSelection(card.id)}
                          className="bg-white shadow-md border-2"
                          onClick={(e) => {
                            // 防止事件冒泡到卡片
                            e.stopPropagation()
                          }}
                        />
                      </div>
                    )}
                    
                    <CardHeader className={`pb-3 ${isSelectMode ? 'pl-12' : ''}`}>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-lg">{card.title}</CardTitle>
                          <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                            <Calendar className="h-4 w-4" />
                            {formatDate(card.created_at)}
                          </div>
                        </div>
                        {!isSelectMode && (
                          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation()
                                downloadCardImage(card)
                              }}
                              className="h-8 w-8 p-0 text-blue-500 hover:text-blue-700"
                              title="下载图片"
                            >
                              <Download className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation()
                                startEditCard(card)
                              }}
                              className="h-8 w-8 p-0"
                              title="编辑卡片"
                            >
                              <Edit3 className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation()
                                startDeleteCard(card)
                              }}
                              className="h-8 w-8 p-0 text-red-500 hover:text-red-700"
                              title="删除卡片"
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        )}
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {/* 图片展示 */}
                      {card.image && (
                        <div className="relative">
                          <img
                            src={`${API_CONFIG.BASE_URL}${card.image}`}
                            alt={card.title}
                            className="w-full h-40 object-cover rounded-lg border cursor-pointer hover:opacity-90 transition-opacity"
                            onClick={(e) => {
                              e.stopPropagation() // 防止触发卡片的点击事件
                              if (!isSelectMode) {
                                previewImage(card.image!, card.title)
                              }
                            }}
                            onError={(e) => {
                              const target = e.target as HTMLImageElement
                              target.style.display = 'none'
                            }}
                          />
                          {/* 预览提示 */}
                          {!isSelectMode && (
                            <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-0 hover:bg-opacity-20 transition-all rounded-lg">
                              <span className="text-white text-sm font-medium opacity-0 hover:opacity-100 transition-opacity">
                                点击预览
                              </span>
                            </div>
                          )}
                          {/* 图片来源标识 */}
                          {card.image_source && (
                            <div className="absolute top-2 right-2">
                              {card.image_source === "extracted" ? (
                                <span className="bg-blue-500 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
                                  📸 原始截图
                                </span>
                              ) : card.image_source === "generated" ? (
                                <span className="bg-purple-500 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
                                  🎨 AI生成
                                </span>
                              ) : null}
                            </div>
                          )}
                        </div>
                      )}
                      
                      {/* 内容展示 - 简化概括 */}
                      <div className="space-y-2">
                        <div className="text-sm text-gray-600 leading-relaxed">
                          {card.content.length > 80 && !expandedCards.has(card.id)
                            ? `${card.content.substring(0, 80)}...` 
                            : card.content
                          }
                        </div>
                        
                        {card.content.length > 80 && (
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="text-blue-600 p-0 h-auto hover:text-blue-800 text-xs"
                            onClick={(e) => {
                              e.stopPropagation() // 防止触发卡片选择
                              toggleCardExpansion(card.id)
                            }}
                          >
                            {expandedCards.has(card.id) ? '收起' : '查看详情'}
                          </Button>
                        )}
                      </div>

                      {/* 文件信息 */}
                      <div className="flex items-center gap-2 text-xs text-gray-500 pt-2 border-t">
                        <FileText className="h-3 w-3" />
                        基于 {card.file_ids.length} 个文件生成
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 编辑对话框 */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>编辑笔记卡片</DialogTitle>
            <DialogDescription>
              修改卡片的标题和内容
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label htmlFor="title">标题</Label>
              <Input
                id="title"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                placeholder="请输入卡片标题"
              />
            </div>
            <div>
              <Label htmlFor="content">内容</Label>
              <Textarea
                id="content"
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                placeholder="请输入卡片内容"
                rows={10}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={cancelEdit}>
              取消
            </Button>
            <Button onClick={saveEdit} disabled={isUpdating}>
              {isUpdating ? '保存中...' : '保存'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 删除确认对话框 */}
      <Dialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认删除</DialogTitle>
            <DialogDescription>
              您确定要删除卡片 "{cardToDelete?.title}" 吗？此操作无法撤销。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={cancelDelete}>
              取消
            </Button>
            <Button variant="destructive" onClick={confirmDelete} disabled={isDeleting}>
              {isDeleting ? '删除中...' : '确认删除'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 批量删除确认对话框 */}
      <Dialog open={isBatchDeleteDialogOpen} onOpenChange={setIsBatchDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>确认批量删除</DialogTitle>
            <DialogDescription>
              您确定要删除选中的 {selectedCards.size} 张卡片吗？此操作无法撤销。
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={cancelBatchDelete}>
              取消
            </Button>
            <Button variant="destructive" onClick={confirmBatchDelete} disabled={isBatchDeleting}>
              {isBatchDeleting ? '删除中...' : '确认删除'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 图片预览对话框 */}
      <Dialog open={isImagePreviewOpen} onOpenChange={setIsImagePreviewOpen}>
        <DialogContent className="max-w-5xl max-h-[95vh] overflow-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ImageIcon className="h-5 w-5" />
              {previewImageTitle}
            </DialogTitle>
            <DialogDescription>
              点击图片可以放大查看，满意后可下载保存
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-center bg-gray-50 rounded-lg p-4">
            <img
              src={previewImageUrl}
              alt={previewImageTitle}
              className="max-w-full max-h-[75vh] object-contain rounded shadow-lg cursor-zoom-in"
              onClick={() => {
                // 点击图片在新窗口中打开原尺寸图片
                window.open(previewImageUrl, '_blank')
              }}
            />
          </div>
          <DialogFooter className="flex justify-between">
            <div className="flex items-center text-sm text-gray-500">
              💡 提示：点击图片可在新窗口查看原尺寸
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                onClick={closeImagePreview}
                className="flex items-center gap-2"
              >
                关闭
              </Button>
              <Button 
                onClick={() => {
                  // 从当前预览的图片中找到对应的卡片并下载
                  const currentCard = cards.find(card => 
                    card.image && `${API_CONFIG.BASE_URL}${card.image}` === previewImageUrl
                  )
                  if (currentCard) {
                    downloadCardImage(currentCard)
                  }
                }}
                className="flex items-center gap-2"
              >
                <Download className="h-4 w-4" />
                下载图片
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
} 