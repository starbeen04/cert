<template>
  <div class="instructor-dashboard">
    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">강사 대시보드</h1>
        <p class="page-description">
          안녕하세요, {{ authStore.user?.full_name || authStore.user?.username }}님! 
          학습자들의 진행 상황을 관리하고 교육 자료를 개선하세요.
        </p>
      </div>
      <el-button type="primary" @click="refreshData">
        <el-icon><Refresh /></el-icon>
        새로고침
      </el-button>
    </div>

    <!-- 통계 카드 -->
    <div class="stats-row">
      <el-card class="stat-card">
        <template #header>
          <span class="stat-title">내 학습자</span>
        </template>
        <div class="stat-content">
          <div class="stat-number">{{ stats.totalStudents }}</div>
          <div class="stat-label">명</div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <template #header>
          <span class="stat-title">처리 대기 신고</span>
        </template>
        <div class="stat-content">
          <div class="stat-number pending">{{ stats.pendingReports }}</div>
          <div class="stat-label">건</div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <template #header>
          <span class="stat-title">관리 자격증</span>
        </template>
        <div class="stat-content">
          <div class="stat-number">{{ stats.managedCertificates }}</div>
          <div class="stat-label">개</div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <template #header>
          <span class="stat-title">이번 달 활동</span>
        </template>
        <div class="stat-content">
          <div class="stat-number">{{ stats.monthlyActivities }}</div>
          <div class="stat-label">회</div>
        </div>
      </el-card>
    </div>

    <div class="content-row">
      <!-- 최근 학습자 활동 -->
      <el-card class="activity-card">
        <template #header>
          <div class="card-header">
            <span>최근 학습자 활동</span>
            <el-button type="text" @click="$router.push('/instructor/students')">
              모두 보기
            </el-button>
          </div>
        </template>

        <div v-if="recentActivities.length === 0" class="empty-state">
          <el-empty description="최근 활동이 없습니다" />
        </div>

        <div v-else class="activity-list">
          <div 
            v-for="activity in recentActivities" 
            :key="activity.id"
            class="activity-item"
          >
            <div class="activity-avatar">
              <el-avatar :size="40">
                {{ activity.studentName.charAt(0) }}
              </el-avatar>
            </div>
            <div class="activity-content">
              <div class="activity-title">{{ activity.studentName }}</div>
              <div class="activity-description">{{ activity.description }}</div>
              <div class="activity-time">{{ formatTime(activity.timestamp) }}</div>
            </div>
            <div class="activity-score" v-if="activity.score">
              <el-tag :type="getScoreType(activity.score)">
                {{ activity.score }}점
              </el-tag>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 신고 대기 목록 -->
      <el-card class="reports-card">
        <template #header>
          <div class="card-header">
            <span>신고 처리 대기</span>
            <el-button type="text" @click="$router.push('/instructor/reports')">
              모두 보기
            </el-button>
          </div>
        </template>

        <div v-if="pendingReportsList.length === 0" class="empty-state">
          <el-empty description="처리할 신고가 없습니다" />
        </div>

        <div v-else class="reports-list">
          <div 
            v-for="report in pendingReportsList" 
            :key="report.id"
            class="report-item"
          >
            <div class="report-icon">
              <el-icon size="24" color="#f56c6c">
                <Warning />
              </el-icon>
            </div>
            <div class="report-content">
              <div class="report-title">{{ report.title }}</div>
              <div class="report-description">{{ report.description }}</div>
              <div class="report-time">{{ formatTime(report.timestamp) }}</div>
            </div>
            <div class="report-actions">
              <el-button 
                type="primary" 
                size="small"
                @click="handleReport(report.id)"
              >
                처리하기
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 강사 협업 및 공지 -->
    <el-card class="collaboration-card">
      <template #header>
        <div class="card-header">
          <span>강사 협업 공간</span>
          <el-button type="text" @click="$router.push('/instructor/collaboration')">
            협업 공간 보기
          </el-button>
        </div>
      </template>

      <div class="collaboration-content">
        <div class="recent-discussions">
          <h4>최근 토론</h4>
          <div v-if="recentDiscussions.length === 0" class="empty-state">
            <p>최근 토론이 없습니다</p>
          </div>
          <div v-else class="discussion-list">
            <div 
              v-for="discussion in recentDiscussions" 
              :key="discussion.id"
              class="discussion-item"
            >
              <div class="discussion-title">{{ discussion.title }}</div>
              <div class="discussion-meta">
                {{ discussion.author }} · {{ formatTime(discussion.timestamp) }}
              </div>
            </div>
          </div>
        </div>

        <div class="quick-actions">
          <h4>빠른 액션</h4>
          <div class="action-buttons">
            <el-button type="primary" @click="$router.push('/instructor/collaboration')">
              <el-icon><ChatDotRound /></el-icon>
              새 토론 시작
            </el-button>
            <el-button @click="$router.push('/instructor/content')">
              <el-icon><Document /></el-icon>
              자료 공유
            </el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Refresh, 
  Warning, 
  ChatDotRound, 
  Document 
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 통계 데이터
const stats = ref({
  totalStudents: 0,
  pendingReports: 0,
  managedCertificates: 0,
  monthlyActivities: 0
})

