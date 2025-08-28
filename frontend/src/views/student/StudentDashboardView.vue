<template>
  <div class="student-dashboard">
    <div class="page-header">
      <h1 class="page-title">학습 대시보드</h1>
      <p class="page-description">안녕하세요, {{ userStore.user?.username }}님! 학습 진행 상황을 확인하세요</p>
      <el-button type="primary" @click="refreshData">
        <el-icon><Refresh /></el-icon>
        새로고침
      </el-button>
    </div>

    <!-- 학습 현황 -->
    <el-card class="study-stats-card">
      <template #header>
        <div class="card-header">
          <span>학습 현황</span>
        </div>
      </template>

      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-icon study">📚</div>
          <div class="stat-details">
            <span class="stat-label">총 학습시간</span>
            <span class="stat-value">{{ studyStats.totalStudyTime }}</span>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon questions">✅</div>
          <div class="stat-details">
            <span class="stat-label">푼 문제 수</span>
            <span class="stat-value">{{ studyStats.solvedQuestions }}</span>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon certificates">🏆</div>
          <div class="stat-details">
            <span class="stat-label">목표 자격증</span>
            <span class="stat-value">{{ studyStats.targetCertificates }}</span>
          </div>
        </div>
        <div class="stat-item">
          <div class="stat-icon accuracy">🎯</div>
          <div class="stat-details">
            <span class="stat-label">평균 정확도</span>
            <span class="stat-value">85%</span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 빠른 액션 -->
    <el-card class="quick-actions-card">
      <template #header>
        <div class="card-header">
          <span>빠른 시작</span>
        </div>
      </template>

      <div class="actions-list">
        <div class="action-item" @click="startStudy">
          <div class="action-icon">📖</div>
          <div class="action-content">
            <h4>학습 계속하기</h4>
            <p>마지막으로 공부했던 자격증 학습을 이어가세요</p>
          </div>
          <el-button type="primary">시작</el-button>
        </div>
        
        <div class="action-item" @click="solvePractice">
          <div class="action-icon">✏️</div>
          <div class="action-content">
            <h4>문제 풀이</h4>
            <p>실력을 점검하고 약점을 파악해보세요</p>
          </div>
          <el-button type="success">문제 풀기</el-button>
        </div>
        
        <div class="action-item" @click="chatWithAI">
          <div class="action-icon">🤖</div>
          <div class="action-content">
            <h4>AI 도우미</h4>
            <p>궁금한 점을 AI에게 물어보세요</p>
          </div>
          <el-button type="info">AI 상담</el-button>
        </div>
        
        <div class="action-item" @click="selectCertificate">
          <div class="action-icon">🎯</div>
          <div class="action-content">
            <h4>새 자격증</h4>
            <p>새로운 자격증 학습을 시작해보세요</p>
          </div>
          <el-button type="warning">자격증 선택</el-button>
        </div>
      </div>
    </el-card>

    <!-- 학습 중인 자격증 -->
    <el-card class="certificates-card">
      <template #header>
        <div class="card-header">
          <span>학습 중인 자격증</span>
        </div>
      </template>

      <div v-if="currentCertificates.length === 0" class="empty-container">
        <el-empty description="학습 중인 자격증이 없습니다">
          <el-button type="primary" @click="selectCertificate">
            자격증 선택하기
          </el-button>
        </el-empty>
      </div>

      <div v-else class="certificates-list">
        <div v-for="cert in currentCertificates" :key="cert.id" class="cert-item">
          <div class="cert-header">
            <div class="cert-info">
              <h4 class="cert-name">{{ cert.title }}</h4>
              <el-tag :type="getDifficultyColor(cert.difficulty_level)" size="small">
                {{ cert.difficulty_level }}
              </el-tag>
              <el-tag type="info" size="small">
                {{ cert.category }}
              </el-tag>
            </div>
          </div>

          <div class="cert-progress-section">
            <div class="progress-info">
              <span class="progress-label">학습 진도</span>
              <span class="progress-value">{{ cert.progress }}%</span>
            </div>
            <el-progress 
              :percentage="cert.progress" 
              :color="getProgressColor(cert.progress)"
              :stroke-width="8"
            />
          </div>

          <div class="cert-stats">
            <div class="stat-group">
              <span class="stat-label">학습시간</span>
              <span class="stat-value">{{ cert.studiedHours }}h</span>
            </div>
            <div class="stat-group">
              <span class="stat-label">문제 해결</span>
              <span class="stat-value">{{ cert.solvedQuestions }}</span>
            </div>
            <div class="stat-group">
              <span class="stat-label">정확도</span>
              <span class="stat-value">{{ cert.accuracy }}%</span>
            </div>
          </div>

          <div class="cert-actions">
            <el-button 
              type="primary" 
              size="small" 
              @click="continueCertificateStudy(cert)"
            >
              계속 학습
            </el-button>
            <el-button 
              type="text" 
              size="small" 
              @click="viewCertificateDetail(cert)"
            >
              상세보기
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 최근 활동 -->
    <el-card class="recent-activity-card">
      <template #header>
        <div class="card-header">
          <span>최근 활동</span>
        </div>
      </template>

      <div v-if="recentActivities.length === 0" class="empty-container">
        <el-empty description="최근 활동이 없습니다" :image-size="80" />
      </div>

      <div v-else class="activity-list">
        <div v-for="activity in recentActivities" :key="activity.id" class="activity-item">
          <div class="activity-icon" :class="activity.type">
            {{ activity.icon }}
          </div>
          <div class="activity-content">
            <h4 class="activity-title">{{ activity.title }}</h4>
            <p class="activity-description">{{ activity.description }}</p>
          </div>
          <div class="activity-time">
            {{ activity.timestamp }}
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { Refresh } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useAuthStore()

