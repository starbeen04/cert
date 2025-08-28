<template>
  <div class="upload-view">
    <div class="page-header">
      <h1 class="page-title">PDF 업로드</h1>
      <p class="page-description">자격증 PDF를 업로드하여 AI 처리 및 학습 자료 생성</p>
    </div>

    <el-row :gutter="20">
      <!-- Upload Form -->
      <el-col :xs="24" :lg="12">
        <el-card class="upload-card">
          <template #header>
            <span class="card-title">자격증 업로드</span>
          </template>
          
          <el-form
            ref="uploadFormRef"
            :model="uploadForm"
            :rules="uploadRules"
            label-width="120px"
          >
            <el-form-item label="자격증 선택" prop="certificate_id" required>
              <el-select
                v-model="uploadForm.certificate_id"
                placeholder="자격증을 선택하세요"
                style="width: 100%"
                @focus="loadCertificates"
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
            </el-form-item>

            <el-form-item label="파일 유형" prop="file_type" required>
              <el-radio-group v-model="uploadForm.file_type">
                <el-radio value="questions">기출문제</el-radio>
                <el-radio value="study_material">학습자료</el-radio>
                <el-radio value="both">문제+자료</el-radio>
              </el-radio-group>
            </el-form-item>


            <el-form-item label="파일 이름" prop="name">
              <el-input
                v-model="uploadForm.name"
                placeholder="파일 이름을 입력하세요"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>
            
            <el-form-item label="설명" prop="description">
              <el-input
                v-model="uploadForm.description"
                type="textarea"
                :rows="3"
                placeholder="선택사항 설명"
                maxlength="500"
                show-word-limit
              />
            </el-form-item>
            
            <el-form-item label="PDF 파일" >
              <el-upload
                ref="uploadRef"
                class="upload-dragger"
                drag
                :auto-upload="false"
                :show-file-list="true"
                :limit="1"
                accept=".pdf"
                :on-change="handleFileChange"
                :on-remove="handleFileRemove"
                :on-exceed="handleExceed"
              >
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">
                  PDF 파일을 여기에 끌어다 놓거나 <em>클릭하여 업로드</em>
                </div>
                <template #tip>
                  <div class="el-upload__tip">
                    PDF 파일만 가능, 최대 크기 50MB
                  </div>
                </template>
              </el-upload>
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                size="large"
                :loading="certificatesStore.isUploading"
                :disabled="!selectedFile"
                @click="handleUpload"
                class="upload-btn"
              >
                <el-icon><Upload /></el-icon>
                {{ certificatesStore.isUploading ? '프로페셔널 처리 중...' : '프로페셔널 PDF 처리 시작' }}
              </el-button>
            </el-form-item>
          </el-form>
          
          <!-- Upload Progress -->
          <div v-if="certificatesStore.isUploading" class="upload-progress">
            <el-progress
              :percentage="certificatesStore.uploadProgress"
              :status="certificatesStore.uploadProgress === 100 ? 'success' : undefined"
            />
            <p class="progress-text">
              {{ selectedFile?.name }} 업로드 중...
            </p>
          </div>
        </el-card>
      </el-col>
      
      <!-- Upload Guidelines -->
      <el-col :xs="24" :lg="12">
        <el-card class="guidelines-card">
          <template #header>
            <span class="card-title">업로드 가이드라인</span>
          </template>
          
          <div class="guidelines-content">
            <div class="guideline-item">
              <el-icon class="guideline-icon" color="#67c23a"><Check /></el-icon>
              <div>
                <h4>지원 형식</h4>
                <p>처리를 위해 PDF 파일만 지원됩니다</p>
              </div>
            </div>
            
            <div class="guideline-item">
              <el-icon class="guideline-icon" color="#409eff"><DataBoard /></el-icon>
              <div>
                <h4>파일 크기 제한</h4>
                <p>업로드당 최대 파일 크기는 50MB입니다</p>
              </div>
            </div>
            
            <div class="guideline-item">
              <el-icon class="guideline-icon" color="#e6a23c"><Document /></el-icon>
              <div>
                <h4>콘텐츠 품질</h4>
                <p>최상의 AI 처리 결과를 위해 PDF에 명확하고 읽기 쉬운 텍스트가 포함되어 있는지 확인하세요</p>
              </div>
            </div>
            
            <div class="guideline-item">
              <el-icon class="guideline-icon" color="#f56c6c"><Warning /></el-icon>
              <div>
                <h4>처리 시간</h4>
                <p>AI 처리는 일반적으로 파일 크기와 복잡성에 따라 2-10분이 소요됩니다</p>
              </div>
            </div>
          </div>
          
          <el-divider />
          
          <div class="features-section">
            <h3>🚀 프로페셔널 파이프라인 진행 과정</h3>
            <el-steps direction="vertical" :active="1">
              <el-step title="🔍 A단계: PDF 구조 파악" description="페이지/이미지 분석, Q/A 분류, 문제 세분화, 특수 요소 감지 (7단계 상세 분석)" />
              <el-step title="📊 B단계: 정규 스키마 저장" description="구조화된 JSON 형식으로 문제, 선택지, 지문, 표/이미지 데이터 정규화" />
              <el-step title="🎯 C단계: LLM 유형·챕터 태깅" description="OpenAI/Claude로 문제 유형 분류 및 챕터별 태깅" />
              <el-step title="🎉 완성: 데이터베이스 저장" description="최종 검증 후 데이터베이스 저장 완료" />
            </el-steps>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Recent Uploads -->
    <el-card class="recent-uploads-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">최근 업로드</span>
          <el-button type="text" :icon="Refresh" @click="refreshRecentUploads">
            새로고침
          </el-button>
        </div>
      </template>
      
      <div v-loading="loadingRecent" class="recent-uploads-list">
        <div
          v-for="upload in recentUploads"
          :key="upload.id"
          class="upload-item"
          @click="viewCertificate(upload)"
        >
          <div class="upload-icon">
            <el-icon size="20"><Document /></el-icon>
          </div>
          <div class="upload-info">
            <div class="upload-name">{{ upload.name }}</div>
            <div class="upload-meta">
              {{ formatFileSize(upload.file_size) }} • {{ formatRelativeTime(upload.upload_date) }}
            </div>
          </div>
          <div class="upload-status">
            <el-tag
              :type="upload.processed ? 'success' : 'warning'"
              size="small"
            >
              {{ upload.processed ? '처리됨' : '처리 중' }}
            </el-tag>
          </div>
          <div class="upload-actions">
            <el-button type="text" size="small" :icon="View">
              보기
            </el-button>
          </div>
        </div>
        
        <el-empty
          v-if="recentUploads.length === 0 && !loadingRecent"
          description="최근 업로드가 없습니다"
          :image-size="60"
        />
      </div>
    </el-card>

    <!-- Processing Results -->
    <el-card v-if="processingResult" class="processing-results-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">처리 결과</span>
          <el-tag :type="processingResult.success ? 'success' : 'danger'" size="small">
            {{ processingResult.success ? '처리 완료' : '처리 실패' }}
          </el-tag>
        </div>
      </template>
      
      <div class="processing-results-content">
        <div v-if="processingResult.success" class="results-summary">
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="stat-item">
                <el-icon class="stat-icon" color="#67c23a"><Document /></el-icon>
                <div class="stat-info">
                  <div class="stat-value">{{ processingResult.total_pages || 0 }}</div>
                  <div class="stat-label">처리된 페이지</div>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-item">
                <el-icon class="stat-icon" color="#409eff"><DataBoard /></el-icon>
                <div class="stat-info">
                  <div class="stat-value">{{ processingResult.questions_count || 0 }}</div>
                  <div class="stat-label">추출된 문제</div>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="stat-item">
                <el-icon class="stat-icon" color="#e6a23c"><Warning /></el-icon>
                <div class="stat-info">
                  <div class="stat-value">{{ processingResult.study_materials_count || 0 }}</div>
                  <div class="stat-label">학습 자료</div>
                </div>
              </div>
            </el-col>
          </el-row>
          
          <div class="results-details">
            <h4>처리 정보</h4>
            <el-descriptions :column="2" size="small" border>
              <el-descriptions-item label="파일명">{{ processingResult.filename }}</el-descriptions-item>
              <el-descriptions-item label="자격증">{{ processingResult.certificate_name }}</el-descriptions-item>
              <el-descriptions-item label="파일 유형">{{ processingResult.file_type }}</el-descriptions-item>
              <el-descriptions-item label="처리 시간">{{ processingResult.processed_at }}</el-descriptions-item>
            </el-descriptions>
          </div>
          
          <div class="results-actions">
            <el-button type="primary" @click="viewDetailedResults">
              상세 결과 보기
            </el-button>
            <el-button @click="clearResults">
              결과 닫기
            </el-button>
          </div>
        </div>
        
        <div v-else class="error-message">
          <el-alert
            title="처리 실패"
            :description="processingResult.error_message"
            type="error"
            :closable="false"
          />
        </div>
      </div>
    </el-card>

    <!-- Processing Details Modal -->
    <el-dialog
      v-model="detailModalVisible"
      title="처리 결과 상세 정보"
      width="80%"
      :close-on-click-modal="false"
    >
      <div v-if="processingResult?.processing_details" class="detail-content">
        <!-- Summary Info -->
        <el-card class="detail-summary">
          <h3>처리 요약</h3>
          <el-descriptions :column="2" border size="small">
            <el-descriptions-item label="파일명">{{ processingResult.filename }}</el-descriptions-item>
            <el-descriptions-item label="자격증">{{ processingResult.certificate_name }}</el-descriptions-item>
            <el-descriptions-item label="파일 유형">{{ processingResult.file_type }}</el-descriptions-item>
            <el-descriptions-item label="처리 시간">{{ processingResult.processed_at }}</el-descriptions-item>
            <el-descriptions-item label="총 페이지">{{ processingResult.total_pages }}</el-descriptions-item>
            <el-descriptions-item label="추출된 문제">{{ processingResult.questions_count }}</el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- Extracted Questions -->
        <el-card v-if="processingResult.processing_details.extracted_questions?.length > 0" class="detail-questions">
          <template #header>
            <h3>추출된 문제 ({{ processingResult.processing_details.extracted_questions.length }}개)</h3>
          </template>
          <div class="questions-list">
            <el-collapse>
              <el-collapse-item
                v-for="(question, index) in processingResult.processing_details.extracted_questions"
                :key="index"
                :title="`문제 ${question.question_number || index + 1}: ${question.question_text?.substring(0, 80)}...`"
              >
                <div class="question-detail">
                  <div class="question-text">
                    <strong>문제:</strong>
                    <p>{{ question.question_text }}</p>
                  </div>
                  
                  <div v-if="question.passage" class="question-passage">
                    <strong>지문/보기/표:</strong>
                    <p>{{ question.passage }}</p>
                  </div>
                  
                  <div v-if="question.options?.length > 0" class="question-options">
                    <strong>선택지:</strong>
                    <ol>
                      <li v-for="(option, optIndex) in question.options" :key="optIndex">
                        {{ option }}
                      </li>
                    </ol>
                  </div>
                  
                  <div v-if="question.additional_info" class="question-additional">
                    <strong>부가 설명:</strong>
                    <p>{{ question.additional_info }}</p>
                  </div>
                  
                  <div class="question-meta">
                    <el-tag v-if="question.correct_answer" type="success" size="small">
                      정답: {{ question.correct_answer }}
                    </el-tag>
                    <el-tag type="info" size="small">페이지: {{ question.page_number }}</el-tag>
                    <el-tag type="warning" size="small">난이도: {{ question.difficulty }}/5</el-tag>
                  </div>
                </div>
              </el-collapse-item>
            </el-collapse>
          </div>
        </el-card>

        <!-- Processing Pages -->
        <el-card v-if="processingResult.processing_details.pages?.length > 0" class="detail-pages">
          <template #header>
            <h3>페이지별 처리 결과 ({{ processingResult.processing_details.pages.length }}페이지)</h3>
          </template>
          <el-table :data="processingResult.processing_details.pages" stripe>
            <el-table-column prop="page_number" label="페이지" width="80" />
            <el-table-column label="텍스트 길이" width="120">
              <template #default="scope">
                {{ scope.row.combined_text?.length || 0 }} 글자
              </template>
            </el-table-column>
            <el-table-column label="텍스트 미리보기">
              <template #default="scope">
                {{ scope.row.combined_text?.substring(0, 100) }}...
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- Processing Errors -->
        <el-card v-if="processingResult.processing_details.processing_errors?.length > 0" class="detail-errors">
          <template #header>
            <h3>처리 오류</h3>
          </template>
          <el-alert
            v-for="(error, index) in processingResult.processing_details.processing_errors"
            :key="index"
            :title="error"
            type="error"
            :closable="false"
            show-icon
          />
        </el-card>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="detailModalVisible = false">닫기</el-button>
          <el-button type="primary" @click="exportResults">결과 내보내기</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 구조 분석 결과 모달 -->
    <StructureAnalysisModal
      v-model:visible="structureAnalysisVisible"
      :upload-id="currentUploadId"
      :file-name="currentFileName"
      :analysis-result="analysisResultData"
      @proceed-processing="proceedWithStructureBasedProcessing"
      @cancel="cancelStructureAnalysis"
    />

    <!-- 처리 상황 모니터링 팝업 -->
    <el-dialog
      v-model="processingModal"
      title="PDF 처리 진행 상황"
      width="600px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <div class="processing-content">
        <div class="file-info">
          <el-icon size="20"><Document /></el-icon>
          <span>{{ processingStatus.filename }}</span>
        </div>
        
        <div class="progress-section">
          <el-progress 
            :percentage="processingStatus.progress" 
            :status="processingStatus.is_complete ? 'success' : undefined"
            :stroke-width="12"
          />
          <p class="current-step">{{ processingStatus.current_step }}</p>
        </div>
        
        <div class="steps-section">
          <div 
            v-for="(step, index) in processingStatus.steps" 
            :key="index"
            class="step-item"
            :class="step.status"
          >
            <div class="step-icon">
              <el-icon v-if="step.status === 'completed'" size="16" color="green">
                <Check />
              </el-icon>
              <el-icon v-else-if="step.status === 'failed'" size="16" color="red">
                <Warning />
              </el-icon>
              <div v-else-if="step.status === 'processing'" class="loading-dot"></div>
              <div v-else class="pending-dot"></div>
            </div>
            <span class="step-name">{{ step.name }}</span>
          </div>
        </div>
      </div>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules, type UploadFile, type UploadFiles, type UploadInstance } from 'element-plus'
