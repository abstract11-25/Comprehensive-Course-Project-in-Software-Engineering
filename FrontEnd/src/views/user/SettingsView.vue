<template>
  <div class="settings-view">
    <el-card shadow="hover" class="page-card">
      <template #header>
        <div class="card-header">
          <div>
            <h2>个人设置</h2>
            <p>管理您的个人信息和账户设置</p>
          </div>
        </div>
      </template>

      <el-tabs v-model="activeTab" class="settings-tabs">
        <el-tab-pane label="个人信息" name="profile">
          <el-form
            :model="profileForm"
            label-width="120px"
            style="max-width: 600px; margin-top: 20px;"
            :rules="profileRules"
            ref="profileFormRef"
          >
            <el-form-item label="用户名">
              <el-input v-model="profileForm.username" disabled />
              <div class="form-help">用户名不可修改</div>
            </el-form-item>
            <el-form-item label="邮箱">
              <el-input v-model="profileForm.email" disabled />
              <div class="form-help">邮箱不可修改，请联系管理员</div>
            </el-form-item>
            <el-form-item label="角色">
              <el-tag :type="profileForm.role === 'admin' ? 'danger' : 'info'" effect="dark">
                {{ profileForm.role === 'admin' ? '管理员' : '普通用户' }}
              </el-tag>
            </el-form-item>
            <el-form-item label="注册时间">
              <span style="color: #909399;">{{ profileForm.created_at || '-' }}</span>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="修改密码" name="password">
          <el-form
            :model="passwordForm"
            label-width="120px"
            style="max-width: 600px; margin-top: 20px;"
            :rules="passwordRules"
            ref="passwordFormRef"
          >
            <el-form-item label="当前密码" prop="oldPassword">
              <el-input
                v-model="passwordForm.oldPassword"
                type="password"
                show-password
                placeholder="请输入当前密码"
              />
            </el-form-item>
            <el-form-item label="新密码" prop="newPassword">
              <el-input
                v-model="passwordForm.newPassword"
                type="password"
                show-password
                placeholder="请输入新密码（至少6位）"
              />
              <div class="form-help">密码长度至少6位，建议使用字母+数字组合</div>
            </el-form-item>
            <el-form-item label="确认新密码" prop="confirmPassword">
              <el-input
                v-model="passwordForm.confirmPassword"
                type="password"
                show-password
                placeholder="请再次输入新密码"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleChangePassword" :loading="changingPassword">
                修改密码
              </el-button>
              <el-button @click="resetPasswordForm">重置</el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import axios from 'axios'
import { useUserStore } from '../../stores/user'

const userStore = useUserStore()

const activeTab = ref('profile')
const changingPassword = ref(false)
const profileFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()

const profileForm = ref({
  username: '',
  email: '',
  role: '',
  created_at: ''
})

const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule: any, value: any, callback: any) => {
  if (value !== passwordForm.value.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const profileRules = {}
const passwordRules = {
  oldPassword: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

function loadProfile() {
  if (userStore.user) {
    profileForm.value = {
      username: userStore.user.username || '',
      email: userStore.user.email || '',
      role: userStore.user.role || '',
      created_at: userStore.user.created_at || ''
    }
  }
}

function resetPasswordForm() {
  passwordForm.value = {
    oldPassword: '',
    newPassword: '',
    confirmPassword: ''
  }
  passwordFormRef.value?.clearValidate()
}

async function handleChangePassword() {
  if (!passwordFormRef.value) return

  await passwordFormRef.value.validate(async (valid) => {
    if (!valid) return

    changingPassword.value = true
    try {
      await axios.post(
        'http://127.0.0.1:8000/api/user/change-password',
        {
          old_password: passwordForm.value.oldPassword,
          new_password: passwordForm.value.newPassword
        },
        {
          headers: { Authorization: `Bearer ${userStore.token}` }
        }
      )
      ElMessage.success('密码修改成功')
      resetPasswordForm()
    } catch (error: any) {
      ElMessage.error(error.response?.data?.detail || '密码修改失败')
    } finally {
      changingPassword.value = false
    }
  })
}

onMounted(() => {
  loadProfile()
})
</script>

<style scoped lang="scss">
.settings-view {
  max-width: 1000px;
  margin: 0 auto;
}

.page-card {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.card-header {
  h2 {
    margin: 0 0 4px 0;
    font-size: 20px;
    color: #303133;
  }
  
  p {
    margin: 0;
    font-size: 14px;
    color: #909399;
  }
}

.settings-tabs {
  :deep(.el-tabs__item) {
    font-size: 16px;
    font-weight: 500;
  }
}

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>

