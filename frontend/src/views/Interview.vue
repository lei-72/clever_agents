<template>
  <div class="interview-page">
    <div class="page-header">
      <h2><el-icon><Microphone /></el-icon> 模拟面试</h2>
      <el-tag v-if="session" :type="statusType" size="large">{{ statusLabel }}</el-tag>
    </div>

    <!-- Start Panel -->
    <el-card v-if="!session" shadow="hover">
      <template #header><span class="card-title">开始面试</span></template>
      <el-form :model="startForm" label-width="100px">
        <el-form-item label="候选人 ID">
          <el-input v-model="startForm.candidate_id" placeholder="candidate-001" />
        </el-form-item>
        <el-form-item label="个人简介">
          <el-input v-model="startForm.resume_profile.summary" type="textarea" :rows="3"
            placeholder="请简要描述你的背景和技能方向" />
        </el-form-item>
        <el-form-item label="技术栈">
          <el-input v-model="skillsStr" placeholder="逗号分隔，如: Java,Spring Boot,MySQL" />
        </el-form-item>
        <el-form-item label="项目经验">
          <el-input v-model="projectsStr" placeholder="逗号分隔，如: 电商系统,博客平台" />
        </el-form-item>
        <el-button type="primary" size="large" @click="handleStart" :loading="loading"
          style="width: 100%; margin-top: 16px">
          <el-icon><VideoPlay /></el-icon> 开始面试
        </el-button>
      </el-form>
    </el-card>

    <!-- Interview Session -->
    <template v-if="session">
      <el-row :gutter="20">
        <el-col :span="16">
          <el-card shadow="hover" class="session-card">
            <!-- Stage Progress -->
            <div class="stage-bar">
              <div v-for="s in stages" :key="s.key" :class="['stage-item', { active: session.current_stage === s.key, done: stageIndex(session.current_stage) > stageIndex(s.key) }]">
                <el-icon><component :is="s.icon" /></el-icon>
                <span>{{ s.label }}</span>
              </div>
            </div>

            <!-- Question & Answer Area -->
            <div class="qa-area" ref="qaRef">
              <div v-for="(turn, i) in session.qna_turns" :key="i" class="qa-turn">
                <div class="question-bubble">
                  <el-avatar :size="32" class="ai-avatar">AI</el-avatar>
                  <div class="bubble ai">
                    <div class="bubble-meta">
                      <el-tag size="small" type="info">{{ turn.question.stage }}</el-tag>
                      <el-tag size="small">难度 {{ turn.question.difficulty }}</el-tag>
                    </div>
                    <p>{{ turn.question.content }}</p>
                  </div>
                </div>
                <div class="answer-bubble">
                  <div class="bubble user">
                    <p>{{ turn.answer }}</p>
                  </div>
                  <el-avatar :size="32" class="user-avatar">U</el-avatar>
                </div>
              </div>

              <!-- Current Question -->
              <div v-if="session.pending_question" class="qa-turn">
                <div class="question-bubble">
                  <el-avatar :size="32" class="ai-avatar">AI</el-avatar>
                  <div class="bubble ai current">
                    <div class="bubble-meta">
                      <el-tag size="small" type="info">{{ session.pending_question.stage }}</el-tag>
                      <el-tag size="small">难度 {{ session.pending_question.difficulty }}</el-tag>
                    </div>
                    <p>{{ session.pending_question.content }}</p>
                  </div>
                </div>
              </div>
            </div>

            <!-- Answer Input -->
            <div v-if="session.status === 'running'" class="answer-input">
              <el-input v-model="answerText" type="textarea" :rows="3"
                placeholder="输入你的回答..." @keyup.ctrl.enter="handleAnswer" />
              <div class="answer-actions">
                <el-button type="primary" @click="handleAnswer" :loading="answering">
                  <el-icon><Promotion /></el-icon> 提交回答
                </el-button>
                <el-button @click="handleInterrupt" :loading="answering">
                  <el-icon><VideoPause /></el-icon> 结束面试
                </el-button>
              </div>
            </div>

            <!-- Completed -->
            <div v-if="session.status !== 'running'" class="session-completed">
              <el-result icon="success" title="面试已结束">
                <template #extra>
                  <el-button type="primary" @click="handleGenerateReport" :loading="generatingReport">
                    <el-icon><DataAnalysis /></el-icon> 生成报告
                  </el-button>
                  <el-button @click="resetSession">重新开始</el-button>
                </template>
              </el-result>
            </div>
          </el-card>
        </el-col>

        <el-col :span="8">
          <!-- Session Info -->
          <el-card shadow="hover" class="card-section">
            <template #header><span class="card-title">会话信息</span></template>
            <el-descriptions :column="1" size="small" border>
              <el-descriptions-item label="会话 ID">{{ session.session_id }}</el-descriptions-item>
              <el-descriptions-item label="候选人">{{ session.candidate_id }}</el-descriptions-item>
              <el-descriptions-item label="当前阶段">{{ stageLabel(session.current_stage) }}</el-descriptions-item>
              <el-descriptions-item label="已答题目">{{ session.qna_turns.length }}</el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- Weak Tags -->
          <el-card v-if="session.weak_tag_marks.length" shadow="hover" class="card-section">
            <template #header><span class="card-title">薄弱标签</span></template>
            <div class="weak-tags">
              <el-tag v-for="t in session.weak_tag_marks" :key="t" type="warning" size="small">{{ t }}</el-tag>
            </div>
          </el-card>

          <!-- Report -->
          <el-card v-if="report" shadow="hover" class="card-section">
            <template #header><span class="card-title">面试报告</span></template>
            <div class="report-score">
              <span class="report-score-num">{{ report.overall_score.toFixed(0) }}</span>
              <span class="report-score-label">/ 100</span>
            </div>
            <div class="radar-chart" ref="interviewRadarRef" style="width: 100%; height: 250px"></div>
            <el-divider />
            <div v-if="report.highlights.length">
              <h4>亮点</h4>
              <ul class="report-list success">
                <li v-for="h in report.highlights" :key="h">{{ h }}</li>
              </ul>
            </div>
            <div v-if="report.weak_points.length" style="margin-top: 12px">
              <h4>待提升</h4>
              <ul class="report-list warning">
                <li v-for="w in report.weak_points" :key="w">{{ w }}</li>
              </ul>
            </div>
            <div v-if="report.suggestions.length" style="margin-top: 12px">
              <h4>建议</h4>
              <ul class="report-list">
                <li v-for="s in report.suggestions" :key="s">{{ s }}</li>
              </ul>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onUnmounted } from 'vue'