import {
  UploadFilled,
  Upload,
  Check,
  DataBoard,
  Document,
  Warning,
  Refresh,
  View,
} from '@element-plus/icons-vue'
import { useCertificatesStore } from '@/stores/certificates'
import type { Certificate, CertificateCreate } from '@/types'
import { formatFileSize, formatRelativeTime } from '@/utils/format'
import StructureAnalysisModal from '@/components/StructureAnalysisModal.vue'

const router = useRouter()
const certificatesStore = useCertificatesStore()

// Form refs
const uploadFormRef = ref<FormInstance>()
const uploadRef = ref<UploadInstance>()

// State
const selectedFile = ref<File | null>(null)
const loadingRecent = ref(false)
const recentUploads = ref<Certificate[]>([])
const availableCertificates = ref<any[]>([])
const processingResult = ref<any>(null)
const detailModalVisible = ref(false)

// Structure analysis state
const structureAnalysisVisible = ref(false)
const currentUploadId = ref<number | null>(null)
const currentFileName = ref<string>('')
const pendingUploadData = ref<any>(null)
const analysisResultData = ref<any>(null)

// Form data
const uploadForm = reactive({
  name: '',
  certificate_id: '',
  file_type: 'questions', // 'questions', 'study_material', 'both'
  description: '',
  processing_method: 'smart', // 'smart', 'legacy', 'compare' - 새로운 처리 방식 옵션
})

