<template>
  <div class="student-practice">
    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">문제 풀이</h1>
        <p class="page-description">
          실전과 같은 환경에서 문제를 풀어보고 실력을 점검하세요.
        </p>
      </div>
      <el-button type="primary" @click="loadCertificates">
        <el-icon><Refresh /></el-icon>
        새로고침
      </el-button>
    </div>

    <!-- Practice Mode Selection -->
    <el-card class="modes-card">
      <template #header>
        <div class="card-header">
          <span>연습 모드 선택</span>
        </div>
      </template>
      
      <div class="modes-list">
        <div class="mode-item" @click="selectMode('quick')">
          <div class="mode-info">
            <div class="mode-icon">⚡</div>
            <div class="mode-details">
              <h4 class="mode-title">빠른 연습</h4>
              <p class="mode-description">10-20문제로 구성된 짧은 연습 세션</p>
              <div class="mode-features">
                <span>10-20문제</span>
                <span>15-30분 소요</span>
                <span>즉시 결과 확인</span>
              </div>
            </div>
          </div>
          <el-button type="primary" size="small" @click.stop="selectMode('quick')">
            시작하기
          </el-button>
        </div>
        
        <div class="mode-item" @click="selectMode('mock')">
          <div class="mode-info">
            <div class="mode-icon">📝</div>
            <div class="mode-details">
              <h4 class="mode-title">모의고사</h4>
              <p class="mode-description">실제 시험과 동일한 조건의 모의고사</p>
              <div class="mode-features">
                <span>실제 문제 수</span>
                <span>실제 시험 시간</span>
                <span>상세한 성적표</span>
              </div>
            </div>
          </div>
          <el-button type="success" size="small" @click.stop="selectMode('mock')">
            시작하기
          </el-button>
        </div>
        
        <div class="mode-item" @click="selectMode('weak')">
          <div class="mode-info">
            <div class="mode-icon">🎯</div>
            <div class="mode-details">
              <h4 class="mode-title">약점 집중</h4>
              <p class="mode-description">틀렸던 문제와 취약 영역 집중 연습</p>
              <div class="mode-features">
                <span>개인맞춤 문제</span>
                <span>취약점 기반</span>
                <span>실력 향상 추적</span>
              </div>
            </div>
          </div>
          <el-button type="warning" size="small" @click.stop="selectMode('weak')">
            시작하기
          </el-button>
        </div>
        
        <div class="mode-item" @click="selectMode('custom')">
          <div class="mode-info">
            <div class="mode-icon">⚙️</div>
            <div class="mode-details">
              <h4 class="mode-title">맞춤 설정</h4>
              <p class="mode-description">문제 수, 시간, 난이도를 직접 설정</p>
              <div class="mode-features">
                <span>문제 수 선택</span>
                <span>시간 제한 설정</span>
                <span>난이도 조절</span>
              </div>
            </div>
          </div>
          <el-button type="info" size="small" @click.stop="selectMode('custom')">
            설정하기
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- Recent Practice Sessions -->
    <el-card class="sessions-card">
      <template #header>
        <div class="card-header">
          <span>최근 연습 기록</span>
        </div>
      </template>
      
      <div v-if="recentSessions.length === 0" class="empty-container">
        <el-empty description="아직 연습 기록이 없습니다">
          <el-button type="primary" @click="selectMode('quick')">
            첫 연습 시작하기
          </el-button>
        </el-empty>
      </div>
      
      <div v-else class="sessions-list">
        <div
          v-for="session in recentSessions"
          :key="session.id"
          class="session-item"
          @click="viewSessionDetail(session)"
        >
          <div class="session-header">
            <div class="session-info">
              <h4 class="session-title">{{ session.certificate_name }}</h4>
              <div class="session-tags">
                <el-tag :type="getScoreColor(session.score)" size="small">
                  {{ session.score }}점
                </el-tag>
                <el-tag size="small" type="info">
                  {{ getSessionTypeLabel(session.type) }}
                </el-tag>
              </div>
            </div>
          </div>
          
          <div class="session-details">
            <div class="detail-group">
              <span class="detail-label">정답률:</span>
              <span class="detail-value">{{ session.accuracy }}% ({{ session.correct_count }}/{{ session.total_questions }})</span>
            </div>
            <div class="detail-group">
              <span class="detail-label">소요시간:</span>
              <span class="detail-value">{{ session.duration }}분</span>
            </div>
            <div class="detail-group">
              <span class="detail-label">완료일:</span>
              <span class="detail-value">{{ formatRelativeTime(session.completed_at) }}</span>
            </div>
          </div>
          
          <div class="session-actions">
            <el-button type="text" size="small" @click.stop="viewSessionDetail(session)">
              <el-icon><View /></el-icon>
              상세보기
            </el-button>
            <el-button type="text" size="small" @click.stop="retrySession(session)">
              <el-icon><RefreshRight /></el-icon>
              다시풀기
            </el-button>
          </div>
        </div>
      </div>
    </el-card>

    <!-- Practice Setup Modal -->
    <el-dialog
      v-model="showSetupModal"
      :title="getSetupTitle()"
      width="600px"
      @close="resetSetup"
    >
      <div class="setup-content">
        <!-- Certificate Selection -->
        <div class="setup-section">
          <h3>자격증 선택</h3>
          <el-select
            v-model="practiceSetup.certificate_id"
            placeholder="연습할 자격증을 선택하세요"
            style="width: 100%"
            @change="loadCertificateInfo"
          >
            <el-option
              v-for="cert in availableCertificates"
              :key="cert.id"
              :label="cert.title"
              :value="cert.id"
            >
              <span style="float: left">{{ cert.title }}</span>
              <span style="float: right; color: #8492a6; font-size: 13px">
                {{ cert.category }}
              </span>
            </el-option>
          </el-select>
        </div>

        <!-- Mode-specific Settings -->
        <div v-if="selectedMode === 'custom'" class="setup-section">
          <h3>연습 설정</h3>
          <el-form :model="practiceSetup" label-width="120px">
            <el-form-item label="문제 수">
              <el-slider
                v-model="practiceSetup.question_count"
                :min="5"
                :max="50"
                :step="5"
                show-stops
                show-input
              />
            </el-form-item>
            
            <el-form-item label="시간 제한">
              <el-switch
                v-model="practiceSetup.time_limited"
                active-text="시간 제한 있음"
                inactive-text="시간 제한 없음"
              />
              <el-input-number
                v-if="practiceSetup.time_limited"
                v-model="practiceSetup.time_limit"
                :min="10"
                :max="180"
                controls-position="right"
                style="margin-left: 12px"
              />
              <span v-if="practiceSetup.time_limited" style="margin-left: 8px">분</span>
            </el-form-item>
            
            <el-form-item label="난이도">
              <el-radio-group v-model="practiceSetup.difficulty">
                <el-radio value="mixed">혼합</el-radio>
                <el-radio value="easy">쉬움</el-radio>
                <el-radio value="medium">보통</el-radio>
                <el-radio value="hard">어려움</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item label="문제 유형">
              <el-checkbox-group v-model="practiceSetup.question_types">
                <el-checkbox value="multiple_choice">객관식</el-checkbox>
                <el-checkbox value="true_false">참/거짓</el-checkbox>
                <el-checkbox value="fill_blank">빈칸 채우기</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-form>
        </div>

        <!-- Setup Summary -->
        <div v-if="practiceSetup.certificate_id" class="setup-summary">
          <h3>연습 정보</h3>
          <el-descriptions :column="2" size="small" border>
            <el-descriptions-item label="자격증">
              {{ getSelectedCertificateName() }}
            </el-descriptions-item>
            <el-descriptions-item label="모드">
              {{ getModeLabel(selectedMode) }}
            </el-descriptions-item>
            <el-descriptions-item label="문제 수">
              {{ getQuestionCount() }}문제
            </el-descriptions-item>
            <el-descriptions-item label="예상 시간">
              {{ getEstimatedTime() }}분
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
      
      <template #footer>
        <div class="modal-actions">
          <el-button @click="showSetupModal = false">취소</el-button>
          <el-button
            type="primary"
            @click="startPractice"
            :disabled="!practiceSetup.certificate_id"
          >
            연습 시작
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  View,
  RefreshRight,
  Lightning,
  Document,
  Target,
  Setting,
  Refresh,
} from '@element-plus/icons-vue'
import { formatRelativeTime } from '@/utils/format'

