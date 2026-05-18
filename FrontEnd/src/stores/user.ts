import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import axios from 'axios'
import { ElMessage } from 'element-plus'

interface User {
  id: number
  username: string
  email: string
  role?: string  // 角色：admin 或 user
}

interface Account {
  id: string  // 账号唯一标识（使用username）
  username: string
  email: string
  role?: string
  token: string
  loginTime: number  // 登录时间戳
}

const STORAGE_KEY_ACCOUNTS = 'user_accounts'
const STORAGE_KEY_CURRENT_ACCOUNT = 'current_account_id'

export const useUserStore = defineStore('user', () => {
  // 账号列表
  const accounts = ref<Map<string, Account>>(new Map())
  // 当前激活的账号ID
  const currentAccountId = ref<string | null>(null)

  // 当前账号信息（计算属性）
  const currentAccount = computed(() => {
    if (!currentAccountId.value) return null
    return accounts.value.get(currentAccountId.value) || null
  })

  const token = computed(() => currentAccount.value?.token || null)
  const user = computed(() => {
    if (!currentAccount.value) return null
    return {
      id: currentAccount.value.id,
      username: currentAccount.value.username,
      email: currentAccount.value.email,
      role: currentAccount.value.role
    }
  })

  const isLoggedIn = computed(() => !!token.value)

  // 所有账号列表（用于显示）
  const accountList = computed(() => Array.from(accounts.value.values()))

  // 从localStorage加载账号数据
  function loadAccounts() {
    try {
      const savedAccounts = localStorage.getItem(STORAGE_KEY_ACCOUNTS)
      const savedCurrentId = localStorage.getItem(STORAGE_KEY_CURRENT_ACCOUNT)
      
      if (savedAccounts) {
        const accountsData = JSON.parse(savedAccounts)
        accounts.value = new Map(accountsData)
      } else {
        // 向后兼容：检查是否有旧的token格式
        const oldToken = localStorage.getItem('token')
        const oldUser = localStorage.getItem('user')
        if (oldToken && oldUser) {
          try {
            const userData = JSON.parse(oldUser)
            const account: Account = {
              id: userData.username,
              username: userData.username,
              email: userData.email,
              role: userData.role,
              token: oldToken,
              loginTime: Date.now()
            }
            accounts.value.set(account.id, account)
            currentAccountId.value = account.id
            saveAccounts()
            // 清除旧数据
            localStorage.removeItem('token')
            localStorage.removeItem('user')
          } catch (e) {
            console.error('Failed to migrate old auth data:', e)
          }
        }
      }

      if (savedCurrentId && accounts.value.has(savedCurrentId)) {
        currentAccountId.value = savedCurrentId
      } else if (accounts.value.size > 0) {
        // 如果没有保存的当前账号，使用第一个账号
        currentAccountId.value = Array.from(accounts.value.keys())[0]
      }
    } catch (e) {
      console.error('Failed to load accounts:', e)
      accounts.value = new Map()
      currentAccountId.value = null
    }
  }

  // 保存账号数据到localStorage
  function saveAccounts() {
    try {
      const accountsData = Array.from(accounts.value.entries())
      localStorage.setItem(STORAGE_KEY_ACCOUNTS, JSON.stringify(accountsData))
      if (currentAccountId.value) {
        localStorage.setItem(STORAGE_KEY_CURRENT_ACCOUNT, currentAccountId.value)
      } else {
        localStorage.removeItem(STORAGE_KEY_CURRENT_ACCOUNT)
      }
    } catch (e) {
      console.error('Failed to save accounts:', e)
    }
  }

  // 添加账号（登录时调用）
  function addAccount(accessToken: string, userData: User) {
    const accountId = userData.username
    const account: Account = {
      id: accountId,
      username: userData.username,
      email: userData.email,
      role: userData.role,
      token: accessToken,
      loginTime: Date.now()
    }
    accounts.value.set(accountId, account)
    currentAccountId.value = accountId
    saveAccounts()
  }

  // 切换账号
  function switchAccount(accountId: string) {
    if (accounts.value.has(accountId)) {
      currentAccountId.value = accountId
      saveAccounts()
      ElMessage.success(`已切换到账号：${accounts.value.get(accountId)?.username}`)
      return true
    }
    return false
  }

  // 删除账号
  function removeAccount(accountId: string) {
    if (accounts.value.has(accountId)) {
      accounts.value.delete(accountId)
      
      // 如果删除的是当前账号，切换到其他账号
      if (currentAccountId.value === accountId) {
        if (accounts.value.size > 0) {
          currentAccountId.value = Array.from(accounts.value.keys())[0]
        } else {
          currentAccountId.value = null
        }
      }
      
      saveAccounts()
      ElMessage.success('账号已移除')
      return true
    }
    return false
  }

  // 设置token和用户信息（保持向后兼容）
  function setAuth(accessToken: string, userData: User) {
    addAccount(accessToken, userData)
  }

  // 清除认证信息（退出当前账号）
  function clearAuth() {
    if (currentAccountId.value) {
      removeAccount(currentAccountId.value)
    }
  }

  // 从localStorage恢复用户信息
  function restoreAuth() {
    loadAccounts()
  }

  // 登录（支持添加新账号而不覆盖）
  async function login(username: string, password: string, switchToNew: boolean = true) {
    try {
      // 使用FormData格式（OAuth2PasswordRequestForm要求）
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)

      // 注意：不要手动设置 Content-Type，让浏览器自动设置（包括 boundary）
      const response = await axios.post('http://127.0.0.1:8000/api/auth/login', formData)

      const { access_token, user: userData } = response.data
      
      // 检查账号是否已存在
      const accountId = userData.username
      const accountExists = accounts.value.has(accountId)
      
      if (accountExists) {
        // 更新已存在账号的token
        const account = accounts.value.get(accountId)!
        account.token = access_token
        account.loginTime = Date.now()
        accounts.value.set(accountId, account)
        if (switchToNew) {
          currentAccountId.value = accountId
        }
        ElMessage.success('账号已更新')
      } else {
        // 添加新账号
        addAccount(access_token, userData)
        ElMessage.success('登录成功')
      }
      
      saveAccounts()
      return true
    } catch (error: any) {
      const message = error.response?.data?.detail || '登录失败，请检查用户名和密码'
      ElMessage.error(message)
      return false
    }
  }

  // 注册
  async function register(username: string, email: string, password: string, role: string = 'user') {
    try {
      const response = await axios.post('http://127.0.0.1:8000/api/auth/register', {
        username,
        email,
        password,
        role
      })

      ElMessage.success('注册成功，请登录')
      return { success: true, message: '注册成功' }
    } catch (error: any) {
      // 获取详细的错误信息
      let errorMessage = '注册失败'
      let errorDetail = ''
      
      if (error.response) {
        // 服务器返回的错误
        const detail = error.response.data?.detail || ''
        errorDetail = detail
        
        // 根据不同的错误类型提供更友好的提示
        if (detail.includes('用户名已存在')) {
          errorMessage = '注册失败：用户名已被使用'
          errorDetail = '该用户名已被其他用户注册，请尝试其他用户名'
        } else if (detail.includes('邮箱已被注册')) {
          errorMessage = '注册失败：邮箱已被注册'
          errorDetail = '该邮箱已被注册，请使用其他邮箱或直接登录'
        } else if (detail.includes('邮箱') || detail.includes('email')) {
          errorMessage = '注册失败：邮箱格式不正确'
          errorDetail = '请输入有效的邮箱地址，格式如：user@example.com'
        } else if (detail) {
          errorMessage = `注册失败：${detail}`
          errorDetail = detail
        }
      } else if (error.request) {
        // 请求已发出但没有收到响应
        errorMessage = '注册失败：无法连接到服务器'
        errorDetail = '请检查网络连接，或确认后端服务是否已启动（http://127.0.0.1:8000）'
      } else {
        // 其他错误
        errorMessage = '注册失败：发生未知错误'
        errorDetail = error.message || '请稍后重试'
      }
      
      ElMessage.error(errorMessage)
      return { success: false, message: errorMessage, detail: errorDetail }
    }
  }

  // 获取当前用户信息
  async function fetchUserInfo() {
    if (!token.value || !currentAccount.value) return false

    try {
      const response = await axios.get('http://127.0.0.1:8000/api/auth/me', {
        headers: {
          Authorization: `Bearer ${token.value}`
        }
      })
      
      // 更新当前账号信息
      const account = currentAccount.value
      account.email = response.data.email
      account.role = response.data.role
      accounts.value.set(account.id, account)
      saveAccounts()
      
      return true
    } catch (error: any) {
      // token可能已过期
      if (error.response?.status === 401) {
        // 移除过期的账号
        if (currentAccountId.value) {
          removeAccount(currentAccountId.value)
        }
        ElMessage.warning('登录已过期，请重新登录')
      }
      return false
    }
  }

  // 退出登录（退出当前账号）
  function logout() {
    if (currentAccountId.value) {
      const username = accounts.value.get(currentAccountId.value)?.username
      removeAccount(currentAccountId.value)
      ElMessage.success(`已退出账号：${username}`)
    }
  }

  // 退出所有账号
  function logoutAll() {
    accounts.value.clear()
    currentAccountId.value = null
    saveAccounts()
    ElMessage.success('已退出所有账号')
  }

  // 初始化：加载账号数据
  loadAccounts()

  return {
    token,
    user,
    isLoggedIn,
    accounts: accountList,
    currentAccountId,
    currentAccount,
    login,
    register,
    logout,
    logoutAll,
    switchAccount,
    removeAccount,
    fetchUserInfo,
    restoreAuth,
    clearAuth,
    addAccount
  }
})

