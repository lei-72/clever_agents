<template>
  <div class="resume-page">
    <div class="page-header">
      <h2><el-icon><Document /></el-icon> 简历审查</h2>
    </div>

    <el-row :gutter="20">
      <el-col :span="10">
        <el-card shadow="hover">
          <template #header><span class="card-title">提交简历</span></template>
          <el-form :model="form" label-width="90px">
            <el-form-item label="目标岗位">
              <el-input v-model="form.target_role" placeholder="例如: Java 后端工程师" />
            </el-form-item>
            <el-form-item label="岗位 JD">
              <el-input v-model="form.job_description" type="textarea" :rows="3"
                placeholder="可选，粘贴岗位描述以获得更精准的匹配分析" />
            </el-form-item>
            <el-form-item label="简历内容">
              <el-input v-model="form.resume_text" type="textarea" :rows="14"
                placeholder="请粘贴完整简历内容（至少20个字符）" />
            </el-form-item>
            <el-button type="primary" size="large" @click="handleReview" :loading="loading"
              style="width: 100%">
              <el-icon><Check /></el-icon> 开始审查
            </el-button>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="14">
        <template v-if="result">
          <!-- Overall Score -->
          <el-card shadow="hover" class="card-section">
            <div class="overall-score">
              <div class="score-circle" :style="{ '--score-color': overallColor }">
                <span class="score-value">{{ result.overall_score.toFixed(0) }}</span>
                <span class="score-label">综合评分</span>
              </div>
              <div class="radar-chart" ref="radarRef" style="width: 360px; height: 280px"></div>
            </div>
          </el-card>

          <!-- Dimension Scores -->
          <el-card shadow="hover" class="card-section">
            <template #header><span class="card-title">六维度评分</span></template>
            <div class="dimension-list">
              <div v-for="d in result.dimension_scores" :key="d.dimension" class="dimension-item">
                <div class="dim-info">
                  <span class="dim-label">{{ dimLabel(d.dimension) }}</span>
                  <span class="dim-score">{{ d.score.toFixed(0) }}</span>
                </div>
                <el-progress :percentage="d.score" :color="dimColor(d.score)" :stroke-width="8"
                  :show-text="false" />
                <p class="dim-rationale">{{ d.rationale }}</p>
              </div>
            </div>
          </el-card>

          <!-- Issues -->
          <el-card v-if="allIssues.length" shadow="hover" class="card-section">
            <template #header><span class="card-title">问题与建议 ({{ allIssues.length }})</span></template>
            <el-collapse>
              <el-collapse-item v-for="(issue, i) in allIssues" :key="i"
                :title="`[${priorityLabel(issue.priority)}] ${issue.issue}`" :name="i">
                <div class="issue-detail">
                  <div class="issue-row">
                    <el-tag size="small" :type="priorityColor(issue.priority)">
                      {{ priorityLabel(issue.priority) }}
                    </el-tag>
                    <el-tag size="small" type="info">{{ dimLabel(issue.dimension) }}</el-tag>
                  </div>
                  <div class="issue-compare">
                    <div class="issue-original">
                      <h5>原文</h5>
                      <p>{{ issue.original_text }}</p>
                    </div>
                    <el-icon :size="20" color="#409eff"><Right /></el-icon>
                    <div class="issue-rewrite">
                      <h5>建议改写</h5>
                      <p>{{ issue.rewritten_text }}</p>
                    </div>
                  </div>
                  <p class="issue-suggestion"><strong>建议：</strong>{{ issue.suggestion }}</p>
                </div>
              </el-collapse-item>
            </el-collapse>
          </el-card>
        </template>

        <el-card v-else shadow="hover" class="empty-card">
          <el-empty description="提交简历后查看诊断报告">
            <template #image>
              <el-icon :size="64" color="#c0c4cc"><Document /></el-icon>
            </template>
          </el-empty>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { resumeApi } from '@/api'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

const loading = ref(false)
const result = ref(null)
const radarRef = ref()
let radarChart = null

const RESUME_STORAGE_KEY = 'resume_review_state_v1'

const form = ref({
  target_role: 'Java 后端工程师',
  job_description: '',
  resume_text: `张三
联系方式：zhangsan@email.com | 138-0000-1234
教育背景：XX大学 计算机科学与技术 本科 2020-2024

专业技能：
- 熟悉 Java、Python 编程语言
- 了解 Spring Boot、MyBatis 框架
- 熟悉 MySQL 数据库
- 了解 Linux 基本操作

项目经历：
1. 在线商城系统 (2023.06 - 2023.09)
使用 Spring Boot + Vue 开发了一个在线商城系统，实现了用户注册登录、商品展示、购物车、订单管理等功能。

2. 学生成绩管理系统 (2023.01 - 2023.04)
使用 Java 开发了成绩管理系统，可以录入和查询学生成绩。

实习经历：
XX科技有限公司 Java实习生 (2023.07 - 2023.09)
负责后端接口开发和bug修复。`,
})

