import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '工作台', icon: 'Monitor' },
      },
      {
        path: 'qa',
        name: 'QA',
        component: () => import('@/views/QA.vue'),
        meta: { title: '智能问答', icon: 'ChatDotRound' },
      },
      {
        path: 'grading',
        name: 'Grading',
        component: () => import('@/views/Grading.vue'),
        meta: { title: '试卷批改', icon: 'EditPen' },
      },
      {
        path: 'resume',
        name: 'Resume',
        component: () => import('@/views/Resume.vue'),
        meta: { title: '简历审查', icon: 'Document' },
      },
      {
        path: 'interview',
        name: 'Interview',
        component: () => import('@/views/Interview.vue'),
        meta: { title: '模拟面试', icon: 'Microphone' },
      },
      {
        path: 'system',
        name: 'System',
        component: () => import('@/views/System.vue'),
        meta: { title: '系统状态', icon: 'Setting', roles: ['admin'] },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const user = JSON.parse(localStorage.getItem('user') || 'null')
  const role = user?.role || ''
  if (!to.meta.public && !token) {
    next('/login')
  } else if (to.meta.roles && !to.meta.roles.includes(role)) {
    next('/dashboard')
  } else if (to.path === '/login' && token) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
