<template>
  <div class="system-page">
    <div class="page-header">
      <h2><el-icon><Setting /></el-icon> 系统状态</h2>
      <el-button type="primary" @click="fetchAll" :loading="loading">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </div>

    <el-row :gutter="20">
      <el-col :span="8">
        <el-card shadow="hover" :class="['status-card', healthOk ? 'ok' : 'error']">
          <div class="status-icon">
            <el-icon :size="40" :color="healthOk ? '#67c23a' : '#f56c6c'">
              <CircleCheckFilled v-if="healthOk" /><CircleCloseFilled v-else />
            </el-icon>
          </div>
          <h3>服务状态</h3>
          <p v-if="health">{{ health.status }} - {{ health.service }}</p>
          <p v-else class="error-text">{{ healthError || '加载中...' }}</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" :class="['status-card', readyOk ? 'ok' : 'error']">
          <div class="status-icon">
            <el-icon :size="40" :color="readyOk ? '#67c23a' : '#f56c6c'">
              <CircleCheckFilled v-if="readyOk" /><CircleCloseFilled v-else />
            </el-icon>
          </div>
          <h3>就绪状态</h3>
          <p v-if="ready">{{ ready.message }}</p>
          <p v-else class="error-text">{{ readyError || '加载中...' }}</p>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover" :class="['status-card', llmConfigured ? 'ok' : 'warn']">
          <div class="status-icon">
            <el-icon :size="40" :color="llmConfigured ? '#67c23a' : '#e6a23c'">
              <CircleCheckFilled v-if="llmConfigured" /><WarningFilled v-else />
            </el-icon>
          </div>
          <h3>LLM 状态</h3>
          <p v-if="llm">{{ llm.configured ? '已配置' : '未配置 API Key' }}</p>
          <p v-else class="error-text">{{ llmError || '加载中...' }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="12">
        <el-card shadow="hover" v-if="health">
          <template #header><span class="card-title">服务信息</span></template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="服务名称">{{ health.service }}</el-descriptions-item>
            <el-descriptions-item label="版本">{{ health.version }}</el-descriptions-item>
            <el-descriptions-item label="环境">
              <el-tag :type="health.environment === 'prod' ? 'danger' : 'success'" size="small">
                {{ health.environment }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag type="success" size="small">{{ health.status }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover" v-if="llm">
          <template #header><span class="card-title">LLM 配置</span></template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="API 配置">
              <el-tag :type="llm.configured ? 'success' : 'warning'" size="small">
                {{ llm.configured ? '已配置' : '未配置' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Base URL">{{ llm.base_url }}</el-descriptions-item>
            <el-descriptions-item label="Chat 模型">{{ llm.chat_model }}</el-descriptions-item>
            <el-descriptions-item label="Embedding 模型">{{ llm.embedding_model }}</el-descriptions-item>
            <el-descriptions-item label="超时时间">{{ llm.timeout_seconds }}s</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="hover" style="margin-top: 20px">
      <template #header><span class="card-title">API 端点列表</span></template>
      <el-table :data="endpoints" stripe size="small">
        <el-table-column prop="method" label="方法" width="80">
          <template #default="{ row }">
            <el-tag :type="methodColor(row.method)" size="small">{{ row.method }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="路径" />
        <el-table-column prop="description" label="说明" />
        <el-table-column prop="module" label="模块" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.module }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { systemApi } from '@/api'

const loading = ref(false)
const health = ref(null)
const ready = ref(null)
const llm = ref(null)
const healthError = ref('')
const readyError = ref('')
const llmError = ref('')

const healthOk = computed(() => health.value?.status === 'ok')
const readyOk = computed(() => !!ready.value?.message)
const llmConfigured = computed(() => llm.value?.configured)

const endpoints = [
  { method: 'GET', path: '/api/v1/system/health', description: '服务存活检查', module: 'System' },
  { method: 'GET', path: '/api/v1/system/ready', description: '就绪检查', module: 'System' },
  { method: 'GET', path: '/api/v1/system/llm', description: 'LLM 配置状态', module: 'System' },
  { method: 'POST', path: '/api/v1/auth/login', description: '用户登录', module: 'Auth' },
  { method: 'GET', path: '/api/v1/rbac/me', description: '获取当前用户', module: 'RBAC' },
  { method: 'POST', path: '/api/v1/qa/ask', description: '智能问答', module: 'QA' },
  { method: 'POST', path: '/api/v1/qa/ingest', description: '知识入库', module: 'QA' },
  { method: 'POST', path: '/api/v1/qa/ingest-file', description: '文件解析入库', module: 'QA' },
  { method: 'POST', path: '/api/v1/grading/grade', description: '试卷批改', module: 'Grading' },
  { method: 'POST', path: '/api/v1/grading/review-publish', description: '教师审核发布', module: 'Grading' },
  { method: 'POST', path: '/api/v1/resume/review', description: '简历评审', module: 'Resume' },
  { method: 'POST', path: '/api/v1/interview/start', description: '启动面试会话', module: 'Interview' },
  { method: 'POST', path: '/api/v1/interview/{id}/answer', description: '提交答案', module: 'Interview' },
  { method: 'GET', path: '/api/v1/interview/{id}', description: '查询会话', module: 'Interview' },
  { method: 'POST', path: '/api/v1/interview/{id}/report/generate', description: '生成报告', module: 'Interview' },
  { method: 'POST', path: '/api/v1/orchestrator/route', description: '路由决策', module: 'Orch' },
  { method: 'POST', path: '/api/v1/orchestrator/stream', description: '流式路由', module: 'Orch' },
  { method: 'POST', path: '/api/v1/orchestrator/execute', description: '单 Agent 执行', module: 'Orch' },
  { method: 'POST', path: '/api/v1/orchestrator/pipeline/execute', description: '流水线执行', module: 'Orch' },
]

function methodColor(m) {
  return { GET: 'success', POST: 'primary', PUT: 'warning', DELETE: 'danger' }[m] || 'info'
}

async function fetchAll() {
  loading.value = true
  const tasks = [
    systemApi.health().then(r => { health.value = r; healthError.value = '' }).catch(e => { healthError.value = '连接失败' }),
    systemApi.ready().then(r => { ready.value = r; readyError.value = '' }).catch(e => { readyError.value = '连接失败' }),
    systemApi.llm().then(r => { llm.value = r; llmError.value = '' }).catch(e => { llmError.value = '连接失败' }),
  ]
  await Promise.allSettled(tasks)
  loading.value = false
}

onMounted(fetchAll)
</script>

<style scoped>
.card-title { font-weight: 600; }

.status-card {
  text-align: center;
  padding: 20px 0;
  border-radius: 12px;
  transition: all 0.3s;
}

.status-card.ok {
  border-top: 3px solid #67c23a;
}

.status-card.error {
  border-top: 3px solid #f56c6c;
}

.status-card.warn {
  border-top: 3px solid #e6a23c;
}

.status-icon {
  margin-bottom: 12px;
}

.status-card h3 {
  font-size: 16px;
  margin-bottom: 8px;
}

.status-card p {
  font-size: 13px;
  color: #606266;
}

.error-text {
  color: #f56c6c !important;
}
</style>
