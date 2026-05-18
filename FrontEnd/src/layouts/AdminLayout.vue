<template>
  <div class="admin-layout">
    <!-- 侧边栏 -->
    <el-aside :width="sidebarWidth" class="admin-sidebar">
      <div class="sidebar-header">
        <h2 class="logo">
          <el-icon><Setting /></el-icon>
          <span>管理控制台</span>
        </h2>
      </div>
      
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        router
        class="admin-menu"
        background-color="#1a1d29"
        text-color="#b4b9c6"
        active-text-color="#409eff"
      >
        <el-menu-item index="/admin/dashboard">
          <el-icon><DataBoard /></el-icon>
          <template #title>仪表盘</template>
        </el-menu-item>
        
        <el-menu-item index="/admin/users">
          <el-icon><User /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
        
        <el-menu-item index="/admin/apikeys">
          <el-icon><Key /></el-icon>
          <template #title>API KEY管理</template>
        </el-menu-item>
        
        <el-menu-item index="/admin/config">
          <el-icon><Tools /></el-icon>
          <template #title>评估体系配置</template>
        </el-menu-item>
      </el-menu>
      
      <div class="sidebar-footer">
        <el-button
          :icon="isCollapse ? Expand : Fold"
          circle
          @click="toggleCollapse"
          class="collapse-btn"
        />
      </div>
    </el-aside>

    <!-- 主内容区 -->
    <div class="admin-main">
      <!-- 顶部导航栏 -->
      <el-header class="admin-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/admin/dashboard' }">管理控制台</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentPageTitle">{{ currentPageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <el-dropdown @command="handleCommand" trigger="click">
            <span class="user-dropdown">
              <el-avatar :size="32" class="user-avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <span class="username">{{ userStore.user?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  <span style="color: #909399;">{{ userStore.user?.email }}</span>
                </el-dropdown-item>
                
                <!-- 账号列表 -->
                <el-dropdown-item v-if="userStore.accounts.length > 1" divided>
                  <div style="color: #909399; font-size: 12px; margin-bottom: 4px;">已登录账号：</div>
                  <div 
                    v-for="account in userStore.accounts" 
                    :key="account.id"
                    class="account-item"
                    :class="{ 'account-active': account.id === userStore.currentAccountId }"
                  >
                    <el-icon v-if="account.id === userStore.currentAccountId" style="color: #409eff;">
                      <Check />
                    </el-icon>
                    <span 
                      class="account-name"
                      @click="switchAccount(account.id)"
                    >
                      {{ account.username }}
                      <span v-if="account.role === 'admin'" style="color: #f56c6c; font-size: 11px;">(管理员)</span>
                    </span>
                    <el-icon 
                      v-if="account.id !== userStore.currentAccountId"
                      class="account-remove"
                      @click.stop="removeAccount(account.id)"
                    >
                      <Close />
                    </el-icon>
                  </div>
                </el-dropdown-item>
                
                <el-dropdown-item divided command="add-account">
                  <el-icon><Plus /></el-icon>
                  添加账号
                </el-dropdown-item>
                <el-dropdown-item command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出当前账号
                </el-dropdown-item>
                <el-dropdown-item 
                  v-if="userStore.accounts.length > 1"
                  command="logout-all"
                  divided
                >
                  <el-icon><SwitchButton /></el-icon>
                  退出所有账号
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 页面内容 -->
      <div class="admin-content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Setting,
  DataBoard,
  User,
  Key,
  Tools,
  Expand,
  Fold,
  ArrowDown,
  SwitchButton,
  Check,
  Close,
  Plus
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const isCollapse = ref(false)
const sidebarWidth = computed(() => isCollapse.value ? '64px' : '240px')

const activeMenu = computed(() => route.path)
const currentPageTitle = computed(() => {
  const titleMap: Record<string, string> = {
    '/admin/dashboard': '仪表盘',
    '/admin/users': '用户管理',
    '/admin/apikeys': 'API KEY管理',
    '/admin/config': '评估体系配置'
  }
  return titleMap[route.path] || ''
})

