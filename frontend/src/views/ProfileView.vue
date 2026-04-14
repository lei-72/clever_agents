<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const user = computed(() => authStore.user)
</script>

<template>
  <div class="card">
    <h3>个人中心（占位）</h3>
    <p v-if="user">
      当前用户：{{ user.name }} / {{ user.role }}
    </p>
    <p v-else>
      尚未登录。
    </p>
  </div>
</template>