// Form validation rules
const uploadRules: FormRules = {
  name: [
    { required: true, message: '파일 이름을 입력하세요', trigger: 'blur' },
    { min: 3, max: 200, message: '길이는 3자에서 200자 사이여야 합니다', trigger: 'blur' },
  ],
  certificate_id: [
    { required: true, message: '자격증을 선택하세요', trigger: 'change' },
  ],
  file_type: [
    { required: true, message: '파일 유형을 선택하세요', trigger: 'change' },
  ],
}

// Methods
const handleFileChange = (file: UploadFile, files: UploadFiles) => {
  // Validate file type
  if (!file.name.toLowerCase().endsWith('.pdf')) {
    ElMessage.error('PDF 파일만 허용됩니다')
    uploadRef.value?.clearFiles()
    return
  }
  
  // Validate file size (50MB)
  const maxSize = 50 * 1024 * 1024
  if (file.size && file.size > maxSize) {
    ElMessage.error('파일 크기는 50MB를 초과할 수 없습니다')
    uploadRef.value?.clearFiles()
    return
  }
  
  selectedFile.value = file.raw as File
  console.log("File selected:", file);
  console.log("File raw:", file.raw);
  console.log("Selected file:", selectedFile.value);
  
  // Auto-fill name if empty
  if (!uploadForm.name && file.name) {
    uploadForm.name = file.name.replace('.pdf', '').replace(/[_-]/g, ' ')
  }
}

