<script setup lang="ts">
import { reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/types/auth'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const form = reactive({
  name: '',
  role: 'student' as UserRole,
})

function login(): void {
  if (!form.name.trim()) {
    return
  }

  authStore.login(
    {
      id: `${Date.now()}-${Math.floor(Math.random() * 100000)}`,
      name: form.name.trim(),
      role: form.role,
    },
    'mock-token',
  )

  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/dashboard'
  router.push(redirect)
}
</script>

<template>
  <div class="card">
    <h2>EduAgent 登录</h2>
    <p>阶段0骨架使用本地 mock 登录，后续阶段接入真实鉴权。</p>
    <div class="form-group">
      <label for="name">用户名</label>
      <input
        id="name"
        v-model="form.name"
        placeholder="请输入用户名"
      >
    </div>
    <div class="form-group">
      <label for="role">角色</label>
      <select
        id="role"
        v-model="form.role"
      >
        <option value="student">
          student
        </option>
        <option value="teacher">
          teacher
        </option>
        <option value="admin">
          admin
        </option>
      </select>
    </div>
    <button @click="login">
      进入系统
    </button>
  </div>
</template>