const router = useRouter()

// State
const showSetupModal = ref(false)
const selectedMode = ref('')
const availableCertificates = ref<any[]>([])

// Practice Setup
const practiceSetup = reactive({
  certificate_id: null,
  question_count: 20,
  time_limited: true,
  time_limit: 30,
  difficulty: 'mixed',
  question_types: ['multiple_choice'],
})

// Recent Sessions (Mock Data)
const recentSessions = ref([
  {
    id: 1,
    certificate_name: 'AWS Solutions Architect',
    type: 'quick',
    score: 85,
    correct_count: 17,
    total_questions: 20,
    accuracy: 85,
    duration: 25,
    completed_at: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 hours ago
  },
  {
    id: 2,
    certificate_name: 'Google Cloud Professional',
    type: 'mock',
    score: 78,
    correct_count: 47,
    total_questions: 60,
    accuracy: 78,
    duration: 120,
    completed_at: new Date(Date.now() - 24 * 60 * 60 * 1000), // 1 day ago
  },
  {
    id: 3,
    certificate_name: 'AWS Solutions Architect',
    type: 'weak',
    score: 92,
    correct_count: 14,
    total_questions: 15,
    accuracy: 93,
    duration: 18,
    completed_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000), // 3 days ago
  }
])

// Methods
const selectMode = (mode: string) => {
  selectedMode.value = mode
  showSetupModal.value = true
  loadCertificates()
}

