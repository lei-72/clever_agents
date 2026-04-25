<template>
  <div class="min-h-screen grid lg:grid-cols-2 w-full font-sans bg-background text-foreground">
    <!-- Left Content Section -->
    <div class="relative hidden lg:flex flex-col justify-between bg-zinc-200 p-12 text-zinc-800 overflow-hidden">
      <div class="relative z-20">
        <div class="flex items-center gap-2 text-lg font-semibold">
          <div class="w-8 h-8 rounded-lg bg-zinc-800/10 backdrop-blur-sm flex items-center justify-center">
            <Sparkles class="w-4 h-4" />
          </div>
          <span>CleverAgents</span>
        </div>
      </div>

      <div class="relative z-20 flex items-end justify-center h-[500px]">
        <!-- Cartoon Characters -->
        <div class="relative" style="width: 550px; height: 400px;">
          <!-- Purple tall rectangle character - Back layer -->
          <div 
            ref="purpleRef"
            class="absolute bottom-0 transition-all duration-700 ease-in-out"
            :style="{
              left: '70px',
              width: '180px',
              height: (isTyping || (loginForm.password.length > 0 && !showPassword)) ? '440px' : '400px',
              backgroundColor: '#6C3FF5',
              borderRadius: '10px 10px 0 0',
              zIndex: 1,
              transform: (loginForm.password.length > 0 && showPassword)
                ? `skewX(0deg)`
                : (isTyping || (loginForm.password.length > 0 && !showPassword))
                  ? `skewX(${(purplePos.bodySkew || 0) - 12}deg) translateX(40px)` 
                  : `skewX(${purplePos.bodySkew || 0}deg)`,
              transformOrigin: 'bottom center',
            }"
          >
            <!-- Eyes -->
            <div 
              class="absolute flex gap-8 transition-all duration-700 ease-in-out"
              :style="{
                left: (loginForm.password.length > 0 && showPassword) ? `${20}px` : isLookingAtEachOther ? `${55}px` : `${45 + purplePos.faceX}px`,
                top: (loginForm.password.length > 0 && showPassword) ? `${35}px` : isLookingAtEachOther ? `${65}px` : `${40 + purplePos.faceY}px`,
              }"
            >
              <EyeBall 
                :size="18" 
                :pupilSize="7" 
                :maxDistance="5" 
                eyeColor="white" 
                pupilColor="#2D2D2D" 
                :isBlinking="isPurpleBlinking || (isPasswordTyping && !showPassword)"
                :forceLookX="(loginForm.password.length > 0 && showPassword) ? (isPurplePeeking ? 4 : -4) : isLookingAtEachOther ? 3 : undefined"
                :forceLookY="(loginForm.password.length > 0 && showPassword) ? (isPurplePeeking ? 5 : -4) : isLookingAtEachOther ? 4 : undefined"
              />
              <EyeBall 
                :size="18" 
                :pupilSize="7" 
                :maxDistance="5" 
                eyeColor="white" 
                pupilColor="#2D2D2D" 
                :isBlinking="isPurpleBlinking || (isPasswordTyping && !showPassword)"
                :forceLookX="(loginForm.password.length > 0 && showPassword) ? (isPurplePeeking ? 4 : -4) : isLookingAtEachOther ? 3 : undefined"
                :forceLookY="(loginForm.password.length > 0 && showPassword) ? (isPurplePeeking ? 5 : -4) : isLookingAtEachOther ? 4 : undefined"
              />
            </div>
          </div>

          <!-- Black tall rectangle character - Middle layer -->
          <div 
            ref="blackRef"
            class="absolute bottom-0 transition-all duration-700 ease-in-out"
            :style="{
              left: '240px',
              width: '120px',
              height: '310px',
              backgroundColor: '#2D2D2D',
              borderRadius: '8px 8px 0 0',
              zIndex: 2,
              transform: (loginForm.password.length > 0 && showPassword)
                ? `skewX(0deg)`
                : isLookingAtEachOther
                  ? `skewX(${(blackPos.bodySkew || 0) * 1.5 + 10}deg) translateX(20px)`
                  : (isTyping || (loginForm.password.length > 0 && !showPassword))
                    ? `skewX(${(blackPos.bodySkew || 0) * 1.5}deg)` 
                    : `skewX(${blackPos.bodySkew || 0}deg)`,
              transformOrigin: 'bottom center',
            }"
          >
            <!-- Eyes -->
            <div 
              class="absolute flex gap-6 transition-all duration-700 ease-in-out"
              :style="{
                left: (loginForm.password.length > 0 && showPassword) ? `${10}px` : isLookingAtEachOther ? `${32}px` : `${26 + blackPos.faceX}px`,
                top: (loginForm.password.length > 0 && showPassword) ? `${28}px` : isLookingAtEachOther ? `${12}px` : `${32 + blackPos.faceY}px`,
              }"
            >
              <EyeBall 
                :size="16" 
                :pupilSize="6" 
                :maxDistance="4" 
                eyeColor="white" 
                pupilColor="#2D2D2D" 
                :isBlinking="isBlackBlinking || (isPasswordTyping && !showPassword)"
                :forceLookX="(loginForm.password.length > 0 && showPassword) ? -4 : isLookingAtEachOther ? 0 : undefined"
                :forceLookY="(loginForm.password.length > 0 && showPassword) ? -4 : isLookingAtEachOther ? -4 : undefined"
              />
              <EyeBall 
                :size="16" 
                :pupilSize="6" 
                :maxDistance="4" 
                eyeColor="white" 
                pupilColor="#2D2D2D" 
                :isBlinking="isBlackBlinking || (isPasswordTyping && !showPassword)"
                :forceLookX="(loginForm.password.length > 0 && showPassword) ? -4 : isLookingAtEachOther ? 0 : undefined"
                :forceLookY="(loginForm.password.length > 0 && showPassword) ? -4 : isLookingAtEachOther ? -4 : undefined"
              />
            </div>
          </div>

          <!-- Orange semi-circle character - Front left -->
          <div 
            ref="orangeRef"
            class="absolute bottom-0 transition-all duration-700 ease-in-out"
            :style="{
              left: '0px',
              width: '240px',
              height: '200px',
              zIndex: 3,
              backgroundColor: '#FF9B6B',
              borderRadius: '120px 120px 0 0',
              transform: (loginForm.password.length > 0 && showPassword) ? `skewX(0deg)` : `skewX(${orangePos.bodySkew || 0}deg)`,
              transformOrigin: 'bottom center',
            }"
          >
            <!-- Eyes - just pupils, no white -->
            <div 
              class="absolute flex gap-8 transition-all duration-200 ease-out"
              :style="{
                left: (loginForm.password.length > 0 && showPassword) ? `${50}px` : `${82 + (orangePos.faceX || 0)}px`,
                top: (loginForm.password.length > 0 && showPassword) ? `${85}px` : `${90 + (orangePos.faceY || 0)}px`,
              }"
            >
              <Pupil :size="12" :maxDistance="5" pupilColor="#2D2D2D" :isBlinking="isPasswordTyping && !showPassword" :forceLookX="(loginForm.password.length > 0 && showPassword) ? -5 : undefined" :forceLookY="(loginForm.password.length > 0 && showPassword) ? -4 : undefined" />
              <Pupil :size="12" :maxDistance="5" pupilColor="#2D2D2D" :isBlinking="isPasswordTyping && !showPassword" :forceLookX="(loginForm.password.length > 0 && showPassword) ? -5 : undefined" :forceLookY="(loginForm.password.length > 0 && showPassword) ? -4 : undefined" />
            </div>
          </div>

          <!-- Yellow tall rectangle character - Front right -->
          <div 
            ref="yellowRef"
            class="absolute bottom-0 transition-all duration-700 ease-in-out"
            :style="{
              left: '310px',
              width: '140px',
              height: '230px',
              backgroundColor: '#E8D754',
              borderRadius: '70px 70px 0 0',
              zIndex: 4,
              transform: (loginForm.password.length > 0 && showPassword) ? `skewX(0deg)` : `skewX(${yellowPos.bodySkew || 0}deg)`,
              transformOrigin: 'bottom center',
            }"
          >
            <!-- Eyes - just pupils, no white -->
            <div 
              class="absolute flex gap-6 transition-all duration-200 ease-out"
              :style="{
                left: (loginForm.password.length > 0 && showPassword) ? `${20}px` : `${52 + (yellowPos.faceX || 0)}px`,
                top: (loginForm.password.length > 0 && showPassword) ? `${35}px` : `${40 + (yellowPos.faceY || 0)}px`,
              }"
            >
              <Pupil :size="12" :maxDistance="5" pupilColor="#2D2D2D" :isBlinking="isPasswordTyping && !showPassword" :forceLookX="(loginForm.password.length > 0 && showPassword) ? -5 : undefined" :forceLookY="(loginForm.password.length > 0 && showPassword) ? -4 : undefined" />
              <Pupil :size="12" :maxDistance="5" pupilColor="#2D2D2D" :isBlinking="isPasswordTyping && !showPassword" :forceLookX="(loginForm.password.length > 0 && showPassword) ? -5 : undefined" :forceLookY="(loginForm.password.length > 0 && showPassword) ? -4 : undefined" />
            </div>
            <!-- Horizontal line for mouth -->
            <div 
              class="absolute w-20 h-[4px] bg-[#2D2D2D] rounded-full transition-all duration-200 ease-out"
              :style="{
                left: (loginForm.password.length > 0 && showPassword) ? `${10}px` : `${40 + (yellowPos.faceX || 0)}px`,
                top: (loginForm.password.length > 0 && showPassword) ? `${88}px` : `${88 + (yellowPos.faceY || 0)}px`,
              }"
            />
          </div>
        </div>
      </div>

      <div class="relative z-20 flex items-center gap-8 text-sm text-zinc-500">
        <a href="#" class="hover:text-zinc-900 transition-colors">隐私政策</a>
        <a href="#" class="hover:text-zinc-900 transition-colors">服务条款</a>
        <a href="#" class="hover:text-zinc-900 transition-colors">联系我们</a>
      </div>

      <!-- Decorative elements -->
      <div class="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMCIgaGVpZ2h0PSIyMCI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiIGZpbGw9InJnYmEoMCwwLDAsMC4wNSkiLz48L3N2Zz4=')] bg-[size:20px_20px]" />
      <div class="absolute top-1/4 right-1/4 w-64 h-64 bg-zinc-400/20 rounded-full blur-3xl" />
      <div class="absolute bottom-1/4 left-1/4 w-96 h-96 bg-zinc-300/30 rounded-full blur-3xl" />
    </div>

    <!-- Right Login Section -->
    <div class="dark flex items-center justify-center p-8 bg-background text-foreground relative z-10">
      <div class="w-full max-w-[420px]">
        <!-- Mobile Logo -->
        <div class="lg:hidden flex items-center justify-center gap-2 text-lg font-semibold mb-12">
          <div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
            <Sparkles class="w-4 h-4 text-primary" />
          </div>
          <span>CleverAgents</span>
        </div>

        <!-- Header -->
        <div class="text-center mb-10">
          <h1 class="text-3xl font-bold tracking-tight mb-2">{{ isRegister ? '创建账号' : '欢迎回来！' }}</h1>
          <p class="text-muted-foreground text-sm">请输入您的详细信息</p>
        </div>

        <!-- Login / Register Form -->
        <form @submit.prevent="isRegister ? handleRegister() : handleLogin()" class="space-y-5">
          <div class="space-y-2">
            <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
              用户名
            </label>
            <input
              type="text"
              v-model="(isRegister ? registerForm : loginForm).username"
              :placeholder="isRegister ? '用户名（最少3个字符）' : '邮箱或手机号'"
              @focus="setIsTyping(true)"
              @blur="setIsTyping(false)"
              required
              class="flex h-12 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 border-border/60 focus:border-primary"
            />
          </div>

          <div class="space-y-2">
            <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
              密码
            </label>
            <div class="relative">
              <input
                :type="showPassword ? 'text' : 'password'"
                v-model="(isRegister ? registerForm : loginForm).password"
                :placeholder="isRegister ? '密码（最少6个字符）' : '••••••••'"
                @focus="isPasswordTyping = true"
                @blur="isPasswordTyping = false"
                required
                class="flex h-12 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 pr-10 border-border/60 focus:border-primary"
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
              >
                <EyeOff v-if="showPassword" class="w-5 h-5" />
                <Eye v-else class="w-5 h-5" />
              </button>
            </div>
          </div>

          <div v-if="isRegister" class="space-y-2">
            <label class="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">
              角色
            </label>
            <select
              v-model="registerForm.role"
              required
              class="flex h-12 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 border-border/60 focus:border-primary"
            >
              <option value="student">学生</option>
              <option value="teacher">教师</option>
              <option value="admin">管理员</option>
            </select>
          </div>

          <div v-if="!isRegister" class="flex items-center justify-between">
            <div class="flex items-center space-x-2">
              <input type="checkbox" id="remember" class="w-4 h-4 rounded-sm border border-primary text-primary focus:ring-primary" />
              <label for="remember" class="text-sm font-normal cursor-pointer">
                记住我 30 天
              </label>
            </div>
            <a href="#" class="text-sm text-primary hover:underline font-medium">
              忘记密码？
            </a>
          </div>

          <button 
            type="submit" 
            class="inline-flex items-center justify-center whitespace-nowrap rounded-md ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-white text-black hover:bg-zinc-200 w-full h-12 text-lg font-bold"
            :disabled="loading"
          >
            {{ loading ? (isRegister ? "注册中..." : "登录中...") : (isRegister ? "注册" : "登录") }}
          </button>
        </form>

        <!-- Demo Accounts (Social Login replacement) -->
        <div class="mt-6" v-if="!isRegister">
          <div class="grid grid-cols-2 gap-3">
            <button 
              @click="fillDemo(demoAccounts[0])"
              class="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-12 border-border/60"
              type="button"
            >
              学生演示账号
            </button>
            <button 
              @click="fillDemo(demoAccounts[1])"
              class="inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-12 border-border/60"
              type="button"
            >
              教师演示账号
            </button>
          </div>
        </div>

        <!-- Toggle Mode -->
        <div class="text-center text-sm text-muted-foreground mt-8">
          {{ isRegister ? "已有账号？" : "还没有账号？" }}
          <a href="#" @click.prevent="toggleMode" class="text-foreground font-medium hover:underline ml-1">
            {{ isRegister ? "登录" : "注册" }}
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { Sparkles, Eye, EyeOff, Mail } from 'lucide-vue-next'
import Pupil from '@/components/Pupil.vue'
import EyeBall from '@/components/EyeBall.vue'