import { interviewApi } from '@/api'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const loading = ref(false)
const answering = ref(false)
const generatingReport = ref(false)
const session = ref(null)
const report = ref(null)
const answerText = ref('')
const qaRef = ref()
const interviewRadarRef = ref()
let radarChart = null

const skillsStr = ref('Java,Spring Boot,MySQL,Redis')
const projectsStr = ref('电商系统,学生管理系统')

const startForm = ref({
  candidate_id: 'candidate-001',
  resume_profile: {
    summary: '计算机科学与技术专业本科应届毕业生，熟悉 Java 后端开发，有 Spring Boot 项目经验。',
    skills: [],
    projects: [],
  },
})

const stages = [
  { key: 'intro', label: '导入', icon: 'User' },
  { key: 'tech', label: '技术', icon: 'Cpu' },
  { key: 'project', label: '项目', icon: 'FolderOpened' },
  { key: 'report', label: '报告', icon: 'DataAnalysis' },
]

function stageIndex(s) {
  return stages.findIndex((st) => st.key === s)
}

function stageLabel(s) {
  const stage = stages.find((st) => st.key === s)
  return stage?.label || s
}

const statusLabel = computed(() => {
  const map = { running: '进行中', interrupted: '已中断', completed: '已完成' }
  return map[session.value?.status] || ''
})

const statusType = computed(() => {
  const map = { running: 'primary', interrupted: 'warning', completed: 'success' }
  return map[session.value?.status] || 'info'
})

function scrollQA() {
  nextTick(() => {
    if (qaRef.value) qaRef.value.scrollTop = qaRef.value.scrollHeight
  })
}

async function handleStart() {
  loading.value = true
  try {
    startForm.value.resume_profile.skills = skillsStr.value.split(',').map(s => s.trim()).filter(Boolean)
    startForm.value.resume_profile.projects = projectsStr.value.split(',').map(s => s.trim()).filter(Boolean)
    const res = await interviewApi.start(startForm.value)
    session.value = res.session
    report.value = null
    ElMessage.success('面试已开始')
  } catch (e) {
    // handled
  } finally {
    loading.value = false
  }
}

