<template>
  <div class="admin-container">
    <el-container>
      <el-header class="admin-header">
        <div class="header-content">
          <h1>管理员控制台</h1>
          <div class="header-actions">
            <span class="username">{{ userStore.user?.username }}</span>
            <el-button type="danger" @click="handleLogout">退出登录</el-button>
          </div>
        </div>
      </el-header>
      
      <el-main class="admin-main">
        <el-tabs v-model="activeTab" type="border-card">
          <!-- 用户管理 -->
          <el-tab-pane label="用户管理" name="users">
            <div class="tab-content">
              <div class="toolbar">
                <el-button type="primary" @click="handleAddUser">添加用户</el-button>
                <el-button @click="loadUsers">刷新</el-button>
              </div>
              
              <el-table :data="users" style="width: 100%" v-loading="usersLoading">
                <el-table-column prop="id" label="ID" width="80" />
                <el-table-column prop="username" label="用户名" />
                <el-table-column prop="email" label="邮箱" />
                <el-table-column prop="role" label="角色" width="100">
                  <template #default="scope">
                    <el-tag :type="scope.row.role === 'admin' ? 'danger' : 'info'">
                      {{ scope.row.role === 'admin' ? '管理员' : '普通用户' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="创建时间" width="180" />
                <el-table-column label="操作" width="200">
                  <template #default="scope">
                    <el-button size="small" @click="handleEditUser(scope.row)">编辑</el-button>
                    <el-button 
                      size="small" 
                      type="danger" 
                      @click="handleDeleteUser(scope.row)"
                      :disabled="scope.row.id === userStore.user?.id"
                    >
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>
          
          <!-- API KEY管理 -->
          <el-tab-pane label="API KEY管理" name="apikeys">
            <div class="tab-content">
              <div class="toolbar">
                <el-button type="primary" @click="handleAddApiKey">添加默认API KEY</el-button>
                <el-button @click="loadApiKeys">刷新</el-button>
              </div>
              
              <el-table :data="apiKeys" style="width: 100%" v-loading="apiKeysLoading">
                <el-table-column prop="id" label="ID" width="80" />
                <el-table-column prop="provider" label="提供商" width="120">
                  <template #default="scope">
                    <el-tag>{{ getProviderName(scope.row.provider) }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="name" label="密钥名称" />
                <el-table-column prop="is_default" label="默认" width="100">
                  <template #default="scope">
                    <el-tag :type="scope.row.is_default ? 'success' : 'info'">
                      {{ scope.row.is_default ? '是' : '否' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" label="创建时间" width="180" />
                <el-table-column prop="updated_at" label="更新时间" width="180" />
                <el-table-column label="操作" width="280">
                  <template #default="scope">
                    <el-button 
                      size="small" 
                      type="success"
                      @click="handleSetDefault(scope.row)"
                      :disabled="scope.row.is_default"
                    >
                      设为默认
                    </el-button>
                    <el-button size="small" @click="handleEditApiKey(scope.row)">编辑</el-button>
                    <el-button 
                      size="small" 
                      type="danger" 
                      @click="handleDeleteApiKey(scope.row)"
                    >
                      删除
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </el-tab-pane>
          
          <!-- 评估体系配置 -->
          <el-tab-pane label="评估体系配置" name="config">
            <div class="tab-content">
              <el-form :model="evaluationConfig" label-width="200px" v-loading="configLoading">
                <el-divider>基础权重配置</el-divider>
                <el-form-item label="基础指标权重">
                  <el-input-number
                    v-model="evaluationConfig.base_weight"
                    :min="0"
                    :max="1"
                    :precision="2"
                    :step="0.1"
                    style="width: 200px"
                  />
                  <div class="form-help">基础指标在总体得分中的权重（0-1）</div>
                </el-form-item>
                <el-form-item label="通用化指标权重">
                  <el-input-number
                    v-model="evaluationConfig.generalization_weight"
                    :min="0"
                    :max="1"
                    :precision="2"
                    :step="0.1"
                    style="width: 200px"
                  />
                  <div class="form-help">通用化指标在总体得分中的权重（0-1）</div>
                </el-form-item>
                
                <el-divider>通用化指标内部权重</el-divider>
                <el-form-item label="适应性权重">
                  <el-input-number
                    v-model="evaluationConfig.adaptivity_weight"
                    :min="0"
                    :max="1"
                    :precision="2"
                    :step="0.1"
                    style="width: 200px"
                  />
                </el-form-item>
                <el-form-item label="鲁棒性权重">
                  <el-input-number
                    v-model="evaluationConfig.robustness_weight"
                    :min="0"
                    :max="1"
                    :precision="2"
                    :step="0.1"
                    style="width: 200px"
                  />
                </el-form-item>
                <el-form-item label="可移植性权重">
                  <el-input-number
                    v-model="evaluationConfig.portability_weight"
                    :min="0"
                    :max="1"
                    :precision="2"
                    :step="0.1"
                    style="width: 200px"
                  />
                </el-form-item>
                <el-form-item label="协作效率权重">
                  <el-input-number
                    v-model="evaluationConfig.collaboration_weight"
                    :min="0"
                    :max="1"
                    :precision="2"
                    :step="0.1"
                    style="width: 200px"
                  />
                </el-form-item>
                
                <el-divider>评估类型权重</el-divider>
                <el-form-item label="功能评估权重">
                  <el-input-number
                    v-model="evaluationConfig.func_weight"
                    :min="0"
                    :max="1"
                    :precision="2"
                    :step="0.1"
                    style="width: 200px"
                  />
                </el-form-item>
                <el-form-item label="安全评估权重">
                  <el-input-number
                    v-model="evaluationConfig.safety_weight"
                    :min="0"
                    :max="1"
                    :precision="2"
                    :step="0.1"
                    style="width: 200px"
                  />
                </el-form-item>
                
                <el-divider>其他系数配置</el-divider>
                <el-form-item label="真实正例总数">
                  <el-input-number
                    v-model="evaluationConfig.ground_truth_total"
                    :min="0"
                    style="width: 200px"
                  />
                  <div class="form-help">用于计算召回率，不填则按用例数量计算</div>
                </el-form-item>
                <el-form-item label="场景类型总数">
                  <el-input-number
                    v-model="evaluationConfig.total_scene_types"
                    :min="0"
                    style="width: 200px"
                  />
                  <div class="form-help">用于计算场景覆盖度</div>
                </el-form-item>
                <el-form-item label="单主体基准耗时（秒）">
                  <el-input-number
                    v-model="evaluationConfig.baseline_single_task_time"
                    :min="0"
                    :precision="3"
                    style="width: 200px"
                  />
                </el-form-item>
                <el-form-item label="基准适配成本">
                  <el-input-number
                    v-model="evaluationConfig.baseline_adaptation_cost"
                    :min="0"
                    :precision="2"
                    style="width: 200px"
                  />
                  <div class="form-help">用于计算适配成本系数</div>
                </el-form-item>
                
                <el-form-item>
                  <el-button type="primary" @click="handleSaveConfig" :loading="savingConfig">保存配置</el-button>
                  <el-button @click="loadConfig">重置</el-button>
                </el-form-item>
              </el-form>
            </div>
          </el-tab-pane>
        </el-tabs>
      </el-main>
    </el-container>
    
    <!-- 用户编辑对话框 -->
    <el-dialog
      v-model="userDialogVisible"
      :title="editingUser ? '编辑用户' : '添加用户'"
      width="500px"
    >
      <el-form :model="userForm" label-width="80px">
        <el-form-item label="用户名" required>
          <el-input v-model="userForm.username" />
        </el-form-item>
        <el-form-item label="邮箱" required>
          <el-input v-model="userForm.email" type="email" />
        </el-form-item>
        <el-form-item label="角色" required>
          <el-radio-group v-model="userForm.role">
            <el-radio label="user">普通用户</el-radio>
            <el-radio label="admin">管理员</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="密码" :required="!editingUser">
          <el-input v-model="userForm.password" type="password" show-password />
          <div class="form-help" v-if="editingUser">留空则不修改密码</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="userDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitUser" :loading="savingUser">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- API KEY编辑对话框 -->
    <el-dialog
      v-model="apiKeyDialogVisible"
      :title="editingApiKey ? '编辑API KEY' : '添加默认API KEY'"
      width="600px"
    >
      <el-form :model="apiKeyForm" label-width="120px">
        <el-form-item label="提供商" required>
          <el-select v-model="apiKeyForm.provider" placeholder="请选择提供商" style="width: 100%" :disabled="!!editingApiKey">
            <el-option
              v-for="provider in providers"
              :key="provider.id"
              :label="provider.name"
              :value="provider.id"
            >
              <span>{{ provider.name }}</span>
              <span style="color: #8492a6; font-size: 13px; margin-left: 10px">{{ provider.description }}</span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="密钥名称" required>
          <el-input v-model="apiKeyForm.name" placeholder="请输入密钥名称（如：生产环境密钥）" />
        </el-form-item>
        <el-form-item label="API KEY" :required="!editingApiKey">
          <el-input 
            v-model="apiKeyForm.api_key" 
            type="password" 
            show-password 
            placeholder="请输入API KEY"
          />
          <div class="form-help" v-if="editingApiKey">留空则不修改API KEY</div>
        </el-form-item>
        <el-form-item label="设为默认">
          <el-switch v-model="apiKeyForm.is_default" />
          <div class="form-help">设置为默认后，该提供商下的其他密钥将自动取消默认状态</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="apiKeyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitApiKey" :loading="savingApiKey">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()

const activeTab = ref('users')
const users = ref([])
const usersLoading = ref(false)
const userDialogVisible = ref(false)
const editingUser = ref(null)
const savingUser = ref(false)
const configLoading = ref(false)
const savingConfig = ref(false)
const apiKeys = ref([])
const apiKeysLoading = ref(false)
const apiKeyDialogVisible = ref(false)
const editingApiKey = ref(null)
const savingApiKey = ref(false)
const providers = ref([])

const userForm = ref({
  username: '',
  email: '',
  role: 'user',
  password: ''
})

const apiKeyForm = ref({
  provider: '',
  name: '',
  api_key: '',
  is_default: false
})

const evaluationConfig = ref({
  base_weight: 0.8,
  generalization_weight: 0.2,
  adaptivity_weight: 0.3,
  robustness_weight: 0.3,
  portability_weight: 0.2,
  collaboration_weight: 0.2,
  func_weight: 0.7,
  safety_weight: 0.3,
  ground_truth_total: null,
  total_scene_types: null,
  baseline_single_task_time: null,
  baseline_adaptation_cost: null
})

// 加载用户列表
async function loadUsers() {
  usersLoading.value = true
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/admin/users', {
      headers: {
        Authorization: `Bearer ${userStore.token}`
      }
    })
    users.value = response.data
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载用户列表失败')
  } finally {
    usersLoading.value = false
  }
}

// 加载评估配置
async function loadConfig() {
  configLoading.value = true
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/admin/evaluation-config', {
      headers: {
        Authorization: `Bearer ${userStore.token}`
      }
    })
    const config = response.data
    evaluationConfig.value = {
      base_weight: parseFloat(config.base_weight) || 0.8,
      generalization_weight: parseFloat(config.generalization_weight) || 0.2,
      adaptivity_weight: parseFloat(config.adaptivity_weight) || 0.3,
      robustness_weight: parseFloat(config.robustness_weight) || 0.3,
      portability_weight: parseFloat(config.portability_weight) || 0.2,
      collaboration_weight: parseFloat(config.collaboration_weight) || 0.2,
      func_weight: parseFloat(config.func_weight) || 0.7,
      safety_weight: parseFloat(config.safety_weight) || 0.3,
      ground_truth_total: config.ground_truth_total,
      total_scene_types: config.total_scene_types,
      baseline_single_task_time: config.baseline_single_task_time ? parseFloat(config.baseline_single_task_time) : null,
      baseline_adaptation_cost: config.baseline_adaptation_cost ? parseFloat(config.baseline_adaptation_cost) : null
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载配置失败')
  } finally {
    configLoading.value = false
  }
}