const router = useRouter()
const userStore = useUserStore()

// State
const loading = ref(false)
const isRegister = ref(false)
const showPassword = ref(false)

// Form State
const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', password: '', role: 'student' })

// Demo Accounts
const demoAccounts = [
  { username: 'student_demo', password: 'student123', label: '学生', type: 'success' },
  { username: 'teacher_demo', password: 'teacher123', label: '教师', type: 'warning' },
  { username: 'admin_demo', password: 'admin123', label: '管理员', type: 'danger' },
]

function fillDemo(acc) {
  loginForm.username = acc.username
  loginForm.password = acc.password
}

function toggleMode() {
  isRegister.value = !isRegister.value
  if (isRegister.value) {
    registerForm.username = ''
    registerForm.password = ''
    registerForm.role = 'student'
  } else {
    loginForm.username = ''
    loginForm.password = ''
  }
}

// Animation State
const mouseX = ref(0)
const mouseY = ref(0)
const isTyping = ref(false)
const isPasswordTyping = ref(false)
const isLookingAtEachOther = ref(false)
const isPurpleBlinking = ref(false)
const isBlackBlinking = ref(false)
const isPurplePeeking = ref(false)

const purpleRef = ref(null)
const blackRef = ref(null)
const yellowRef = ref(null)
const orangeRef = ref(null)

