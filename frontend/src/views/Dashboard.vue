<template>
  <div class="dashboard">
    <div class="welcome-section">
      <div class="welcome-text">
        <h1>欢迎回来，{{ userStore.username }}</h1>
        <p>clever_agents AI 智能教学辅助系统 — 让教与学更高效</p>
      </div>
    </div>

    <el-row :gutter="20" class="stat-cards">
      <el-col :span="6" v-for="card in statCards" :key="card.title">
        <el-card shadow="hover" class="stat-card">
          <div class="stat-card-body">
            <div class="stat-icon" :style="{ background: card.bg }">
              <el-icon :size="28" color="#fff"><component :is="card.icon" /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-title">{{ card.title }}</div>
              <div class="stat-desc">{{ card.desc }}</div>
            </div>
          </div>
          <el-button type="primary" text @click="$router.push(card.path)">
            立即使用 <el-icon><ArrowRight /></el-icon>
          </el-button>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col :span="16">
        <el-card shadow="hover">
          <template #header>
            <span class="card-title">系统功能概览</span>
          </template>
          <div class="feature-grid">
            <div v-for="f in features" :key="f.title" class="feature-item" @click="$router.push(f.path)">
              <el-icon :size="32" :color="f.color"><component :is="f.icon" /></el-icon>
              <h4>{{ f.title }}</h4>
              <p>{{ f.desc }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <template #header>
            <span class="card-title">快速入门</span>
          </template>
          <el-timeline>
            <el-timeline-item v-for="(step, i) in quickSteps" :key="i"
              :timestamp="'步骤 ' + (i + 1)" placement="top">
              {{ step }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const statCards = [
  { title: '智能问答', desc: 'RAG 知识检索问答', icon: 'ChatDotRound', bg: 'linear-gradient(135deg, #409eff, #79bbff)', path: '/qa' },
  { title: '试卷批改', desc: 'AI 自动批改评分', icon: 'EditPen', bg: 'linear-gradient(135deg, #67c23a, #95d475)', path: '/grading' },
  { title: '简历审查', desc: '六维度简历诊断', icon: 'Document', bg: 'linear-gradient(135deg, #e6a23c, #eebe77)', path: '/resume' },
  { title: '模拟面试', desc: 'AI 驱动面试训练', icon: 'Microphone', bg: 'linear-gradient(135deg, #f56c6c, #f89898)', path: '/interview' },
]

const features = [
  { title: '智能问答', desc: '基于 RAG + HyDE 的知识检索与精准问答，支持文档上传入库', icon: 'ChatDotRound', color: '#409eff', path: '/qa' },
  { title: '试卷批改', desc: '支持客观题、主观题、编程题三种类型的自动化批改', icon: 'EditPen', color: '#67c23a', path: '/grading' },
  { title: '简历审查', desc: '六维度评分 + 雷达图 + 逐句问题定位与改写建议', icon: 'Document', color: '#e6a23c', path: '/resume' },
  { title: '模拟面试', desc: '四阶段面试流程 + 动态出题 + 双轨评估与能力报告', icon: 'Microphone', color: '#f56c6c', path: '/interview' },
  { title: '智能编排', desc: '多 Agent 统一入口，自动意图识别与路由分发', icon: 'Connection', color: '#9b59b6', path: '/qa' },
  { title: '系统监控', desc: '健康检查、LLM 状态监控、Prometheus 指标', icon: 'DataLine', color: '#606266', path: '/system' },
]

const quickSteps = [
  '使用演示账号登录系统',
  '在智能问答模块提问或上传知识文档',
  '前往试卷批改提交作业进行自动评分',
  '使用简历审查获取六维度诊断报告',
  '通过模拟面试进行 AI 面试训练',
]
</script>

<style scoped>
.welcome-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 32px;
  margin-bottom: 20px;
  color: #fff;
}

.welcome-text h1 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
}

.welcome-text p {
  opacity: 0.85;
  font-size: 14px;
}

.stat-cards {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 12px;
}

.stat-card-body {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-title {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.stat-desc {
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.feature-item {
  text-align: center;
  padding: 20px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #ebeef5;
}

.feature-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  border-color: #409eff;
}

.feature-item h4 {
  margin: 10px 0 6px;
  font-size: 14px;
  color: #303133;
}

.feature-item p {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}
</style>
