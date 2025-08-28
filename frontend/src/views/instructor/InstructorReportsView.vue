<template>
  <div class="instructor-reports">
    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">신고 관리</h1>
        <p class="page-description">
          학습자들이 신고한 AI 생성 자료 오류를 검토하고 수정하세요.
        </p>
      </div>
      <div class="header-actions">
        <el-button type="success" @click="bulkApprove" :disabled="selectedReports.length === 0">
          <el-icon><Check /></el-icon>
          일괄 승인
        </el-button>
        <el-button @click="refreshReports">
          <el-icon><Refresh /></el-icon>
          새로고침
        </el-button>
      </div>
    </div>

    <!-- 필터 -->
    <el-card class="filter-card">
      <div class="filter-row">
        <div class="filter-left">
          <el-input
            v-model="searchQuery"
            placeholder="신고 제목 또는 내용 검색..."
            :prefix-icon="Search"
            clearable
            style="width: 300px; margin-right: 16px;"
          />
          <el-select
            v-model="selectedStatus"
            placeholder="처리 상태"
            clearable
            style="width: 150px; margin-right: 16px;"
          >
            <el-option label="모든 상태" value="" />
            <el-option label="처리 대기" value="pending" />
            <el-option label="검토 중" value="reviewing" />
            <el-option label="승인됨" value="approved" />
            <el-option label="거부됨" value="rejected" />
          </el-select>
          <el-select
            v-model="selectedType"
            placeholder="신고 유형"
            clearable
            style="width: 180px; margin-right: 16px;"
          >
            <el-option label="모든 유형" value="" />
            <el-option label="문제 오류" value="question_error" />
            <el-option label="내용 부정확" value="content_inaccuracy" />
            <el-option label="번역 오류" value="translation_error" />
            <el-option label="기타" value="other" />
          </el-select>
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="~"
            start-placeholder="시작 날짜"
            end-placeholder="끝 날짜"
            style="width: 240px;"
          />
        </div>
        <div class="filter-right">
          <el-button @click="resetFilters">초기화</el-button>
          <el-button type="primary" @click="applyFilters">적용</el-button>
        </div>
      </div>
    </el-card>

    <!-- 신고 목록 -->
    <el-card class="reports-card">
      <template #header>
        <div class="card-header">
          <span>신고 목록 ({{ filteredReports.length }}건)</span>
          <div class="status-stats">
            <el-tag type="warning" size="small">
              대기: {{ getStatusCount('pending') }}
            </el-tag>
            <el-tag type="info" size="small">
              검토: {{ getStatusCount('reviewing') }}
            </el-tag>
            <el-tag type="success" size="small">
              완료: {{ getStatusCount('approved') }}
            </el-tag>
          </div>
        </div>
      </template>

      <el-table 
        :data="filteredReports" 
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="title" label="제목" width="250">
          <template #default="{ row }">
            <div class="report-title">
              <el-icon class="report-icon" :color="getTypeColor(row.type)">
                <component :is="getTypeIcon(row.type)" />
              </el-icon>
              <div>
                <div class="title-text">{{ row.title }}</div>
                <div class="report-meta">
                  {{ getTypeText(row.type) }} · 
                  신고자: {{ row.reporter }}
                </div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="content" label="내용" min-width="200">
          <template #default="{ row }">
            <div class="report-content">
              {{ row.description }}
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="certificate" label="자격증" width="180">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.certificate }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="priority" label="우선순위" width="100">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" size="small">
              {{ getPriorityText(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="상태" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="createdAt" label="신고일" width="120">
          <template #default="{ row }">
            {{ formatDate(row.createdAt) }}
          </template>
        </el-table-column>

        <el-table-column label="작업" width="200" fixed="right">
          <template #default="{ row }">
            <el-dropdown trigger="click" @command="(command) => handleAction(command, row)">
              <el-button type="primary" size="small">
                처리하기 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="review" :disabled="row.status !== 'pending'">
                    <el-icon><View /></el-icon>
                    상세 검토
                  </el-dropdown-item>
                  <el-dropdown-item command="approve" :disabled="row.status === 'approved'">
                    <el-icon><Check /></el-icon>
                    승인
                  </el-dropdown-item>
                  <el-dropdown-item command="reject" :disabled="row.status === 'rejected'">
                    <el-icon><Close /></el-icon>
                    거부
                  </el-dropdown-item>
                  <el-dropdown-item command="edit" divided>
                    <el-icon><Edit /></el-icon>
                    내용 수정
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="filteredReports.length === 0" class="empty-state">
        <el-empty description="조건에 맞는 신고가 없습니다" />
      </div>
    </el-card>

    <!-- 신고 상세 모달 -->
    <el-dialog
      v-model="showDetailModal"
      title="신고 상세 내용"
      width="60%"
      :before-close="closeDetailModal"
    >
      <div v-if="selectedReport" class="report-detail">
        <div class="detail-section">
          <h4>신고 정보</h4>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="제목">
              {{ selectedReport.title }}
            </el-descriptions-item>
            <el-descriptions-item label="신고자">
              {{ selectedReport.reporter }}
            </el-descriptions-item>
            <el-descriptions-item label="신고 유형">
              <el-tag :type="getTypeColor(selectedReport.type)" size="small">
                {{ getTypeText(selectedReport.type) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="우선순위">
              <el-tag :type="getPriorityType(selectedReport.priority)" size="small">
                {{ getPriorityText(selectedReport.priority) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="관련 자격증">
              {{ selectedReport.certificate }}
            </el-descriptions-item>
            <el-descriptions-item label="신고일">
              {{ formatDateTime(selectedReport.createdAt) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="detail-section">
          <h4>신고 내용</h4>
          <div class="report-description">
            {{ selectedReport.description }}
          </div>
        </div>

        <div class="detail-section" v-if="selectedReport.screenshots">
          <h4>첨부 스크린샷</h4>
          <div class="screenshots">
            <el-image
              v-for="(screenshot, index) in selectedReport.screenshots"
              :key="index"
              :src="screenshot"
              :preview-src-list="selectedReport.screenshots"
              :initial-index="index"
              fit="cover"
              style="width: 150px; height: 100px; margin-right: 8px;"
            />
          </div>
        </div>

        <div class="detail-section">
          <h4>처리 결과</h4>
          <el-form :model="reviewForm" label-width="100px">
            <el-form-item label="처리 상태">
              <el-radio-group v-model="reviewForm.status">
                <el-radio label="approved">승인</el-radio>
                <el-radio label="rejected">거부</el-radio>
                <el-radio label="reviewing">검토 중</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="처리 의견">
              <el-input
                v-model="reviewForm.comment"
                type="textarea"
                :rows="4"
                placeholder="처리 결과에 대한 설명을 입력하세요..."
              />
            </el-form-item>
          </el-form>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="closeDetailModal">취소</el-button>
          <el-button type="primary" @click="submitReview">
            처리 완료
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  Check,
  Close,
  Edit,
  View,
  ArrowDown,
  Warning,
  Document,
  QuestionFilled
} from '@element-plus/icons-vue'

// 필터 상태
const searchQuery = ref('')
const selectedStatus = ref('')
const selectedType = ref('')
const dateRange = ref([])

// 선택된 신고 목록
const selectedReports = ref([])

// 모달 상태
const showDetailModal = ref(false)
const selectedReport = ref(null)
const reviewForm = ref({
  status: 'reviewing',
  comment: ''
})

// 신고 데이터 (실제로는 API에서 가져올 예정)
const reports = ref([
  {
    id: 1,
    title: 'AWS 문제 정답 오류',
    description: 'EC2 인스턴스 유형에 관한 문제에서 정답이 잘못 표시됩니다. t2.micro가 정답인데 t2.small로 표시되어 있어요.',
    type: 'question_error',
    certificate: 'AWS Solutions Architect Associate',
    reporter: '김학생',
    priority: 'high',
    status: 'pending',
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000),
    screenshots: null
  },
  {
    id: 2,
    title: '클라우드 보안 내용 부정확',
    description: '보안 그룹에 대한 설명에서 포트 설정 예시가 현재 AWS 콘솔과 다릅니다. 최신 정보로 업데이트가 필요합니다.',
    type: 'content_inaccuracy',
    certificate: 'AWS Solutions Architect Associate',
    reporter: '이학습',
    priority: 'medium',
    status: 'reviewing',
    createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000),
    screenshots: ['/screenshots/security-group-1.png', '/screenshots/security-group-2.png']
  },
  {
    id: 3,
    title: '번역 오류 신고',
    description: 'Lambda 함수 설명에서 "실행 시간"이 "runtime"으로 번역되어야 하는데 "execution time"으로 번역되어 있습니다.',
    type: 'translation_error',
    certificate: 'AWS Solutions Architect Associate',
    reporter: '박공부',
    priority: 'low',
    status: 'approved',
    createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000),
    screenshots: null
  },
  {
    id: 4,
    title: 'CompTIA 문제 중복',
    description: '보안 원칙에 관한 문제가 3번과 15번에서 동일한 내용으로 출제되었습니다.',
    type: 'question_error',
    certificate: 'CompTIA Security+',
    reporter: '정열공',
    priority: 'medium',
    status: 'pending',
    createdAt: new Date(Date.now() - 6 * 60 * 60 * 1000),
    screenshots: null
  }
])

// 필터된 신고 목록
const filteredReports = computed(() => {
  let result = reports.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(report => 
      report.title.toLowerCase().includes(query) ||
      report.description.toLowerCase().includes(query)
    )
  }

  if (selectedStatus.value) {
    result = result.filter(report => report.status === selectedStatus.value)
  }

  if (selectedType.value) {
    result = result.filter(report => report.type === selectedType.value)
  }

  return result.sort((a, b) => {
    // 우선순위 정렬 (high > medium > low)
    const priorityOrder = { high: 3, medium: 2, low: 1 }
    if (priorityOrder[a.priority] !== priorityOrder[b.priority]) {
      return priorityOrder[b.priority] - priorityOrder[a.priority]
    }
    // 날짜 정렬 (최신순)
    return b.createdAt.getTime() - a.createdAt.getTime()
  })
})

// 메서드
const getStatusCount = (status: string) => {
  return reports.value.filter(report => report.status === status).length
}

const getTypeColor = (type: string) => {
  switch (type) {
    case 'question_error': return '#f56c6c'
    case 'content_inaccuracy': return '#e6a23c'
    case 'translation_error': return '#409eff'
    case 'other': return '#909399'
    default: return '#909399'
  }
}

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'question_error': return QuestionFilled
    case 'content_inaccuracy': return Document
    case 'translation_error': return Edit
    case 'other': return Warning
    default: return Warning
  }
}

const getTypeText = (type: string) => {
  switch (type) {
    case 'question_error': return '문제 오류'
    case 'content_inaccuracy': return '내용 부정확'
    case 'translation_error': return '번역 오류'
    case 'other': return '기타'
    default: return '알 수 없음'
  }
}

const getPriorityType = (priority: string) => {
  switch (priority) {
    case 'high': return 'danger'
    case 'medium': return 'warning'
    case 'low': return 'info'
    default: return 'info'
  }
}

const getPriorityText = (priority: string) => {
  switch (priority) {
    case 'high': return '높음'
    case 'medium': return '보통'
    case 'low': return '낮음'
    default: return '보통'
  }
}

const getStatusType = (status: string) => {
  switch (status) {
    case 'pending': return 'warning'
    case 'reviewing': return 'info'
    case 'approved': return 'success'
    case 'rejected': return 'danger'
    default: return 'info'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'pending': return '대기'
    case 'reviewing': return '검토 중'
    case 'approved': return '승인됨'
    case 'rejected': return '거부됨'
    default: return '알 수 없음'
  }
}

const formatDate = (date: Date) => {
  return date.toLocaleDateString('ko-KR', {
    month: '2-digit',
    day: '2-digit'
  })
}

const formatDateTime = (date: Date) => {
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const handleSelectionChange = (selection: any[]) => {
  selectedReports.value = selection
}

const resetFilters = () => {
  searchQuery.value = ''
  selectedStatus.value = ''
  selectedType.value = ''
  dateRange.value = []
}

const applyFilters = () => {
  ElMessage.success('필터가 적용되었습니다')
}

const refreshReports = async () => {
  try {
    // TODO: API 호출
    ElMessage.success('신고 목록을 새로고침했습니다')
  } catch (error) {
    ElMessage.error('새로고침에 실패했습니다')
  }
}

const bulkApprove = async () => {
  try {
    await ElMessageBox.confirm(
      `선택된 ${selectedReports.value.length}건의 신고를 모두 승인하시겠습니까?`,
      '일괄 승인',
      {
        confirmButtonText: '승인',
        cancelButtonText: '취소',
        type: 'warning'
      }
    )
    
    // TODO: 실제 일괄 승인 처리
    ElMessage.success('선택된 신고가 모두 승인되었습니다')
    selectedReports.value = []
  } catch {
    // User cancelled
  }
}

const handleAction = async (command: string, report: any) => {
  switch (command) {
    case 'review':
      selectedReport.value = report
      reviewForm.value.status = report.status
      reviewForm.value.comment = ''
      showDetailModal.value = true
      break
    case 'approve':
      await approveReport(report)
      break
    case 'reject':
      await rejectReport(report)
      break
    case 'edit':
      ElMessage.info('내용 수정 기능을 구현 중입니다')
      break
  }
}

const approveReport = async (report: any) => {
  try {
    report.status = 'approved'
    ElMessage.success('신고가 승인되었습니다')
  } catch (error) {
    ElMessage.error('신고 승인에 실패했습니다')
  }
}

const rejectReport = async (report: any) => {
  try {
    await ElMessageBox.confirm(
      '이 신고를 거부하시겠습니까?',
      '신고 거부',
      {
        confirmButtonText: '거부',
        cancelButtonText: '취소',
        type: 'warning'
      }
    )
    
    report.status = 'rejected'
    ElMessage.success('신고가 거부되었습니다')
  } catch {
    // User cancelled
  }
}

const closeDetailModal = () => {
  showDetailModal.value = false
  selectedReport.value = null
  reviewForm.value = {
    status: 'reviewing',
    comment: ''
  }
}

const submitReview = async () => {
  try {
    if (selectedReport.value) {
      selectedReport.value.status = reviewForm.value.status
      // TODO: API 호출로 실제 처리
    }
    ElMessage.success('신고 처리가 완료되었습니다')
    closeDetailModal()
  } catch (error) {
    ElMessage.error('신고 처리에 실패했습니다')
  }
}

onMounted(() => {
  // 신고 데이터 로드
})
</script>

<style scoped>
.instructor-reports {
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

.header-actions {
  display: flex;
  gap: 8px;
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

.status-stats {
  display: flex;
  gap: 8px;
}

.report-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.report-icon {
  font-size: 16px;
}

.title-text {
  font-weight: 500;
  color: #303133;
  margin-bottom: 4px;
}

.report-meta {
  font-size: 12px;
  color: #909399;
}

.report-content {
  color: #606266;
  font-size: 14px;
  line-height: 1.4;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-state {
  text-align: center;
  padding: 40px;
}

/* 모달 스타일 */
.report-detail .detail-section {
  margin-bottom: 24px;
}

.report-detail h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.report-description {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 6px;
  color: #606266;
  line-height: 1.6;
}

.screenshots {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.dialog-footer {
  display: flex;
  gap: 8px;
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

  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }

  .header-actions {
    justify-content: flex-start;
  }
}
</style>