const loadCertificates = async () => {
  try {
    const response = await fetch('http://localhost:8100/api/admin/certificates/list')
    const data = await response.json()
    
    if (data.success) {
      availableCertificates.value = data.certificates || []
    }
  } catch (error) {
    console.error('Failed to load certificates:', error)
    ElMessage.error('자격증 목록을 불러오는데 실패했습니다')
  }
}

const loadCertificateInfo = (certificateId: number) => {
  // Load specific certificate info if needed
  console.log('Loading certificate info for:', certificateId)
}

const startPractice = () => {
  if (!practiceSetup.certificate_id) {
    ElMessage.warning('자격증을 선택해주세요')
    return
  }
  
  showSetupModal.value = false
  
  // Navigate to practice session
  router.push({
    name: 'StudentPracticeDetail',
    params: { id: practiceSetup.certificate_id },
    query: {
      mode: selectedMode.value,
      questions: practiceSetup.question_count,
      timeLimit: practiceSetup.time_limited ? practiceSetup.time_limit : 0,
      difficulty: practiceSetup.difficulty,
    }
  })
}

const viewSessionDetail = (session: any) => {
  // Navigate to session detail view
  router.push(`/student/practice/session/${session.id}`)
}

const retrySession = (session: any) => {
  // Retry the same practice session
  ElMessage.info('동일한 설정으로 새로운 연습을 시작합니다')
  router.push({
    name: 'StudentPracticeDetail',
    params: { id: session.certificate_name }, // This should be certificate ID
    query: {
      mode: session.type,
      retry: 'true'
    }
  })
}

const resetSetup = () => {
  Object.assign(practiceSetup, {
    certificate_id: null,
    question_count: 20,
    time_limited: true,
    time_limit: 30,
    difficulty: 'mixed',
    question_types: ['multiple_choice'],
  })
}

