<template>
  <div class="dashboard-container">
    <!-- 欢迎卡片 -->
    <el-card class="welcome-card" shadow="hover">
      <div class="welcome-content">
        <div class="welcome-text">
          <h1>欢迎回来，{{ userStore.user?.username }}！</h1>
          <p>这里是智能体评估系统的管理控制台，您可以在这里管理用户、API密钥和评估配置。</p>
        </div>
        <div class="welcome-icon">
          <el-icon :size="80" color="#409eff"><DataBoard /></el-icon>
        </div>
      </div>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon user-icon">
              <el-icon :size="32"><User /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalUsers }}</div>
              <div class="stat-label">总用户数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon admin-icon">
              <el-icon :size="32"><UserFilled /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.adminUsers }}</div>
              <div class="stat-label">管理员</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon key-icon">
              <el-icon :size="32"><Key /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.totalApiKeys }}</div>
              <div class="stat-label">API密钥</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon default-icon">
              <el-icon :size="32"><Star /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.defaultKeys }}</div>
              <div class="stat-label">默认密钥</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 快捷操作 -->
    <el-row :gutter="20" class="quick-actions-row">
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="quick-action-card" shadow="hover" @click="goToUsers">
          <div class="action-content">
            <el-icon :size="48" color="#409eff"><User /></el-icon>
            <h3>用户管理</h3>
            <p>添加、编辑或删除用户账号</p>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="quick-action-card" shadow="hover" @click="goToApiKeys">
          <div class="action-content">
            <el-icon :size="48" color="#67c23a"><Key /></el-icon>
            <h3>API KEY管理</h3>
            <p>管理默认API密钥，供所有用户使用</p>
          </div>
        </el-card>
      </el-col>
      
      <el-col :xs="24" :sm="12" :md="8">
        <el-card class="quick-action-card" shadow="hover" @click="goToConfig">
          <div class="action-content">
            <el-icon :size="48" color="#e6a23c"><Tools /></el-icon>
            <h3>评估配置</h3>
            <p>配置评估体系的权重和参数</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'
import axios from 'axios'
import { DataBoard, User, UserFilled, Key, Star, Tools } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()

const stats = ref({
  totalUsers: 0,
  adminUsers: 0,
  totalApiKeys: 0,
  defaultKeys: 0
})

async function loadStats() {
  try {
    // 加载用户统计
    const usersResponse = await axios.get('http://127.0.0.1:8000/api/admin/users', {
      headers: { Authorization: `Bearer ${userStore.token}` }
    })
    const users = usersResponse.data
    stats.value.totalUsers = users.length
    stats.value.adminUsers = users.filter((u: any) => u.role === 'admin').length
    
    // 加载API密钥统计
    const keysResponse = await axios.get('http://127.0.0.1:8000/api/apikeys', {
      headers: { Authorization: `Bearer ${userStore.token}` }
    })
    const keys = keysResponse.data
    stats.value.totalApiKeys = keys.length
    stats.value.defaultKeys = keys.filter((k: any) => k.is_default).length
  } catch (error) {
    console.error('加载统计信息失败:', error)
  }
}

function goToUsers() {
  router.push('/admin/users')
}

function goToApiKeys() {
  router.push('/admin/apikeys')
}

function goToConfig() {
  router.push('/admin/config')
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped lang="scss">
.dashboard-container {
  max-width: 1400px;
  margin: 0 auto;
}

.welcome-card {
  margin-bottom: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  
  :deep(.el-card__body) {
    padding: 32px;
  }
}

.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #fff;
  
  .welcome-text {
    flex: 1;
    
    h1 {
      font-size: 28px;
      margin: 0 0 12px 0;
      font-weight: 600;
    }
    
    p {
      font-size: 16px;
      opacity: 0.9;
      margin: 0;
    }
  }
  
  .welcome-icon {
    opacity: 0.3;
  }
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  border: none;
  transition: transform 0.3s;
  
  &:hover {
    transform: translateY(-4px);
  }
  
  :deep(.el-card__body) {
    padding: 20px;
  }
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &.user-icon {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
  }
  
  &.admin-icon {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: #fff;
  }
  
  &.key-icon {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    color: #fff;
  }
  
  &.default-icon {
    background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    color: #fff;
  }
}

.stat-info {
  flex: 1;
  
  .stat-value {
    font-size: 32px;
    font-weight: 700;
    color: #303133;
    line-height: 1;
    margin-bottom: 8px;
  }
  
  .stat-label {
    font-size: 14px;
    color: #909399;
  }
}

.quick-actions-row {
  margin-bottom: 24px;
}

.quick-action-card {
  cursor: pointer;
  transition: all 0.3s;
  border: none;
  height: 100%;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12) !important;
  }
  
  :deep(.el-card__body) {
    padding: 32px;
  }
}

.action-content {
  text-align: center;
  
  .el-icon {
    margin-bottom: 16px;
  }
  
  h3 {
    font-size: 20px;
    margin: 0 0 8px 0;
    color: #303133;
    font-weight: 600;
  }
  
  p {
    font-size: 14px;
    color: #909399;
    margin: 0;
  }
}
</style>

