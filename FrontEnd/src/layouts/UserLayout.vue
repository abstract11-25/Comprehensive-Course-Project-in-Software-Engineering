<template>
  <div class="user-layout">
    <!-- 顶部导航栏 -->
    <el-header class="user-header">
      <div class="header-left">
        <div class="logo">
          <el-icon><DataBoard /></el-icon>
          <span>智能体评估系统</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          mode="horizontal"
          router
          class="header-menu"
        >
          <el-menu-item index="/">
            <el-icon><DataBoard /></el-icon>
            <span>评估工作台</span>
          </el-menu-item>
          <el-menu-item index="/history">
            <el-icon><Clock /></el-icon>
            <span>评估历史</span>
          </el-menu-item>
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span>个人设置</span>
          </el-menu-item>
        </el-menu>
      </div>
      
      <div class="header-right">
        <el-dropdown @command="handleCommand" trigger="click">
          <span class="user-dropdown">
            <el-avatar :size="32" class="user-avatar">
              {{ userStore.user?.username?.charAt(0).toUpperCase() }}
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
    <div class="user-content">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { DataBoard, ArrowDown, SwitchButton, Clock, Setting, Check, Close, Plus } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)

function handleCommand(command: string) {
  if (command === 'logout') {
    userStore.logout()
    if (userStore.accounts.length === 0) {
      router.push('/login')
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
      // 如果删除的是当前账号，刷新页面
      window.location.reload()
    }
  }).catch(() => {})
}
</script>

<style scoped lang="scss">
.user-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.user-header {
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
  display: flex;
  align-items: center;
  gap: 32px;
  
  .logo {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 20px;
    font-weight: 600;
    color: #303133;
    
    .el-icon {
      font-size: 24px;
      color: #409eff;
    }
  }
  
  .header-menu {
    border: none;
    background: transparent;
    
    :deep(.el-menu-item) {
      height: 64px;
      line-height: 64px;
      border-bottom: 2px solid transparent;
      
      &:hover {
        background: transparent;
        border-bottom-color: #409eff;
      }
      
      &.is-active {
        border-bottom-color: #409eff;
        color: #409eff;
      }
    }
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
      color: #fff;
      font-weight: 600;
    }
    
    .username {
      font-weight: 500;
      color: #303133;
    }
  }
}

.user-content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
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

