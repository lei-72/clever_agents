<template>
  <div class="grading-page">
    <div class="page-header">
      <h2><el-icon><EditPen /></el-icon> 试卷批改</h2>
    </div>

    <el-row :gutter="20">
      <el-col :span="14">
        <el-card shadow="hover">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span class="card-title">试卷信息</span>
              <el-button type="primary" size="small" @click="addQuestion">
                <el-icon><Plus /></el-icon> 添加题目
              </el-button>
            </div>
          </template>

          <el-form :model="form" label-width="90px">
            <el-row :gutter="16">
              <el-col :span="8">
                <el-form-item label="试卷 ID">
                  <el-input v-model="form.exam_id" placeholder="exam-001" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="学生 ID">
                  <el-input v-model="form.student_id" placeholder="stu-001" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="教师 ID">
                  <el-input v-model="form.teacher_id" placeholder="可选" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>

          <div v-for="(q, idx) in form.questions" :key="idx" class="question-item">
            <div class="question-header">
              <el-tag :type="typeColor(q.question_type)" size="small">
                {{ typeLabel(q.question_type) }}
              </el-tag>
              <span class="q-title">第 {{ idx + 1 }} 题 ({{ q.max_score }}分)</span>
              <el-button type="danger" text size="small" @click="form.questions.splice(idx, 1)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>
            <el-form label-width="90px" size="small">
              <el-row :gutter="12">
                <el-col :span="8">
                  <el-form-item label="题目类型">
                    <el-select v-model="q.question_type" style="width: 100%">
                      <el-option label="客观题" value="objective" />
                      <el-option label="主观题" value="subjective" />
                      <el-option label="编程题" value="coding" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="满分">
                    <el-input-number v-model="q.max_score" :min="1" :max="100" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="知识标签">
                    <el-input v-model="q.knowledge_tags_str" placeholder="逗号分隔" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="题干">
                <el-input v-model="q.stem" type="textarea" :rows="2" placeholder="输入题目内容" />
              </el-form-item>
              <el-form-item label="学生作答">
                <el-input v-model="q.student_answer" type="textarea" :rows="2" placeholder="学生的答案" />
              </el-form-item>
              <el-form-item v-if="q.question_type === 'objective'" label="标准答案">
                <el-input v-model="q.expected_answer" placeholder="标准答案" />
              </el-form-item>
            </el-form>
          </div>

          <el-button type="primary" size="large" @click="handleGrade" :loading="loading"
            style="width: 100%; margin-top: 16px">
            <el-icon><Check /></el-icon> 提交批改
          </el-button>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card v-if="result" shadow="hover" class="result-card">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center">
              <span class="card-title">批改结果</span>
              <el-tag :type="result.reviewed ? 'success' : 'info'" size="small">
                {{ result.reviewed ? '已审核' : '待审核' }}
              </el-tag>
            </div>
          </template>

          <div class="score-summary">
            <div class="score-big">
              <span class="score-num">{{ result.total_score }}</span>
              <span class="score-sep">/</span>
              <span class="score-full">{{ result.full_score }}</span>
            </div>
            <el-progress :percentage="Math.round(result.total_score / result.full_score * 100)"
              :color="scoreColor" :stroke-width="12" />
          </div>

          <el-divider>各题详情</el-divider>

          <div v-for="qr in result.question_results" :key="qr.question_id" class="result-item">
            <div class="result-item-header">
              <el-tag :type="typeColor(qr.question_type)" size="small">
                {{ typeLabel(qr.question_type) }}
              </el-tag>
              <span>{{ qr.question_id }}</span>
              <el-tag :type="qr.score > 0 ? 'success' : 'danger'" size="small">
                {{ qr.score }} 分
              </el-tag>
            </div>
            <p class="rationale">{{ qr.rationale }}</p>
            <div v-if="qr.matched_points.length" class="points">
              <el-tag v-for="p in qr.matched_points" :key="p" size="small" type="success">{{ p }}</el-tag>
            </div>
            <div v-if="qr.missed_points.length" class="points">
              <el-tag v-for="p in qr.missed_points" :key="p" size="small" type="danger">{{ p }}</el-tag>
            </div>
          </div>

          <el-divider v-if="result.analysis_report">学情分析</el-divider>
          <div v-if="result.analysis_report" class="analysis">
            <div v-if="result.analysis_report.weak_knowledge_points.length">
              <h4>薄弱知识点</h4>
              <el-tag v-for="w in result.analysis_report.weak_knowledge_points" :key="w.tag"
                type="warning" size="small" class="weak-tag">
                {{ w.tag }} (影响: {{ w.impact_score }})
              </el-tag>
            </div>
            <div v-if="result.analysis_report.optimization_suggestions.length" style="margin-top: 12px">
              <h4>优化建议</h4>
              <ul>
                <li v-for="s in result.analysis_report.optimization_suggestions" :key="s">{{ s }}</li>
              </ul>
            </div>
          </div>
        </el-card>

        <el-card v-else shadow="hover" class="result-card empty">
          <el-empty description="提交试卷后查看批改结果" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { gradingApi } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const result = ref(null)

