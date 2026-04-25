<template>
  <div class="qa-page">
    <div class="page-header">
      <h2><el-icon><ChatDotRound /></el-icon> 智能问答</h2>
      <el-button type="primary" @click="showUploadDialog = true">
        <el-icon><Upload /></el-icon> 上传知识文档
      </el-button>
    </div>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card shadow="hover" class="chat-card">
          <div class="chat-messages" ref="chatRef">
            <div v-if="messages.length === 0" class="empty-hint">
              <el-icon :size="48" color="#c0c4cc"><ChatDotRound /></el-icon>
              <p>输入你的问题，AI 将基于知识库为你智能解答</p>
            </div>
            <div v-for="(msg, i) in messages" :key="i" :class="['message', msg.role]">
              <div class="msg-avatar">
                <el-avatar :size="36" :class="msg.role">
                  {{ msg.role === 'user' ? 'U' : 'AI' }}
                </el-avatar>
              </div>
              <div class="msg-content">
                <div class="msg-text" :class="{ 'is-loading': msg.isLoading }">{{ msg.content }}</div>
                <div v-if="msg.sources && msg.sources.length" class="msg-sources">
                  <el-divider content-position="left">参考来源</el-divider>
                  <el-tag v-for="(s, j) in msg.sources" :key="j" size="small" type="info"
                    class="source-tag">
                    {{ s.title }} ({{ (s.score * 100).toFixed(0) }}%)
                  </el-tag>
                </div>
                <div v-if="msg.confidence !== undefined" class="msg-meta">
                  <el-tag size="small" :type="msg.confidence > 0.7 ? 'success' : 'warning'">
                    置信度: {{ (msg.confidence * 100).toFixed(0) }}%
                  </el-tag>
                  <el-tag v-if="msg.should_escalate" size="small" type="danger">需知识补充</el-tag>
                </div>
              </div>
            </div>
          </div>
          <div class="chat-input">
            <el-input v-model="query" placeholder="输入你的问题..." size="large"
              @keyup.enter="handleAsk" :disabled="loading">
              <template #append>
                <el-button type="primary" @click="handleAsk" :loading="loading">
                  <el-icon><Promotion /></el-icon>
                </el-button>
              </template>
            </el-input>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header><span class="card-title">使用说明</span></template>
          <div class="help-content">
            <h4>功能介绍</h4>
            <p>基于 RAG（检索增强生成）技术，从知识库中检索相关内容并生成精准回答。</p>
            <el-divider />
            <h4>支持的操作</h4>
            <ul>
              <li>直接输入问题进行智能问答</li>
              <li>上传 PDF / DOCX / TXT / MD 文档入库</li>
              <li>查看回答的引用来源和置信度</li>
            </ul>
            <el-divider />
            <h4>示例问题</h4>
            <div class="example-questions">
              <el-tag v-for="q in exampleQuestions" :key="q" class="example-tag"
                @click="query = q; handleAsk()" style="cursor: pointer">
                {{ q }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Upload Dialog -->
    <el-dialog v-model="showUploadDialog" title="上传知识文档" width="500px">
      <el-form :model="uploadForm" label-width="100px">
        <el-form-item label="文档 ID">
          <el-input v-model="uploadForm.document_id" placeholder="自定义文档标识" />
        </el-form-item>
        <el-form-item label="来源地址">
          <el-input v-model="uploadForm.source_uri" placeholder="可选，文档来源 URL" />
        </el-form-item>
        <el-form-item label="选择文件">
          <el-upload ref="uploadRef" :auto-upload="false" :limit="1" accept=".txt,.md,.pdf,.docx"
            :on-change="handleFileChange">
            <el-button type="primary"><el-icon><Upload /></el-icon> 选择文件</el-button>
            <template #tip>
              <div class="el-upload__tip">支持 txt / md / pdf / docx 格式</div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showUploadDialog = false">取消</el-button>
        <el-button type="primary" @click="handleUpload" :loading="uploading">上传并入库</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, reactive } from 'vue'
import { qaApi } from '@/api'
import { ElMessage } from 'element-plus'

const query = ref('')
const loading = ref(false)
const messages = ref([])
const chatRef = ref()
const qaSessionId = ref('')
const QA_STORAGE_KEY = 'qa_chat_state_v1'

const showUploadDialog = ref(false)
const uploading = ref(false)
const uploadForm = ref({ document_id: '', source_uri: '' })
const selectedFile = ref(null)

const exampleQuestions = ['什么是机器学习？', 'Python 有哪些数据类型？', '如何编写单元测试？']

function buildSessionId() {
  return 'web-' + Date.now() + '-' + Math.random().toString(36).slice(2, 8)
}

function persistChatState() {
  const payload = {
    session_id: qaSessionId.value,
    messages: messages.value,
  }
  localStorage.setItem(QA_STORAGE_KEY, JSON.stringify(payload))
}

