import type { RouteRecordRaw } from 'vue-router'
import type { UserRole } from '@/types/auth'

export interface AppRouteMeta {
  title: string
  requiresAuth?: boolean
  roles?: UserRole[]
  hidden?: boolean
}

declare module 'vue-router' {
  interface RouteMeta {
    title: string
    requiresAuth?: boolean
    roles?: UserRole[]
    hidden?: boolean
  }
}

export const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: {
      title: '登录',
      hidden: true,
    },
  },
  {
    path: '/',
    component: () => import('@/layouts/AppShell.vue'),
    meta: {
      title: '工作台',
      requiresAuth: true,
    },
    children: [
      {
        path: '',
        redirect: '/dashboard',
      },
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: {
          title: 'Dashboard',
          requiresAuth: true,
        },
      },
      {
        path: 'qa-workbench',
        name: 'qa-workbench',
        component: () => import('@/views/AgentWorkbenchView.vue'),
        meta: {
          title: '智能问答工作台',
          requiresAuth: true,
          roles: ['student', 'teacher', 'admin'],
        },
      },
      {
        path: 'teacher/review',
        name: 'teacher-review',
        component: () => import('@/views/TeacherReviewView.vue'),
        meta: {
          title: '教师审核台',
          requiresAuth: true,
          roles: ['teacher', 'admin'],
        },
      },
      {
        path: 'admin/system',
        name: 'admin-system',
        component: () => import('@/views/AdminSystemView.vue'),
        meta: {
          title: '系统管理',
          requiresAuth: true,
          roles: ['admin'],
        },
      },
      {
        path: 'profile',
        name: 'profile',
        component: () => import('@/views/ProfileView.vue'),
        meta: {
          title: '个人中心',
          requiresAuth: true,
        },
      },
    ],
  },
]
