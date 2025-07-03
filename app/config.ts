// API配置 - 支持开发和生产环境
const isClient = typeof window !== 'undefined'
const isDevelopment = process.env.NODE_ENV === 'development'

// 动态检测环境和API地址
const getBaseUrl = () => {
  if (!isClient) {
    // 服务端渲染时使用默认值
    return 'http://localhost:8001'
  }
  
  if (isDevelopment) {
    // 开发环境使用localhost
    return 'http://localhost:8001'
  } else {
    // 生产环境使用当前域名的8001端口，或者通过代理
    const hostname = window.location.hostname
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8001'
    } else {
      // 服务器环境，使用当前服务器的8001端口
      return `http://${hostname}:8001`
    }
  }
}

export const API_CONFIG = {
  BASE_URL: getBaseUrl(),
  ENDPOINTS: {
    COURSES: '/api/courses',
    UPLOAD: '/api/upload',
    CHAT: '/api/chat',
    GENERATE_HANDWRITTEN: '/api/generate-handwritten-note',
    CARDS: '/api/courses/all/cards'
  }
}

// 工具函数
export const getApiUrl = (endpoint: string) => `${API_CONFIG.BASE_URL}${endpoint}`

export const getCourseUrl = (courseId: string, action: string) => 
  `${API_CONFIG.BASE_URL}/api/courses/${courseId}${action}`

export const getCardUrl = (cardId: string, action: string = '') => 
  `${API_CONFIG.BASE_URL}/api/cards/${cardId}${action}` 