const handleFileRemove = () => {
  selectedFile.value = null
}

const handleExceed = () => {
  ElMessage.warning('한 번에 하나의 파일만 업로드할 수 있습니다')
}

// Direct upload function with enhanced debugging
const uploadPdfDirect = async (file: File, uploadData: any) => {
  console.log("=== uploadPdfDirect called ===");
  console.log("Input file:", file);
  console.log("Input uploadData:", uploadData);
  
  if (!file) {
    console.error("ERROR: file is null or undefined");
    throw new Error("File is null or undefined");
  }
  
  try {
    const formData = new FormData();
    console.log("FormData created");
    
    formData.append("file", file);
    console.log("File appended to FormData");
    
    formData.append("name", uploadData.name);
    formData.append("certificate_id", uploadData.certificate_id.toString());
    formData.append("file_type", uploadData.file_type);
    if (uploadData.description) {
      formData.append("description", uploadData.description);
    }
    
    console.log("All form fields appended");

    console.log("FormData being sent:");
    for (let [key, value] of formData.entries()) {
      console.log(`  ${key}:`, value);
    }

    // 기본 PDF 업로드 API 사용
    const apiEndpoint = "/api/upload/pdf";
    
    console.log(`Making fetch request to ${apiEndpoint}`);
    const response = await fetch(apiEndpoint, {
      method: "POST",
      body: formData
    });
    
    console.log("Response received:", response.status, response.statusText);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("Response error:", errorText);
      throw new Error(errorText);
    }

    const result = await response.json();
    console.log("Response JSON:", result);
    return result;
  } catch (error) {
    console.error("uploadPdfDirect error:", error);
    throw error;
  }
};




const handleUpload = async () => {
  if (!uploadFormRef.value || !selectedFile.value) return
  console.log("🎯 프로페셔널 A/B/C 단계 처리 시작...");
  console.log("Selected file:", selectedFile.value);
  console.log("Upload form:", uploadForm);
  
  try {
    console.log("Starting form validation...");
    const validationResult = await uploadFormRef.value.validate();
    if (!validationResult) {
      console.error("Form validation failed!");
      return;
    }
    
    // 기본 데이터 설정
    currentFileName.value = selectedFile.value.name;
    pendingUploadData.value = { ...uploadForm };
    
    // 처리 진행 메시지
    ElMessage.info({
      message: '🎯 프로페셔널 A/B/C 단계 PDF 처리를 시작합니다... (2-3분 소요)',
      duration: 0,
      showClose: true
    });
    
    // 처리 모달 표시
    processingModal.value = true;
    processingStatus.value = {
      filename: currentFileName.value,
      progress: 0,
      current_step: 'A단계: PDF 구조 파악 중...',
      is_complete: false,
      steps: [
        { name: 'A단계: PDF 구조 파악', status: 'active' },
        { name: 'B단계: 정규 스키마 저장', status: 'waiting' },
        { name: 'C단계: LLM 유형·챕터 태깅', status: 'waiting' },
        { name: '처리 완료', status: 'waiting' }
      ]
    };
    
    console.log("🎯 프로페셔널 처리 API 호출 시작");
    
    // 프로페셔널 A/B/C 단계 처리 시작
    const processingResult = await uploadWithProfessionalProcessing(selectedFile.value, uploadForm);
    
    console.log("🎯 프로페셔널 처리 결과:", processingResult);
    
    // A단계 완료 - 진행률 업데이트
    processingStatus.value.progress = 33;
    processingStatus.value.current_step = 'B단계: 정규 스키마 저장 중...';
    processingStatus.value.steps[0].status = 'completed';
    processingStatus.value.steps[1].status = 'active';
    
    // 지연 효과 (진행률 표시)
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // B단계 완료 - 진행률 업데이트
    processingStatus.value.progress = 66;
    processingStatus.value.current_step = 'C단계: LLM 유형·챕터 태깅 중...';
    processingStatus.value.steps[1].status = 'completed';
    processingStatus.value.steps[2].status = 'active';
    
    // 지연 효과 (진행률 표시)
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // 최종 진행률 업데이트
    processingStatus.value.progress = 100;
    processingStatus.value.current_step = '프로페셔널 처리 완료';
    processingStatus.value.steps[2].status = 'completed';
    processingStatus.value.steps[3].status = 'completed';
    processingStatus.value.is_complete = true;
    
    // 결과 처리
    await handleProfessionalProcessingResult(processingResult);
    
    ElMessage.closeAll(); // 기존 메시지 제거
    
  } catch (error) {
    console.error("🎯 프로페셔널 처리 실패:", error);
    
    processingResult.value = {
      success: false,
      filename: selectedFile.value?.name || 'Unknown',
      error_message: error.message || '알 수 없는 오류가 발생했습니다',
      processed_at: new Date().toLocaleString('ko-KR')
    }
    
    ElMessage.error('프로페셔널 PDF 처리에 실패했습니다');
  } finally {
    // 정리 작업
    processingModal.value = false;
    selectedFile.value = null;
    pendingUploadData.value = null;
    currentUploadId.value = null;
    ElMessage.closeAll();
  }
}