// 保存评估配置
async function handleSaveConfig() {
  savingConfig.value = true
  try {
    const configData: any = {
      base_weight: String(evaluationConfig.value.base_weight),
      generalization_weight: String(evaluationConfig.value.generalization_weight),
      adaptivity_weight: String(evaluationConfig.value.adaptivity_weight),
      robustness_weight: String(evaluationConfig.value.robustness_weight),
      portability_weight: String(evaluationConfig.value.portability_weight),
      collaboration_weight: String(evaluationConfig.value.collaboration_weight),
      func_weight: String(evaluationConfig.value.func_weight),
      safety_weight: String(evaluationConfig.value.safety_weight)
    }
    
    if (evaluationConfig.value.ground_truth_total !== null) {
      configData.ground_truth_total = evaluationConfig.value.ground_truth_total
    }
    if (evaluationConfig.value.total_scene_types !== null) {
      configData.total_scene_types = evaluationConfig.value.total_scene_types
    }
    if (evaluationConfig.value.baseline_single_task_time !== null) {
      configData.baseline_single_task_time = String(evaluationConfig.value.baseline_single_task_time)
    }
    if (evaluationConfig.value.baseline_adaptation_cost !== null) {
      configData.baseline_adaptation_cost = String(evaluationConfig.value.baseline_adaptation_cost)
    }
    
    await axios.put('http://127.0.0.1:8000/api/admin/evaluation-config', configData, {
      headers: {
        Authorization: `Bearer ${userStore.token}`
      }
    })
    ElMessage.success('配置已保存')
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '保存配置失败')
  } finally {
    savingConfig.value = false
  }
}