const setIsTyping = (val) => {
  isTyping.value = val
}

const handleMouseMove = (e) => {
  mouseX.value = e.clientX
  mouseY.value = e.clientY
}

onMounted(() => {
  window.addEventListener("mousemove", handleMouseMove)
})
onUnmounted(() => {
  window.removeEventListener("mousemove", handleMouseMove)
})

// Purple Blinking
onMounted(() => {
  let timeout
  const scheduleBlink = () => {
    timeout = setTimeout(() => {
      isPurpleBlinking.value = true
      setTimeout(() => {
        isPurpleBlinking.value = false
        scheduleBlink()
      }, 150)
    }, Math.random() * 4000 + 3000)
  }
  scheduleBlink()
  return () => clearTimeout(timeout)
})

// Black Blinking
onMounted(() => {
  let timeout
  const scheduleBlink = () => {
    timeout = setTimeout(() => {
      isBlackBlinking.value = true
      setTimeout(() => {
        isBlackBlinking.value = false
        scheduleBlink()
      }, 150)
    }, Math.random() * 4000 + 3000)
  }
  scheduleBlink()
  return () => clearTimeout(timeout)
})

// Looking at each other
watch(isTyping, (newVal) => {
  if (newVal) {
    isLookingAtEachOther.value = true
    setTimeout(() => {
      isLookingAtEachOther.value = false
    }, 800)
  } else {
    isLookingAtEachOther.value = false
  }
})

