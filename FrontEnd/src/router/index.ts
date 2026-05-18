import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import EvaluationView from '../views/EvaluationView.vue'
import LoginView from '../views/LoginView.vue'
import UserLayout from '../layouts/UserLayout.vue'
import AdminLayout from '../layouts/AdminLayout.vue'
import DashboardView from '../views/admin/DashboardView.vue'
import UserManagementView from '../views/admin/UserManagementView.vue'
import ApiKeyManagementView from '../views/admin/ApiKeyManagementView.vue'
import EvaluationConfigView from '../views/admin/EvaluationConfigView.vue'
import { useUserStore } from '../stores/user'

// 定义路由类型
const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: UserLayout,
    meta: { requiresAuth: true, requiresUser: true },
    children: [
      {
        path: '',
        name: 'evaluation',
        component: EvaluationView,
        meta: { requiresAuth: true, requiresUser: true }
      },
      {
        path: 'history',
        name: 'history',
        component: () => import('../views/user/HistoryView.vue'),
        meta: { requiresAuth: true, requiresUser: true }
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('../views/user/SettingsView.vue'),
        meta: { requiresAuth: true, requiresUser: true }
      }
    ]
  },
  {
    path: '/admin',
    component: AdminLayout,
    meta: { requiresAuth: true, requiresAdmin: true },
    redirect: '/admin/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'admin-dashboard',
        component: DashboardView,
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'users',
        name: 'admin-users',
        component: UserManagementView,
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'apikeys',
        name: 'admin-apikeys',
        component: ApiKeyManagementView,
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'config',
        name: 'admin-config',
        component: EvaluationConfigView,
        meta: { requiresAuth: true, requiresAdmin: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫：检查登录状态和角色
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  
  // 如果路由需要认证
  if (to.meta.requiresAuth) {
    if (userStore.isLoggedIn) {
      const userRole = userStore.user?.role
      
      // 检查是否需要管理员权限
      if (to.meta.requiresAdmin) {
        if (userRole === 'admin') {
          next()
        } else {
          // 非管理员，跳转到评估页面
          next('/')
        }
        return
      }
      
      // 检查管理员路由的子路由
      if (to.path.startsWith('/admin')) {
        if (userRole === 'admin') {
          next()
        } else {
          next('/')
        }
        return
      }
      
      // 检查是否需要普通用户权限（评估页面）
      if (to.meta.requiresUser) {
        if (userRole === 'user') {
          next()
        } else if (userRole === 'admin') {
          // 管理员不能访问评估页面，跳转到管理员页面
          next('/admin')
        } else {
          next({ name: 'login', query: { redirect: to.fullPath } })
        }
        return
      }
      
      // 其他需要认证的页面
      next()
    } else {
      // 未登录，跳转到登录页
      next({ name: 'login', query: { redirect: to.fullPath } })
    }
  } else {
    // 登录页面，如果已登录则根据角色跳转
    if (to.name === 'login' && userStore.isLoggedIn) {
      const userRole = userStore.user?.role
      if (userRole === 'admin') {
        next('/admin')
      } else {
        next('/')
      }
    } else {
      next()
    }
  }
})

export default router