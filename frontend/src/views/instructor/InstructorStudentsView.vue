<template>
  <div class="instructor-students">
    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">학습자 관리</h1>
        <p class="page-description">
          내 자격증을 학습 중인 학습자들의 진행 상황을 확인하고 관리하세요.
        </p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="exportStudentData">
          <el-icon><Download /></el-icon>
          데이터 내보내기
        </el-button>
      </div>
    </div>

    <!-- 필터 및 검색 -->
    <el-card class="filter-card">
      <div class="filter-row">
        <div class="filter-left">
          <el-input
            v-model="searchQuery"
            placeholder="학습자 이름 또는 이메일 검색..."
            :prefix-icon="Search"
            clearable
            @input="handleSearch"
            style="width: 300px; margin-right: 16px;"
          />
          <el-select
            v-model="selectedCertificate"
            placeholder="자격증 선택"
            clearable
            style="width: 200px; margin-right: 16px;"
          >
            <el-option label="모든 자격증" value="" />
            <el-option 
              v-for="cert in certificates" 
              :key="cert.id" 
              :label="cert.name" 
              :value="cert.id" 
            />
          </el-select>
          <el-select
            v-model="selectedStatus"
            placeholder="학습 상태"
            clearable
            style="width: 150px;"
          >
            <el-option label="모든 상태" value="" />
            <el-option label="학습 중" value="active" />
            <el-option label="완료" value="completed" />
            <el-option label="중단" value="paused" />
          </el-select>
        </div>
        <div class="filter-right">
          <el-button @click="resetFilters">초기화</el-button>
          <el-button type="primary" @click="applyFilters">적용</el-button>
        </div>
      </div>
    </el-card>

    <!-- 학습자 목록 -->
    <el-card class="students-card">
      <template #header>
        <div class="card-header">
          <span>학습자 목록 ({{ filteredStudents.length }}명)</span>
          <div class="view-options">
            <el-radio-group v-model="viewMode" size="small">
              <el-radio-button label="list">목록</el-radio-button>
              <el-radio-button label="grid">카드</el-radio-button>
            </el-radio-group>
          </div>
        </div>
      </template>

      <!-- 목록 뷰 -->
      <div v-if="viewMode === 'list'" class="list-view">
        <el-table :data="filteredStudents" style="width: 100%">
          <el-table-column prop="name" label="학습자" width="200">
            <template #default="{ row }">
              <div class="student-info">
                <el-avatar :size="32">{{ row.name.charAt(0) }}</el-avatar>
                <div class="student-details">
                  <div class="student-name">{{ row.name }}</div>
                  <div class="student-email">{{ row.email }}</div>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column prop="certificate" label="학습 자격증" width="250">
            <template #default="{ row }">
              <el-tag type="info">{{ row.certificate }}</el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="progress" label="진행률" width="150">
            <template #default="{ row }">
              <el-progress 
                :percentage="row.progress" 
                :status="row.progress === 100 ? 'success' : ''" 
                :stroke-width="6"
              />
            </template>
          </el-table-column>

          <el-table-column prop="lastActivity" label="최근 활동" width="150">
            <template #default="{ row }">
              {{ formatDate(row.lastActivity) }}
            </template>
          </el-table-column>

          <el-table-column prop="averageScore" label="평균 점수" width="120">
            <template #default="{ row }">
              <el-tag :type="getScoreType(row.averageScore)">
                {{ row.averageScore }}점
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="status" label="상태" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column label="작업" width="200" fixed="right">
            <template #default="{ row }">
              <el-button 
                type="primary" 
                size="small" 
                @click="viewStudentDetail(row.id)"
              >
                상세보기
              </el-button>
              <el-button 
                size="small" 
                @click="sendMessage(row.id)"
              >
                메시지
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 카드 뷰 -->
      <div v-else class="grid-view">
        <div 
          v-for="student in filteredStudents" 
          :key="student.id"
          class="student-card"
        >
          <div class="student-header">
            <el-avatar :size="48">{{ student.name.charAt(0) }}</el-avatar>
            <div class="student-info">
              <h4 class="student-name">{{ student.name }}</h4>
              <p class="student-email">{{ student.email }}</p>
            </div>
            <el-tag :type="getStatusType(student.status)" size="small">
              {{ getStatusText(student.status) }}
            </el-tag>
          </div>

          <div class="student-content">
            <div class="study-info">
              <div class="info-item">
                <span class="label">자격증:</span>
                <span class="value">{{ student.certificate }}</span>
              </div>
              <div class="info-item">
                <span class="label">평균 점수:</span>
                <el-tag :type="getScoreType(student.averageScore)" size="small">
                  {{ student.averageScore }}점
                </el-tag>
              </div>
            </div>

            <div class="progress-section">
              <div class="progress-label">
                학습 진행률 ({{ student.progress }}%)
              </div>
              <el-progress 
                :percentage="student.progress" 
                :status="student.progress === 100 ? 'success' : ''"
              />
            </div>

            <div class="activity-info">
              <span class="activity-label">최근 활동:</span>
              <span class="activity-date">{{ formatDate(student.lastActivity) }}</span>
            </div>
          </div>

          <div class="student-actions">
            <el-button 
              type="primary" 
              size="small" 
              @click="viewStudentDetail(student.id)"
            >
              상세보기
            </el-button>
            <el-button 
              size="small" 
              @click="sendMessage(student.id)"
            >
              메시지 보내기
            </el-button>
          </div>
        </div>
      </div>

      <!-- 빈 상태 -->
      <div v-if="filteredStudents.length === 0" class="empty-state">
        <el-empty description="조건에 맞는 학습자가 없습니다" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Download } from '@element-plus/icons-vue'

