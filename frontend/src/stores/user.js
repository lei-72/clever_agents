import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

  const isLoggedIn = computed(() => !!token.value)
  const role = computed(() => user.value?.role || '')
  const username = computed(() => user.value?.username || '')

  async function login(username, password) {
    const res = await authApi.login({ username, password })
    token.value = res.access_token
    user.value = { username, role: res.role }
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('user', JSON.stringify({ username, role: res.role }))
    return res
  }

  async function register(username, password, role) {
    const res = await authApi.register({ username, password, role })
    token.value = res.access_token
    user.value = { username, role: res.role }
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('user', JSON.stringify({ username, role: res.role }))
    return res
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return { token, user, isLoggedIn, role, username, login, register, logout }
})