function persistState() {
  try {
    localStorage.setItem(
      RESUME_STORAGE_KEY,
      JSON.stringify({
        form: form.value,
        result: result.value,
      })
    )
  } catch {
    // ignore
  }
}

function restoreState() {
  const raw = localStorage.getItem(RESUME_STORAGE_KEY)
  if (!raw) return
  try {
    const parsed = JSON.parse(raw)
    if (parsed?.form) form.value = { ...form.value, ...parsed.form }
    if (parsed?.result) result.value = parsed.result
  } catch {
    // ignore
  }
}

const overallColor = computed(() => {
  if (!result.value) return '#909399'
  const s = result.value.overall_score
  if (s >= 80) return '#67c23a'
  if (s >= 60) return '#e6a23c'
  return '#f56c6c'
})

const allIssues = computed(() => {
  if (!result.value) return []
  return [
    ...result.value.high_priority_issues,
    ...result.value.medium_priority_issues,
    ...result.value.low_priority_issues,
  ]
})

function dimLabel(d) {
  const map = {
    work_experience: '工作经验',
    skill_matching: '技能匹配',
    project_description: '项目描述',
    quantitative_data: '量化数据',
    formatting_layout: '排版布局',
    language_expression: '语言表达',
  }
  return map[d] || d
}

function dimColor(score) {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

function priorityLabel(p) {
  return { high: '高优先', medium: '中优先', low: '低优先' }[p] || p
}

function priorityColor(p) {
  return { high: 'danger', medium: 'warning', low: 'info' }[p] || 'info'
}

function renderRadar() {
  if (!result.value?.radar_chart || !radarRef.value) return
  if (radarChart) radarChart.dispose()
  try {
    radarChart = echarts.init(radarRef.value)
    const data = result.value.radar_chart
    radarChart.setOption({
      radar: {
        indicator: (data.indicators || []).map((name) => ({ name, max: data.max_value || 100 })),
        shape: 'polygon',
        splitNumber: 4,
      },
      series: [{
        type: 'radar',
        data: [{
          value: data.values || [],
          name: '评分',
          areaStyle: { color: 'rgba(64,158,255,0.2)' },
          lineStyle: { color: '#409eff' },
          itemStyle: { color: '#409eff' },
        }],
      }],
    })
    radarChart.resize()
  } catch (e) {
    // 图表失败不影响文本结果展示
  }
}

async function handleReview() {
  if (form.value.resume_text.length < 20) {
    ElMessage.warning('简历内容至少需要20个字符')
    return
  }
  loading.value = true
  try {
    result.value = await resumeApi.review({
      resume_text: form.value.resume_text,
      target_role: form.value.target_role || undefined,
      job_description: form.value.job_description || undefined,
    })
    ElMessage.success('简历审查完成')
    persistState()
    nextTick(() => {
      requestAnimationFrame(() => renderRadar())
    })
  } catch (e) {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  restoreState()
  nextTick(() => {
    requestAnimationFrame(() => renderRadar())
  })
})

watch(
  form,
  () => persistState(),
  { deep: true }
)
watch(result, () => persistState(), { deep: true })

onUnmounted(() => {
  if (radarChart) radarChart.dispose()
})
</script>

<style scoped>
.card-title { font-weight: 600; }

.overall-score {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  padding: 20px 0;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: 6px solid var(--score-color);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.score-value {
  font-size: 36px;
  font-weight: 700;
  color: var(--score-color);
}

.score-label {
  font-size: 12px;
  color: #909399;
}

.dimension-item {
  margin-bottom: 16px;
}

.dim-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.dim-label { font-weight: 600; font-size: 14px; }
.dim-score { color: #409eff; font-weight: 600; }

.dim-rationale {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  line-height: 1.6;
}

.issue-detail { padding: 8px 0; }

.issue-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.issue-compare {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.issue-original, .issue-rewrite {
  flex: 1;
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
}

.issue-original {
  background: #fef0f0;
  border: 1px solid #fde2e2;
}

.issue-rewrite {
  background: #f0f9eb;
  border: 1px solid #e1f3d8;
}

.issue-original h5, .issue-rewrite h5 {
  font-size: 12px;
  margin-bottom: 6px;
  color: #909399;
}

.issue-suggestion {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.empty-card {
  min-height: 500px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
