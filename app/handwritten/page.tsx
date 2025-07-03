'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, FileText, Download, Share2, Palette } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { API_CONFIG, getApiUrl } from '../config';

interface Course {
  id: string;
  name: string;
  created_at: number;
}

export default function HandwrittenNotePage() {
  const router = useRouter();
  const [courses, setCourses] = useState<Course[]>([]);
  const [selectedCourse, setSelectedCourse] = useState<string>('');
  const [noteContent, setNoteContent] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImageUrl, setGeneratedImageUrl] = useState<string>('');
  const [error, setError] = useState<string>('');

  // 获取课程列表
  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    try {
      const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.COURSES));
      const data = await response.json();
      setCourses(data.courses || []);
    } catch (error) {
      console.error('获取课程列表失败:', error);
    }
  };

  const generateHandwrittenNote = async () => {
    if (!noteContent.trim()) {
      setError('请输入笔记内容');
      return;
    }

    if (!selectedCourse) {
      setError('请选择课程');
      return;
    }

    setIsGenerating(true);
    setError('');

    try {
      const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.GENERATE_HANDWRITTEN), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: noteContent,
          courseId: selectedCourse,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setGeneratedImageUrl(`${API_CONFIG.BASE_URL}${data.imageUrl}`);
      } else {
        setError(data.error || '生成手写笔记失败');
      }
    } catch (error) {
      setError('网络错误，请重试');
      console.error('生成手写笔记失败:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadImage = () => {
    if (generatedImageUrl) {
      const link = document.createElement('a');
      link.href = generatedImageUrl;
      link.download = `handwritten_note_${Date.now()}.png`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const shareImage = async () => {
    if (navigator.share && generatedImageUrl) {
      try {
        await navigator.share({
          title: '手写笔记',
          text: '我生成了一份手写笔记',
          url: generatedImageUrl,
        });
      } catch (error) {
        console.log('分享失败:', error);
      }
    } else {
      // 复制链接到剪贴板
      navigator.clipboard.writeText(generatedImageUrl);
      alert('图片链接已复制到剪贴板');
    }
  };

  const clearAll = () => {
    setNoteContent('');
    setGeneratedImageUrl('');
    setError('');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* 头部导航 */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.back()}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>返回</span>
              </button>
              <div className="flex items-center space-x-2">
                <Palette className="w-6 h-6 text-indigo-600" />
                <h1 className="text-xl font-semibold text-gray-900">手写笔记生成器</h1>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* 左侧：输入区域 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center space-x-2 mb-6">
              <FileText className="w-5 h-5 text-indigo-600" />
              <h2 className="text-lg font-semibold text-gray-900">创建手写笔记</h2>
            </div>

            {/* 课程选择 */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                选择课程
              </label>
              <select
                value={selectedCourse}
                onChange={(e) => setSelectedCourse(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              >
                <option value="">请选择课程</option>
                {courses.map((course) => (
                  <option key={course.id} value={course.id}>
                    {course.name}
                  </option>
                ))}
              </select>
            </div>

            {/* 笔记内容输入 */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                笔记内容
              </label>
              <textarea
                value={noteContent}
                onChange={(e) => setNoteContent(e.target.value)}
                placeholder="输入你的笔记内容...&#10;&#10;提示：&#10;- 使用 # 开头表示标题&#10;- 包含 ★ 或 '重点'、'关键' 等词汇会被高亮显示&#10;- 支持多行文本，会自动换行处理"
                className="w-full h-64 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
              />
              <div className="mt-2 text-sm text-gray-500">
                {noteContent.length} 字符
              </div>
            </div>

            {/* 错误提示 */}
            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            {/* 操作按钮 */}
            <div className="flex space-x-3">
              <button
                onClick={generateHandwrittenNote}
                disabled={isGenerating || !noteContent.trim() || !selectedCourse}
                className="flex-1 bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center space-x-2"
              >
                {isGenerating ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>生成中...</span>
                  </>
                ) : (
                  <>
                    <Palette className="w-4 h-4" />
                    <span>生成手写笔记</span>
                  </>
                )}
              </button>
              
              <button
                onClick={clearAll}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                清空
              </button>
            </div>

            {/* 使用说明 */}
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h3 className="text-sm font-medium text-blue-900 mb-2">使用说明：</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• 选择对应的课程，输入笔记内容</li>
                <li>• 使用 # 开头的行会被识别为标题</li>
                <li>• 包含 ★ 或重点关键词的内容会被高亮显示</li>
                <li>• 生成的笔记具有手写风格，包含笔记本线条和装饰</li>
                <li>• 支持下载和分享生成的笔记图片</li>
              </ul>
            </div>
          </div>

          {/* 右侧：预览区域 */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">笔记预览</h2>
            
            {generatedImageUrl ? (
              <div className="space-y-4">
                <div className="border-2 border-gray-200 rounded-lg overflow-hidden">
                  <img
                    src={generatedImageUrl}
                    alt="生成的手写笔记"
                    className="w-full h-auto"
                  />
                </div>
                
                {/* 操作按钮 */}
                <div className="flex space-x-3">
                  <button
                    onClick={downloadImage}
                    className="flex-1 bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center space-x-2"
                  >
                    <Download className="w-4 h-4" />
                    <span>下载图片</span>
                  </button>
                  
                  <button
                    onClick={shareImage}
                    className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2"
                  >
                    <Share2 className="w-4 h-4" />
                    <span>分享</span>
                  </button>
                </div>
              </div>
            ) : (
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
                <Palette className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-500 mb-2">手写笔记预览</p>
                <p className="text-sm text-gray-400">
                  输入内容并点击生成按钮，手写笔记将在这里显示
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
} 