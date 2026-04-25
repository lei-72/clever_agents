<template>
  <el-container class="main-layout">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
      <div class="logo" @click="$router.push('/dashboard')">
        <el-icon :size="28" color="#fff"><Monitor /></el-icon>
        <span v-show="!isCollapse" class="logo-text">clever_agents</span>
      </div>
      <el-menu
        :default-active="currentRoute"
        router
        :collapse="isCollapse"
        background-color="#1d1e3a"
        text-color="#a8abb2"
        active-text-color="#409eff"
        class="sidebar-menu"
      >
        <el-menu-item v-for="item in visibleMenuItems" :key="item.path" :index="item.path">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>
      <div class="collapse-btn" @click="isCollapse = !isCollapse">
        <el-icon><Fold v-if="!isCollapse" /><Expand v-else /></el-icon>
      </div>
    </el-aside>

    <el-container>
      <el-header class="topbar">
        <div class="topbar-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-if="currentTitle">{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="topbar-right">
          <el-tag :type="roleTagType" size="small" class="role-tag">{{ roleLabel }}</el-tag>
          <el-dropdown trigger="click" @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="32" class="user-avatar">
                {{ userStore.username.charAt(0).toUpperCase() }}
              </el-avatar>
              <span class="username">{{ userStore.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>个人信息
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>

    <!-- 个人信息弹窗 -->
    <el-dialog
      v-model="showProfileDialog"
      title="个人信息"
      width="400px"
      custom-class="profile-dialog"
      append-to-body
    >
      <div class="profile-card">
        <div class="profile-header">
          <el-avatar :size="80" class="profile-avatar">
            {{ userStore.username.charAt(0).toUpperCase() }}
          </el-avatar>
          <div class="profile-title">{{ userStore.username }}</div>
          <el-tag :type="roleTagType" effect="dark" class="profile-role-tag">
            {{ roleLabel }}
          </el-tag>
        </div>
        <div class="profile-details">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="用户名">
              <div class="detail-item">
                <el-icon><User /></el-icon>
                <span>{{ userStore.username }}</span>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="账号角色">
              <div class="detail-item">
                <el-icon><Avatar /></el-icon>
                <span>{{ roleLabel }} ({{ userStore.role }})</span>
              </div>
            </el-descriptions-item>
            <el-descriptions-item label="账号状态">
              <div class="detail-item text-success">
                <el-icon><CircleCheck /></el-icon>
                <span>正常</span>
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showProfileDialog = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const isCollapse = ref(false)
const showProfileDialog = ref(false)

const menuItems = [
  { path: '/dashboard', title: '工作台', icon: 'Monitor' },
  { path: '/qa', title: '智能问答', icon: 'ChatDotRound' },
  { path: '/grading', title: '试卷批改', icon: 'EditPen' },
  { path: '/resume', title: '简历审查', icon: 'Document' },
  { path: '/interview', title: '模拟面试', icon: 'Microphone' },
  { path: '/system', title: '系统状态', icon: 'Setting', roles: ['admin'] },
]

const visibleMenuItems = computed(() =>
  menuItems.filter((item) => !item.roles || item.roles.includes(userStore.role))
)

const currentRoute = computed(() => route.path)
const currentTitle = computed(() => {
  const item = visibleMenuItems.value.find((m) => m.path === route.path)
  return item?.title || ''
})

const roleLabel = computed(() => {
  const map = { student: '学生', teacher: '教师', admin: '管理员' }
  return map[userStore.role] || userStore.role
})

const roleTagType = computed(() => {
  const map = { student: 'success', teacher: 'warning', admin: 'danger' }
  return map[userStore.role] || 'info'
})

function handleCommand(cmd) {
  if (cmd === 'logout') {
    userStore.logout()
    router.push('/login')
  } else if (cmd === 'profile') {
    showProfileDialog.value = true
  }
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.sidebar {
  background: #1d1e3a;
  display: flex;
  flex-direction: column;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.logo-text {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  white-space: nowrap;
}

.sidebar-menu {
  flex: 1;
  border-right: none !important;
  overflow-y: auto;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 220px;
}

.collapse-btn {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #a8abb2;
  cursor: pointer;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.collapse-btn:hover {
  color: #409eff;
}

.topbar {
  background: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
  padding: 0 20px;
  height: 56px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.user-avatar {
  background: linear-gradient(135deg, #409eff, #667eea);
  color: #fff;
  font-weight: 600;
}

.username {
  font-size: 14px;
  color: #606266;
}

.main-content {
  background: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}

.profile-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px 0;
}

.profile-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 24px;
}

.profile-avatar {
  background: linear-gradient(135deg, #409eff, #667eea);
  color: #fff;
  font-size: 32px;
  font-weight: 600;
  margin-bottom: 16px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.profile-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.profile-role-tag {
  border-radius: 12px;
  padding: 0 12px;
}

.profile-details {
  width: 100%;
}

.detail-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.text-success {
  color: #67c23a;
}
</style>