function restoreChatState() {
  const raw = localStorage.getItem(QA_STORAGE_KEY)
  if (!raw) {
    qaSessionId.value = buildSessionId()
    return
  }
  try {
    const parsed = JSON.parse(raw)
    qaSessionId.value = parsed.session_id || buildSessionId()
    messages.value = Array.isArray(parsed.messages) ? parsed.messages : []
  } catch {
    qaSessionId.value = buildSessionId()
    messages.value = []
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight
  })
}

async function handleAsk() {
  if (!query.value.trim() || loading.value) return
  const q = query.value.trim()
  messages.value.push({ role: 'user', content: q })
  persistChatState()
  query.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const assistantMsg = reactive({
      role: 'assistant',
      content: '正在连接...',
      isLoading: true,
      confidence: undefined,
      should_escalate: false,
      sources: [],
    })
    messages.value.push(assistantMsg)
    persistChatState()
    scrollToBottom()

    await qaApi.askStream(
      {
        query: q,
        session_id: qaSessionId.value,
      },
      {
        onProgress: (text) => {
          if (assistantMsg.isLoading) assistantMsg.content = text
        },
        onDelta: (chunk) => {
          if (!chunk) return
          if (assistantMsg.isLoading) {
            assistantMsg.content = ''
            assistantMsg.isLoading = false
          }
          assistantMsg.content += chunk
          persistChatState()
          scrollToBottom()
        },
        onMeta: (meta) => {
          assistantMsg.confidence = meta.confidence
          assistantMsg.should_escalate = meta.should_escalate
          assistantMsg.sources = meta.sources || []
          persistChatState()
        },
        onError: (message) => {
          assistantMsg.content = message || '抱歉，流式请求失败，请稍后重试。'
          assistantMsg.isLoading = false
          persistChatState()
        },
      }
    )
  } catch (e) {
    const last = messages.value[messages.value.length - 1]
    if (last?.role === 'assistant') {
      last.content = '抱歉，请求出现错误，请稍后再试。'
      last.isLoading = false
    } else {
      messages.value.push({
        role: 'assistant',
        content: '抱歉，请求出现错误，请稍后再试。',
      })
    }
    persistChatState()
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function handleFileChange(file) {
  selectedFile.value = file.raw
}

async function handleUpload() {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  if (!uploadForm.value.document_id) {
    uploadForm.value.document_id = 'doc-' + Date.now()
  }
  uploading.value = true
  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('document_id', uploadForm.value.document_id)
    if (uploadForm.value.source_uri) {
      formData.append('source_uri', uploadForm.value.source_uri)
    }
    const res = await qaApi.ingestFile(formData)
    ElMessage.success(`文档入库成功，共 ${res.chunk_count} 个分块`)
    showUploadDialog.value = false
    uploadForm.value = { document_id: '', source_uri: '' }
    selectedFile.value = null
  } catch (e) {
    // handled by interceptor
  } finally {
    uploading.value = false
  }
}

onMounted(() => {
  restoreChatState()
  scrollToBottom()
})
</script>

<style scoped>
.chat-card {
  height: calc(100vh - 180px);
  display: flex;
  flex-direction: column;
}

.chat-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #c0c4cc;
  gap: 12px;
}

.message {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.message.user { flex-direction: row-reverse; }

.msg-avatar .el-avatar.user {
  background: linear-gradient(135deg, #409eff, #667eea);
  color: #fff;
}

.msg-avatar .el-avatar.assistant {
  background: linear-gradient(135deg, #67c23a, #95d475);
  color: #fff;
}

.msg-content {
  max-width: 70%;
}

.msg-text {
  background: #f4f4f5;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.6;
  font-size: 14px;
  white-space: pre-wrap;
}

.message.user .msg-text {
  background: #409eff;
  color: #fff;
  border-radius: 12px 12px 0 12px;
}

.message.assistant .msg-text {
  border-radius: 12px 12px 12px 0;
}

.msg-sources {
  margin-top: 8px;
}

.source-tag {
  margin: 2px 4px 2px 0;
}

.msg-meta {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}

.msg-text.is-loading {
  color: #909399;
  font-style: italic;
  position: relative;
  display: inline-block;
}

.msg-text.is-loading::after {
  content: '...';
  position: absolute;
  animation: typing 1.5s infinite;
  width: 0;
  overflow: hidden;
  display: inline-block;
  vertical-align: bottom;
}

@keyframes typing {
  0% { content: ''; }
  25% { content: '.'; }
  50% { content: '..'; }
  75% { content: '...'; }
  100% { content: ''; }
}

.chat-input {
  padding: 16px 20px;
  border-top: 1px solid #ebeef5;
}

.card-title {
  font-weight: 600;
}

.help-content h4 {
  font-size: 14px;
  margin-bottom: 8px;
  color: #303133;
}

.help-content p, .help-content li {
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
}

.help-content ul {
  padding-left: 20px;
}

.example-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.example-tag:hover {
  transform: scale(1.02);
}
</style>
