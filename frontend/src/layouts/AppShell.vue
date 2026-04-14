<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types/auth'

interface MenuItem {
  label: string
  routeName: string
  roles: UserRole[]
}

const menuItems: MenuItem[] = [
  { label: 'Dashboard', routeName: 'dashboard', roles: ['student', 'teacher', 'admin'] },
  {
    label: '智能问答工作台',
    routeName: 'qa-workbench',
    roles: ['student', 'teacher', 'admin'],
  },
  { label: '教师审核台', routeName: 'teacher-review', roles: ['teacher', 'admin'] },
  { label: '系统管理', routeName: 'admin-system', roles: ['admin'] },
  { label: '个人中心', routeName: 'profile', roles: ['student', 'teacher', 'admin'] },
]

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const visibleMenuItems = computed(() => menuItems.filter((item) => authStore.canAccess(item.roles)))
const roleLabel = computed(() => authStore.user?.role ?? 'guest')

function navigate(routeName: string): void {
  router.push({ name: routeName })
}

function logout(): void {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="shell">
    <aside class="sidebar">
      <h1 class="brand">
        EduAgent
      </h1>
      <p class="subtitle">
        Frontend Scaffold
      </p>
      <nav class="menu">
        <button
          v-for="item in visibleMenuItems"
          :key="item.routeName"
          class="menu-item"
          :class="{ active: route.name === item.routeName }"
          @click="navigate(item.routeName)"
        >
          {{ item.label }}
        </button>
      </nav>
    </aside>

    <main class="content">
      <header class="topbar">
        <div>
          <h2>{{ route.meta.title }}</h2>
          <p>当前角色：{{ roleLabel }}</p>
        </div>
        <button
          class="danger"
          @click="logout"
        >
          退出登录
        </button>
      </header>
      <section class="page">
        <RouterView />
      </section>
    </main>
  </div>
</template>