// Helper functions
const getSetupTitle = () => {
  const titles = {
    quick: '빠른 연습 설정',
    mock: '모의고사 설정',
    weak: '약점 집중 연습 설정',
    custom: '맞춤 연습 설정'
  }
  return titles[selectedMode.value as keyof typeof titles] || '연습 설정'
}

const getModeLabel = (mode: string) => {
  const labels = {
    quick: '빠른 연습',
    mock: '모의고사',
    weak: '약점 집중',
    custom: '맞춤 설정'
  }
  return labels[mode as keyof typeof labels] || mode
}

const getSelectedCertificateName = () => {
  const cert = availableCertificates.value.find(c => c.id === practiceSetup.certificate_id)
  return cert?.title || ''
}

const getQuestionCount = () => {
  if (selectedMode.value === 'quick') return '10-20'
  if (selectedMode.value === 'mock') return '실제 문제 수'
  return practiceSetup.question_count
}

const getEstimatedTime = () => {
  if (selectedMode.value === 'quick') return '15-30'
  if (selectedMode.value === 'mock') return '실제 시험 시간'
  return practiceSetup.time_limit || 30
}

const getSessionIcon = (type: string) => {
  const icons = {
    quick: 'Lightning',
    mock: 'Document',
    weak: 'Target',
    custom: 'Setting'
  }
  return icons[type as keyof typeof icons] || 'Document'
}

const getSessionTypeLabel = (type: string) => {
  const labels = {
    quick: '빠른 연습',
    mock: '모의고사',
    weak: '약점 집중',
    custom: '맞춤 연습'
  }
  return labels[type as keyof typeof labels] || type
}

const getScoreColor = (score: number) => {
  if (score >= 90) return 'success'
  if (score >= 80) return 'primary'
  if (score >= 70) return 'warning'
  return 'danger'
}

// Initialize
onMounted(() => {
  // Load any initial data if needed
})
</script>

<style scoped>
.student-practice {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  margin: 0;
  color: #303133;
}

.page-description {
  margin: 8px 0 0 0;
  color: #606266;
}

.modes-card, .sessions-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-container {
  padding: 40px;
}

/* Mode Items */
.modes-list {
  
}

.mode-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mode-item:hover {
  background: #f0f9ff;
  border-color: #409eff;
}

.mode-info {
  display: flex;
  gap: 16px;
  flex: 1;
}

.mode-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  background: #f5f7fa;
  flex-shrink: 0;
}

.mode-details {
  flex: 1;
}

.mode-title {
  margin: 0 0 4px 0;
  color: #303133;
  font-size: 16px;
}

.mode-description {
  margin: 0 0 8px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.4;
}

.mode-features {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.mode-features span {
  padding: 2px 8px;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 12px;
  color: #909399;
}

/* Session Items */
.sessions-list {
  
}

.session-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.2s;
}

.session-item:hover {
  background: #f0f9ff;
  border-color: #409eff;
}

.session-header {
  margin-bottom: 12px;
}

.session-info {
  
}

.session-title {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 16px;
}

.session-tags {
  display: flex;
  gap: 8px;
}

.session-details {
  margin-bottom: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 8px;
}

.detail-group {
  display: flex;
  font-size: 14px;
}

.detail-label {
  color: #909399;
  min-width: 70px;
}

.detail-value {
  color: #303133;
  font-weight: 500;
}

.session-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

/* Modal Styles */
.setup-content {
  padding: 20px 0;
}

.setup-section {
  margin-bottom: 24px;
}

.setup-section h3 {
  margin: 0 0 16px 0;
  color: #303133;
}

.setup-summary {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
}

.modal-actions {
  display: flex;
  gap: 12px;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .mode-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .mode-info {
    width: 100%;
  }
  
  .session-details {
    grid-template-columns: 1fr;
  }
  
  .session-actions {
    justify-content: flex-start;
  }
}
</style>