const router = useRouter()

// 필터 상태
const searchQuery = ref('')
const selectedCertificate = ref('')
const selectedStatus = ref('')
const viewMode = ref('list')

// 자격증 목록
const certificates = ref([
  { id: 1, name: 'AWS Solutions Architect Associate' },
  { id: 2, name: 'Google Cloud Professional Cloud Architect' },
  { id: 3, name: 'Microsoft Azure Fundamentals' },
  { id: 4, name: 'CompTIA Security+' },
  { id: 5, name: 'CISSP' }
])

// 학습자 데이터 (실제로는 API에서 가져올 예정)
const students = ref([
  {
    id: 1,
    name: '김학생',
    email: 'student1@example.com',
    certificate: 'AWS Solutions Architect Associate',
    progress: 75,
    averageScore: 85,
    status: 'active',
    lastActivity: new Date(Date.now() - 2 * 60 * 60 * 1000),
    totalStudyTime: 120,
    completedTests: 8
  },
  {
    id: 2,
    name: '이학습',
    email: 'student2@example.com',
    certificate: 'Google Cloud Professional Cloud Architect',
    progress: 100,
    averageScore: 92,
    status: 'completed',
    lastActivity: new Date(Date.now() - 24 * 60 * 60 * 1000),
    totalStudyTime: 200,
    completedTests: 15
  },
  {
    id: 3,
    name: '박공부',
    email: 'student3@example.com',
    certificate: 'CompTIA Security+',
    progress: 45,
    averageScore: 78,
    status: 'active',
    lastActivity: new Date(Date.now() - 6 * 60 * 60 * 1000),
    totalStudyTime: 80,
    completedTests: 5
  },
  {
    id: 4,
    name: '정열공',
    email: 'student4@example.com',
    certificate: 'Microsoft Azure Fundamentals',
    progress: 30,
    averageScore: 65,
    status: 'paused',
    lastActivity: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    totalStudyTime: 45,
    completedTests: 3
  }
])

// 필터된 학습자 목록
const filteredStudents = computed(() => {
  let result = students.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(student => 
      student.name.toLowerCase().includes(query) ||
      student.email.toLowerCase().includes(query)
    )
  }

  if (selectedCertificate.value) {
    result = result.filter(student => student.certificate.includes(selectedCertificate.value))
  }

  if (selectedStatus.value) {
    result = result.filter(student => student.status === selectedStatus.value)
  }

  return result
})

// 메서드
const handleSearch = () => {
  // 검색 로직은 computed에서 처리
}

const resetFilters = () => {
  searchQuery.value = ''
  selectedCertificate.value = ''
  selectedStatus.value = ''
}

const applyFilters = () => {
  ElMessage.success('필터가 적용되었습니다')
}

const exportStudentData = () => {
  // TODO: 실제 데이터 내보내기 구현
  ElMessage.success('학습자 데이터를 내보내는 중입니다')
}

const viewStudentDetail = (studentId: number) => {
  router.push(`/instructor/students/${studentId}`)
}

const sendMessage = (studentId: number) => {
  // TODO: 메시지 보내기 기능 구현
  ElMessage.info('메시지 보내기 기능을 구현 중입니다')
}

const formatDate = (date: Date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))
  
  if (hours < 1) return '방금 전'
  if (hours < 24) return `${hours}시간 전`
  
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}일 전`
  
  return date.toLocaleDateString('ko-KR')
}

const getScoreType = (score: number) => {
  if (score >= 90) return 'success'
  if (score >= 70) return 'warning'
  return 'danger'
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'active': return 'success'
    case 'completed': return 'primary'
    case 'paused': return 'warning'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'active': return '학습 중'
    case 'completed': return '완료'
    case 'paused': return '중단'
    default: return '알 수 없음'
  }
}

onMounted(() => {
  // 학습자 데이터 로드
})
</script>

<style scoped>
.instructor-students {
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

.filter-card {
  margin-bottom: 24px;
}

.filter-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-left {
  display: flex;
  align-items: center;
  flex: 1;
}

.filter-right {
  display: flex;
  gap: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.student-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.student-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.student-name {
  font-weight: 500;
  color: #303133;
}

.student-email {
  font-size: 12px;
  color: #909399;
}

/* 카드 뷰 스타일 */
.grid-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.student-card {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  background: white;
  transition: shadow 0.3s ease;
}

.student-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.student-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.student-header .student-info {
  flex: 1;
  gap: 4px;
}

.student-header .student-name {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.student-header .student-email {
  margin: 0;
  font-size: 13px;
  color: #606266;
}

.student-content {
  margin-bottom: 16px;
}

.study-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-item .label {
  font-size: 14px;
  color: #606266;
}

.info-item .value {
  font-size: 14px;
  color: #303133;
}

.progress-section {
  margin-bottom: 12px;
}

.progress-label {
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
}

.activity-info {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.activity-label {
  color: #606266;
}

.activity-date {
  color: #909399;
}

.student-actions {
  display: flex;
  gap: 8px;
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
}

.student-actions .el-button {
  flex: 1;
}

.empty-state {
  text-align: center;
  padding: 40px;
}

@media (max-width: 768px) {
  .filter-row {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .filter-left {
    flex-direction: column;
    gap: 12px;
  }

  .grid-view {
    grid-template-columns: 1fr;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
}
</style>