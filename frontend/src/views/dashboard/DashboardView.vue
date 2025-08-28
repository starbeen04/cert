<template>
  <div class="dashboard">
    <div class="page-header">
      <h1 class="page-title">대시보드</h1>
      <p class="page-description">CertFast 관리자 대시보드에 오신 것을 환영합니다</p>
    </div>

    <!-- Stats Cards -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card users">
          <div class="stat-icon">
            <el-icon size="24"><User /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ dashboardStore.stats.total_users }}</div>
            <div class="stat-label">총 사용자</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card certificates">
          <div class="stat-icon">
            <el-icon size="24"><Document /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ dashboardStore.stats.total_certificates }}</div>
            <div class="stat-label">자격증</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card materials">
          <div class="stat-icon">
            <el-icon size="24"><Reading /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ dashboardStore.stats.total_study_materials }}</div>
            <div class="stat-label">학습 자료</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card agents">
          <div class="stat-icon">
            <el-icon size="24"><Cpu /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ dashboardStore.stats.active_ai_agents }}</div>
            <div class="stat-label">활성 AI 에이전트</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Charts and Recent Activity -->
    <el-row :gutter="20" class="content-row">
      <!-- Recent Activity -->
      <el-col :xs="24" :lg="12">
        <el-card class="activity-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">최근 활동</span>
              <el-button type="text" @click="refreshData">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </template>
          
          <div v-loading="dashboardStore.isLoading" class="activity-list">
            <div class="activity-item">
              <div class="activity-icon upload">
                <el-icon><Upload /></el-icon>
              </div>
              <div class="activity-content">
                <div class="activity-title">최근 업로드</div>
                <div class="activity-value">{{ dashboardStore.stats.recent_uploads }} 개 새 파일</div>
              </div>
            </div>

            <div class="activity-item">
              <div class="activity-icon processing">
                <el-icon><Loading /></el-icon>
              </div>
              <div class="activity-content">
                <div class="activity-title">처리 대기열</div>
                <div class="activity-value">{{ dashboardStore.stats.processing_queue }} 개 파일 대기 중</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- Quick Actions -->
      <el-col :xs="24" :lg="12">
        <el-card class="actions-card">
          <template #header>
            <span class="card-title">빠른 작업</span>
          </template>
          
          <div class="quick-actions">
            <el-button
              type="primary"
              size="large"
              class="action-btn"
              @click="goToUpload"
            >
              <el-icon><Upload /></el-icon>
              자격증 업로드
            </el-button>

            <el-button
              type="success"
              size="large"
              class="action-btn"
              @click="goToUsers"
            >
              <el-icon><UserFilled /></el-icon>
              사용자 관리
            </el-button>

            <el-button
              type="warning"
              size="large"
              class="action-btn"
              @click="goToAIAgents"
            >
              <el-icon><Setting /></el-icon>
              AI 에이전트
            </el-button>

            <el-button
              type="info"
              size="large"
              class="action-btn"
              @click="goToMonitoring"
            >
              <el-icon><DataAnalysis /></el-icon>
              모니터링
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- System Status -->
    <el-row :gutter="20" class="status-row">
      <el-col :span="24">
        <el-card class="status-card">
          <template #header>
            <span class="card-title">시스템 상태</span>
          </template>
          
          <div class="status-grid">
            <div class="status-item">
              <div class="status-indicator online"></div>
              <span class="status-label">API 서버</span>
              <span class="status-value">온라인</span>
            </div>

            <div class="status-item">
              <div class="status-indicator online"></div>
              <span class="status-label">데이터베이스</span>
              <span class="status-value">연결됨</span>
            </div>

            <div class="status-item">
              <div class="status-indicator online"></div>
              <span class="status-label">AI 서비스</span>
              <span class="status-value">활성</span>
            </div>

            <div class="status-item">
              <div class="status-indicator online"></div>
              <span class="status-label">파일 저장소</span>
              <span class="status-value">사용 가능</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  User,
  Document,
  Reading,
  Cpu,
  Refresh,
  Upload,
  Loading,
  UserFilled,
  Setting,
  DataAnalysis,
} from '@element-plus/icons-vue'
import { useDashboardStore } from '@/stores/dashboard'

const router = useRouter()
const dashboardStore = useDashboardStore()

// Methods
const refreshData = async () => {
  try {
    await dashboardStore.refreshStats()
    ElMessage.success('데이터가 성공적으로 새로고침되었습니다')
  } catch (error) {
    console.error('Failed to refresh data:', error)
    ElMessage.error('데이터 새로고침에 실패했습니다')
  }
}

const goToUpload = () => {
  router.push('/admin/certificates')
}

const goToUsers = () => {
  router.push('/admin/users')
}

const goToAIAgents = () => {
  router.push('/admin/ai-agents')
}

const goToMonitoring = () => {
  router.push('/admin/monitoring')
}

// Initialize
onMounted(() => {
  dashboardStore.fetchDashboardStats()
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.stats-row {
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
  height: 100px;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-card.users .stat-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card.certificates .stat-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-card.materials .stat-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-card.agents .stat-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #7f8c8d;
  font-weight: 500;
}

.content-row {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.activity-list {
  min-height: 200px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 0;
  border-bottom: 1px solid #f0f2f5;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.activity-icon.upload {
  background: #409eff;
}

.activity-icon.processing {
  background: #e6a23c;
}

.activity-title {
  font-size: 16px;
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 4px;
}

.activity-value {
  font-size: 14px;
  color: #7f8c8d;
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.action-btn {
  height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
}

.status-row {
  margin-bottom: 24px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.status-indicator.online {
  background: #67c23a;
  animation: pulse 2s infinite;
}

.status-indicator.offline {
  background: #f56c6c;
}

.status-label {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  flex: 1;
}

.status-value {
  font-size: 14px;
  color: #67c23a;
  font-weight: 500;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(103, 194, 58, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(103, 194, 58, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(103, 194, 58, 0);
  }
}

/* Responsive design */
@media (max-width: 768px) {
  .quick-actions {
    grid-template-columns: 1fr;
  }
  
  .status-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-card {
    height: auto;
    padding: 16px;
  }
  
  .stat-value {
    font-size: 24px;
  }
}
</style>