// 프로페셔널 A/B/C 단계 처리를 위한 업로드 함수
const uploadWithProfessionalProcessing = async (file: File, uploadData: any) => {
  console.log("🎯 프로페셔널 A/B/C 단계 PDF 처리 시작");
  
  const formData = new FormData();
  formData.append("file", file);
  formData.append("name", uploadData.name);
  formData.append("certificate_id", uploadData.certificate_id.toString());
  formData.append("file_type", uploadData.file_type);
  if (uploadData.description) {
    formData.append("description", uploadData.description);
  }
  
  try {
    const response = await fetch("/api/smart-pdf/professional-process", {
      method: "POST",
      body: formData,
      // 프로페셔널 처리는 더 오래 걸릴 수 있음 (최대 5분)
      signal: AbortSignal.timeout(300000) // 5분 타임아웃
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText);
    }
    
    return await response.json();
  } catch (error) {
    console.error("Professional processing upload error:", error);
    throw error;
  }
};

// 프로페셔널 처리 결과 처리 함수
const handleProfessionalProcessingResult = async (result: any) => {
  console.log("🎯 프로페셔널 처리 결과:", result);
  
  // 바로 최종 결과 처리
  if (result.success) {
    // 성공 처리
    processingResult.value = {
      success: true,
      filename: result.filename || currentFileName.value,
      total_questions: result.total_questions || 0,
      processing_method: '프로페셔널 A/B/C 단계 파이프라인',
      stage_a_result: result.stage_a_result,
      stage_b_result: result.stage_b_result,
      stage_c_result: result.stage_c_result,
      processed_at: new Date().toLocaleString('ko-KR'),
      temp_upload_id: result.temp_upload_id,
      processing_details: {
        extracted_questions: result.stage_b_result?.questions || []
      }
    };
    
    ElMessage.success(`프로페셔널 PDF 처리 완료! ${result.total_questions}개 문제가 추출되었습니다.`);
  } else {
    // 실패 처리
    processingResult.value = {
      success: false,
      filename: result.filename || currentFileName.value,
      error_message: result.error || '알 수 없는 오류가 발생했습니다',
      processed_at: new Date().toLocaleString('ko-KR')
    };
    
    ElMessage.error('프로페셔널 PDF 처리에 실패했습니다');
  }
};