// 학습 통계
const studyStats = reactive({
  totalStudyTime: '24시간',
  solvedQuestions: 156,
  targetCertificates: 3
})

// 현재 학습 중인 자격증들
const currentCertificates = ref([
  {
    id: 1,
    title: 'AWS Solutions Architect',
    category: 'Cloud',
    difficulty_level: 'intermediate',
    progress: 75,
    studiedHours: 18,
    solvedQuestions: 89,
    accuracy: 87
  },
  {
    id: 2,
    title: 'Google Cloud Professional',
    category: 'Cloud', 
    difficulty_level: 'advanced',
    progress: 45,
    studiedHours: 12,
    solvedQuestions: 34,
    accuracy: 82
  }
])

// 최근 활동
const recentActivities = ref([
  {
    id: 1,
    title: 'AWS 네트워킹 학습 완료',
    description: 'VPC와 서브넷 구성에 대한 학습을 완료했습니다.',
    timestamp: '2시간 전',
    type: 'success',
    icon: 'Check'
  },
  {
    id: 2,
    title: '문제 풀이 세션',
    description: 'AWS 보안 관련 문제 15개를 풀었습니다.',
    timestamp: '4시간 전',
    type: 'primary',
    icon: 'Edit'
  },
  {
    id: 3,
    title: 'AI 도우미 상담',
    description: 'IAM 정책에 대해 AI와 상담했습니다.',
    timestamp: '어제',
    type: 'info',
    icon: 'ChatDotRound'
  }
])

// 메서드들
const startStudy = () => {
  router.push('/student/study')
}

const solvePractice = () => {
  router.push('/student/practice')
}

const chatWithAI = () => {
  router.push('/student/chat')
}

const selectCertificate = () => {
  router.push('/student/certificates')
}

const continueCertificateStudy = (cert: any) => {
  router.push(`/student/study/${cert.id}`)
}

const viewCertificateDetail = (cert: any) => {
  router.push(`/student/certificates/${cert.id}`)
}

const getDifficultyColor = (difficulty: string) => {
  switch (difficulty) {
    case 'Beginner': return 'success'
    case 'intermediate': return 'warning'
    case 'advanced': return 'danger'
    default: return 'info'
  }
}

const getProgressColor = (progress: number) => {
  if (progress >= 80) return '#67c23a'
  if (progress >= 60) return '#e6a23c'
  return '#f56c6c'
}

// 데이터 로드
const refreshData = async () => {
  try {
    ElMessage.success('데이터를 새로고침했습니다')
    await loadDashboardData()
  } catch (error) {
    ElMessage.error('데이터 새로고침에 실패했습니다')
  }
}

const loadDashboardData = async () => {
  try {
    // TODO: 실제 API 호출로 학습 데이터 가져오기
    console.log('Loading dashboard data...')
  } catch (error) {
    console.error('Failed to load dashboard data:', error)
    ElMessage.error('대시보드 데이터를 불러오는데 실패했습니다')
  }
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.student-dashboard {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: #333;
}

.page-description {
  font-size: 14px;
  color: #666;
  margin: 4px 0 0 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

/* 학습 현황 카드 */
.study-stats-card {
  margin-bottom: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  padding: 20px 0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.stat-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #409eff;
  color: white;
  border-radius: 8px;
}

.stat-details {
  flex: 1;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.stat-value {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

/* 빠른 액션 카드 */
.quick-actions-card {
  margin-bottom: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.actions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.action-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  cursor: pointer;
  transition: all 0.3s;
}

.action-item:hover {
  background: #f5f7fa;
  border-color: #409eff;
}

.action-icon {
  font-size: 24px;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f9ff;
  border-radius: 8px;
}

.action-content {
  flex: 1;
}

.action-content h4 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.action-content p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

/* 자격증 카드 */
.certificates-card {
  margin-bottom: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.empty-container {
  padding: 40px;
  text-align: center;
}

.certificates-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.cert-item {
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #f8f9fa;
}

.cert-header {
  margin-bottom: 16px;
}

.cert-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cert-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.cert-progress-section {
  margin-bottom: 16px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.progress-label {
  font-size: 14px;
  color: #666;
}

.progress-value {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.cert-stats {
  display: flex;
  justify-content: space-around;
  margin-bottom: 16px;
  padding: 12px;
  background: white;
  border-radius: 8px;
}

.stat-group {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-group .stat-label {
  font-size: 12px;
  color: #666;
}

.stat-group .stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.cert-actions {
  display: flex;
  gap: 8px;
}

/* 최근 활동 카드 */
.recent-activity-card {
  margin-bottom: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.activity-icon {
  font-size: 20px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.activity-icon.success {
  background: #f0f9ff;
  color: #67c23a;
}

.activity-icon.primary {
  background: #f0f9ff;
  color: #409eff;
}

.activity-icon.info {
  background: #f4f4f5;
  color: #909399;
}

.activity-content {
  flex: 1;
}

.activity-title {
  margin: 0 0 2px 0;
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.activity-description {
  margin: 0;
  font-size: 12px;
  color: #666;
}

.activity-time {
  font-size: 12px;
  color: #909399;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .cert-stats {
    flex-direction: column;
    gap: 8px;
  }
  
  .action-item {
    flex-direction: column;
    text-align: center;
  }
  
  .cert-actions {
    flex-direction: column;
  }
}
</style>