// Peeking
watch([() => loginForm.password, showPassword], ([pwd, showPwd]) => {
  if (pwd.length > 0 && showPwd) {
    let peekInterval = setTimeout(() => {
      isPurplePeeking.value = true
      setTimeout(() => {
        isPurplePeeking.value = false
      }, 800)
    }, Math.random() * 3000 + 2000)
    return () => clearTimeout(peekInterval)
  } else {
    isPurplePeeking.value = false
  }
})

const calculatePosition = (refObj) => {
  if (!refObj) return { faceX: 0, faceY: 0, bodySkew: 0 }
  
  const rect = refObj.getBoundingClientRect()
  if (rect.width === 0 && rect.height === 0) return { faceX: 0, faceY: 0, bodySkew: 0 }
  
  const centerX = rect.left + rect.width / 2
  const centerY = rect.top + rect.height / 3

  const deltaX = mouseX.value - centerX
  const deltaY = mouseY.value - centerY

  const faceX = Math.max(-15, Math.min(15, deltaX / 20))
  const faceY = Math.max(-10, Math.min(10, deltaY / 30))
  const bodySkew = Math.max(-6, Math.min(6, -deltaX / 120))

  return { faceX, faceY, bodySkew }
}

const purplePos = computed(() => calculatePosition(purpleRef.value))
const blackPos = computed(() => calculatePosition(blackRef.value))
const yellowPos = computed(() => calculatePosition(yellowRef.value))
const orangePos = computed(() => calculatePosition(orangeRef.value))

// Handlers
async function handleLogin() {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.error('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await userStore.login(loginForm.username, loginForm.password)
    ElMessage.success({ message: '欢迎回来！', duration: 2000 })
    router.push('/dashboard')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '凭证无效，请重试。')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!registerForm.username || !registerForm.password || !registerForm.role) {
    ElMessage.error('请填写所有字段')
    return
  }
  if (registerForm.username.length < 3 || registerForm.password.length < 6) {
    ElMessage.error('用户名至少3个字符，密码至少6个字符')
    return
  }
  loading.value = true
  try {
    await userStore.register(registerForm.username, registerForm.password, registerForm.role)
    ElMessage.success({ message: '注册成功！已登录。', duration: 2000 })
    router.push('/dashboard')
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '注册失败。')
  } finally {
    loading.value = false
  }
}
</script>