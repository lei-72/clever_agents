import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { UserProfile, UserRole } from '@/types/auth'

const TOKEN_KEY = 'eduagent_token'
const USER_KEY = 'eduagent_user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) ?? '')
  const user = ref<UserProfile | null>(readStoredUser())

  const isAuthenticated = computed(() => Boolean(token.value))

  function login(payload: UserProfile, accessToken: string): void {
    user.value = payload
    token.value = accessToken
    localStorage.setItem(TOKEN_KEY, accessToken)
    localStorage.setItem(USER_KEY, JSON.stringify(payload))
  }

  function logout(): void {
    user.value = null
    token.value = ''
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  function canAccess(roles: UserRole[]): boolean {
    if (!roles.length) {
      return true
    }

    return user.value !== null && roles.includes(user.value.role)
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    logout,
    canAccess,
  }
})

function readStoredUser(): UserProfile | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) {
    return null
  }

  try {
    return JSON.parse(raw) as UserProfile
  } catch {
    localStorage.removeItem(USER_KEY)
    return null
  }
}