// 기존 구조 분석에 기반한 처리 진행 (사용 안함)
const proceedWithStructureBasedProcessing = async (analysisResult: any) => {
  console.log("🚀 구조 분석 결과로 처리 진행:", analysisResult);
  
  // 데이터 백업 (finally에서 초기화되기 전에 미리 복사)
  const uploadDataBackup = {
    ...pendingUploadData.value
  };
  const uploadIdBackup = currentUploadId.value;
  const fileNameBackup = currentFileName.value;
  
  try {
    // 처리 모달 표시 및 초기화
    processingModal.value = true;
    processingStatus.value = {
      filename: fileNameBackup,
      progress: 0,
      current_step: '구조 기반 맞춤형 처리 시작 중...',
      is_complete: false,
      steps: [
        { name: '구조 분석 활용', status: 'active' },
        { name: '맞춤형 문제 추출', status: 'waiting' },
        { name: '품질 검증', status: 'waiting' },
        { name: '최종 처리', status: 'waiting' }
      ]
    };
    
    // 실제 처리를 위해 구조 분석 결과를 포함하여 처리 시작
    const processingData = {
      ...uploadDataBackup,
      structure_analysis: analysisResult,
      temp_upload_id: uploadIdBackup
    };
    
    // 진행률 업데이트
    processingStatus.value.progress = 10;
    processingStatus.value.current_step = '구조 분석 결과 기반 맞춤형 처리 중...';
    processingStatus.value.steps[0].status = 'completed';
    processingStatus.value.steps[1].status = 'active';
    
    // 실제 처리 API 호출 (새로운 구조 기반 처리)
    const response = await fetch("/api/smart-pdf/proceed-with-structure", {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(processingData)
    });
    
    // 중간 진행률 업데이트
    processingStatus.value.progress = 70;
    processingStatus.value.current_step = '처리 결과 분석 중...';
    processingStatus.value.steps[1].status = 'completed';
    processingStatus.value.steps[2].status = 'active';
    
    const result = await response.json();
    
    if (result.success) {
      // 처리 완료 - 진행률 100%
      processingStatus.value.progress = 100;
      processingStatus.value.current_step = '스마트 분석 기반 처리 완료!';
      processingStatus.value.is_complete = true;
      processingStatus.value.steps = processingStatus.value.steps.map(step => ({ ...step, status: 'completed' }));
      
      processingResult.value = {
        success: true,
        filename: fileNameBackup,
        certificate_name: availableCertificates.value.find(cert => cert.id == uploadDataBackup.certificate_id)?.name || 'Unknown',
        file_type: uploadDataBackup.file_type,
        structure_analysis: analysisResult,
        processing_result: result.processing_result,
        processed_at: new Date().toLocaleString('ko-KR'),
        processing_details: result.processing_result
      };
      
      // 성공 메시지 표시 전 잠시 대기
      setTimeout(() => {
        processingModal.value = false;
        ElMessage.success('🎉 스마트 분석 기반 처리가 성공적으로 완료되었습니다!');
        
        // 성공 시 상태 초기화
        structureAnalysisVisible.value = false;
        currentUploadId.value = null;
        currentFileName.value = '';
        pendingUploadData.value = null;
        resetForm();
        fetchRecentUploads();
      }, 2000); // 2초 후 모달 닫기
    } else {
      throw new Error(result.error || '처리 실패');
    }
  } catch (error) {
    console.error("구조 기반 처리 실패:", error);
    
    // 처리 실패 상태 업데이트
    if (processingModal.value) {
      processingStatus.value.progress = 100;
      processingStatus.value.current_step = `처리 실패: ${error.message}`;
      processingStatus.value.is_complete = true;
      processingStatus.value.steps = processingStatus.value.steps.map(step => ({ ...step, status: 'error' }));
      
      // 실패 모달 3초 후 닫기
      setTimeout(() => {
        processingModal.value = false;
        ElMessage.error(`처리 실패: ${error.message}`);
        
        // 실패 시 상태 초기화
        structureAnalysisVisible.value = false;
        currentUploadId.value = null;
        currentFileName.value = '';
        pendingUploadData.value = null;
        resetForm();
        fetchRecentUploads();
      }, 3000);
    } else {
      ElMessage.error(`처리 실패: ${error.message}`);
      
      // 즉시 실패 시 상태 초기화
      structureAnalysisVisible.value = false;
      currentUploadId.value = null;
      currentFileName.value = '';
      pendingUploadData.value = null;
      resetForm();
      fetchRecentUploads();
    }
  }
  // finally 블록 제거 - 각 경우에서 개별 처리
};

// 구조 분석 취소
const cancelStructureAnalysis = () => {
  console.log("❌ 구조 분석 취소");
  
  structureAnalysisVisible.value = false;
  currentUploadId.value = null;
  currentFileName.value = '';
  pendingUploadData.value = null;
  
  ElMessage.info('구조 분석이 취소되었습니다.');
};

const resetForm = () => {
  uploadForm.name = ''
  uploadForm.certificate_id = ''
  uploadForm.file_type = 'questions'
  uploadForm.description = ''
  // processing_method는 항상 'smart'로 고정
  selectedFile.value = null
  uploadRef.value?.clearFiles()
  uploadFormRef.value?.resetFields()
}

const viewCertificate = (certificate: Certificate) => {
  router.push(`/certificates/${certificate.id}`)
}

const fetchRecentUploads = async () => {
  try {
    loadingRecent.value = true
    
    // Fetch recent uploads from the store
    const files = await certificatesStore.fetchUploadedFiles()
    recentUploads.value = files.slice(0, 5).map(file => ({
      id: file.filename,
      name: file.filename.replace(/^\d{8}_\d{6}_[a-f0-9]{8}_/, ''),
      file_size: file.size,
      upload_date: file.uploaded_at,
      processed: false
    }))
  } catch (error) {
    console.error('Failed to fetch recent uploads:', error)
  } finally {
    loadingRecent.value = false
  }
}

const refreshRecentUploads = () => {
  fetchRecentUploads()
}

const loadCertificates = async () => {
  try {
    availableCertificates.value = await certificatesStore.fetchCertificatesInfo()
  } catch (error) {
    console.error('Failed to load certificates:', error)
  }
}

const viewDetailedResults = () => {
  if (processingResult.value?.processing_details) {
    detailModalVisible.value = true
  }
}

const clearResults = () => {
  processingResult.value = null
}

// 처리 상황 모니터링 관련
const processingModal = ref(false)
const processingStatus = ref({
  upload_id: null,
  filename: '',
  progress: 0,
  current_step: '',
  steps: [],
  is_complete: false
})

