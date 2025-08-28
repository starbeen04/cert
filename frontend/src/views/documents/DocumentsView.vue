<template>
  <div class="documents-view">
    <div class="container">
      <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <el-icon class="title-icon"><Document /></el-icon>
            처리된 문서 관리
          </h1>
          <p class="page-description">PDF 문서 처리 결과 및 추출된 문제 관리</p>
        </div>
        <div class="stats-section">
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ totalDocuments }}</div>
              <div class="stat-label">전체 문서</div>
            </div>
          </el-card>
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ completedCount }}</div>
              <div class="stat-label">처리 완료</div>
            </div>
          </el-card>
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ pendingCount }}</div>
              <div class="stat-label">대기중</div>
            </div>
          </el-card>
          <el-card class="stat-card">
            <div class="stat-item">
              <div class="stat-value">{{ failedCount }}</div>
              <div class="stat-label">처리 실패</div>
            </div>
          </el-card>
        </div>
      </div>
    </div>

    <!-- Actions Bar -->
    <div class="actions-bar">
      <div class="search-section">
        <el-input
          v-model="searchQuery"
          placeholder="문서명으로 검색..."
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
          style="width: 300px"
        />
        <el-select
          v-model="statusFilter"
          placeholder="처리 상태"
          clearable
          @change="handleSearch"
          style="width: 120px; margin-left: 12px"
        >
          <el-option label="전체" value="" />
          <el-option label="완료" value="completed" />
          <el-option label="처리중" value="processing" />
          <el-option label="실패" value="failed" />
          <el-option label="대기중" value="pending" />
        </el-select>
        <el-select
          v-model="activeFilter"
          placeholder="활성 상태"
          clearable
          @change="handleSearch"
          style="width: 120px; margin-left: 12px"
        >
          <el-option label="전체" value="" />
          <el-option label="활성" value="true" />
          <el-option label="비활성" value="false" />
        </el-select>
        <el-select
          v-model="certificateFilter"
          placeholder="자격증"
          clearable
          @change="handleSearch"
          style="width: 160px; margin-left: 12px"
        >
          <el-option label="전체" value="" />
          <el-option
            v-for="cert in availableCertificates"
            :key="cert"
            :label="cert"
            :value="cert"
          />
        </el-select>
        <el-select
          v-model="typeFilter"
          placeholder="파일 유형"
          clearable
          @change="handleSearch"
          style="width: 120px; margin-left: 12px"
        >
          <el-option label="전체" value="" />
          <el-option label="문제집" value="questions" />
          <el-option label="학습자료" value="study_material" />
          <el-option label="통합" value="both" />
        </el-select>
      </div>
      
      <div class="action-buttons">
        <el-button :icon="Refresh" @click="refreshDocuments">
          새로고침
        </el-button>
        <el-button 
          type="primary" 
          :icon="Upload" 
          @click="$router.push('/admin/upload')"
        >
          문서 업로드
        </el-button>
      </div>
    </div>

    <!-- 일괄 작업 섹션 -->
    <el-row v-if="selectedDocuments.length > 0" class="bulk-actions-section">
      <el-col :span="24">
        <el-card class="bulk-card" shadow="never">
          <div class="bulk-header">
            <div class="bulk-info">
              <el-icon class="bulk-icon"><Select /></el-icon>
              <span class="bulk-text">{{ selectedDocuments.length }}개 문서 선택됨</span>
            </div>
            <div class="bulk-actions">
              <el-button 
                type="success" 
                size="small"
                @click="bulkToggleStatus(true)"
                :disabled="isBulkProcessing"
                :icon="Check"
              >
                활성화
              </el-button>
              <el-button 
                type="warning" 
                size="small"
                @click="bulkToggleStatus(false)"
                :disabled="isBulkProcessing"
                :icon="Close"
              >
                비활성화
              </el-button>
              <el-button 
                type="primary" 
                size="small"
                @click="bulkReprocess"
                :disabled="isBulkProcessing"
                :icon="Refresh"
              >
                재처리
              </el-button>
              <el-button 
                type="info" 
                size="small"
                @click="showBulkEditDialog = true"
                :disabled="isBulkProcessing"
                :icon="Edit"
              >
                정보 수정
              </el-button>
              <el-button 
                type="danger" 
                size="small"
                @click="bulkDelete"
                :disabled="isBulkProcessing"
                :icon="Delete"
              >
                삭제
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 문서 목록 -->
    <el-card class="documents-card">
      <el-table
        v-loading="isLoading"
        :data="documents"
        stripe
        @sort-change="handleSortChange"
        @row-click="viewDocument"
        @selection-change="handleSelectionChange"
        style="cursor: pointer"
      >
        <el-table-column
          type="selection"
          width="60"
          :selectable="row => true"
        />
        
        
        <el-table-column
          prop="original_name"
          label="문서명"
          min-width="200"
          sortable
          show-overflow-tooltip
        >
          <template #default="scope">
            <div class="document-info">
              <div class="document-icon">
                <el-icon size="16" color="#f56c6c"><Document /></el-icon>
              </div>
              <div class="document-details">
                <div class="document-name">{{ scope.row.original_name }}</div>
                <div class="document-size">{{ formatFileSize(scope.row.file_size) }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column
          prop="certificate_name"
          label="자격증"
          width="120"
          sortable
          show-overflow-tooltip
          align="center"
        >
          <template #default="scope">
            <el-tag type="info" size="small" effect="plain" class="cert-tag">
              {{ scope.row.certificate_name || '미지정' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          prop="file_type"
          label="유형"
          width="110"
          sortable
          align="center"
        >
          <template #default="scope">
            <el-tag 
              :type="getFileTypeColor(scope.row.file_type)" 
              size="small"
            >
              {{ getFileTypeLabel(scope.row.file_type) }}
            </el-tag>
          </template>
        </el-table-column>


        <el-table-column
          prop="processing_status"
          label="처리상태"
          width="120"
          sortable
          align="center"
        >
          <template #default="scope">
            <el-tag 
              :type="getStatusColor(scope.row.processing_status)" 
              size="small"
            >
              <el-icon v-if="scope.row.processing_status === 'processing'" class="is-loading">
                <Loading />
              </el-icon>
              {{ getStatusLabel(scope.row.processing_status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          label="추출결과"
          width="120"
          align="center"
        >
          <template #default="scope">
            <div v-if="scope.row.processing_status === 'completed'" class="extraction-stats-horizontal">
              <div class="stat-row">
                <el-icon size="12" color="#67c23a"><QuestionFilled /></el-icon>
                <span>{{ scope.row.questions_count || 0 }}개</span>
              </div>
              <div class="stat-row">
                <el-icon size="12" color="#409eff"><Reading /></el-icon>
                <span>{{ scope.row.materials_count || 0 }}개</span>
              </div>
            </div>
            <span v-else class="no-data">-</span>
          </template>
        </el-table-column>

        <el-table-column
          prop="upload_date"
          label="업로드일"
          width="130"
          sortable
          align="center"
        >
          <template #default="scope">
            {{ formatDateShort(scope.row.upload_date) }}
          </template>
        </el-table-column>

        <el-table-column
          prop="processed_date"
          label="처리완료일"
          width="130"
          sortable
          align="center"
        >
          <template #default="scope">
            {{ scope.row.processed_date ? formatDateShort(scope.row.processed_date) : '-' }}
          </template>
        </el-table-column>

        <el-table-column
          label="작업"
          width="180"
          align="center"
        >
          <template #default="scope">
            <div class="action-controls-new">
              <div class="status-switch">
                <el-switch
                  v-model="scope.row.is_active"
                  size="small"
                  :disabled="scope.row.processing_status !== 'completed'"
                  @change="toggleDocumentStatus(scope.row)"
                />
              </div>
              <div class="action-buttons-horizontal">
                <el-tooltip v-if="scope.row.processing_status === 'completed'" content="결과 보기" placement="top">
                  <el-button
                    class="action-btn"
                    type="primary"
                    :icon="View"
                    @click.stop="viewResults(scope.row)"
                    circle
                    size="small"
                  />
                </el-tooltip>
                <el-tooltip v-if="scope.row.processing_status === 'failed' || scope.row.processing_status === 'pending'" content="재처리" placement="top">
                  <el-button
                    class="action-btn"
                    type="warning"
                    :icon="Refresh"
                    @click.stop="reprocessDocument(scope.row)"
                    circle
                    size="small"
                  />
                </el-tooltip>
                <el-tooltip content="편집" placement="top">
                  <el-button
                    class="action-btn"
                    type="info"
                    :icon="Edit"
                    @click.stop="editDocument(scope.row)"
                    circle
                    size="small"
                  />
                </el-tooltip>
                <el-tooltip content="삭제" placement="top">
                  <el-button
                    class="action-btn"
                    type="danger"
                    :icon="Delete"
                    @click.stop="deleteDocument(scope.row)"
                    circle
                    size="small"
                  />
                </el-tooltip>
              </div>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- 페이지네이션 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalDocuments"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 결과 상세보기 다이얼로그 -->
    <el-dialog
      v-model="showResultsDialog"
      title="문서 처리 결과"
      width="900px"
      @close="resetResults"
    >
      <div v-if="currentDocument" class="results-content">
        <!-- 문서 기본 정보 -->
        <el-card class="document-summary" shadow="never">
          <div class="summary-header">
            <div class="document-title">
              <el-icon size="20" color="#409eff"><Document /></el-icon>
              {{ currentDocument.original_name }}
            </div>
            <el-tag :type="getFileTypeColor(currentDocument.file_type)">
              {{ getFileTypeLabel(currentDocument.file_type) }}
            </el-tag>
          </div>
          <div class="summary-stats">
            <div class="stat-group">
              <div class="stat-item">
                <span class="stat-label">파일 크기:</span>
                <span class="stat-value">{{ formatFileSize(currentDocument.file_size) }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">처리 시간:</span>
                <span class="stat-value">{{ getProcessingTime(currentDocument) }}</span>
              </div>
            </div>
            <div class="stat-group">
              <div class="stat-item">
                <span class="stat-label">추출된 문제:</span>
                <span class="stat-value">{{ currentDocument.questions_count || 0 }}개</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">학습 자료:</span>
                <span class="stat-value">{{ currentDocument.materials_count || 0 }}개</span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 탭 컨테이너 -->
        <el-tabs v-model="activeTab" class="results-tabs">
          <!-- 추출된 문제 탭 -->
          <el-tab-pane label="추출된 문제" name="questions" :badge="currentDocument.questions_count">
            <div class="questions-list">
              <div 
                v-for="(question, index) in extractedQuestions" 
                :key="question.id"
                class="question-item"
              >
                <div class="question-header">
                  <span class="question-number">문제 {{ index + 1 }}</span>
                  <el-tag v-if="question.difficulty_level" size="small">
                    {{ question.difficulty_level }}
                  </el-tag>
                  <el-tag v-if="question.topic_category" type="info" size="small">
                    {{ question.topic_category }}
                  </el-tag>
                </div>
                <div class="question-content">
                  <!-- 문제 본문 -->
                  <div class="question-text">{{ question.question_text }}</div>
                  
                  <!-- 지문/보기/표 섹션 -->
                  <div v-if="question.passage || question.estimated_time" class="question-passage">
                    <div class="passage-header">
                      <div class="passage-label">
                        <el-icon><Files /></el-icon>
                        지문 · 보기 · 표
                      </div>
                      <div class="passage-tags">
                        <el-tag v-if="hasTable(question)" type="warning" size="small">
                          <el-icon><Menu /></el-icon> 표
                        </el-tag>
                        <el-tag v-if="hasCode(question)" type="danger" size="small">
                          <el-icon><Monitor /></el-icon> 코드
                        </el-tag>
                        <el-tag v-if="hasFigure(question)" type="info" size="small">
                          <el-icon><PictureRounded /></el-icon> 그림
                        </el-tag>
                      </div>
                    </div>
                    <div class="passage-content" v-html="formatPassage(question.passage || question.estimated_time)"></div>
                  </div>
                  
                  <!-- 선택지 섹션 -->
                  <div v-if="question.options && parseOptions(question.options).length > 0" class="question-options">
                    <div class="options-label">
                      <el-icon><ListIcon /></el-icon>
                      선택지
                    </div>
                    <div 
                      v-for="(option, optIndex) in parseOptions(question.options)" 
                      :key="optIndex"
                      class="option-item"
                      :class="{ 'correct-option': isCorrectOption(question.correct_answer, optIndex) }"
                    >
                      <span class="option-marker">{{ getOptionMarker(option) }}</span>
                      <span class="option-text" v-html="formatOptionText(option)"></span>
                    </div>
                  </div>
                  
                  <!-- 정답 및 해설 -->
                  <div v-if="question.correct_answer" class="correct-answer">
                    <el-icon><Check /></el-icon>
                    <strong>정답: {{ question.correct_answer }}</strong>
                  </div>
                  
                  <div v-if="question.explanation" class="question-explanation">
                    <div class="explanation-label">
                      <el-icon><ChatRound /></el-icon>
                      해설
                    </div>
                    <div class="explanation-content">{{ question.explanation }}</div>
                  </div>
                  
                  <!-- 메타데이터 -->
                  <div v-if="question.additional_info" class="question-metadata">
                    <div class="metadata-label">메타데이터</div>
                    <div class="metadata-content">{{ formatMetadata(question.additional_info) }}</div>
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 학습 자료 탭 -->
          <el-tab-pane label="학습 자료" name="materials" :badge="currentDocument.materials_count">
            <div class="materials-list">
              <div 
                v-for="material in studyMaterials" 
                :key="material.id"
                class="material-item"
              >
                <div class="material-header">
                  <h4 class="material-title">{{ material.title }}</h4>
                  <el-tag v-if="material.content_type" type="success" size="small">
                    {{ material.content_type }}
                  </el-tag>
                </div>
                <div class="material-content">
                  {{ material.content }}
                </div>
                <div v-if="material.chapter_number || material.section_number" class="material-meta">
                  <span v-if="material.chapter_number">챕터 {{ material.chapter_number }}</span>
                  <span v-if="material.section_number">섹션 {{ material.section_number }}</span>
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showResultsDialog = false">닫기</el-button>
          <el-button v-if="currentDocument" type="primary" @click="exportResults">
            결과 내보내기
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 일괄 편집 다이얼로그 -->
    <el-dialog
      v-model="showBulkEditDialog"
      title="선택된 문서 정보 수정"
      width="600px"
      @close="resetBulkEditForm"
    >
      <el-form
        ref="bulkEditFormRef"
        :model="bulkEditForm"
        label-width="120px"
      >
        <el-form-item label="자격증">
          <el-select
            v-model="bulkEditForm.certificate_name"
            placeholder="자격증을 선택하세요"
            clearable
            style="width: 100%"
            popper-class="cert-select-popper"
          >
            <el-option 
              v-for="cert in availableCertificates" 
              :key="cert"
              :label="cert" 
              :value="cert"
              class="cert-option"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="파일 유형">
          <el-select
            v-model="bulkEditForm.file_type"
            placeholder="파일 유형을 선택하세요"
            clearable
            style="width: 100%"
          >
            <el-option label="문제집" value="questions" />
            <el-option label="학습자료" value="study_material" />
            <el-option label="통합" value="both" />
          </el-select>
        </el-form-item>

        

        <el-form-item label="발급기관">
          <div class="form-text-display">
            자격증 관리에서 설정된 발급기관이 자동으로 적용됩니다
          </div>
          <small style="color: #909399; margin-top: 4px; display: block;">
            발급기관 수정은 자격증 관리 페이지에서 가능합니다
          </small>
        </el-form-item>
        
        <div class="edit-note">
          <el-alert 
            type="info" 
            :closable="false"
            show-icon
            :title="`선택된 ${selectedDocuments.length}개 문서에 적용됩니다`"
            description="빈 필드는 변경되지 않습니다."
          />
        </div>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showBulkEditDialog = false">취소</el-button>
          <el-button type="primary" @click="saveBulkEdit" :loading="isBulkProcessing">
            적용
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 개별 문서 편집 다이얼로그 -->
    <el-dialog
      v-model="showEditDialog"
      title="문서 정보 수정"
      width="600px"
      @close="resetEditForm"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        label-width="120px"
        v-if="currentEditDocument"
      >
        <el-form-item label="문서명">
          <el-input v-model="editForm.original_name" disabled />
        </el-form-item>

        <el-form-item label="자격증">
          <el-select
            v-model="editForm.certificate_name"
            placeholder="자격증을 선택하세요"
            clearable
            style="width: 100%"
            popper-class="cert-select-popper"
          >
            <el-option 
              v-for="cert in availableCertificates" 
              :key="cert"
              :label="cert" 
              :value="cert"
              class="cert-option"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="발급기관">
          <div class="form-text-display">
            {{ editForm.issuing_authority || '자격증 관리에서 설정된 발급기관이 자동으로 적용됩니다' }}
          </div>
          <small style="color: #909399; margin-top: 4px; display: block;">
            발급기관 수정은 자격증 관리 페이지에서 가능합니다
          </small>
        </el-form-item>
        
        <el-form-item label="파일 유형">
          <el-select
            v-model="editForm.file_type"
            placeholder="파일 유형을 선택하세요"
            style="width: 100%"
          >
            <el-option label="문제집" value="questions" />
            <el-option label="학습자료" value="study_material" />
            <el-option label="통합" value="both" />
          </el-select>
        </el-form-item>

        

        <el-form-item label="파일 크기">
          <el-input :value="formatFileSize(currentEditDocument.file_size)" disabled />
        </el-form-item>

        <el-form-item label="업로드 일시">
          <el-input :value="formatDate(currentEditDocument.upload_date)" disabled />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">취소</el-button>
          <el-button type="primary" @click="saveEdit" :loading="isEditProcessing">
            저장
          </el-button>
        </span>
      </template>
    </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Refresh,
  Upload,
  Document,
  View,
  Delete,
  Loading,
  QuestionFilled,
  Reading,
  Select,
  Check,
  Close,
  Edit,
  Files,
  Menu,
  Monitor,
  PictureRounded,
  List as ListIcon,
  ChatRound,
} from '@element-plus/icons-vue'
import { formatDate } from '@/utils/format'

const router = useRouter()

// 상태 관리
const isLoading = ref(false)
const documents = ref<any[]>([])
const totalDocuments = ref(0)
const completedCount = ref(0)
const pendingCount = ref(0) 
const failedCount = ref(0)
const processingCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 필터 및 검색
const searchQuery = ref('')
const statusFilter = ref('')
const typeFilter = ref('')
const certificateFilter = ref('')
const activeFilter = ref('')
const availableCertificates = ref<string[]>([])

// 일괄 작업
const selectedDocuments = ref<any[]>([])
const isBulkProcessing = ref(false)
const showBulkEditDialog = ref(false)

// 개별 편집
const showEditDialog = ref(false)
const currentEditDocument = ref<any>(null)
const isEditProcessing = ref(false)

// 일괄 편집 폼
const bulkEditForm = reactive({
  certificate_name: '',
  file_type: '',
  issuing_authority: ''
})

// 개별 편집 폼
const editForm = reactive({
  original_name: '',
  certificate_name: '',
  issuing_authority: '',
  file_type: ''
})

// 결과 다이얼로그
const showResultsDialog = ref(false)
const currentDocument = ref<any>(null)
const activeTab = ref('questions')
const extractedQuestions = ref<any[]>([])
const studyMaterials = ref<any[]>([])

// 통계 상태는 위에서 이미 선언됨

// 유틸리티 함수들
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getFileTypeColor = (type: string) => {
  switch (type) {
    case 'questions': return 'success'
    case 'study_material': return 'primary'
    case 'both': return 'warning'
    default: return 'info'
  }
}

const getFileTypeLabel = (type: string) => {
  switch (type) {
    case 'questions': return '문제집'
    case 'study_material': return '학습자료'
    case 'both': return '통합'
    default: return type
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'processing': return 'primary'
    case 'failed': return 'danger'
    case 'pending': return 'warning'
    default: return 'info'
  }
}

const getStatusLabel = (status: string) => {
  switch (status) {
    case 'completed': return '완료'
    case 'processing': return '처리중'
    case 'failed': return '실패'
    case 'pending': return '대기'
    default: return status
  }
}

const getProcessingTime = (document: any) => {
  if (!document.processed_date || !document.upload_date) return '-'
  const start = new Date(document.upload_date)
  const end = new Date(document.processed_date)
  const diffMinutes = Math.round((end.getTime() - start.getTime()) / (1000 * 60))
  if (diffMinutes < 1) return '1분 미만'
  if (diffMinutes < 60) return `${diffMinutes}분`
  const hours = Math.floor(diffMinutes / 60)
  const minutes = diffMinutes % 60
  return `${hours}시간 ${minutes}분`
}

const parseOptions = (options: string) => {
  if (!options) return []
  try {
    if (typeof options === 'string') {
      return JSON.parse(options)
    }
    return options
  } catch {
    return options.split('\n').filter(opt => opt.trim())
  }
}

// 새로운 메서드들 추가
const hasTable = (question: any) => {
  const additionalInfo = parseAdditionalInfo(question.additional_info)
  const content = question.passage || question.estimated_time || ''
  return additionalInfo?.has_table || content.includes('|') || content.includes('표')
}

const hasCode = (question: any) => {
  const additionalInfo = parseAdditionalInfo(question.additional_info)
  const content = question.passage || question.estimated_time || ''
  return additionalInfo?.has_code || content.includes('class') || content.includes('function') || 
         content.includes('```') || content.includes('public') || content.includes('{')
}

const hasFigure = (question: any) => {
  const additionalInfo = parseAdditionalInfo(question.additional_info)
  const content = question.passage || question.estimated_time || ''
  return additionalInfo?.has_figure || content.includes('그림') || content.includes('도표')
}

const parseAdditionalInfo = (additionalInfo: string) => {
  if (!additionalInfo) return {}
  try {
    return JSON.parse(additionalInfo)
  } catch {
    return {}
  }
}

const formatPassage = (passage: string) => {
  if (!passage) return ''
  
  let formatted = passage
  
  // HTML 테이블이 이미 있는 경우 그대로 사용
  if (formatted.includes('<table')) {
    return formatted
  }
  
  // 파이프 테이블을 HTML 테이블로 변환
  const lines = formatted.split('\n')
  let inTable = false
  let tableRows = []
  let result = []
  
  for (const line of lines) {
    const trimmedLine = line.trim()
    
    // 테이블 행인지 확인 (최소 2개의 파이프 필요)
    if (trimmedLine.includes('|') && (trimmedLine.match(/\|/g) || []).length >= 2) {
      if (!inTable) {
        inTable = true
        tableRows = []
      }
      
      // 파이프로 분할하여 셀 생성
      const cells = trimmedLine.split('|').map(cell => cell.trim()).filter(cell => cell)
      if (cells.length > 0) {
        tableRows.push(cells)
      }
    } else {
      // 테이블이 끝났으면 HTML로 변환
      if (inTable && tableRows.length > 0) {
        result.push(convertToHtmlTable(tableRows))
        tableRows = []
        inTable = false
      }
      
      if (trimmedLine) {
        result.push(line)
      }
    }
  }
  
  // 마지막 테이블 처리
  if (inTable && tableRows.length > 0) {
    result.push(convertToHtmlTable(tableRows))
  }
  
  formatted = result.join('\n')
  
  // 줄바꿈 처리
  formatted = formatted.replace(/\n/g, '<br>')
  
  // 코드 블록 처리 (들여쓰기 보존 강화)
  formatted = formatted.replace(/```(.*?)```/gs, (match, code) => {
    // 들여쓰기 보존을 위해 공백을 &nbsp;로 변환
    const preservedCode = code
      .replace(/^ {4}/gm, '&nbsp;&nbsp;&nbsp;&nbsp;')  // 4칸 들여쓰기
      .replace(/^ {2}/gm, '&nbsp;&nbsp;')              // 2칸 들여쓰기
      .replace(/^\t/gm, '&nbsp;&nbsp;&nbsp;&nbsp;')    // 탭을 4칸 공백으로
      .replace(/  /g, '&nbsp;&nbsp;')                  // 연속 공백 보존
    
    return `<pre style="background: #1e1e1e; color: #d4d4d4; padding: 16px; border-radius: 8px; overflow-x: auto; font-family: 'Consolas', 'Monaco', monospace; margin: 16px 0; white-space: pre; line-height: 1.4;"><code>${preservedCode}</code></pre>`
  })
  
  // 인라인 코드 처리 (들여쓰기 보존)
  formatted = formatted.replace(/`([^`]+)`/g, 
    '<code style="background: #f3f4f6; color: #374151; padding: 2px 6px; border-radius: 4px; font-family: \'Consolas\', \'Monaco\', monospace; white-space: pre;">$1</code>')
  
  // 강조 표시
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
  formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>')
  
  // 선택지 기호 강화
  formatted = formatted.replace(/([①②③④⑤])/g, '<span style="display: inline-block; width: 24px; height: 24px; line-height: 24px; text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 50%; font-weight: bold; font-size: 12px; margin-right: 8px;">$1</span>')
  
  // 이미지 마크다운을 HTML 이미지로 변환
  formatted = formatted.replace(/!\[IMG_(\d+)\]\((\/images\/upload_\d+\/IMG_\d+\.[^)]+)\)/g, 
    '<img src="$2" alt="IMG_$1" style="max-width: 100%; height: auto; margin: 8px 0; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15);" />')
  
  // [그림: 설명] 형태 처리
  formatted = formatted.replace(/\[그림:\s*([^\]]+)\]/g, (match, description) => {
    return `<div style="background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); border: 1px solid #0ea5e9; border-radius: 8px; padding: 12px 16px; margin: 8px 0; font-size: 14px; color: #0369a1; display: flex; align-items: center; gap: 8px;">
      <i class="el-icon-picture" style="font-size: 16px;"></i>
      <span>그림: ${description}</span>
    </div>`
  })
  
  return formatted
}

// 테이블 행 배열을 HTML 테이블로 변환하는 헬퍼 함수
const convertToHtmlTable = (rows) => {
  if (rows.length === 0) return ''
  
  let html = '<table style="width: 100%; border-collapse: collapse; margin: 16px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-radius: 8px; overflow: hidden;">'
  
  // 첫 번째 행을 헤더로 처리
  if (rows.length > 0) {
    html += '<thead style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;"><tr>'
    rows[0].forEach(cell => {
      html += `<th style="padding: 12px 16px; text-align: left; font-weight: 600; border-bottom: 2px solid #ddd;">${escapeHtml(cell)}</th>`
    })
    html += '</tr></thead>'
  }
  
  // 나머지 행을 데이터로 처리
  if (rows.length > 1) {
    html += '<tbody>'
    for (let i = 1; i < rows.length; i++) {
      const rowStyle = i % 2 === 0 ? 'background: #f8f9fa;' : 'background: #fff;'
      html += `<tr style="${rowStyle} transition: background-color 0.2s ease;" onmouseover="this.style.background='#e3f2fd'" onmouseout="this.style.background='${i % 2 === 0 ? '#f8f9fa' : '#fff'}'">`
      rows[i].forEach(cell => {
        html += `<td style="padding: 10px 16px; border-bottom: 1px solid #eee; vertical-align: top;">${escapeHtml(cell)}</td>`
      })
      html += '</tr>'
    }
    html += '</tbody>'
  }
  
  html += '</table>'
  return html
}

// HTML 이스케이프 헬퍼 함수
const escapeHtml = (text) => {
  if (!text) return ''
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

const getOptionMarker = (option: string) => {
  const match = option.match(/^([①②③④⑤]|[ABCDE]\.|[1-5]\)|\([1-5]\))/)
  return match ? match[0] : ''
}

const cleanOptionText = (option: string) => {
  return option.replace(/^([①②③④⑤]|[ABCDE]\.|[1-5]\)|\([1-5]\))\s*/, '').trim()
}

const formatOptionText = (option: string) => {
  let text = cleanOptionText(option)
  
  // IMG_XXX_IMAGE 형태의 이미지 참조 처리 (백엔드에서 올라오는 형태)
  text = text.replace(/IMG_(\d+)_IMAGE/g, (match, imgNum) => {
    return `<div class="image-placeholder" style="background: #e8f4fd; border: 1px solid #409eff; border-radius: 4px; padding: 8px 12px; margin: 4px; font-size: 12px; color: #409eff; display: inline-flex; align-items: center;">
      <i class="el-icon-picture" style="margin-right: 4px;"></i>이미지 선택지 ${imgNum}
    </div>`
  })
  
  // DIAGRAM_IMAGE 형태의 다이어그램 이미지 처리
  text = text.replace(/DIAGRAM_IMAGE/g, () => {
    return `<div class="image-placeholder" style="background: #f0f9ff; border: 1px solid #67c23a; border-radius: 4px; padding: 8px 12px; margin: 4px; font-size: 12px; color: #67c23a; display: inline-flex; align-items: center;">
      <i class="el-icon-picture" style="margin-right: 4px;"></i>다이어그램 이미지
    </div>`
  })
  
  // 🖼️ 실제 이미지 경로 패턴 감지 및 HTML 이미지 태그로 변환
  // ![IMG_001](/images/upload_5/IMG_001.jpg) 형태를 실제 이미지로 변환
  text = text.replace(/!\[IMG_(\d+)\]\((\/images\/upload_\d+\/IMG_\d+\.[^)]+)\)/g, (match, imgNum, imgPath) => {
    return `<div class="image-choice" style="display: inline-block; margin: 4px; text-align: center;">
      <img src="${imgPath}" alt="선택지 ${imgNum}" 
           style="max-width: 120px; max-height: 100px; border-radius: 6px; 
                  box-shadow: 0 2px 12px rgba(0,0,0,0.15); border: 2px solid #e4e7ed;
                  cursor: pointer; transition: all 0.3s ease;" 
           onmouseover="this.style.borderColor='#409eff'; this.style.transform='scale(1.05)'"
           onmouseout="this.style.borderColor='#e4e7ed'; this.style.transform='scale(1)'" />
      <div style="font-size: 12px; color: #909399; margin-top: 4px;">선택지 ${imgNum}</div>
    </div>`
  })
  
  // [그림: 설명] 형태도 이미지로 변환 시도
  text = text.replace(/\[그림:\s*([^\]]+)\]/g, (match, description) => {
    return `<div class="image-placeholder" style="background: #f0f2f5; border: 1px dashed #d9d9d9; border-radius: 4px; padding: 8px 12px; margin: 4px; font-size: 12px; color: #666;">
      <i class="el-icon-picture" style="margin-right: 4px;"></i>그림: ${description}
    </div>`
  })
  
  return text
}

const isCorrectOption = (correctAnswer: string, optionIndex: number) => {
  if (!correctAnswer) return false
  const markers = ['①', '②', '③', '④', '⑤']
  const letters = ['A', 'B', 'C', 'D', 'E']
  const numbers = ['1', '2', '3', '4', '5']
  
  return correctAnswer.includes(markers[optionIndex]) || 
         correctAnswer.includes(letters[optionIndex]) || 
         correctAnswer.includes(numbers[optionIndex])
}

const formatMetadata = (additionalInfo: string) => {
  const info = parseAdditionalInfo(additionalInfo)
  if (!info || Object.keys(info).length === 0) return '메타데이터 없음'
  
  const items = []
  if (info.source_page) items.push(`페이지: ${info.source_page}`)
  if (info.extraction_method) items.push(`추출방법: ${info.extraction_method}`)
  if (info.has_table) items.push('표 포함')
  if (info.has_code) items.push('코드 포함')  
  if (info.has_figure) items.push('그림 포함')
  
  return items.join(' | ')
}

const formatDateShort = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('ko-KR')
}

const setQuickFilter = (type: string, value: string) => {
  if (type === 'status') {
    statusFilter.value = value
  }
  handleSearch()
}

// API 호출 함수들
const fetchDocuments = async () => {
  try {
    isLoading.value = true
    const params = new URLSearchParams({
      skip: ((currentPage.value - 1) * pageSize.value).toString(),
      limit: pageSize.value.toString(),
    })
    
    if (searchQuery.value) {
      params.append('search', searchQuery.value)
    }
    if (statusFilter.value) {
      params.append('status', statusFilter.value)
    }
    if (typeFilter.value) {
      params.append('type', typeFilter.value)
    }
    if (certificateFilter.value) {
      params.append('certificate', certificateFilter.value)
    }
    if (activeFilter.value) {
      params.append('active', activeFilter.value)
    }

    const response = await fetch(`/api/upload/files?${params}`)
    const data = await response.json()
    
    // 최신 순으로 정렬하고 is_active 기본값 추가 (완료되지 않은 문서는 자동 비활성화)
    documents.value = (data.files || []).map(doc => ({
      ...doc,
      is_active: doc.processing_status === 'completed' ? (doc.is_active !== undefined ? doc.is_active : true) : false
    })).sort((a, b) => new Date(b.upload_date).getTime() - new Date(a.upload_date).getTime())
    
    // 실제 데이터 기반 통계 계산
    totalDocuments.value = data.total || 0
    completedCount.value = documents.value.filter(doc => doc.processing_status === 'completed').length
    failedCount.value = documents.value.filter(doc => doc.processing_status === 'failed').length
    pendingCount.value = documents.value.filter(doc => doc.processing_status === 'pending').length
    processingCount.value = documents.value.filter(doc => doc.processing_status === 'processing').length

    // 전체 자격증 목록 가져오기 (필터와 무관하게)
    try {
      const certsResponse = await fetch('/api/upload/files?limit=1000')
      const certsData = await certsResponse.json()
      const allCerts = new Set(certsData.files?.map(doc => doc.certificate_name).filter(Boolean) || [])
      availableCertificates.value = Array.from(allCerts).sort()
    } catch (error) {
      console.error('Failed to fetch certificates:', error)
    }

    // 각 문서의 추출 결과 개수를 가져오기
    for (const doc of documents.value) {
      if (doc.processing_status === 'completed') {
        try {
          const resultsResponse = await fetch(`/api/upload/files/${doc.id}/results`)
          const resultsData = await resultsResponse.json()
          doc.questions_count = resultsData.questions?.total || 0
          doc.materials_count = resultsData.study_materials?.total || 0
        } catch (error) {
          console.error('Failed to fetch results for document:', doc.id, error)
        }
      }
    }
  } catch (error) {
    console.error('Failed to fetch documents:', error)
    ElMessage.error('문서 목록을 불러오는데 실패했습니다')
  } finally {
    isLoading.value = false
  }
}

const fetchDocumentResults = async (documentId: number) => {
  try {
    const response = await fetch(`/api/upload/files/${documentId}/results`)
    const data = await response.json()
    
    extractedQuestions.value = data.questions?.items || []
    studyMaterials.value = data.study_materials?.items || []
  } catch (error) {
    console.error('Failed to fetch document results:', error)
    ElMessage.error('문서 결과를 불러오는데 실패했습니다')
  }
}

// 이벤트 핸들러
const handleSearch = () => {
  currentPage.value = 1
  fetchDocuments()
}

const handleSortChange = () => {
  fetchDocuments()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchDocuments()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchDocuments()
}

const refreshDocuments = () => {
  fetchDocuments()
}

const viewDocument = (row: any) => {
  if (row.processing_status === 'completed') {
    viewResults(row)
  }
}

const viewResults = async (document: any) => {
  currentDocument.value = document
  showResultsDialog.value = true
  await fetchDocumentResults(document.id)
}

const resetResults = () => {
  currentDocument.value = null
  extractedQuestions.value = []
  studyMaterials.value = []
  activeTab.value = 'questions'
}

const reprocessDocument = async (document: any) => {
  try {
    await ElMessageBox.confirm(
      `문서 "${document.original_name}"을 재처리하시겠습니까?`,
      '재처리 확인',
      {
        confirmButtonText: '재처리',
        cancelButtonText: '취소',
        type: 'warning',
      }
    )

    const response = await fetch(`/api/upload/files/${document.id}/reprocess`, {
      method: 'POST'
    })
    
    const data = await response.json()
    
    if (response.ok && data.success) {
      ElMessage.success('문서 재처리가 시작되었습니다')
      fetchDocuments()
    } else {
      throw new Error(data.message || '재처리에 실패했습니다')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to reprocess document:', error)
      ElMessage.error('문서 재처리에 실패했습니다')
    }
  }
}

const deleteDocument = async (document: any) => {
  try {
    await ElMessageBox.confirm(
      `문서 "${document.original_name}"을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`,
      '삭제 확인',
      {
        confirmButtonText: '삭제',
        cancelButtonText: '취소',
        type: 'warning',
      }
    )

    const response = await fetch(`/api/upload/files/${document.id}`, {
      method: 'DELETE'
    })
    
    const data = await response.json()
    
    if (response.ok && data.success) {
      ElMessage.success('문서가 삭제되었습니다')
      fetchDocuments()
    } else {
      throw new Error(data.message || '삭제에 실패했습니다')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete document:', error)
      ElMessage.error('문서 삭제에 실패했습니다')
    }
  }
}

const exportResults = () => {
  if (!currentDocument.value) return
  
  const data = {
    document: currentDocument.value,
    questions: extractedQuestions.value,
    materials: studyMaterials.value,
  }
  
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${currentDocument.value.original_name.replace('.pdf', '')}_results.json`
  a.click()
  URL.revokeObjectURL(url)
  
  ElMessage.success('결과가 내보내졌습니다')
}

// 일괄 작업 함수들
const handleSelectionChange = (selection: any[]) => {
  selectedDocuments.value = selection
}

const toggleDocumentStatus = async (document: any) => {
  try {
    const response = await fetch(`/api/upload/files/${document.id}/toggle-status`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ is_active: document.is_active })
    })
    
    const data = await response.json()
    
    if (response.ok && data.success) {
      ElMessage.success(`문서가 ${document.is_active ? '활성화' : '비활성화'}되었습니다`)
    } else {
      throw new Error(data.message || '상태 변경에 실패했습니다')
    }
  } catch (error) {
    console.error('Failed to toggle document status:', error)
    ElMessage.error('상태 변경에 실패했습니다')
    // 실패시 원래 상태로 되돌림
    document.is_active = !document.is_active
  }
}

const bulkToggleStatus = async (isActive: boolean) => {
  if (selectedDocuments.value.length === 0) return

  try {
    isBulkProcessing.value = true
    const action = isActive ? '활성화' : '비활성화'
    
    // 활성화하려는 경우 완료되지 않은 문서 확인
    if (isActive) {
      const incompleteDocuments = selectedDocuments.value.filter(doc => doc.processing_status !== 'completed')
      if (incompleteDocuments.length > 0) {
        ElMessage.warning(`처리상태가 완료가 아닌 ${incompleteDocuments.length}개의 문서가 있어서 활성화할 수 없습니다.`)
        return
      }
    }
    
    // 비활성화하려는 경우 이미 비활성화된 문서 확인
    if (!isActive) {
      const alreadyInactiveDocuments = selectedDocuments.value.filter(doc => !doc.is_active)
      if (alreadyInactiveDocuments.length === selectedDocuments.value.length) {
        ElMessage.info('선택된 모든 문서가 이미 비활성화되어 있습니다.')
        return
      }
    } else {
      // 활성화하려는 경우 이미 활성화된 문서 확인
      const alreadyActiveDocuments = selectedDocuments.value.filter(doc => doc.is_active && doc.processing_status === 'completed')
      if (alreadyActiveDocuments.length === selectedDocuments.value.length) {
        ElMessage.info('선택된 모든 문서가 이미 활성화되어 있습니다.')
        return
      }
    }
    
    await ElMessageBox.confirm(
      `선택된 ${selectedDocuments.value.length}개 문서를 ${action}하시겠습니까?`,
      `일괄 ${action}`,
      {
        confirmButtonText: action,
        cancelButtonText: '취소',
        type: 'warning',
      }
    )

    // 실제로 변경될 문서들만 필터링
    const documentsToChange = isActive 
      ? selectedDocuments.value.filter(doc => !doc.is_active && doc.processing_status === 'completed')
      : selectedDocuments.value.filter(doc => doc.is_active)
    
    const promises = documentsToChange.map(async (doc) => {
      const response = await fetch(`/api/upload/files/${doc.id}/toggle-status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ is_active: isActive })
      })
      return response.json()
    })

    await Promise.all(promises)
    
    // UI 업데이트 - 실제로 변경된 문서들만
    documentsToChange.forEach(doc => {
      doc.is_active = isActive
    })
    
    if (documentsToChange.length > 0) {
      ElMessage.success(`${documentsToChange.length}개 문서가 ${action}되었습니다`)
    } else {
      ElMessage.info(`변경된 문서가 없습니다`)
    }
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to bulk toggle status:', error)
      ElMessage.error(`일괄 ${isActive ? '활성화' : '비활성화'}에 실패했습니다`)
    }
  } finally {
    isBulkProcessing.value = false
  }
}

const bulkReprocess = async () => {
  if (selectedDocuments.value.length === 0) return

  try {
    isBulkProcessing.value = true
    
    await ElMessageBox.confirm(
      `선택된 ${selectedDocuments.value.length}개 문서를 재처리하시겠습니까?`,
      '일괄 재처리',
      {
        confirmButtonText: '재처리',
        cancelButtonText: '취소',
        type: 'warning',
      }
    )

    const promises = selectedDocuments.value.map(async (doc) => {
      const response = await fetch(`/api/upload/files/${doc.id}/reprocess`, {
        method: 'POST'
      })
      return response.json()
    })

    await Promise.all(promises)
    ElMessage.success(`${selectedDocuments.value.length}개 문서 재처리가 시작되었습니다`)
    fetchDocuments()
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to bulk reprocess:', error)
      ElMessage.error('일괄 재처리에 실패했습니다')
    }
  } finally {
    isBulkProcessing.value = false
  }
}

const bulkDelete = async () => {
  if (selectedDocuments.value.length === 0) return

  try {
    isBulkProcessing.value = true
    
    await ElMessageBox.confirm(
      `선택된 ${selectedDocuments.value.length}개 문서를 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`,
      '일괄 삭제',
      {
        confirmButtonText: '삭제',
        cancelButtonText: '취소',
        type: 'error',
      }
    )

    const promises = selectedDocuments.value.map(async (doc) => {
      const response = await fetch(`/api/upload/files/${doc.id}`, {
        method: 'DELETE'
      })
      return response.json()
    })

    await Promise.all(promises)
    ElMessage.success(`${selectedDocuments.value.length}개 문서가 삭제되었습니다`)
    selectedDocuments.value = []
    fetchDocuments()
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to bulk delete:', error)
      ElMessage.error('일괄 삭제에 실패했습니다')
    }
  } finally {
    isBulkProcessing.value = false
  }
}

const resetBulkEditForm = () => {
  bulkEditForm.certificate_name = ''
  bulkEditForm.file_type = ''
}

const editDocument = (document: any) => {
  currentEditDocument.value = document
  editForm.original_name = document.original_name
  editForm.certificate_name = document.certificate_name || ''
  editForm.issuing_authority = document.issuing_authority || ''
  editForm.file_type = document.file_type
  showEditDialog.value = true
}

const resetEditForm = () => {
  currentEditDocument.value = null
  editForm.original_name = ''
  editForm.certificate_name = ''
  editForm.issuing_authority = ''
  editForm.file_type = ''
}

const saveEdit = async () => {
  if (!currentEditDocument.value) return

  try {
    isEditProcessing.value = true
    
    const updateData = {
      certificate_name: editForm.certificate_name,
      file_type: editForm.file_type
    }

    const response = await fetch(`/api/upload/files/${currentEditDocument.value.id}/update`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updateData)
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`HTTP ${response.status}: ${errorText}`)
    }
    
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success('문서 정보가 수정되었습니다')
      showEditDialog.value = false
      resetEditForm()
      fetchDocuments()
    } else {
      throw new Error(data.message || '수정에 실패했습니다')
    }
    
  } catch (error: any) {
    console.error('Failed to edit document:', error)
    
    let errorMessage = '문서 수정에 실패했습니다'
    if (error?.message) {
      errorMessage += ': ' + error.message
    }
    ElMessage.error(errorMessage)
  } finally {
    isEditProcessing.value = false
  }
}

const saveBulkEdit = async () => {
  if (selectedDocuments.value.length === 0) return

  try {
    isBulkProcessing.value = true
    
    // 빈 필드 제거
    const updateData: any = {}
    if (bulkEditForm.certificate_name) updateData.certificate_name = bulkEditForm.certificate_name
    if (bulkEditForm.file_type) updateData.file_type = bulkEditForm.file_type
    
    if (Object.keys(updateData).length === 0) {
      ElMessage.warning('변경할 정보를 입력하세요')
      return
    }

    // 일괄 수정 API 호출
    const response = await fetch('/api/upload/files/bulk-update', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        file_ids: selectedDocuments.value.map(doc => doc.id),
        ...updateData
      })
    })

    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`HTTP ${response.status}: ${errorText}`)
    }
    
    const result = await response.json()
    if (!result.success) {
      throw new Error(result.message || '일괄 수정에 실패했습니다')
    }
    
    ElMessage.success(`${selectedDocuments.value.length}개 문서 정보가 수정되었습니다`)
    showBulkEditDialog.value = false
    resetBulkEditForm()
    fetchDocuments()
    
  } catch (error: any) {
    console.error('Failed to bulk edit:', error)
    console.error('Selected documents:', selectedDocuments.value.map(doc => doc.id))
    
    let errorMessage = '일괄 수정에 실패했습니다'
    if (error?.message) {
      errorMessage += ': ' + error.message
    }
    ElMessage.error(errorMessage)
  } finally {
    isBulkProcessing.value = false
  }
}

// 초기화
onMounted(() => {
  fetchDocuments()
})
</script>

<style scoped>
.documents-view {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 16px;
}

.container {
  width: 100%;
  max-width: 100%;
  margin: 0;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

/* ===== 현대적인 액션 바 스타일 ===== */
.actions-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 16px 16px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
}

.search-section {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.search-section .el-input,
.search-section .el-select {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.action-buttons .el-button {
  border-radius: 8px;
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.action-buttons .el-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

/* ===== 폼 요소 스타일 ===== */
.form-text-display {
  padding: 12px 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  color: #64748b;
  font-size: 14px;
  transition: all 0.2s ease;
}

.form-text-display:hover {
  border-color: #cbd5e1;
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
}

.disabled-note {
  margin-top: 8px;
  padding: 8px 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
}

/* ===== 다이얼로그 스타일 ===== */
:deep(.el-dialog) {
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
  overflow: hidden;
}

:deep(.el-dialog__header) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-bottom: 1px solid #e2e8f0;
  padding: 20px 24px;
}

:deep(.el-dialog__title) {
  font-weight: 600;
  font-size: 18px;
  color: #1e293b;
}

:deep(.el-dialog__body) {
  padding: 24px;
  max-height: 70vh;
  overflow-y: auto;
}

:deep(.el-dialog__footer) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-top: 1px solid #e2e8f0;
  padding: 16px 24px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #374151;
}

/* ===== 액션 버튼 스타일 (자격증 관리와 동일) ===== */
/* 새로운 액션 컨트롤 스타일 */
.action-controls-new {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 60px;
  padding: 8px 0;
}

.action-buttons-horizontal {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  flex-wrap: wrap;
}

/* 기존 스타일 유지 */
.action-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
  min-width: 180px;
}

.status-switch {
  display: flex;
  align-items: center;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 표준 버튼 스타일 - 규격 통일 */
.action-btn {
  width: 28px !important;
  height: 28px !important;
  min-width: 28px !important;
  padding: 0 !important;
  border-radius: 50% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.action-btn :deep(.el-icon) {
  margin: 0 !important;
  position: relative;
  top: 0;
  left: 0;
}

.action-btn :deep(span) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-btn.el-button--primary {
  background-color: #409eff;
  border-color: #409eff;
}

.action-btn.el-button--danger {
  background-color: #f56c6c;
  border-color: #f56c6c;
}

.action-btn.el-button--info {
  background-color: #909399;
  border-color: #909399;
}

.action-btn.el-button--warning {
  background-color: #e6a23c;
  border-color: #e6a23c;
}

/* ===== 페이지 헤더 ===== */
.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 0;
  padding: 32px 24px;
  margin-bottom: 0;
  color: white;
  position: relative;
}

.page-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.title-section {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0 0 12px 0;
  font-size: 32px;
  font-weight: 700;
  color: white;
}

.title-icon {
  font-size: 36px;
  color: rgba(255, 255, 255, 0.9);
}

.page-description {
  margin: 0;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.5;
}

.stats-section {
  display: flex;
  gap: 20px;
  align-items: center;
}

.stat-card {
  background: rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  padding: 0;
  min-width: 120px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.stat-card:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.18);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.stat-card :deep(.el-card__body) {
  padding: 20px 16px;
  text-align: center;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: white;
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* ===== 필터 카드 ===== */
.filter-card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  margin-bottom: 24px;
}

.filter-card :deep(.el-card__body) {
  padding: 20px;
}

.filter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  flex-wrap: wrap;
}

.search-main {
  flex: 1;
  min-width: 300px;
}

.main-search {
  width: 100%;
}

.quick-filters .filter-buttons {
  display: flex;
  gap: 4px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.advanced-filters {
  margin-top: 16px;
}

.advanced-filter-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-item label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

.filters-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  align-items: center;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.search-input {
  width: 100%;
}

.filter-select {
  width: 100%;
}

.filter-select.wide {
  grid-column: span 2;
}

.date-picker {
  width: 100%;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-btn {
  width: 100%;
  justify-content: flex-start;
}

.action-btn.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
}

/* ===== 일괄 작업 섹션 ===== */
.bulk-actions-section {
  margin: 0 16px 16px 16px;
  animation: slideDown 0.3s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.bulk-card {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #0ea5e9;
  border-radius: 16px;
  box-shadow: 0 6px 24px rgba(14, 165, 233, 0.12);
  overflow: hidden;
}

.bulk-card :deep(.el-card__body) {
  padding: 16px 24px;
}

.bulk-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.bulk-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.bulk-icon {
  font-size: 20px;
  color: #0ea5e9;
}

.bulk-text {
  font-size: 16px;
  font-weight: 600;
  color: #0369a1;
}

.bulk-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* ===== 테이블 스타일링 ===== */
.documents-card :deep(.el-table td) {
  height: 70px !important;
  padding: 8px 12px !important;
  vertical-align: middle !important;
}

.documents-card :deep(.el-table .cell) {
  line-height: 1.3 !important;
  padding: 4px 8px !important;
}

.documents-card :deep(.el-table tbody tr) {
  height: 70px !important;
}

.document-number {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.document-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.document-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.document-details {
  flex: 1;
  overflow: hidden;
}

.document-name {
  font-weight: 500;
  color: #2c3e50;
  font-size: 13px;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.document-size {
  font-size: 11px;
  color: #7f8c8d;
  line-height: 1.2;
}

.cert-tag {
  font-size: 11px;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.action-buttons-group {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  justify-content: center;
}

.action-buttons-group .el-button {
  font-size: 11px;
  padding: 4px 8px;
}

.documents-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
  border: 1px solid #f1f5f9;
  overflow: hidden;
  margin: 0 16px 16px 16px;
}

.documents-card :deep(.el-card__body) {
  padding: 0;
}

.documents-card :deep(.el-table) {
  border-radius: 16px;
  border: none;
}

.documents-card :deep(.el-table th) {
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  font-weight: 600;
  color: #374151;
  font-size: 13px;
  padding: 16px 12px;
}

.documents-card :deep(.el-table tr:hover > td) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%) !important;
  transform: scale(1.01);
  transition: all 0.2s ease;
}

.document-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.document-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.document-name {
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 2px;
}

.document-size {
  font-size: 12px;
  color: #7f8c8d;
}

.extraction-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.extraction-stats-horizontal {
  display: flex;
  flex-direction: row;
  gap: 8px;
  justify-content: center;
  align-items: center;
}

.stat-row {
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: #606266;
  white-space: nowrap;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #606266;
}

.no-data {
  color: #c0c4cc;
  font-size: 14px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  padding: 24px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-top: 1px solid #e2e8f0;
  margin-top: 0;
}

.pagination-wrapper :deep(.el-pagination) {
  background: transparent;
}

.pagination-wrapper :deep(.el-pagination .el-pager li) {
  border-radius: 8px;
  margin: 0 4px;
  transition: all 0.2s ease;
}

.pagination-wrapper :deep(.el-pagination .el-pager li:hover),
.pagination-wrapper :deep(.el-pagination .el-pager li.is-active) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.results-content {
  max-height: 70vh;
  overflow-y: auto;
}

.document-summary {
  margin-bottom: 20px;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.document-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.summary-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.stat-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  color: #606266;
  font-size: 14px;
}

.stat-value {
  font-weight: 600;
  color: #2c3e50;
}

.results-tabs {
  margin-top: 20px;
}

.questions-list,
.materials-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-height: 400px;
  overflow-y: auto;
  padding: 16px 0;
}

.question-item,
.material-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafafa;
}

.question-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.question-number {
  font-weight: 600;
  color: #2c3e50;
}

.question-content {
  line-height: 1.6;
}

.question-text {
  margin-bottom: 12px;
  color: #2c3e50;
}

.question-passage {
  margin-bottom: 16px;
  padding: 16px;
  background: #f8fafc;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
}

.passage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e1e8ed;
}

.passage-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #3b82f6;
  font-size: 14px;
}

.passage-tags {
  display: flex;
  gap: 4px;
}

.passage-content {
  padding: 12px;
  background: #ffffff;
  border: 1px solid #e1e8ed;
  border-radius: 6px;
  line-height: 1.6;
  font-family: 'Consolas', 'Monaco', monospace;
  white-space: pre-wrap;
  word-wrap: break-word;
  overflow-x: auto;
}

.question-additional {
  margin-bottom: 12px;
}

.additional-label {
  font-weight: 600;
  color: #67c23a;
  margin-bottom: 4px;
}

.additional-content {
  padding: 12px;
  background: #f0f9ff;
  border-left: 4px solid #67c23a;
  border-radius: 6px;
  line-height: 1.5;
}

.question-options {
  margin-bottom: 16px;
  padding: 16px;
  background: #f9fafb;
  border: 1px solid #e1e8ed;
  border-radius: 8px;
}

.options-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e1e8ed;
}

.option-item {
  display: flex;
  align-items: flex-start;
  margin-bottom: 8px;
  padding: 8px 12px;
  background: #ffffff;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.option-item.correct-option {
  background: #ecfdf5;
  border-color: #10b981;
}

.option-marker {
  font-weight: 600;
  margin-right: 12px;
  color: #6b7280;
  min-width: 24px;
}

.option-item.correct-option .option-marker {
  color: #10b981;
}

.option-text {
  color: #374151;
  line-height: 1.5;
}

.option-item.correct-option .option-text {
  color: #065f46;
  font-weight: 500;
}

.correct-answer {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 16px;
  background: #ecfdf5;
  border: 1px solid #10b981;
  border-radius: 6px;
  color: #065f46;
  margin-bottom: 12px;
}

.question-explanation {
  margin-bottom: 16px;
  padding: 16px;
  background: #fffbeb;
  border: 1px solid #f59e0b;
  border-radius: 8px;
}

.explanation-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  color: #f59e0b;
  font-size: 14px;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #fde68a;
}

.explanation-content {
  color: #92400e;
  line-height: 1.6;
}

.question-metadata {
  margin-top: 16px;
  padding: 12px;
  background: #f3f4f6;
  border-radius: 6px;
}

.metadata-label {
  font-weight: 600;
  color: #6b7280;
  font-size: 12px;
  margin-bottom: 4px;
}

.metadata-content {
  color: #9ca3af;
  font-size: 12px;
}

.material-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.material-title {
  margin: 0;
  color: #2c3e50;
  font-size: 16px;
}

.material-content {
  color: #2c3e50;
  line-height: 1.6;
  margin-bottom: 12px;
  white-space: pre-wrap;
}

.material-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #909399;
}

.dialog-footer {
  display: flex;
  gap: 12px;
}

/* ===== 체크박스 크기 확대 ===== */
.documents-card :deep(.el-table .el-checkbox) {
  transform: scale(1.2);
}

.documents-card :deep(.el-table .el-checkbox__input) {
  transform: scale(1.1);
}

.documents-card :deep(.el-table .el-table-column--selection .cell) {
  padding: 12px 0;
}

/* ===== 셀렉트 옵션 말줄임표 처리 ===== */
:deep(.cert-select-popper) {
  max-width: 500px;
}

:deep(.cert-option) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 480px;
}

:deep(.cert-select-popper .el-select-dropdown__item) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 480px;
}

/* ===== 반응형 디자인 ===== */

/* 태블릿 */
@media (max-width: 1024px) {
  .filter-row {
    grid-template-columns: 1fr 1fr;
  }
  
  .filter-select.wide {
    grid-column: span 1;
  }
  
  .summary-stats {
    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    gap: 16px;
  }
  
  .bulk-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .bulk-actions {
    width: 100%;
    justify-content: flex-start;
  }
}

/* 모바일 */
@media (max-width: 768px) {
  .documents-view {
    padding: 0 16px;
  }
  
  .page-header {
    padding: 24px;
    margin-bottom: 24px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 24px;
  }
  
  .stats-section {
    justify-content: center;
  }
  
  .control-section .el-col {
    margin-bottom: 16px;
  }
  
  .filter-row {
    grid-template-columns: 1fr;
  }
  
  .action-buttons {
    flex-direction: row;
  }
  
  .action-btn {
    flex: 1;
  }
  
  .bulk-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  
  .bulk-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  .bulk-actions .el-button {
    width: 100%;
  }
  
  .document-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .extraction-stats {
    flex-direction: row;
    gap: 12px;
  }
  
  .documents-card :deep(.el-table) {
    font-size: 12px;
  }
  
  .documents-card :deep(.el-table .cell) {
    padding: 8px 4px;
  }
}

/* 작은 모바일 */
@media (max-width: 480px) {
  .documents-view {
    padding: 0 12px;
  }
  
  .page-header {
    padding: 20px;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .title-icon {
    font-size: 28px;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .bulk-card :deep(.el-card__body) {
    padding: 12px 16px;
  }
  
  .bulk-text {
    font-size: 14px;
  }
  
  .documents-card :deep(.el-table .cell) {
    padding: 6px 2px;
  }
}
</style>