function toggleCollapse() {
  isCollapse.value = !isCollapse.value
}

function handleCommand(command: string) {
  if (command === 'logout') {
    userStore.logout()
    if (userStore.accounts.length === 0) {
      router.push('/login')
    } else {
      // 如果还有其他账号，检查当前账号是否是管理员
      const currentAccount = userStore.currentAccount
      if (!currentAccount || currentAccount.role !== 'admin') {
        router.push('/')
      } else {
        window.location.reload()
      }
    }
  } else if (command === 'logout-all') {
    ElMessageBox.confirm(
      '确定要退出所有账号吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    ).then(() => {
      userStore.logoutAll()
      router.push('/login')
    }).catch(() => {})
  } else if (command === 'add-account') {
    router.push('/login?addAccount=true')
  }
}

function switchAccount(accountId: string) {
  userStore.switchAccount(accountId)
  // 刷新页面以更新所有组件
  window.location.reload()
}

function removeAccount(accountId: string) {
  const account = userStore.accounts.find(a => a.id === accountId)
  if (!account) return
  
  ElMessageBox.confirm(
    `确定要移除账号 "${account.username}" 吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(() => {
    userStore.removeAccount(accountId)
    if (userStore.accounts.length === 0) {
      router.push('/login')
    } else if (userStore.currentAccountId === accountId) {
      // 如果删除的是当前账号，检查新账号是否是管理员
      const currentAccount = userStore.currentAccount
      if (!currentAccount || currentAccount.role !== 'admin') {
        router.push('/')
      } else {
        window.location.reload()
      }
    }
  }).catch(() => {})
}
</script>

<style scoped lang="scss">
.admin-layout {
  display: flex;
  height: 100vh;
  background: #f5f7fa;
}

.admin-sidebar {
  background: linear-gradient(180deg, #1a1d29 0%, #252936 100%);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  overflow: hidden;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  
  .logo {
    display: flex;
    align-items: center;
    gap: 12px;
    color: #fff;
    font-size: 18px;
    font-weight: 600;
    margin: 0;
    
    .el-icon {
      font-size: 24px;
      color: #409eff;
    }
  }
}

.admin-menu {
  flex: 1;
  border: none;
  padding: 10px 0;
  
  :deep(.el-menu-item) {
    margin: 4px 12px;
    border-radius: 8px;
    height: 48px;
    line-height: 48px;
    
    &:hover {
      background-color: rgba(64, 158, 255, 0.1) !important;
    }
    
    &.is-active {
      background-color: rgba(64, 158, 255, 0.2) !important;
      color: #409eff !important;
    }
  }
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: center;
  
  .collapse-btn {
    background: rgba(255, 255, 255, 0.1);
    border: none;
    color: #b4b9c6;
    
    &:hover {
      background: rgba(255, 255, 255, 0.2);
      color: #409eff;
    }
  }
}

.admin-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.admin-header {
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
  z-index: 100;
}

.header-left {
  :deep(.el-breadcrumb) {
    font-size: 14px;
  }
}

.header-right {
  .user-dropdown {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
    padding: 8px 12px;
    border-radius: 8px;
    transition: background 0.3s;
    
    &:hover {
      background: #f5f7fa;
    }
    
    .user-avatar {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .username {
      font-weight: 500;
      color: #303133;
    }
  }
}

.admin-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  background: #f5f7fa;
}

.account-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 0;
  cursor: pointer;
  transition: background 0.2s;
  border-radius: 4px;
  padding: 4px 8px;
  margin: 2px 0;
  
  &:hover {
    background: #f5f7fa;
  }
  
  &.account-active {
    background: #ecf5ff;
    color: #409eff;
  }
  
  .account-name {
    flex: 1;
    font-size: 13px;
  }
  
  .account-remove {
    color: #909399;
    font-size: 14px;
    transition: color 0.2s;
    
    &:hover {
      color: #f56c6c;
    }
  }
}
</style>

