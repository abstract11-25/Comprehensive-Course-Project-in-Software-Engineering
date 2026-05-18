<template>
  <div class="user-management">
    <el-card shadow="hover" class="page-card">
      <template #header>
        <div class="card-header">
          <div>
            <h2>用户管理</h2>
            <p>管理系统中的所有用户账号</p>
          </div>
          <el-button type="primary" @click="handleAddUser" :icon="Plus">
            添加用户
          </el-button>
        </div>
      </template>

      <div class="table-toolbar">
        <el-input
          v-model="searchText"
          placeholder="搜索用户名或邮箱"
          clearable
          style="width: 300px"
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button @click="loadUsers" :icon="Refresh">刷新</el-button>
      </div>

      <el-table
        :data="filteredUsers"
        style="width: 100%"
        v-loading="usersLoading"
        stripe
        class="user-table"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" min-width="120">
          <template #default="scope">
            <div class="user-cell">
              <el-avatar :size="32" class="user-avatar">
                {{ scope.row.username.charAt(0).toUpperCase() }}
              </el-avatar>
              <span>{{ scope.row.username }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column prop="role" label="角色" width="120">
          <template #default="scope">
            <el-tag :type="scope.row.role === 'admin' ? 'danger' : 'info'" effect="dark">
              {{ scope.row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button
              size="small"
              type="primary"
              plain
              @click="handleEditUser(scope.row)"
              :icon="Edit"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              type="danger"
              plain
              @click="handleDeleteUser(scope.row)"
              :disabled="scope.row.id === userStore.user?.id"
              :icon="Delete"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 用户编辑对话框 -->
    <el-dialog
      v-model="userDialogVisible"
      :title="editingUser ? '编辑用户' : '添加用户'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="userForm" label-width="80px" :rules="userFormRules" ref="userFormRef">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userForm.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userForm.email" type="email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-radio-group v-model="userForm.role">
            <el-radio label="user">普通用户</el-radio>
            <el-radio label="admin">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="密码" :prop="editingUser ? '' : 'password'">
          <el-input
            v-model="userForm.password"
            type="password"
            show-password
            placeholder="请输入密码"
          />
          <div class="form-help" v-if="editingUser">留空则不修改密码</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitUser" :loading="savingUser">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useUserStore } from '../../stores/user'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import axios from 'axios'
import { Plus, Refresh, Search, Edit, Delete } from '@element-plus/icons-vue'

const userStore = useUserStore()

const users = ref([])
const usersLoading = ref(false)
const userDialogVisible = ref(false)
const editingUser = ref(null)
const savingUser = ref(false)
const searchText = ref('')
const userFormRef = ref<FormInstance>()

const userForm = ref({
  username: '',
  email: '',
  role: 'user',
  password: ''
})

const userFormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const filteredUsers = computed(() => {
  if (!searchText.value) return users.value
  const text = searchText.value.toLowerCase()
  return users.value.filter(
    (user: any) =>
      user.username.toLowerCase().includes(text) || user.email.toLowerCase().includes(text)
  )
})

async function loadUsers() {
  usersLoading.value = true
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/admin/users', {
      headers: { Authorization: `Bearer ${userStore.token}` }
    })
    users.value = response.data
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载用户列表失败')
  } finally {
    usersLoading.value = false
  }
}

function handleSearch() {
  // 搜索逻辑已在computed中处理
}

function handleAddUser() {
  editingUser.value = null
  userForm.value = {
    username: '',
    email: '',
    role: 'user',
    password: ''
  }
  userDialogVisible.value = true
  userFormRef.value?.clearValidate()
}

function handleEditUser(user: any) {
  editingUser.value = user
  userForm.value = {
    username: user.username,
    email: user.email,
    role: user.role,
    password: ''
  }
  userDialogVisible.value = true
  userFormRef.value?.clearValidate()
}

async function handleSubmitUser() {
  if (!userFormRef.value) return
  
  await userFormRef.value.validate((valid) => {
    if (!valid) return
    
    if (!editingUser.value && !userForm.value.password) {
      ElMessage.warning('请设置密码')
      return
    }
    
    savingUser.value = true
    const submit = async () => {
      try {
        if (editingUser.value) {
          const updateData: any = {
            username: userForm.value.username,
            email: userForm.value.email,
            role: userForm.value.role
          }
          if (userForm.value.password) {
            updateData.password = userForm.value.password
          }
          
          await axios.put(
            `http://127.0.0.1:8000/api/admin/users/${editingUser.value.id}`,
            updateData,
            { headers: { Authorization: `Bearer ${userStore.token}` } }
          )
          ElMessage.success('用户已更新')
        } else {
          await userStore.register(
            userForm.value.username,
            userForm.value.email,
            userForm.value.password,
            userForm.value.role
          )
          ElMessage.success('用户已创建')
        }
        userDialogVisible.value = false
        loadUsers()
      } catch (error: any) {
        ElMessage.error(error.response?.data?.detail || '操作失败')
      } finally {
        savingUser.value = false
      }
    }
    submit()
  })
}

async function handleDeleteUser(user: any) {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await axios.delete(`http://127.0.0.1:8000/api/admin/users/${user.id}`, {
      headers: { Authorization: `Bearer ${userStore.token}` }
    })
    ElMessage.success('用户已删除')
    loadUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped lang="scss">
.user-management {
  max-width: 1400px;
  margin: 0 auto;
}

.page-card {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  
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

.table-toolbar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 12px;
}

.user-table {
  :deep(.user-cell) {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .user-avatar {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: #fff;
      font-weight: 600;
    }
  }
}

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>

