<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>智能体评估系统</h2>
          <p v-if="isAddAccountMode">添加新账号</p>
          <p v-else>请登录或注册账号</p>
        </div>
      </template>

      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="登录" name="login">
          <el-form
            ref="loginFormRef"
            :model="loginForm"
            :rules="loginRules"
            label-width="80px"
            @submit.prevent="handleLogin"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="loginForm.username"
                placeholder="请输入用户名或邮箱"
                clearable
              />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="请输入密码"
                show-password
                @keyup.enter="handleLogin"
              />
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :loading="loading"
                @click="handleLogin"
                style="width: 100%"
              >
                登录
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <!-- 注册要求提示 -->
          <el-alert
            type="info"
            :closable="false"
            show-icon
            style="margin-bottom: 20px;"
          >
            <template #title>
              <div style="font-size: 13px;">
                <div><strong>注册要求：</strong></div>
                <div>• 用户名：至少3个字符，必须唯一</div>
                <div>• 邮箱：必须是有效的邮箱格式（如：user@example.com）</div>
                <div>• 密码：至少6个字符，建议使用字母+数字组合</div>
              </div>
            </template>
          </el-alert>

          <!-- 错误提示（如果有） -->
          <el-alert
            v-if="registerError"
            type="error"
            :closable="true"
            show-icon
            @close="registerError = ''"
            style="margin-bottom: 20px;"
          >
            <template #title>
              <div style="font-size: 13px;">
                <div><strong>{{ registerError }}</strong></div>
                <div v-if="registerErrorDetail" style="margin-top: 5px; color: #909399;">
                  {{ registerErrorDetail }}
                </div>
              </div>
            </template>
          </el-alert>

          <el-form
            ref="registerFormRef"
            :model="registerForm"
            :rules="registerRules"
            label-width="80px"
            @submit.prevent="handleRegister"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="registerForm.username"
                placeholder="请输入用户名（至少3个字符）"
                clearable
                @input="clearRegisterError"
              />
              <div class="form-tip">用户名将用于登录，请确保唯一性</div>
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input
                v-model="registerForm.email"
                placeholder="请输入邮箱（如：user@example.com）"
                clearable
                @input="clearRegisterError"
              />
              <div class="form-tip">用于登录和找回密码，请使用真实邮箱</div>
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="registerForm.password"
                type="password"
                placeholder="请输入密码（至少6位）"
                show-password
                @input="clearRegisterError"
              />
              <div class="form-tip">建议使用字母、数字组合，提高安全性</div>
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="registerForm.confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                show-password
                @input="clearRegisterError"
                @keyup.enter="handleRegister"
              />
              <div class="form-tip">请确保与上方密码完全一致</div>
            </el-form-item>
            <el-form-item label="用户角色" prop="role">
              <el-radio-group v-model="registerForm.role">
                <el-radio label="user">普通用户</el-radio>
                <el-radio label="admin">管理员</el-radio>
              </el-radio-group>
              <div class="form-tip">普通用户只能使用管理员添加的API密钥，管理员可以添加和管理API密钥</div>
            </el-form-item>
            <el-form-item>
              <el-button
                type="primary"
                :loading="loading"
                @click="handleRegister"
                style="width: 100%"
              >
                注册
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeTab = ref('login')
const loading = ref(false)
const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()
const registerError = ref('')
const registerErrorDetail = ref('')
const isAddAccountMode = ref(false)

// 检查是否是添加账号模式
onMounted(() => {
  isAddAccountMode.value = route.query.addAccount === 'true'
  if (isAddAccountMode.value && userStore.accounts.length > 0) {
    ElMessage.info('请登录新账号，新账号将被添加到账号列表中')
  }
})

const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  role: 'user'  // 默认普通用户
})

// 登录表单验证规则
const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ]
}

// 注册表单验证规则
const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value !== registerForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const registerRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, message: '用户名长度至少3位', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 处理标签页切换
const handleTabChange = () => {
  loginFormRef.value?.clearValidate()
  registerFormRef.value?.clearValidate()
  clearRegisterError()
}

// 清除注册错误提示
const clearRegisterError = () => {
  registerError.value = ''
  registerErrorDetail.value = ''
}

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      // 如果是添加账号模式，不自动切换到新账号
      const success = await userStore.login(loginForm.username, loginForm.password, !isAddAccountMode.value)
      loading.value = false
      if (success) {
        if (isAddAccountMode.value) {
          // 添加账号模式：清空表单，提示成功
          loginForm.username = ''
          loginForm.password = ''
          loginFormRef.value.resetFields()
          ElMessage.success('账号已添加，可以在右上角切换账号')
          // 可以选择返回上一页或留在登录页
          setTimeout(() => {
            router.back()
          }, 1500)
        } else {
          // 正常登录：跳转到主页
          router.push('/')
        }
      }
    }
  })
}

// 处理注册
const handleRegister = async () => {
  if (!registerFormRef.value) return

  // 清除之前的错误提示
  clearRegisterError()

  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      const result = await userStore.register(
        registerForm.username,
        registerForm.email,
        registerForm.password,
        registerForm.role
      )
      loading.value = false
      
      if (result.success) {
        // 注册成功后切换到登录标签页
        activeTab.value = 'login'
        loginForm.username = registerForm.username
        registerFormRef.value.resetFields()
        clearRegisterError()
      } else {
        // 显示详细的错误信息
        registerError.value = result.message || '注册失败'
        registerErrorDetail.value = result.detail || ''
      }
    }
  })
}
</script>

<style scoped lang="scss">
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 1px, transparent 1px);
    background-size: 50px 50px;
    animation: move 20s linear infinite;
  }
  
  @keyframes move {
    0% {
      transform: translate(0, 0);
    }
    100% {
      transform: translate(50px, 50px);
    }
  }
}

.login-card {
  width: 100%;
  max-width: 480px;
  border: none;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  border-radius: 16px;
  position: relative;
  z-index: 1;
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.98);
  
  :deep(.el-card__header) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    border-radius: 16px 16px 0 0;
    padding: 32px 24px;
  }
  
  :deep(.el-card__body) {
    padding: 32px;
  }
  
  :deep(.el-tabs__header) {
    margin-bottom: 24px;
  }
  
  :deep(.el-tabs__item) {
    font-size: 16px;
    font-weight: 500;
  }
  
  :deep(.el-tabs__active-bar) {
    height: 3px;
  }
}

.card-header {
  text-align: center;
  
  h2 {
    margin: 0 0 8px 0;
    color: #fff;
    font-size: 28px;
    font-weight: 700;
  }
  
  p {
    margin: 0;
    color: rgba(255, 255, 255, 0.9);
    font-size: 14px;
  }
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.4;
}

:deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px #dcdfe6 inset;
  transition: all 0.3s;
  
  &:hover {
    box-shadow: 0 0 0 1px #c0c4cc inset;
  }
  
  &.is-focus {
    box-shadow: 0 0 0 1px #409eff inset;
  }
}

:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  height: 44px;
}
</style>

