<template>
  <div class="history-view">
    <el-card shadow="hover" class="page-card">
      <template #header>
        <div class="card-header">
          <div>
            <h2>评估历史</h2>
            <p>查看和管理您的评估记录</p>
          </div>
          <el-button @click="loadHistory" :icon="Refresh">刷新</el-button>
        </div>
      </template>

      <div class="table-toolbar">
        <el-input
          v-model="searchText"
          placeholder="搜索评估记录"
          clearable
          style="width: 300px"
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select
          v-model="filterStatus"
          placeholder="筛选状态"
          clearable
          style="width: 150px"
          @change="handleSearch"
        >
          <el-option label="已完成" value="completed" />
          <el-option label="进行中" value="running" />
          <el-option label="已失败" value="failed" />
        </el-select>
      </div>

      <el-table
        :data="filteredHistory"
        style="width: 100%"
        v-loading="loading"
        stripe
        class="history-table"
      >
        <el-table-column prop="task_id" label="任务ID" width="120" />
        <el-table-column prop="provider" label="服务商" width="120">
          <template #default="scope">
            <el-tag type="primary">{{ getProviderName(scope.row.provider) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="model" label="模型" width="150" />
        <el-table-column prop="status" label="状态" width="150">
          <template #default="scope">
            <div style="display: flex; align-items: center; gap: 8px;">
              <el-tag :type="getStatusType(scope.row.status)" effect="dark">
                {{ getStatusText(scope.row.status) }}
              </el-tag>
              <el-progress
                v-if="scope.row.status === 'running'"
                :percentage="scope.row.progress || 0"
                :stroke-width="6"
                :show-text="false"
                style="width: 60px;"
              />
              <span v-if="scope.row.status === 'running'" style="font-size: 12px; color: #909399;">
                {{ scope.row.current_index || 0 }}/{{ scope.row.total_cases || 0 }}
              </span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="overall_score" label="总体得分" width="120">
          <template #default="scope">
            <span v-if="scope.row.overall_score !== null">
              {{ (scope.row.overall_score * 100).toFixed(2) }}
            </span>
            <span v-else style="color: #909399;">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="scope">
            <el-button
              v-if="scope.row.status === 'running'"
              size="small"
              type="primary"
              @click="goToEvaluation(scope.row.task_id)"
              :icon="DataBoard"
            >
              返回评估
            </el-button>
            <el-button
              size="small"
              type="primary"
              plain
              @click="viewDetail(scope.row)"
              :icon="View"
            >
              查看详情
            </el-button>
            <el-button
              size="small"
              type="success"
              plain
              @click="exportReport(scope.row)"
              :icon="Download"
              :disabled="scope.row.status !== 'completed'"
            >
              导出
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && filteredHistory.length === 0" description="暂无评估记录" />
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog
      v-model="detailVisible"
      title="评估详情"
      width="80%"
      :close-on-click-modal="false"
    >
      <div v-if="currentDetail" class="detail-content">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">{{ currentDetail.task_id }}</el-descriptions-item>
          <el-descriptions-item label="服务商">{{ getProviderName(currentDetail.provider) }}</el-descriptions-item>
          <el-descriptions-item label="模型">{{ currentDetail.model || '未指定' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentDetail.status)">
              {{ getStatusText(currentDetail.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="总体得分" v-if="currentDetail.overall_score !== null">
            {{ (currentDetail.overall_score * 100).toFixed(2) }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ currentDetail.created_at }}</el-descriptions-item>
        </el-descriptions>

        <el-card v-if="currentDetail.summary" style="margin-top: 20px;" shadow="never">
          <template #header>评估结果概览</template>
          <el-row :gutter="20">
            <el-col :span="6" v-if="currentDetail.summary.functional">
              <div class="stat-card">
                <div class="stat-label">功能评估准确率</div>
                <div class="stat-value">
                  {{ (currentDetail.summary.functional.accuracy * 100).toFixed(1) }}%
                </div>
              </div>
            </el-col>
            <el-col :span="6" v-if="currentDetail.summary.safety">
              <div class="stat-card">
                <div class="stat-label">安全评估通过率</div>
                <div class="stat-value">
                  {{ (currentDetail.summary.safety.safety_rate * 100).toFixed(1) }}%
                </div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="stat-card">
                <div class="stat-label">总耗时</div>
                <div class="stat-value">{{ currentDetail.summary.total_time }}s</div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
        <el-button
          type="primary"
          @click="exportReport(currentDetail)"
          :disabled="currentDetail?.status !== 'completed'"
        >
          导出报告
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useUserStore } from '../../stores/user'
import { Refresh, Search, View, Download, DataBoard } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const loading = ref(false)
const history = ref([])
const searchText = ref('')
const filterStatus = ref('')
const detailVisible = ref(false)
const currentDetail = ref(null)
let pollInterval: NodeJS.Timeout | null = null

const providerMap: Record<string, string> = {
  zhipu: '智谱 GLM',
  openai: 'OpenAI',
  deepseek: 'DeepSeek',
  moonshot: 'Moonshot',
  qwen: '通义千问',
  baichuan: '百川',
  custom: '自定义'
}

const filteredHistory = computed(() => {
  let result = history.value

  if (searchText.value) {
    const text = searchText.value.toLowerCase()
    result = result.filter(
      (item: any) =>
        item.task_id?.toLowerCase().includes(text) ||
        item.provider?.toLowerCase().includes(text) ||
        item.model?.toLowerCase().includes(text)
    )
  }

  if (filterStatus.value) {
    result = result.filter((item: any) => item.status === filterStatus.value)
  }

  return result
})

function getProviderName(provider: string) {
  return providerMap[provider] || provider
}

function getStatusType(status: string) {
  const map: Record<string, string> = {
    completed: 'success',
    running: 'primary',
    failed: 'danger',
    cancelled: 'info'
  }
  return map[status] || 'info'
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    completed: '已完成',
    running: '进行中',
    failed: '已失败',
    cancelled: '已取消'
  }
  return map[status] || status
}

async function loadHistory() {
  loading.value = true
  try {
    // 1. 从localStorage加载历史记录
    const stored = localStorage.getItem('evaluation_history')
    let localHistory: any[] = []
    if (stored) {
      try {
        localHistory = JSON.parse(stored)
      } catch (e) {
        localHistory = []
      }
    }
    
    // 2. 从后端获取进行中的任务
    try {
      const response = await axios.get('http://127.0.0.1:8000/api/evaluation/running/list', {
        headers: { Authorization: `Bearer ${userStore.token}` }
      })
      const runningTasks = response.data.tasks || []
      
      // 合并历史记录和进行中的任务
      const taskIdMap = new Map()
      
      // 先添加localStorage中的历史记录
      localHistory.forEach((item: any) => {
        taskIdMap.set(item.task_id, item)
      })
      
      // 用进行中的任务覆盖（如果存在）
      runningTasks.forEach((task: any) => {
        taskIdMap.set(task.task_id, task)
      })
      
      // 转换为数组并排序（最新的在前）
      history.value = Array.from(taskIdMap.values()).sort((a: any, b: any) => {
        const timeA = new Date(a.created_at || 0).getTime()
        const timeB = new Date(b.created_at || 0).getTime()
        return timeB - timeA
      })
    } catch (error: any) {
      // 如果获取进行中任务失败，只使用localStorage的数据
      console.warn('获取进行中任务失败:', error)
      history.value = localHistory
    }
  } catch (error) {
    ElMessage.error('加载历史记录失败')
    history.value = []
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  // 搜索逻辑已在computed中处理
}

function viewDetail(item: any) {
  currentDetail.value = item
  detailVisible.value = true
}

function exportReport(item: any) {
  if (!item || item.status !== 'completed') {
    ElMessage.warning('只能导出已完成的评估报告')
    return
  }

  try {
    const report = {
      task_id: item.task_id,
      provider: item.provider,
      model: item.model,
      created_at: item.created_at,
      summary: item.summary,
      results: item.results
    }

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `evaluation_report_${item.task_id}.json`
    link.click()
    URL.revokeObjectURL(url)

    ElMessage.success('报告导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  }
}

function goToEvaluation(taskId: string) {
  // 跳转到评估页面，并保存taskId到sessionStorage，让评估页面可以继续显示该任务
  sessionStorage.setItem('current_task_id', taskId)
  router.push('/')
}

// 轮询更新进行中的任务状态
async function pollRunningTasks() {
  try {
    const response = await axios.get('http://127.0.0.1:8000/api/evaluation/running/list', {
      headers: { Authorization: `Bearer ${userStore.token}` }
    })
    const runningTasks = response.data.tasks || []
    
    // 更新历史记录中的进行中任务
    const taskIdMap = new Map()
    history.value.forEach((item: any) => {
      taskIdMap.set(item.task_id, item)
    })
    
    // 更新进行中的任务
    runningTasks.forEach((task: any) => {
      taskIdMap.set(task.task_id, task)
    })
    
    // 检查是否有任务已完成（从running变为completed），需要从后端获取完整状态
    for (const task of runningTasks) {
      try {
        const statusResponse = await axios.get(`http://127.0.0.1:8000/api/evaluation/${task.task_id}`, {
          headers: { Authorization: `Bearer ${userStore.token}` }
        })
        const taskStatus = statusResponse.data
        
        // 如果任务已完成或失败，保存到localStorage并更新历史
        if (taskStatus.status === 'completed' || taskStatus.status === 'failed') {
          const historyItem = {
            task_id: task.task_id,
            provider: taskStatus.agent?.provider || task.provider,
            model: taskStatus.agent?.model || task.model || '未指定',
            status: taskStatus.status,
            overall_score: taskStatus.summary?.summary?.overall_score || null,
            summary: taskStatus.summary,
            results: taskStatus.results || [],
            created_at: new Date(taskStatus.started_at * 1000).toLocaleString('zh-CN')
          }
          
          taskIdMap.set(task.task_id, historyItem)
          
          // 保存到localStorage
          const stored = localStorage.getItem('evaluation_history')
          let localHistory: any[] = []
          if (stored) {
            try {
              localHistory = JSON.parse(stored)
            } catch (e) {
              localHistory = []
            }
          }
          
          // 更新或添加历史记录
          const existingIndex = localHistory.findIndex((item: any) => item.task_id === task.task_id)
          if (existingIndex >= 0) {
            localHistory[existingIndex] = historyItem
          } else {
            localHistory.unshift(historyItem)
          }
          
          // 限制历史记录数量
          if (localHistory.length > 100) {
            localHistory = localHistory.slice(0, 100)
          }
          
          localStorage.setItem('evaluation_history', JSON.stringify(localHistory))
        } else {
          // 更新进行中任务的状态
          taskIdMap.set(task.task_id, {
            ...task,
            progress: taskStatus.progress || 0,
            current_index: taskStatus.current_index || 0,
            total_cases: taskStatus.total_cases || 0,
            current_case: taskStatus.current_case || ''
          })
        }
      } catch (error) {
        // 忽略单个任务查询失败
        console.warn(`获取任务 ${task.task_id} 状态失败:`, error)
      }
    }
    
    // 更新历史记录
    history.value = Array.from(taskIdMap.values()).sort((a: any, b: any) => {
      const timeA = new Date(a.created_at || 0).getTime()
      const timeB = new Date(b.created_at || 0).getTime()
      return timeB - timeA
    })
  } catch (error) {
    // 轮询失败不影响页面显示
    console.warn('轮询进行中任务失败:', error)
  }
}

onMounted(() => {
  loadHistory()
  
  // 每3秒轮询一次进行中的任务
  pollInterval = setInterval(() => {
    // 只在有进行中任务时才轮询
    const hasRunning = history.value.some((item: any) => item.status === 'running')
    if (hasRunning) {
      pollRunningTasks()
    }
  }, 3000)
})

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
})
</script>

<style scoped lang="scss">
.history-view {
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
  gap: 12px;
  margin-bottom: 16px;
}

.detail-content {
  .stat-card {
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
    border: 1px solid rgba(102, 126, 234, 0.2);
    
    .stat-label {
      color: #909399;
      font-size: 14px;
      margin-bottom: 8px;
    }
    
    .stat-value {
      font-size: 24px;
      font-weight: 700;
      color: #303133;
    }
  }
}
</style>

