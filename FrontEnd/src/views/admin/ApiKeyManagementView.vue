<template>
  <div class="apikey-management">
    <el-card shadow="hover" class="page-card">
      <template #header>
        <div class="card-header">
          <div>
            <h2>API KEY管理</h2>
            <p>管理默认API密钥，供所有用户使用</p>
          </div>
          <el-button type="primary" @click="handleAddApiKey" :icon="Plus">
            添加默认API KEY
          </el-button>
        </div>
      </template>

      <div class="table-toolbar">
        <el-select
          v-model="filterProvider"
          placeholder="筛选提供商"
          clearable
          style="width: 200px"
          @change="loadApiKeys"
        >
          <el-option
            v-for="provider in providers"
            :key="provider.id"
            :label="provider.name"
            :value="provider.id"
          />
        </el-select>
        <el-button @click="loadApiKeys" :icon="Refresh">刷新</el-button>
      </div>

      <el-table
        :data="apiKeys"
        style="width: 100%"
        v-loading="apiKeysLoading"
        stripe
        class="apikey-table"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="provider" label="提供商" width="150">
          <template #default="scope">
            <el-tag type="primary" effect="dark">
              {{ getProviderName(scope.row.provider) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="密钥名称" min-width="200" />
        <el-table-column prop="is_default" label="默认" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.is_default ? 'success' : 'info'" effect="dark">
              {{ scope.row.is_default ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column prop="updated_at" label="更新时间" width="180" />
        <el-table-column label="操作" width="300" fixed="right">
          <template #default="scope">
            <el-button
              size="small"
              type="success"
              plain
              @click="handleSetDefault(scope.row)"
              :disabled="scope.row.is_default"
              :icon="Star"
            >
              设为默认
            </el-button>
            <el-button
              size="small"
              type="primary"
              plain
              @click="handleEditApiKey(scope.row)"
              :icon="Edit"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              type="danger"
              plain
              @click="handleDeleteApiKey(scope.row)"
              :icon="Delete"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- API KEY编辑对话框 -->
    <el-dialog
      v-model="apiKeyDialogVisible"
      :title="editingApiKey ? '编辑API KEY' : '添加默认API KEY'"
      width="600px"
      :close-on-click-modal="false"
    >
      <el-form :model="apiKeyForm" label-width="120px" :rules="apiKeyFormRules" ref="apiKeyFormRef">
        <el-form-item label="提供商" prop="provider">
          <el-select
            v-model="apiKeyForm.provider"
            placeholder="请选择提供商"
            style="width: 100%"
            :disabled="!!editingApiKey"
          >
            <el-option
              v-for="provider in providers"
              :key="provider.id"
              :label="provider.name"
              :value="provider.id"
            >
              <span>{{ provider.name }}</span>
              <span style="color: #8492a6; font-size: 13px; margin-left: 10px">
                {{ provider.description }}
              </span>
            </el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="密钥名称" prop="name">
          <el-input
            v-model="apiKeyForm.name"
            placeholder="请输入密钥名称（如：生产环境密钥）"
          />
        </el-form-item>
        <el-form-item :label="'API KEY'" :prop="editingApiKey ? '' : 'api_key'">
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
        <el-button type="primary" @click="handleSubmitApiKey" :loading="savingApiKey">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useUserStore } from '../../stores/user'
import { ElMessage, ElMessageBox, type FormInstance } from 'element-plus'
import axios from 'axios'
import { Plus, Refresh, Edit, Delete, Star } from '@element-plus/icons-vue'

const userStore = useUserStore()

const apiKeys = ref([])
const apiKeysLoading = ref(false)
const apiKeyDialogVisible = ref(false)
const editingApiKey = ref(null)
const savingApiKey = ref(false)
const providers = ref([])
const filterProvider = ref('')
const apiKeyFormRef = ref<FormInstance>()

const apiKeyForm = ref({
  provider: '',
  name: '',
  api_key: '',
  is_default: false
})

const apiKeyFormRules = {
  provider: [{ required: true, message: '请选择提供商', trigger: 'change' }],
  name: [{ required: true, message: '请输入密钥名称', trigger: 'blur' }],
  api_key: [{ required: true, message: '请输入API KEY', trigger: 'blur' }]
}

async function loadApiKeys() {
  apiKeysLoading.value = true
  try {
    const params: any = {}
    if (filterProvider.value) {
      params.provider = filterProvider.value
    }
    const response = await axios.get('http://127.0.0.1:8000/api/apikeys', {
      params,
      headers: { Authorization: `Bearer ${userStore.token}` }
    })
    apiKeys.value = response.data
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载API KEY列表失败')
  } finally {
    apiKeysLoading.value = false
  }
}

async function loadProviders() {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/providers')
    providers.value = response.data.filter((p: any) => p.requires_api_key)
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '加载提供商列表失败')
  }
}

function getProviderName(providerId: string) {
  const provider = providers.value.find((p: any) => p.id === providerId)
  return provider ? provider.name : providerId
}

function handleAddApiKey() {
  editingApiKey.value = null
  apiKeyForm.value = {
    provider: '',
    name: '',
    api_key: '',
    is_default: false
  }
  apiKeyDialogVisible.value = true
  apiKeyFormRef.value?.clearValidate()
}

function handleEditApiKey(apiKey: any) {
  editingApiKey.value = apiKey
  apiKeyForm.value = {
    provider: apiKey.provider,
    name: apiKey.name,
    api_key: '',
    is_default: apiKey.is_default
  }
  apiKeyDialogVisible.value = true
  apiKeyFormRef.value?.clearValidate()
}

async function handleSubmitApiKey() {
  if (!apiKeyFormRef.value) return
  
  await apiKeyFormRef.value.validate((valid) => {
    if (!valid) return
    
    if (!editingApiKey.value && !apiKeyForm.value.api_key) {
      ElMessage.warning('请填写API KEY')
      return
    }
    
    savingApiKey.value = true
    const submit = async () => {
      try {
        if (editingApiKey.value) {
          const updateData: any = {
            name: apiKeyForm.value.name,
            is_default: apiKeyForm.value.is_default
          }
          if (apiKeyForm.value.api_key) {
            updateData.api_key = apiKeyForm.value.api_key
          }
          
          await axios.put(
            `http://127.0.0.1:8000/api/apikeys/${editingApiKey.value.id}`,
            updateData,
            { headers: { Authorization: `Bearer ${userStore.token}` } }
          )
          ElMessage.success('API KEY已更新')
        } else {
          await axios.post(
            'http://127.0.0.1:8000/api/apikeys',
            {
              provider: apiKeyForm.value.provider,
              name: apiKeyForm.value.name,
              api_key: apiKeyForm.value.api_key,
              is_default: apiKeyForm.value.is_default
            },
            { headers: { Authorization: `Bearer ${userStore.token}` } }
          )
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
    submit()
  })
}

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
      headers: { Authorization: `Bearer ${userStore.token}` }
    })
    ElMessage.success('API KEY已删除')
    loadApiKeys()
  } catch (error: any) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

async function handleSetDefault(apiKey: any) {
  try {
    await axios.post(
      `http://127.0.0.1:8000/api/apikeys/${apiKey.id}/set-default`,
      {},
      { headers: { Authorization: `Bearer ${userStore.token}` } }
    )
    ElMessage.success('已设置为默认API KEY')
    loadApiKeys()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '设置失败')
  }
}

onMounted(() => {
  loadApiKeys()
  loadProviders()
})
</script>

<style scoped lang="scss">
.apikey-management {
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

.form-help {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>