// 添加用户
function handleAddUser() {
  editingUser.value = null
  userForm.value = {
    username: '',
    email: '',
    role: 'user',
    password: ''
  }
  userDialogVisible.value = true
}

// 编辑用户
function handleEditUser(user: any) {
  editingUser.value = user
  userForm.value = {
    username: user.username,
    email: user.email,
    role: user.role,
    password: ''
  }
  userDialogVisible.value = true
}

// 提交用户
async function handleSubmitUser() {
  if (!userForm.value.username || !userForm.value.email) {
    ElMessage.warning('请填写用户名和邮箱')
    return
  }
  
  if (!editingUser.value && !userForm.value.password) {
    ElMessage.warning('请设置密码')
    return
  }
  
  savingUser.value = true
  try {
    if (editingUser.value) {
      // 更新用户
      const updateData: any = {
        username: userForm.value.username,
        email: userForm.value.email,
        role: userForm.value.role
      }
      if (userForm.value.password) {
        updateData.password = userForm.value.password
      }
      
      await axios.put(`http://127.0.0.1:8000/api/admin/users/${editingUser.value.id}`, updateData, {
        headers: {
          Authorization: `Bearer ${userStore.token}`
        }
      })
      ElMessage.success('用户已更新')
    } else {
      // 创建用户（通过注册接口）
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

// 删除用户
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
      headers: {
        Authorization: `Bearer ${userStore.token}`
      }
    })
    ElMessage.success('用户已删除')
    loadUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 退出登录
function handleLogout() {
  userStore.logout()
  router.push('/login')
}

// 加载API KEY列表
async function loadApiKeys() {
  apiKeysLoading.value = true
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/apikeys', {
      headers: {
        Authorization: `Bearer ${userStore.token}`
      }
    })
    apiKeys.value = response.data
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载API KEY列表失败')
  } finally {
    apiKeysLoading.value = false
  }
}

