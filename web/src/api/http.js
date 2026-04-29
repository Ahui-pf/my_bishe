import axios from 'axios'
import router from '@/router'
import { clearStoredToken, getStoredToken, hasValidToken } from '@/utils/auth'

function redirectToLogin() {
  if (router.currentRoute.value.path !== '/login') {
    router.push('/login')
  }
}

function normalizeError(error) {
  const status = error.response?.status
  const data = error.response?.data

  if (data && typeof data === 'object') {
    return {
      status,
      ...data,
      data,
      message: data.message || data.msg || data.error || error.message,
      detail: data.detail || data.error || data.msg || data.message,
    }
  }

  return {
    status,
    data,
    message: typeof data === 'string' ? data : error.message,
    detail: typeof data === 'string' ? data : undefined,
  }
}

// 认证服务实例
export const authHttp = axios.create({ 
  baseURL: 'http://127.0.0.1:5000',  // Flask认证服务端口
  timeout: 5000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// AI模型服务实例
export const modelHttp = axios.create({ 
  baseURL: 'http://127.0.0.1:8000',  // FastAPI模型服务端口
  timeout: 600000  // 10分钟超时，适合处理完整视频
})

// 认证服务拦截器
authHttp.interceptors.request.use(
  config => {
    const token = getStoredToken()
    if (token) {
      if (hasValidToken()) {
        config.headers.Authorization = `Bearer ${token}`
      } else {
        clearStoredToken()
        redirectToLogin()
      }
    }
    return config
  },
  error => Promise.reject(error)
)

authHttp.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response && error.response.status === 401) {
      clearStoredToken()
      redirectToLogin()
    }
    return Promise.reject(normalizeError(error))
  }
)

// AI模型服务拦截器
modelHttp.interceptors.request.use(
  config => {
    const token = getStoredToken()
    if (token) {
      if (hasValidToken()) {
        config.headers.Authorization = `Bearer ${token}`
      } else {
        clearStoredToken()
        redirectToLogin()
      }
    }
    return config
  },
  error => Promise.reject(error)
)

modelHttp.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response && error.response.status === 401) {
      clearStoredToken()
      redirectToLogin()
    }
    return Promise.reject(normalizeError(error))
  }
)

// 默认导出认证服务实例
export default authHttp


