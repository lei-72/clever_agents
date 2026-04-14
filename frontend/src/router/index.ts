import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { routes } from './routes'

export const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return {
      name: 'login',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  if (to.meta.roles && !authStore.canAccess(to.meta.roles)) {
    return {
      name: 'dashboard',
    }
  }

  if (to.name === 'login' && authStore.isAuthenticated) {
    return {
      name: 'dashboard',
    }
  }

  return true
})