// 加载提供商列表
async function loadProviders() {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/providers')
    providers.value = response.data.filter((p: any) => p.requires_api_key)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载提供商列表失败')
  }
}

// 获取提供商名称
function getProviderName(providerId: string) {
  const provider = providers.value.find((p: any) => p.id === providerId)
  return provider ? provider.name : providerId
}

// 添加API KEY
function handleAddApiKey() {
  editingApiKey.value = null
  apiKeyForm.value = {
    provider: '',
    name: '',
    api_key: '',
    is_default: false
  }
  apiKeyDialogVisible.value = true
}

// 编辑API KEY
function handleEditApiKey(apiKey: any) {
  editingApiKey.value = apiKey
  apiKeyForm.value = {
    provider: apiKey.provider,
    name: apiKey.name,
    api_key: '',
    is_default: apiKey.is_default
  }
  apiKeyDialogVisible.value = true
}

// 提交API KEY
async function handleSubmitApiKey() {
  if (!apiKeyForm.value.provider || !apiKeyForm.value.name) {
    ElMessage.warning('请填写提供商和密钥名称')
    return
  }
  
  if (!editingApiKey.value && !apiKeyForm.value.api_key) {
    ElMessage.warning('请填写API KEY')
    return
  }
  
  savingApiKey.value = true
  try {
    if (editingApiKey.value) {
      // 更新API KEY
      const updateData: any = {
        name: apiKeyForm.value.name,
        is_default: apiKeyForm.value.is_default
      }
      if (apiKeyForm.value.api_key) {
        updateData.api_key = apiKeyForm.value.api_key
      }
      
      await axios.put(`http://127.0.0.1:8000/api/apikeys/${editingApiKey.value.id}`, updateData, {
        headers: {
          Authorization: `Bearer ${userStore.token}`
        }
      })
      ElMessage.success('API KEY已更新')
    } else {
      // 创建API KEY
      await axios.post('http://127.0.0.1:8000/api/apikeys', {
        provider: apiKeyForm.value.provider,
        name: apiKeyForm.value.name,
        api_key: apiKeyForm.value.api_key,
        is_default: apiKeyForm.value.is_default
      }, {
        headers: {
          Authorization: `Bearer ${userStore.token}`
        }
      })
      ElMessage.success('API KEY已添加')
    }
    apiKeyDialogVisible.value = false
    loadApiKeys()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    savingApiKey.value = false
  }
}