const startProcessingMonitor = async (uploadId) => {
  if (!uploadId) return
  
  processingStatus.value = {
    upload_id: uploadId,
    filename: selectedFile.value?.name || 'Unknown',
    progress: 0,
    current_step: 'OCR 처리 중...',
    steps: [
      { name: 'OCR 텍스트 추출', status: 'processing' },
      { name: 'Claude AI 문서 분석', status: 'pending' },
      { name: 'Claude AI 문제 추출', status: 'pending' },
      { name: 'Claude AI 학습자료 생성', status: 'pending' },
      { name: 'Claude AI 품질 검증', status: 'pending' },
      { name: '데이터베이스 저장', status: 'pending' }
    ],
    is_complete: false
  }
  
  processingModal.value = true
  
  // 3초마다 상태 확인 (더 빈번한 체크)
  let retryCount = 0
  const maxRetries = 60 // 3분 최대 대기
  
  const interval = setInterval(async () => {
    try {
      const response = await fetch(`/api/upload/files/${uploadId}/status`)
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      const status = await response.json()
      console.log('Processing status:', status)
      
      // 진행률 기반 업데이트 (백엔드에서 계산된 값 사용)
      if (status.progress_percentage !== undefined) {
        processingStatus.value.progress = Math.min(status.progress_percentage, 100)
      }
      
      // 처리 완료 확인
      if (status.processing_status === 'completed' || status.progress_percentage >= 100) {
        processingStatus.value.progress = 100
        processingStatus.value.current_step = '처리 완료!'
        processingStatus.value.is_complete = true
        processingStatus.value.steps = processingStatus.value.steps.map(step => ({ ...step, status: 'completed' }))
        clearInterval(interval)
        
        // 처리 결과 정보 추가
        if (status.processing_result || status.questions_count !== undefined) {
          processingStatus.value.result = {
            questions_count: status.questions_count || 0,
            materials_count: status.materials_count || 0,
            total_cost: status.total_cost || 0,
            quality_score: status.quality_score || 0
          }
          processingStatus.value.current_step = `처리 완료! 문제 ${status.questions_count || 0}개, 자료 ${status.materials_count || 0}개 생성`
        }
        
        // 5초 후에 닫기 (결과 확인 시간)
        setTimeout(() => {
          processingModal.value = false
          fetchRecentUploads()
        }, 5000)
        return
      }
      
      // 실패 처리
      if (status.processing_status === 'failed') {
        processingStatus.value.current_step = '처리 실패: ' + (status.error_message || '알 수 없는 오류')
        processingStatus.value.steps = processingStatus.value.steps.map((step, i) => 
          i === 0 ? { ...step, status: 'failed' } : step
        )
        clearInterval(interval)
        return
      }
      
      // 처리 중 단계별 업데이트
      if (status.processing_steps && status.processing_steps.length > 0) {
        const currentStep = status.processing_steps.find(step => step.status === 'processing')
        if (currentStep) {
          processingStatus.value.current_step = `${currentStep.name} 처리 중...`
        }
        
        // 단계별 진행률 자동 계산 (백엔드 값이 없을 경우)
        if (status.progress_percentage === undefined || status.progress_percentage === 0) {
          const completedSteps = status.processing_steps.filter(step => step.status === 'completed').length
          const totalSteps = status.processing_steps.length
          processingStatus.value.progress = Math.min((completedSteps / totalSteps) * 90, 90)
        }
      } else {
        // 백엔드에서 단계 정보가 없을 경우 점진적 증가 (최대 85%까지)
        processingStatus.value.progress = Math.min(processingStatus.value.progress + 5, 85)
      }
      
      retryCount = 0 // 성공시 재시도 카운트 리셋
      
    } catch (error) {
      console.error('Status check failed:', error)
      retryCount++
      
      if (retryCount >= maxRetries) {
        processingStatus.value.current_step = '처리 시간 초과 (3분 경과)'
        processingStatus.value.steps = processingStatus.value.steps.map((step, i) => 
          i === 0 ? { ...step, status: 'failed' } : step
        )
        clearInterval(interval)
      }
    }
  }, 3000)
}

