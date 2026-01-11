<template>
  <div class="home-container">
    <el-row :gutter="20">
      <!-- 欢迎区域 -->
      <el-col :span="24">
        <el-card class="welcome-card" shadow="never">
          <div class="welcome-content">
            <div class="welcome-text">
              <h1>欢迎使用 AIOps 网络运维平台</h1>
              <p>基于人工智能的网络运维管理系统，提供智能化的故障诊断和排障知识图谱</p>
            </div>
            <div class="welcome-stats">
              <el-row :gutter="16">
                <el-col :span="6">
                  <el-statistic title="网络节点" :value="nodeCount" />
                </el-col>
                <el-col :span="6">
                  <el-statistic title="连接关系" :value="relationshipCount" />
                </el-col>
                <el-col :span="6">
                  <el-statistic title="故障案例" :value="faultCases" />
                </el-col>
                <el-col :span="6">
                  <el-statistic title="解决方案" :value="solutions" />
                </el-col>
              </el-row>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 快速操作 -->
      <el-col :span="12">
        <el-card class="feature-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Share /></el-icon>
              <span>排障知识图谱</span>
            </div>
          </template>
          <div class="card-content">
            <p>构建和管理网络故障排障的知识图谱，通过可视化的方式展示网络拓扑和故障关系</p>
            <el-button type="primary" @click="goToKnowledgeGraph">
              <el-icon><Right /></el-icon>
              进入图谱管理
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 系统信息 -->
      <el-col :span="12">
        <el-card class="feature-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <el-icon><Setting /></el-icon>
              <span>系统概览</span>
            </div>
          </template>
          <div class="card-content">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="Neo4j版本">5.28.2</el-descriptions-item>
              <el-descriptions-item label="后端状态">
                <el-tag type="success">运行中</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="数据库连接">
                <el-tag type="success">正常</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="最后更新">{{ lastUpdate }}</el-descriptions-item>
            </el-descriptions>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <el-row style="margin-top: 20px">
      <el-col :span="24">
        <el-card class="activity-card" shadow="never">
          <template #header>
            <div class="card-header">
              <el-icon><Clock /></el-icon>
              <span>最近活动</span>
            </div>
          </template>
          <el-timeline>
            <el-timeline-item
              v-for="activity in recentActivities"
              :key="activity.id"
              :timestamp="activity.timestamp"
              :type="activity.type"
            >
              {{ activity.content }}
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 统计数据
const nodeCount = ref(0)
const relationshipCount = ref(0)
const faultCases = ref(0)
const solutions = ref(0)
const lastUpdate = ref('')

// 最近活动
const recentActivities = ref([
  {
    id: 1,
    content: '创建了新的网络节点：服务器-001',
    timestamp: '2024-01-20 14:30',
    type: 'primary'
  },
  {
    id: 2,
    content: '建立了节点间的连接关系',
    timestamp: '2024-01-20 13:45',
    type: 'success'
  },
  {
    id: 3,
    content: '更新了故障排除知识库',
    timestamp: '2024-01-20 10:20',
    type: 'info'
  }
])

const goToKnowledgeGraph = () => {
  router.push('/knowledge-graph')
}

const loadStatistics = async () => {
  try {
    // 这里后续可以调用API获取真实数据
    nodeCount.value = 128
    relationshipCount.value = 256
    faultCases.value = 42
    solutions.value = 89
    lastUpdate.value = new Date().toLocaleString('zh-CN')
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

onMounted(() => {
  loadStatistics()
})
</script>

<style scoped>
.home-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
}

.welcome-card :deep(.el-card__body) {
  padding: 40px;
}

.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.welcome-text h1 {
  margin: 0 0 10px 0;
  font-size: 32px;
  font-weight: bold;
}

.welcome-text p {
  margin: 0;
  font-size: 16px;
  opacity: 0.9;
}

.welcome-stats {
  min-width: 400px;
}

.welcome-stats :deep(.el-statistic__content) {
  color: white;
}

.welcome-stats :deep(.el-statistic__head) {
  color: rgba(255, 255, 255, 0.8);
}

.feature-card, .activity-card {
  height: 100%;
}

.card-header {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
}

.card-header .el-icon {
  margin-right: 8px;
  font-size: 18px;
}

.card-content {
  padding: 10px 0;
}

.card-content p {
  margin-bottom: 20px;
  color: #666;
  line-height: 1.6;
}
</style>