// 删除API KEY
async function handleDeleteApiKey(apiKey: any) {
  try {
    await ElMessageBox.confirm(
      `确定要删除API KEY "${apiKey.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await axios.delete(`http://127.0.0.1:8000/api/apikeys/${apiKey.id}`, {
      headers: {
        Authorization: `Bearer ${userStore.token}`
      }
    })
    ElMessage.success('API KEY已删除')
    loadApiKeys()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 设置默认API KEY
async function handleSetDefault(apiKey: any) {
  try {
    await axios.post(`http://127.0.0.1:8000/api/apikeys/${apiKey.id}/set-default`, {}, {
      headers: {
        Authorization: `Bearer ${userStore.token}`
      }
    })
    ElMessage.success('已设置为默认API KEY')
    loadApiKeys()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '设置失败')
  }
}

onMounted(() => {
  if (userStore.user?.role !== 'admin') {
    ElMessage.error('您没有权限访问此页面')
    router.push('/login')
    return
  }
  loadUsers()
  loadConfig()
  loadApiKeys()
  loadProviders()
})
</script>

<style scoped>
.admin-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.admin-header {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0 20px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.header-content h1 {
  margin: 0;
  font-size: 24px;
  color: #333;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 15px;
}

.username {
  color: #666;
  font-size: 14px;
}

.admin-main {
  padding: 20px;
}

.tab-content {
  padding: 20px;
  background: white;
  border-radius: 8px;
}

.toolbar {
  margin-bottom: 20px;
}

.form-help {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

:deep(.el-tabs__content) {
  padding: 0;
}
</style>

