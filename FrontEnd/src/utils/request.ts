import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import router from '../router'

// 创建axios实例
const request = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 30000
})

// 请求拦截器：自动添加token
request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：处理错误
request.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // token过期或无效，清除登录状态并跳转到登录页
      const userStore = useUserStore()
      userStore.clearAuth()
      ElMessage.warning('登录已过期，请重新登录')
      router.push('/login')
    } else if (error.response?.status >= 500) {
      ElMessage.error('服务器错误，请稍后重试')
    }
    return Promise.reject(error)
  }
)

export default request