const exportResults = () => {
  if (!processingResult.value?.processing_details) return
  
  // Create JSON export
  const exportData = {
    filename: processingResult.value.filename,
    certificate_name: processingResult.value.certificate_name,
    processed_at: processingResult.value.processed_at,
    summary: {
      total_pages: processingResult.value.total_pages,
      questions_count: processingResult.value.questions_count,
      study_materials_count: processingResult.value.study_materials_count
    },
    extracted_questions: processingResult.value.processing_details.extracted_questions || [],
    pages: processingResult.value.processing_details.pages || [],
    processing_errors: processingResult.value.processing_details.processing_errors || []
  }
  
  // Create and download file
  const dataStr = JSON.stringify(exportData, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  const link = document.createElement('a')
  link.href = url
  link.download = `processing_results_${processingResult.value.filename.replace('.pdf', '')}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  
  ElMessage.success('처리 결과를 JSON 파일로 내보냈습니다')
}

// Initialize
onMounted(() => {
  loadCertificates()
  fetchRecentUploads()
})
</script>

<style scoped>
.upload-view {
  max-width: 1200px;
  margin: 0 auto;
}

.upload-card {
  margin-bottom: 24px;
  height: fit-content;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.upload-dragger {
  width: 100%;
}

.upload-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
}

.upload-progress {
  margin-top: 20px;
  padding: 20px;
}

/* Processing Modal Styles */
.processing-content {
  text-align: center;
}

.file-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-bottom: 24px;
  font-weight: 500;
  color: #606266;
}

.progress-section {
  margin-bottom: 32px;
}

.current-step {
  margin-top: 12px;
  font-size: 14px;
  color: #909399;
}

.steps-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  text-align: left;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.step-icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #409eff;
  animation: pulse 1.5s ease-in-out infinite;
}

.pending-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #dcdfe6;
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.4;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.2);
  }
}

.step-item.completed .step-name {
  color: #67c23a;
}

.step-item.failed .step-name {
  color: #f56c6c;
}

.step-item.processing .step-name {
  color: #409eff;
  font-weight: 500;
}

.progress-text {
  margin-top: 8px;
  text-align: center;
  color: #606266;
  font-size: 14px;
}

.guidelines-card {
  margin-bottom: 24px;
}

.guidelines-content {
  margin-bottom: 24px;
}

.guideline-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 20px;
}

.guideline-icon {
  margin-top: 2px;
  flex-shrink: 0;
}

.guideline-item h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
}

.guideline-item p {
  margin: 0;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

.features-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #2c3e50;
}

.recent-uploads-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recent-uploads-list {
  min-height: 200px;
}

.upload-item {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid #f0f2f5;
  cursor: pointer;
  transition: background-color 0.2s;
}

.upload-item:hover {
  background-color: #f8f9fa;
}

.upload-item:last-child {
  border-bottom: none;
}

.upload-icon {
  width: 40px;
  height: 40px;
  background: #f0f9ff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #409eff;
  margin-right: 12px;
  flex-shrink: 0;
}

.upload-info {
  flex: 1;
  min-width: 0;
}

.upload-name {
  font-size: 14px;
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.upload-meta {
  font-size: 12px;
  color: #7f8c8d;
}

.upload-status {
  margin-right: 12px;
  flex-shrink: 0;
}

.upload-actions {
  flex-shrink: 0;
}

/* Responsive design */
@media (max-width: 768px) {
  .guideline-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .guideline-icon {
    margin-top: 0;
  }
  
  .upload-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .upload-info {
    width: 100%;
  }
  
  .upload-name {
    white-space: normal;
  }
  
  .upload-status,
  .upload-actions {
    align-self: flex-end;
  }
}

/* Upload component overrides */
:deep(.el-upload-dragger) {
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  width: 100%;
  height: 140px;
  position: relative;
  overflow: hidden;
  background-color: #fafafa;
  transition: border-color 0.3s;
}

:deep(.el-upload-dragger:hover) {
  border-color: #409eff;
}

:deep(.el-upload-dragger.is-dragover) {
  border-color: #409eff;
  background-color: rgba(64, 158, 255, 0.06);
}

:deep(.el-icon--upload) {
  font-size: 48px;
  color: #c0c4cc;
  margin-bottom: 16px;
}

:deep(.el-upload__text) {
  color: #606266;
  font-size: 14px;
}

:deep(.el-upload__text em) {
  color: #409eff;
  font-style: normal;
}

:deep(.el-upload__tip) {
  font-size: 12px;
  color: #909399;
  margin-top: 8px;
}

/* Processing Results Styles */
.processing-results-card {
  margin-top: 24px;
  margin-bottom: 24px;
}

.processing-results-content {
  padding: 16px 0;
}

.results-summary {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.stat-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.stat-info {
  flex: 1;
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #6c757d;
}

.results-details {
  background: #ffffff;
  border: 1px solid #e9ecef;
  border-radius: 8px;
  padding: 16px;
}

.results-details h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #2c3e50;
}

.results-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.error-message {
  padding: 16px;
  background: #fef2f2;
  border-radius: 8px;
  border: 1px solid #fecaca;
}

/* Modal Styles */
.detail-content {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-summary,
.detail-questions,
.detail-pages,
.detail-errors {
  margin-bottom: 20px;
}

.detail-summary h3,
.detail-questions h3,
.detail-pages h3,
.detail-errors h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #2c3e50;
}

.questions-list {
  max-height: 400px;
  overflow-y: auto;
}

.question-detail {
  padding: 16px 0;
}

.question-text {
  margin-bottom: 12px;
}

.question-text p {
  margin: 8px 0;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  line-height: 1.5;
}

.question-passage {
  margin-bottom: 12px;
}

.question-passage p {
  margin: 8px 0;
  padding: 12px;
  background: #e8f4fd;
  border-left: 4px solid #409eff;
  border-radius: 6px;
  line-height: 1.5;
}

.question-additional {
  margin-bottom: 12px;
}

.question-additional p {
  margin: 8px 0;
  padding: 12px;
  background: #f0f9ff;
  border-left: 4px solid #67c23a;
  border-radius: 6px;
  line-height: 1.5;
}

.question-options {
  margin-bottom: 12px;
}

.question-options ol {
  margin: 8px 0;
  padding-left: 20px;
}

.question-options li {
  margin-bottom: 4px;
  line-height: 1.4;
}

.question-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>