// 최근 학습자 활동
const recentActivities = ref([
  {
    id: 1,
    studentName: '김학생',
    description: 'AWS 솔루션 아키텍트 문제 풀이 완료',
    timestamp: new Date(Date.now() - 30 * 60 * 1000),
    score: 85
  },
  {
    id: 2,
    studentName: '이학습',
    description: '구글 클라우드 학습 자료 열람',
    timestamp: new Date(Date.now() - 60 * 60 * 1000),
    score: null
  },
  {
    id: 3,
    studentName: '박공부',
    description: 'CompTIA Security+ 모의시험 응시',
    timestamp: new Date(Date.now() - 120 * 60 * 1000),
    score: 92
  }
])

// 신고 대기 목록
const pendingReportsList = ref([
  {
    id: 1,
    title: 'AI 생성 문제 오류',
    description: 'AWS 문제에서 정답이 잘못 표시됩니다',
    timestamp: new Date(Date.now() - 20 * 60 * 1000)
  },
  {
    id: 2,
    title: '학습 자료 내용 부정확',
    description: '클라우드 보안 섹션에 오래된 정보가 있습니다',
    timestamp: new Date(Date.now() - 45 * 60 * 1000)
  }
])

// 최근 토론
const recentDiscussions = ref([
  {
    id: 1,
    title: 'AWS 자격증 문제 출제 방향 논의',
    author: '김강사',
    timestamp: new Date(Date.now() - 180 * 60 * 1000)
  },
  {
    id: 2,
    title: '클라우드 보안 최신 동향 공유',
    author: '이교수',
    timestamp: new Date(Date.now() - 300 * 60 * 1000)
  }
])

// 메서드
const refreshData = async () => {
  try {
    // TODO: API 호출로 실제 데이터 가져오기
    stats.value = {
      totalStudents: Math.floor(Math.random() * 100) + 50,
      pendingReports: Math.floor(Math.random() * 10) + 2,
      managedCertificates: Math.floor(Math.random() * 5) + 3,
      monthlyActivities: Math.floor(Math.random() * 50) + 20
    }
    ElMessage.success('데이터를 새로고침했습니다')
  } catch (error) {
    console.error('Failed to refresh data:', error)
    ElMessage.error('데이터 새로고침에 실패했습니다')
  }
}

const formatTime = (timestamp: Date) => {
  const now = new Date()
  const diff = now.getTime() - timestamp.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  
  if (minutes < 1) return '방금 전'
  if (minutes < 60) return `${minutes}분 전`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}시간 전`
  
  const days = Math.floor(hours / 24)
  return `${days}일 전`
}

const getScoreType = (score: number) => {
  if (score >= 90) return 'success'
  if (score >= 70) return 'warning'
  return 'danger'
}

const handleReport = (reportId: number) => {
  // 신고 처리 페이지로 이동
  ElMessage.info('신고 처리 기능을 구현 중입니다')
}

onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.instructor-dashboard {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e4e7ed;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.page-description {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 8px;
}

.stat-title {
  font-weight: 500;
  color: #606266;
}

.stat-content {
  display: flex;
  align-items: baseline;
  gap: 8px;
  padding: 12px 0;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  color: #409eff;
}

.stat-number.pending {
  color: #f56c6c;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}

.content-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.activity-list,
.reports-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.activity-item,
.report-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.activity-avatar {
  flex-shrink: 0;
}

.activity-content,
.report-content {
  flex: 1;
  min-width: 0;
}

.activity-title,
.report-title {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.activity-description,
.report-description {
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
}

.activity-time,
.report-time {
  font-size: 12px;
  color: #909399;
}

.activity-score,
.report-actions {
  flex-shrink: 0;
}

.report-icon {
  flex-shrink: 0;
}

.collaboration-card {
  border-radius: 8px;
}

.collaboration-content {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 24px;
}

.recent-discussions h4,
.quick-actions h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.discussion-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.discussion-item {
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.discussion-item:last-child {
  border-bottom: none;
}

.discussion-title {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.discussion-meta {
  font-size: 12px;
  color: #909399;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.empty-state {
  text-align: center;
  padding: 20px;
  color: #909399;
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .content-row {
    grid-template-columns: 1fr;
  }

  .collaboration-content {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
    gap: 16px;
  }
}
</style>