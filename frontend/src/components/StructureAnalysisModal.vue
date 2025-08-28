<template>
  <el-dialog
    :model-value="visible"
    @update:model-value="handleVisibleChange"
    title="📊 PDF 구조 분석 결과"
    width="80%"
    :before-close="handleClose"
    :close-on-click-modal="false"
    center
    class="structure-analysis-modal"
  >
    <!-- 로딩 상태 -->
    <div v-if="loading" class="loading-container">
      <div class="analysis-progress">
        <el-progress 
          :percentage="progressPercentage" 
          :status="progressStatus"
          :stroke-width="8"
        />
        <div class="progress-text">
          <h3>🔍 {{ currentStep }}</h3>
          <p>{{ currentDescription }}</p>
          <div class="time-info">
            <span>⏱️ 경과시간: {{ elapsedTime }}초</span>
            <span>📊 예상 완료: {{ estimatedCompletion }}</span>
          </div>
        </div>
      </div>
      
      <!-- 실시간 로그 -->
      <div class="real-time-logs" v-if="realtimeLogs.length > 0">
        <h4>📝 실시간 분석 로그</h4>
        <div class="log-container">
          <div 
            v-for="(log, index) in realtimeLogs" 
            :key="index" 
            class="log-item"
            :class="log.type"
          >
            <span class="log-time">{{ log.timestamp }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 분석 완료 결과 -->
    <div v-else-if="analysisResult" class="analysis-result">
      <!-- 분석 요약 -->
      <div class="analysis-summary">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-card class="summary-card">
              <div class="summary-item">
                <div class="summary-icon">📄</div>
                <div class="summary-content">
                  <h3>문서 타입</h3>
                  <p>{{ getDocumentTypeText(analysisResult.analysis_summary?.document_type) }}</p>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="summary-card">
              <div class="summary-item">
                <div class="summary-icon">📊</div>
                <div class="summary-content">
                  <h3>총 문제 수</h3>
                  <p class="big-number">{{ analysisResult.analysis_summary?.total_questions || 0 }}</p>
                </div>
              </div>
            </el-card>
          </el-col>
          <el-col :span="8">
            <el-card class="summary-card">
              <div class="summary-item">
                <div class="summary-icon">🎯</div>
                <div class="summary-content">
                  <h3>분석 신뢰도</h3>
                  <p class="confidence-score">
                    {{ Math.round((analysisResult.analysis_summary?.confidence_score || 0) * 100) }}%
                  </p>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 페이지별 상세 분석 -->
      <div class="page-analysis" v-if="analysisResult.page_analysis">
        <h3>📄 페이지별 상세 분석</h3>
        <div class="page-grid">
          <div 
            v-for="page in analysisResult.page_analysis" 
            :key="page.page_number"
            class="page-card"
            :class="getPageTypeClass(page.page_type)"
          >
            <div class="page-header">
              <span class="page-number">페이지 {{ page.page_number }}</span>
              <span class="page-type">{{ getPageTypeText(page.page_type) }}</span>
            </div>
            <div class="page-details">
              <div class="detail-item">
                <span class="label">문제 수:</span>
                <span class="value">{{ page.question_density || 0 }}개</span>
              </div>
              <div class="detail-item" v-if="page.questions_on_page?.length">
                <span class="label">문제 번호:</span>
                <span class="value">{{ page.questions_on_page.join(', ') }}</span>
              </div>
              <div class="detail-item" v-if="page.special_elements?.length">
                <span class="label">특별 요소:</span>
                <div class="special-elements">
                  <el-tag 
                    v-for="element in page.special_elements" 
                    :key="element"
                    size="small"
                    :type="getElementTagType(element)"
                  >
                    {{ getElementText(element) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 문제별 상세 분석 -->
      <div class="question-analysis" v-if="analysisResult.question_analysis?.detailed_questions">
        <h3>📝 문제별 상세 분석</h3>
        <el-table 
          :data="analysisResult.question_analysis.detailed_questions.slice(0, 10)" 
          style="width: 100%"
          size="small"
        >
          <el-table-column prop="question_number" label="번호" width="60" />
          <el-table-column prop="question_type" label="유형" width="120">
            <template #default="scope">
              {{ getQuestionTypeText(scope.row.question_type) }}
            </template>
          </el-table-column>
          <el-table-column prop="choices_count" label="선택지" width="80" />
          <el-table-column prop="page_location" label="페이지" width="80" />
          <el-table-column label="특성" min-width="200">
            <template #default="scope">
              <div class="question-features">
                <el-tag v-if="scope.row.has_passage" size="small" type="info">지문</el-tag>
                <el-tag v-if="scope.row.has_table" size="small" type="warning">표</el-tag>
                <el-tag v-if="scope.row.has_images" size="small" type="success">이미지</el-tag>
                <el-tag v-if="scope.row.has_code" size="small" type="danger">코드</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="processing_complexity" label="처리 복잡도" width="100">
            <template #default="scope">
              <el-tag 
                size="small" 
                :type="getComplexityTagType(scope.row.processing_complexity)"
              >
                {{ scope.row.processing_complexity }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
        <div v-if="analysisResult.question_analysis.detailed_questions.length > 10" class="more-questions">
          <p>총 {{ analysisResult.question_analysis.detailed_questions.length }}개 문제 중 10개만 표시</p>
        </div>
      </div>

      <!-- 특별 요소 분석 -->
      <div class="special-elements-analysis" v-if="analysisResult.special_elements">
        <h3>🎯 특별 요소 분석</h3>
        <el-row :gutter="20">
          <!-- 표 분석 -->
          <el-col :span="12" v-if="analysisResult.special_elements.tables?.length">
            <el-card class="element-card">
              <template #header>
                <span>📊 표 분석</span>
              </template>
              <div v-for="table in analysisResult.special_elements.tables" :key="table.location">
                <div class="element-item">
                  <strong>{{ table.location }}</strong>
                  <p>유형: {{ table.table_type }}</p>
                  <p>복잡도: {{ table.complexity }}</p>
                  <p>데이터 완성도: {{ table.data_completeness }}</p>
                </div>
              </div>
            </el-card>
          </el-col>
          
          <!-- 이미지 분석 -->
          <el-col :span="12" v-if="analysisResult.special_elements.images?.length">
            <el-card class="element-card">
              <template #header>
                <span>🖼️ 이미지 분석</span>
              </template>
              <div v-for="image in analysisResult.special_elements.images" :key="image.location">
                <div class="element-item">
                  <strong>{{ image.location }}</strong>
                  <p>용도: {{ getImagePurposeText(image.image_purpose) }}</p>
                  <p>개수: {{ image.image_count_at_location }}개</p>
                </div>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </div>

      <!-- 처리 전략 -->
      <div class="processing-strategy" v-if="analysisResult.processing_strategy">
        <h3>⚙️ 권장 처리 전략</h3>
        <el-card>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="권장 접근법">
              {{ analysisResult.processing_strategy.recommended_approach }}
            </el-descriptions-item>
            <el-descriptions-item label="청크 크기">
              {{ analysisResult.processing_strategy.chunk_size_recommendation }}
            </el-descriptions-item>
            <el-descriptions-item label="예상 처리 시간">
              {{ analysisResult.processing_strategy.estimated_processing_time }}
            </el-descriptions-item>
            <el-descriptions-item label="특별 처리 사항" :span="2">
              <div class="special-handling">
                <el-tag 
                  v-for="item in analysisResult.processing_strategy.special_handling" 
                  :key="item"
                  class="strategy-tag"
                >
                  {{ item }}
                </el-tag>
              </div>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </div>

      <!-- 품질 검사 결과 -->
      <div class="quality-checks" v-if="analysisResult.quality_checks">
        <h3>✅ 분석 품질 검사</h3>
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="quality-item">
              <div class="quality-label">완성도</div>
              <el-progress 
                :percentage="Math.round(analysisResult.quality_checks.completeness_score * 100)"
                :stroke-width="8"
                :show-text="true"
              />
            </div>
          </el-col>
          <el-col :span="8">
            <div class="quality-item">
              <div class="quality-label">일관성</div>
              <el-progress 
                :percentage="Math.round(analysisResult.quality_checks.consistency_score * 100)"
                :stroke-width="8"
                :show-text="true"
              />
            </div>
          </el-col>
          <el-col :span="8">
            <div class="quality-item">
              <div class="quality-label">신뢰성</div>
              <el-progress 
                :percentage="Math.round(analysisResult.quality_checks.reliability_score * 100)"
                :stroke-width="8"
                :show-text="true"
              />
            </div>
          </el-col>
        </el-row>
        <div v-if="analysisResult.quality_checks.issues_found?.length" class="quality-issues">
          <h4>⚠️ 발견된 이슈</h4>
          <el-alert
            v-for="issue in analysisResult.quality_checks.issues_found"
            :key="issue"
            :title="issue"
            type="warning"
            show-icon
            :closable="false"
          />
        </div>
      </div>
    </div>

    <!-- 오류 상태 -->
    <div v-else-if="error" class="error-state">
      <el-result
        icon="error"
        title="분석 실패"
        :sub-title="error"
      >
        <template #extra>
          <el-button type="primary" @click="retryAnalysis">다시 시도</el-button>
        </template>
      </el-result>
    </div>

    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose" :disabled="loading">취소</el-button>
        <el-button 
          v-if="!loading && analysisResult" 
          type="primary" 
          @click="proceedWithProcessing"
        >
          이 구조로 처리 진행
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'

interface Props {
  visible: boolean
  uploadId?: number
  fileName?: string
  analysisResult?: any
}

interface Emits {
  (e: 'update:visible', value: boolean): void
  (e: 'proceed-processing', analysisResult: any): void
  (e: 'cancel'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// 상태 관리
const loading = ref(true)
const analysisResult = ref<any>(null)
const error = ref<string>('')

// 진행률 관리
const progressPercentage = ref(0)
const progressStatus = ref<'success' | 'exception' | undefined>(undefined)
const currentStep = ref('PDF 구조 분석 준비 중...')
const currentDescription = ref('고해상도 이미지 생성 및 초기 분석 시작')
const elapsedTime = ref(0)
const estimatedCompletion = ref('2-3분')

// 실시간 로그
const realtimeLogs = ref<Array<{
  timestamp: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
}>>([])

// 타이머
let progressTimer: NodeJS.Timeout | null = null
let elapsedTimer: NodeJS.Timeout | null = null

// 컴포넌트 마운트 시 분석 시작
onMounted(() => {
  console.log('🔍 StructureAnalysisModal mounted:', {
    visible: props.visible,
    uploadId: props.uploadId,
    fileName: props.fileName
  });
  // watch에서 처리하므로 여기서는 분석 시작 안 함
})

onUnmounted(() => {
  clearTimers()
})

// visible prop 변경 감지
watch(() => props.visible, (newVisible) => {
  console.log('🔍 StructureAnalysisModal visible 변경:', newVisible);
  
  if (newVisible) {
    console.log('✅ 모달 표시됨');
    
    if (props.analysisResult) {
      // 이미 분석 완료된 결과가 있으면 바로 표시
      console.log('✅ 분석 결과 있음, 바로 표시', props.analysisResult);
      analysisResult.value = props.analysisResult;
      loading.value = false;
      progressPercentage.value = 100;
      progressStatus.value = 'success';
      currentStep.value = '구조 분석 완료';
      currentDescription.value = '분석 결과를 확인하세요';
    } else {
      // 분석 결과가 없으면 오류 표시
      console.log('⚠️ 분석 결과 없음 - 이런 일은 말라');
      error.value = '분석 결과를 받지 못했습니다.';
      loading.value = false;
    }
  } else {
    // 모달이 닫히면 상태 리셋
    loading.value = false;
    analysisResult.value = null;
    error.value = '';
    clearTimers();
  }
})

const clearTimers = () => {
  if (progressTimer) clearInterval(progressTimer)
  if (elapsedTimer) clearInterval(elapsedTimer)
}

const startStructureAnalysis = async () => {
  loading.value = true
  progressPercentage.value = 0
  elapsedTime.value = 0
  
  // 경과 시간 타이머
  elapsedTimer = setInterval(() => {
    elapsedTime.value++
  }, 1000)
  
  // 진행률 시뮬레이션 (실제로는 백엔드에서 진행률 받아올 것)
  progressTimer = setInterval(() => {
    if (progressPercentage.value < 90) {
      progressPercentage.value += Math.random() * 10
      updateProgressStatus()
    }
  }, 2000)
  
  try {
    // 실제 구조 분석 API 호출
    const response = await fetch(`/api/smart-pdf/analyze-structure/${props.uploadId}`)
    const result = await response.json()
    
    if (result.success) {
      analysisResult.value = result.structure_analysis
      progressPercentage.value = 100
      progressStatus.value = 'success'
      currentStep.value = '구조 분석 완료'
      currentDescription.value = '분석 결과를 확인하세요'
      
      addLog('구조 분석 완료 - 결과를 확인하세요', 'success')
      
      // 분석 완료 메시지
      ElMessage.success({
        message: '🎉 PDF 구조 분석이 완료되었습니다! 결과를 확인하고 처리를 진행하세요.',
        duration: 5000,
        showClose: true
      })
    } else {
      throw new Error(result.error || '구조 분석 실패')
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : '알 수 없는 오류'
    progressStatus.value = 'exception'
    addLog(`분석 실패: ${error.value}`, 'error')
  } finally {
    loading.value = false
    clearTimers()
  }
}

const updateProgressStatus = () => {
  if (progressPercentage.value < 30) {
    currentStep.value = 'PDF 페이지 이미지 변환 중...'
    currentDescription.value = '초고해상도 이미지 생성'
    addLog('PDF 페이지를 고해상도 이미지로 변환 중', 'info')
  } else if (progressPercentage.value < 60) {
    currentStep.value = 'GPT Vision 구조 분석 중...'
    currentDescription.value = '문서 타입, 페이지 구성, 문제 유형 분석'
    addLog('GPT Vision으로 문서 구조 분석 중', 'info')
  } else if (progressPercentage.value < 90) {
    currentStep.value = '분석 결과 검증 및 보완 중...'
    currentDescription.value = '분석 품질 검사 및 처리 전략 수립'
    addLog('분석 결과 품질 검증 중', 'info')
  }
}

const addLog = (message: string, type: 'info' | 'success' | 'warning' | 'error') => {
  const now = new Date()
  realtimeLogs.value.push({
    timestamp: now.toLocaleTimeString(),
    message,
    type
  })
  
  // 로그 개수 제한
  if (realtimeLogs.value.length > 20) {
    realtimeLogs.value.shift()
  }
}

const handleVisibleChange = (value: boolean) => {
  emit('update:visible', value)
}

const handleClose = () => {
  emit('update:visible', false)
  emit('cancel')
}

const proceedWithProcessing = () => {
  emit('proceed-processing', analysisResult.value)
  handleClose()
}

const retryAnalysis = () => {
  error.value = ''
  startStructureAnalysis()
}

// 텍스트 변환 함수들
const getDocumentTypeText = (type: string) => {
  const types: Record<string, string> = {
    'questions_only': '문제집',
    'theory_only': '이론서',
    'mixed': '문제+이론 혼합',
    'answers_explanations': '답안+해설',
    'practice_tests': '모의고사',
    'summary_notes': '요약노트'
  }
  return types[type] || type
}

const getPageTypeText = (type: string) => {
  const types: Record<string, string> = {
    'pure_questions': '문제',
    'theory_explanation': '이론',
    'mixed_content': '혼합',
    'answer_sheet': '답안',
    'cover_page': '표지',
    'table_of_contents': '목차'
  }
  return types[type] || type
}

const getPageTypeClass = (type: string) => {
  const classes: Record<string, string> = {
    'pure_questions': 'page-questions',
    'theory_explanation': 'page-theory',
    'mixed_content': 'page-mixed',
    'answer_sheet': 'page-answers'
  }
  return classes[type] || 'page-default'
}

const getQuestionTypeText = (type: string) => {
  const types: Record<string, string> = {
    'text_only': '텍스트만',
    'with_passage': '지문형',
    'with_table': '표 포함',
    'with_image': '이미지 포함',
    'with_code': '코드 포함',
    'with_diagram': '도표 포함'
  }
  return types[type] || type
}

const getElementText = (element: string) => {
  const elements: Record<string, string> = {
    'tables': '표',
    'diagrams': '도표',
    'code_blocks': '코드',
    'mathematical_formulas': '수식',
    'images': '이미지'
  }
  return elements[element] || element
}

const getElementTagType = (element: string) => {
  const types: Record<string, any> = {
    'tables': 'warning',
    'diagrams': 'success',
    'code_blocks': 'danger',
    'mathematical_formulas': 'info',
    'images': 'primary'
  }
  return types[element] || 'default'
}

const getComplexityTagType = (complexity: string) => {
  const types: Record<string, any> = {
    'low': 'success',
    'medium': 'warning',
    'high': 'danger'
  }
  return types[complexity] || 'info'
}

const getImagePurposeText = (purpose: string) => {
  const purposes: Record<string, string> = {
    '선택지': '선택지용',
    '설명': '설명용',
    '장식': '장식용'
  }
  return purposes[purpose] || purpose
}
</script>

<style scoped>
.structure-analysis-modal {
  .loading-container {
    text-align: center;
    padding: 40px 20px;
  }
  
  .analysis-progress {
    margin-bottom: 30px;
    
    .progress-text {
      margin-top: 20px;
      
      h3 {
        margin-bottom: 8px;
        color: #409eff;
      }
      
      p {
        color: #666;
        margin-bottom: 15px;
      }
      
      .time-info {
        display: flex;
        justify-content: center;
        gap: 30px;
        font-size: 12px;
        color: #999;
      }
    }
  }
  
  .real-time-logs {
    margin-top: 30px;
    text-align: left;
    
    h4 {
      margin-bottom: 10px;
    }
    
    .log-container {
      max-height: 200px;
      overflow-y: auto;
      background: #f5f5f5;
      border-radius: 6px;
      padding: 10px;
      
      .log-item {
        display: flex;
        margin-bottom: 5px;
        font-size: 12px;
        
        .log-time {
          color: #999;
          margin-right: 10px;
          min-width: 60px;
        }
        
        .log-message {
          flex: 1;
        }
        
        &.success .log-message { color: #67c23a; }
        &.warning .log-message { color: #e6a23c; }
        &.error .log-message { color: #f56c6c; }
        &.info .log-message { color: #409eff; }
      }
    }
  }
  
  .analysis-result {
    .analysis-summary {
      margin-bottom: 30px;
      
      .summary-card {
        .summary-item {
          display: flex;
          align-items: center;
          
          .summary-icon {
            font-size: 32px;
            margin-right: 15px;
          }
          
          .summary-content {
            h3 {
              margin: 0 0 5px 0;
              font-size: 14px;
              color: #666;
            }
            
            p {
              margin: 0;
              font-size: 16px;
              font-weight: 600;
              
              &.big-number {
                font-size: 24px;
                color: #409eff;
              }
              
              &.confidence-score {
                color: #67c23a;
              }
            }
          }
        }
      }
    }
    
    .page-analysis {
      margin-bottom: 30px;
      
      .page-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
        gap: 15px;
        margin-top: 15px;
        
        .page-card {
          border: 1px solid #ddd;
          border-radius: 8px;
          padding: 15px;
          
          &.page-questions {
            border-left: 4px solid #409eff;
          }
          
          &.page-theory {
            border-left: 4px solid #67c23a;
          }
          
          &.page-mixed {
            border-left: 4px solid #e6a23c;
          }
          
          &.page-answers {
            border-left: 4px solid #f56c6c;
          }
          
          .page-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
            
            .page-number {
              font-weight: 600;
            }
            
            .page-type {
              font-size: 12px;
              color: #666;
            }
          }
          
          .page-details {
            .detail-item {
              display: flex;
              justify-content: space-between;
              margin-bottom: 8px;
              font-size: 12px;
              
              .label {
                color: #666;
              }
              
              .value {
                font-weight: 500;
              }
              
              .special-elements {
                display: flex;
                flex-wrap: wrap;
                gap: 4px;
              }
            }
          }
        }
      }
    }
    
    .question-analysis {
      margin-bottom: 30px;
      
      .question-features {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
      }
      
      .more-questions {
        text-align: center;
        color: #666;
        font-size: 12px;
        margin-top: 10px;
      }
    }
    
    .special-elements-analysis {
      margin-bottom: 30px;
      
      .element-card {
        .element-item {
          margin-bottom: 15px;
          padding-bottom: 15px;
          border-bottom: 1px solid #eee;
          
          &:last-child {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
          }
          
          strong {
            display: block;
            margin-bottom: 5px;
            color: #409eff;
          }
          
          p {
            margin: 2px 0;
            font-size: 12px;
            color: #666;
          }
        }
      }
    }
    
    .processing-strategy {
      margin-bottom: 30px;
      
      .special-handling {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        
        .strategy-tag {
          margin: 2px 0;
        }
      }
    }
    
    .quality-checks {
      .quality-item {
        text-align: center;
        
        .quality-label {
          margin-bottom: 10px;
          font-weight: 600;
        }
      }
      
      .quality-issues {
        margin-top: 20px;
        
        h4 {
          margin-bottom: 10px;
        }
        
        .el-alert {
          margin-bottom: 8px;
        }
      }
    }
  }
  
  .error-state {
    text-align: center;
    padding: 40px 20px;
  }
}
</style>