async function handleAnswer() {
  if (!answerText.value.trim() || answering.value) return
  answering.value = true
  try {
    const res = await interviewApi.answer(session.value.session_id, {
      answer: answerText.value.trim(),
    })
    session.value = res.session
    answerText.value = ''
    scrollQA()
  } catch (e) {
    // handled
  } finally {
    answering.value = false
  }
}

async function handleInterrupt() {
  answering.value = true
  try {
    const res = await interviewApi.answer(session.value.session_id, {
      answer: '结束面试',
      interrupt: true,
    })
    session.value = res.session
  } catch (e) {
    // handled
  } finally {
    answering.value = false
  }
}

async function handleGenerateReport() {
  generatingReport.value = true
  try {
    const res = await interviewApi.generateReport(session.value.session_id)
    if (res.report) {
      report.value = res.report
      nextTick(() => renderRadar())
    } else {
      // Poll for report
      const reportRes = await interviewApi.getReport(session.value.session_id)
      report.value = reportRes.report
      nextTick(() => renderRadar())
    }
    ElMessage.success('报告生成完成')
  } catch (e) {
    // handled
  } finally {
    generatingReport.value = false
  }
}

function renderRadar() {
  if (!report.value?.radar_chart || !interviewRadarRef.value) return
  if (radarChart) radarChart.dispose()
  radarChart = echarts.init(interviewRadarRef.value)
  const data = report.value.radar_chart
  radarChart.setOption({
    radar: {
      indicator: data.indicators.map((name) => ({ name, max: data.max_value })),
      shape: 'polygon',
      splitNumber: 4,
    },
    series: [{
      type: 'radar',
      data: [{
        value: data.values,
        name: '能力评估',
        areaStyle: { color: 'rgba(64,158,255,0.2)' },
        lineStyle: { color: '#409eff' },
        itemStyle: { color: '#409eff' },
      }],
    }],
  })
}

function resetSession() {
  session.value = null
  report.value = null
}

onUnmounted(() => {
  if (radarChart) radarChart.dispose()
})
</script>

<style scoped>
.card-title { font-weight: 600; }

.stage-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  padding: 8px;
}

.stage-item {
  flex: 1;
  text-align: center;
  padding: 10px;
  border-radius: 6px;
  font-size: 13px;
  color: #909399;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.3s;
}

.stage-item.active {
  background: #409eff;
  color: #fff;
  font-weight: 600;
}

.stage-item.done {
  background: #e1f3d8;
  color: #67c23a;
}

.qa-area {
  max-height: calc(100vh - 420px);
  overflow-y: auto;
  padding: 16px 0;
}

.qa-turn {
  margin-bottom: 20px;
}

.question-bubble, .answer-bubble {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}

.answer-bubble {
  justify-content: flex-end;
}

.ai-avatar {
  background: linear-gradient(135deg, #67c23a, #95d475);
  color: #fff;
  flex-shrink: 0;
}

.user-avatar {
  background: linear-gradient(135deg, #409eff, #667eea);
  color: #fff;
  flex-shrink: 0;
}

.bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
}

.bubble.ai {
  background: #f4f4f5;
  border-radius: 2px 12px 12px 12px;
}

.bubble.ai.current {
  border: 2px solid #409eff;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { border-color: #409eff; }
  50% { border-color: #79bbff; }
}

.bubble.user {
  background: #409eff;
  color: #fff;
  border-radius: 12px 2px 12px 12px;
}

.bubble-meta {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}

.answer-input {
  border-top: 1px solid #ebeef5;
  padding-top: 16px;
}

.answer-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
  justify-content: flex-end;
}

.session-completed {
  padding: 40px 0;
  text-align: center;
}

.weak-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.report-score {
  text-align: center;
  margin: 16px 0;
}

.report-score-num {
  font-size: 48px;
  font-weight: 700;
  color: #409eff;
}

.report-score-label {
  font-size: 20px;
  color: #909399;
}

.report-list {
  padding-left: 20px;
  font-size: 13px;
  line-height: 2;
}

.report-list.success li::marker { color: #67c23a; }
.report-list.warning li::marker { color: #e6a23c; }

h4 {
  font-size: 14px;
  color: #303133;
  margin-bottom: 6px;
}
</style>