const form = ref({
  exam_id: 'exam-001',
  student_id: 'stu-001',
  teacher_id: '',
  questions: [
    {
      question_id: 'q1',
      question_type: 'objective',
      stem: 'Python 中哪个关键字用于定义函数？',
      max_score: 10,
      student_answer: 'def',
      expected_answer: 'def',
      knowledge_tags_str: 'Python基础',
    },
    {
      question_id: 'q2',
      question_type: 'subjective',
      stem: '请简述面向对象编程的三大特性。',
      max_score: 20,
      student_answer: '封装、继承、多态。封装是将数据和方法包装在类中，继承是子类获取父类特性，多态是同一接口不同实现。',
      expected_answer: '',
      knowledge_tags_str: '面向对象',
    },
  ],
})

function addQuestion() {
  const idx = form.value.questions.length + 1
  form.value.questions.push({
    question_id: `q${idx}`,
    question_type: 'objective',
    stem: '',
    max_score: 10,
    student_answer: '',
    expected_answer: '',
    knowledge_tags_str: '',
  })
}

function typeLabel(t) {
  return { objective: '客观题', subjective: '主观题', coding: '编程题' }[t] || t
}
function typeColor(t) {
  return { objective: 'success', subjective: 'warning', coding: 'danger' }[t] || 'info'
}

const scoreColor = [
  { color: '#f56c6c', percentage: 40 },
  { color: '#e6a23c', percentage: 70 },
  { color: '#67c23a', percentage: 100 },
]

async function handleGrade() {
  loading.value = true
  try {
    const payload = {
      exam_id: form.value.exam_id,
      student_id: form.value.student_id,
      teacher_id: form.value.teacher_id || undefined,
      questions: form.value.questions.map((q) => ({
        question_id: q.question_id,
        question_type: q.question_type,
        stem: q.stem,
        max_score: q.max_score,
        student_answer: q.student_answer,
        objective_rule: q.question_type === 'objective' ? { expected_answer: q.expected_answer } : undefined,
        subjective_rubric: q.question_type === 'subjective'
          ? [{ key: 'overall', description: '覆盖关键要点，表达清晰完整', score: q.max_score }]
          : undefined,
        knowledge_tags: q.knowledge_tags_str ? q.knowledge_tags_str.split(',').map(s => s.trim()) : [],
      })),
    }
    result.value = await gradingApi.grade(payload)
    ElMessage.success('批改完成')
  } catch (e) {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.card-title { font-weight: 600; }

.question-item {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.question-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.q-title { font-weight: 600; flex: 1; }

.score-summary {
  text-align: center;
  margin-bottom: 16px;
}

.score-big {
  margin-bottom: 12px;
}

.score-num {
  font-size: 48px;
  font-weight: 700;
  color: #409eff;
}

.score-sep {
  font-size: 24px;
  color: #c0c4cc;
  margin: 0 4px;
}

.score-full {
  font-size: 24px;
  color: #909399;
}

.result-item {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.result-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.rationale {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  margin-bottom: 8px;
}

.points {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 4px;
}

.analysis h4 {
  font-size: 14px;
  margin-bottom: 8px;
}

.analysis ul {
  padding-left: 20px;
  font-size: 13px;
  color: #606266;
}

.analysis li {
  line-height: 1.8;
}

.weak-tag {
  margin: 2px;
}

.result-card.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
}
</style>
