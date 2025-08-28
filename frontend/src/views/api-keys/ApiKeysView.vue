<template>
  <div class="api-keys-view">
    <div class="container">
      <div class="page-header">
        <div class="header-content">
          <div class="title-section">
            <h1 class="page-title">
              <el-icon class="title-icon"><Key /></el-icon>
              API 키 관리
            </h1>
            <p class="page-description">Claude와 OpenAI API 키를 관리하고 토큰 사용량을 모니터링하세요</p>
          </div>
          <div class="action-buttons">
            <el-button :icon="Refresh" @click="refreshData">새로고침</el-button>
            <el-button type="primary" :icon="Plus" @click="showAddDialog = true">API 키 추가</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- API 키 목록 -->
    <div class="api-keys-container">
      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>API 키 정보를 가져오는 중...</span>
      </div>

      <div v-else-if="apiKeys.length === 0" class="empty-container">
        <el-empty description="등록된 API 키가 없습니다">
          <el-button type="primary" @click="showAddDialog = true">첫 번째 API 키 추가</el-button>
        </el-empty>
      </div>

      <div v-else class="api-keys-grid">
        <el-card v-for="key in apiKeys" :key="key.id" class="api-key-card" shadow="hover">
          <template #header>
            <div class="key-header">
              <div class="key-info">
                <h3 class="key-name">{{ key.name }}</h3>
                <div class="key-tags">
                  <el-tag :type="getProviderTagType(key.provider)" size="small">
                    {{ getProviderLabel(key.provider) }}
                  </el-tag>
                  <el-tag :type="key.is_active ? 'success' : 'danger'" size="small">
                    {{ key.is_active ? '활성' : '비활성' }}
                  </el-tag>
                </div>
              </div>
              <div class="key-actions">
                <el-tooltip content="상세보기" placement="top">
                  <el-button :icon="View" type="info" size="small" @click="viewKeyDetails(key)" circle />
                </el-tooltip>
                <el-tooltip content="편집" placement="top">
                  <el-button :icon="Edit" size="small" @click="editKey(key)" circle />
                </el-tooltip>
                <el-tooltip content="삭제" placement="top">
                  <el-button :icon="Delete" type="danger" size="small" @click="deleteKey(key)" circle />
                </el-tooltip>
              </div>
            </div>
          </template>

          <div class="key-content">
            <div class="key-preview">
              <span class="key-label">API 키:</span>
              <span class="key-text">{{ maskApiKey(key.api_key) }}</span>
            </div>

            <!-- 토큰 크레딧 정보 -->
            <div class="credit-info">
              <div class="credit-item">
                <div class="credit-label">남은 크레딧</div>
                <div class="credit-value" :class="getCreditColorClass(key.remaining_credits, key.total_credits)">
                  {{ formatCurrency(key.remaining_credits, 2) }}
                </div>
              </div>
              <div class="credit-item">
                <div class="credit-label">총 크레딧</div>
                <div class="credit-value">
                  {{ formatCurrency(key.total_credits, 2) }}
                </div>
              </div>
            </div>

            <!-- 크레딧 사용 현황 -->
            <div class="credit-usage">
              <div class="usage-label">크레딧 사용률</div>
              <el-progress 
                :percentage="getCreditUsagePercentage(key)" 
                :color="getProgressColor(getCreditUsagePercentage(key))"
                :stroke-width="6"
                :show-text="false"
              />
              <div class="usage-text">
                {{ safeToFixed(getCreditUsagePercentage(key), 1) }}% 사용 
                ({{ formatCurrency((key.total_credits || 0) - (key.remaining_credits || 0), 2) }} 사용됨)
              </div>
            </div>

            <!-- 사용 통계 -->
            <div class="usage-stats">
              <div class="usage-item">
                <span class="usage-number">{{ formatNumber(key.total_requests || 0) }}</span>
                <span class="usage-label">총 요청</span>
              </div>
              <div class="usage-item">
                <span class="usage-number">{{ formatNumber(key.total_tokens || 0) }}</span>
                <span class="usage-label">총 토큰</span>
              </div>
              <div class="usage-item">
                <span class="usage-number">{{ formatCurrency(key.total_cost, 4) }}</span>
                <span class="usage-label">총 비용</span>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 환경 변수 상태 -->
    <el-card class="env-status-card">
      <template #header>
        <div class="card-header">
          <span>환경 변수 상태</span>
        </div>
      </template>

      <div v-if="envStatus" class="env-status">
        <div v-for="(status, key) in envStatus" :key="key" class="env-item">
          <span class="env-name">{{ key }}:</span>
          <el-tag :type="status ? 'success' : 'info'" size="small">
            {{ status ? '설정됨' : '미설정' }}
          </el-tag>
        </div>
      </div>
    </el-card>

    <!-- 시스템 전체 통계 -->
    <el-card class="system-stats-card">
      <template #header>
        <div class="card-header">
          <span>시스템 통계</span>
        </div>
      </template>

      <div v-if="systemStats" class="system-stats">
        <div class="stats-row">
          <div class="stat-box">
            <div class="stat-icon">🔑</div>
            <div class="stat-content">
              <div class="stat-number">{{ systemStats.api_keys.active }} / {{ systemStats.api_keys.total }}</div>
              <div class="stat-desc">활성 API 키</div>
            </div>
          </div>
          <div class="stat-box">
            <div class="stat-icon">🤖</div>
            <div class="stat-content">
              <div class="stat-number">{{ systemStats.ai_agents.active }} / {{ systemStats.ai_agents.total }}</div>
              <div class="stat-desc">활성 AI 에이전트</div>
            </div>
          </div>
          <div class="stat-box">
            <div class="stat-icon">📊</div>
            <div class="stat-content">
              <div class="stat-number">{{ systemStats.usage_summary.week.requests }}</div>
              <div class="stat-desc">주간 요청 수</div>
            </div>
          </div>
          <div class="stat-box">
            <div class="stat-icon">💰</div>
            <div class="stat-content">
              <div class="stat-number">{{ formatCurrency(systemStats.usage_summary.week.cost, 4) }}</div>
              <div class="stat-desc">주간 비용</div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- API 키 추가/편집 다이얼로그 -->
    <el-dialog
      v-model="showAddDialog"
      :title="editingKey ? 'API 키 편집' : 'API 키 추가'"
      width="600px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="keyForm"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="키 이름" prop="name">
          <el-input 
            v-model="keyForm.name" 
            placeholder="예: Claude Production API"
          />
        </el-form-item>

        <el-form-item label="프로바이더" prop="provider">
          <el-select 
            v-model="keyForm.provider" 
            placeholder="API 프로바이더 선택 또는 직접 입력"
            style="width: 100%"
            filterable
            allow-create
            default-first-option
          >
            <el-option label="Anthropic (Claude)" value="anthropic" />
            <el-option label="OpenAI (GPT)" value="openai" />
            <el-option label="Google AI" value="google" />
            <el-option label="기타 (직접 입력)" value="custom" />
          </el-select>
        </el-form-item>

        <el-form-item label="API 키" prop="api_key">
          <div class="api-key-input-group">
            <el-input 
              v-model="keyForm.api_key" 
              type="password"
              show-password
              :placeholder="getApiKeyPlaceholder(keyForm.provider)"
              @blur="validateApiKey"
            />
            <el-button 
              type="primary" 
              :loading="validatingKey"
              @click="validateApiKey"
              :disabled="!keyForm.api_key"
            >
              {{ validatingKey ? '검증중...' : '키 검증' }}
            </el-button>
          </div>
          <div v-if="keyValidation.message" :class="['validation-message', keyValidation.type]">
            <el-icon v-if="keyValidation.type === 'success'"><CircleCheckFilled /></el-icon>
            <el-icon v-if="keyValidation.type === 'error'"><CircleCloseFilled /></el-icon>
            {{ keyValidation.message }}
          </div>
        </el-form-item>

        <!-- API 키 검증 결과 표시 -->
        <el-form-item v-if="keyValidation.data" label="API 검증 정보">
          <div class="api-validation-info">
            <!-- 기본 크레딧 정보 -->
            <div class="validation-section">
              <h4>크레딧 정보</h4>
              <div class="credit-validation-info">
                <div class="credit-item">
                  <span class="credit-label">플랜:</span>
                  <el-tag type="primary" size="small">{{ keyValidation.data.plan || 'Unknown' }}</el-tag>
                </div>
                <div class="credit-item">
                  <span class="credit-label">총 크레딧:</span>
                  <span class="credit-amount">{{ formatCurrency(keyValidation.data.total_credits, 2) }}</span>
                </div>
                <div class="credit-item">
                  <span class="credit-label">남은 크레딧:</span>
                  <span class="credit-amount">{{ formatCurrency(keyValidation.data.remaining_credits, 2) }}</span>
                </div>
                <div class="credit-item">
                  <span class="credit-label">사용된 크레딧:</span>
                  <span class="credit-amount">{{ formatCurrency((keyValidation.data.total_credits || 0) - (keyValidation.data.remaining_credits || 0), 2) }}</span>
                </div>
              </div>
            </div>

            <!-- 현재 사용량 정보 -->
            <div v-if="keyValidation.data.current_usage" class="validation-section">
              <h4>현재 사용량</h4>
              <div class="usage-info">
                <div v-if="keyValidation.data.current_usage.total_tokens" class="usage-item">
                  <span class="usage-label">토큰 사용량:</span>
                  <span class="usage-value">{{ formatNumber(keyValidation.data.current_usage.total_tokens) }}</span>
                </div>
                <div v-if="keyValidation.data.current_usage.estimated_cost" class="usage-item">
                  <span class="usage-label">추정 비용:</span>
                  <span class="usage-value">{{ formatCurrency(keyValidation.data.current_usage.estimated_cost, 4) }}</span>
                </div>
              </div>
            </div>

            <!-- 레이트 제한 정보 -->
            <div v-if="keyValidation.data.rate_limits" class="validation-section">
              <h4>레이트 제한</h4>
              <div class="rate-limits-info">
                <div class="rate-limit-item">
                  <span class="rate-label">분당 요청:</span>
                  <span class="rate-value">{{ formatNumber(keyValidation.data.rate_limits.requests_per_minute) }}</span>
                </div>
                <div class="rate-limit-item">
                  <span class="rate-label">분당 토큰:</span>
                  <span class="rate-value">{{ formatNumber(keyValidation.data.rate_limits.tokens_per_minute) }}</span>
                </div>
              </div>
            </div>

            <!-- 에이전트별 사용량 -->
            <div v-if="keyValidation.data.usage_by_agent?.length" class="validation-section">
              <h4>에이전트별 사용량</h4>
              <div class="agent-usage-list">
                <div v-for="agent in keyValidation.data.usage_by_agent" :key="agent.agent_name" class="agent-usage-item">
                  <div class="agent-name">{{ agent.agent_name }}</div>
                  <div class="agent-stats">
                    <span>요청: {{ formatNumber(agent.requests) }}</span>
                    <span>토큰: {{ formatNumber(agent.tokens) }}</span>
                    <span>비용: {{ formatCurrency(agent.cost, 2) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="설명">
          <el-input 
            v-model="keyForm.description" 
            type="textarea" 
            :rows="3"
            placeholder="이 API 키에 대한 설명 (선택사항)"
          />
        </el-form-item>

        <el-form-item label="활성 상태">
          <el-switch
            v-model="keyForm.is_active"
            active-text="활성"
            inactive-text="비활성"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showAddDialog = false">취소</el-button>
          <el-button 
            type="primary" 
            @click="saveKey"
            :loading="saving"
          >
            {{ editingKey ? '수정' : '추가' }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- API 키 상세보기 다이얼로그 -->
    <el-dialog
      v-model="showDetailsDialog"
      :title="`${currentDetailKey?.name} 상세 정보`"
      width="900px"
      @close="resetDetails"
    >
      <div v-if="currentDetailKey" class="key-details">
        <!-- 기본 정보 -->
        <el-card class="detail-section">
          <template #header>
            <h3>기본 정보</h3>
          </template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="키 이름">{{ currentDetailKey.name }}</el-descriptions-item>
            <el-descriptions-item label="프로바이더">
              <el-tag :type="getProviderTagType(currentDetailKey.provider)">
                {{ getProviderLabel(currentDetailKey.provider) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="API 키">{{ maskApiKey(currentDetailKey.api_key) }}</el-descriptions-item>
            <el-descriptions-item label="상태">
              <el-tag :type="currentDetailKey.is_active ? 'success' : 'danger'">
                {{ currentDetailKey.is_active ? '활성' : '비활성' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="총 크레딧">{{ formatCurrency(currentDetailKey.total_credits, 2) }}</el-descriptions-item>
            <el-descriptions-item label="남은 크레딧">
              <span :class="getCreditColorClass(currentDetailKey.remaining_credits, currentDetailKey.total_credits)">
                {{ formatCurrency(currentDetailKey.remaining_credits, 2) }}
              </span>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 사용량 통계 -->
        <el-card class="detail-section">
          <template #header>
            <h3>사용량 통계</h3>
          </template>
          <div class="usage-overview">
            <div class="usage-card">
              <div class="usage-icon">🔄</div>
              <div class="usage-info">
                <div class="usage-value">{{ formatNumber(currentDetailKey.total_requests || 0) }}</div>
                <div class="usage-label">총 요청 수</div>
              </div>
            </div>
            <div class="usage-card">
              <div class="usage-icon">🎯</div>
              <div class="usage-info">
                <div class="usage-value">{{ formatNumber(currentDetailKey.total_tokens || 0) }}</div>
                <div class="usage-label">총 토큰</div>
              </div>
            </div>
            <div class="usage-card">
              <div class="usage-icon">💰</div>
              <div class="usage-info">
                <div class="usage-value">{{ formatCurrency(currentDetailKey.total_cost, 4) }}</div>
                <div class="usage-label">총 비용</div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 에이전트별 사용량 -->
        <el-card class="detail-section">
          <template #header>
            <div class="section-header">
              <h3>에이전트별 사용량</h3>
              <el-button :icon="Refresh" size="small" @click="refreshAgentUsage" :loading="loadingAgentUsage">
                새로고침
              </el-button>
            </div>
          </template>
          <div v-if="loadingAgentUsage" class="loading-container">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>에이전트 사용량을 불러오는 중...</span>
          </div>
          <el-table v-else :data="agentUsageData" stripe>
            <el-table-column prop="agent_name" label="에이전트" width="150" />
            <el-table-column prop="task_type" label="작업 유형" width="120" />
            <el-table-column prop="requests_count" label="요청 수" width="100" align="center" />
            <el-table-column prop="tokens_used" label="토큰 사용" width="120" align="center">
              <template #default="scope">
                {{ formatNumber(scope.row.tokens_used) }}
              </template>
            </el-table-column>
            <el-table-column prop="cost" label="비용" width="100" align="center">
              <template #default="scope">
                {{ formatCurrency(scope.row.cost, 4) }}
              </template>
            </el-table-column>
            <el-table-column prop="last_used" label="마지막 사용" width="150">
              <template #default="scope">
                {{ formatDate(scope.row.last_used) }}
              </template>
            </el-table-column>
            <el-table-column prop="description" label="작업 설명" show-overflow-tooltip />
          </el-table>
        </el-card>

        <!-- 최근 사용 내역 -->
        <el-card class="detail-section">
          <template #header>
            <h3>최근 사용 내역 (최근 50개)</h3>
          </template>
          <el-table :data="recentUsageData" stripe max-height="300">
            <el-table-column prop="timestamp" label="시간" width="150">
              <template #default="scope">
                {{ formatDateTime(scope.row.timestamp) }}
              </template>
            </el-table-column>
            <el-table-column prop="agent_name" label="에이전트" width="120" />
            <el-table-column prop="task" label="작업" width="150" show-overflow-tooltip />
            <el-table-column prop="tokens" label="토큰" width="100" align="center">
              <template #default="scope">
                {{ formatNumber(scope.row.tokens) }}
              </template>
            </el-table-column>
            <el-table-column prop="cost" label="비용" width="100" align="center">
              <template #default="scope">
                {{ formatCurrency(scope.row.cost, 4) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="상태" width="80" align="center">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'" size="small">
                  {{ scope.row.status === 'success' ? '성공' : '실패' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Loading, InfoFilled, Key, Plus, Edit, Delete, View, CircleCheckFilled, CircleCloseFilled } from '@element-plus/icons-vue'
import { formatNumber, formatCurrency, safeToFixed } from '@/utils/format'

// 반응형 데이터
const loading = ref(false)
const saving = ref(false)
const apiKeys = ref<any[]>([])
const envStatus = ref<any>(null)
const systemStats = ref<any>(null)

// 다이얼로그 상태
const showAddDialog = ref(false)
const showDetailsDialog = ref(false)
const editingKey = ref<any>(null)
const currentDetailKey = ref<any>(null)
const formRef = ref()

// API 키 검증 상태
const validatingKey = ref(false)
const keyValidation = ref({
  message: '',
  type: '',
  data: null
})

// 상세보기 관련 상태
const loadingAgentUsage = ref(false)
const agentUsageData = ref<any[]>([])
const recentUsageData = ref<any[]>([])

// 폼 데이터
const keyForm = ref({
  name: '',
  provider: '',
  api_key: '',
  description: '',
  is_active: true
})

// 폼 검증 규칙
const formRules = {
  name: [
    { required: true, message: '키 이름을 입력해주세요', trigger: 'blur' }
  ],
  provider: [
    { required: true, message: '프로바이더를 선택해주세요', trigger: 'change' }
  ],
  api_key: [
    { required: true, message: 'API 키를 입력해주세요', trigger: 'blur' }
  ]
}

// API 키 목록 가져오기
const fetchApiKeys = async () => {
  try {
    loading.value = true
    const response = await fetch('/api/admin/api-keys')
    
    if (!response.ok) {
      throw new Error(`HTTP Error: ${response.status} - ${response.statusText}`)
    }
    
    const data = await response.json()
    console.log('API Keys Response:', data)
    
    if (data.success !== false) {
      // success가 false가 아닌 경우 성공으로 처리 (undefined도 허용)
      apiKeys.value = data.api_keys || []
    } else {
      console.error('API Error:', data.error)
      ElMessage.error(data.error || 'API 키 목록 조회 실패')
      apiKeys.value = []
    }
  } catch (error) {
    console.error('Failed to fetch API keys:', error)
    ElMessage.error(`API 키 목록을 가져오는데 실패했습니다: ${error.message}`)
    apiKeys.value = []
  } finally {
    loading.value = false
  }
}

// 샘플 데이터 초기화 (개발용)
const initializeSampleData = () => {
  apiKeys.value = [
    {
      id: 1,
      name: 'Claude API Key',
      provider: 'anthropic',
      api_key: 'sk-ant-api03-...',
      total_credits: 100.00,
      remaining_credits: 75.50,
      total_requests: 1250,
      total_tokens: 45000,
      total_cost: 24.50,
      is_active: true,
      description: 'Production Claude API for document processing'
    },
    {
      id: 2,
      name: 'OpenAI GPT API',
      provider: 'openai',
      api_key: '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',
      total_credits: 50.00,
      remaining_credits: 45.25,
      total_requests: 0,
      total_tokens: 0,
      total_cost: 0,
      is_active: true,
      description: 'OpenAI GPT API for additional AI capabilities'
    }
  ]
}

// 추가 시스템 통계 가져오기
const fetchSystemStats = async () => {
  try {
    const response = await fetch('http://localhost:8100/api/admin/usage-stats')
    const data = await response.json()
    
    if (data.success) {
      systemStats.value = {
        api_keys: data.api_keys,
        ai_agents: data.ai_agents,
        usage_summary: data.usage_summary
      }
    }
  } catch (error) {
    console.error('Failed to fetch system stats:', error)
  }
}

// 프로바이더 관련 함수들
const getProviderTagType = (provider: string) => {
  switch (provider.toLowerCase()) {
    case 'anthropic': return 'success'
    case 'openai': return 'primary'
    case 'google': return 'warning'
    default: return 'info'
  }
}

const getProviderLabel = (provider: string) => {
  switch (provider.toLowerCase()) {
    case 'anthropic': return 'Claude'
    case 'openai': return 'OpenAI GPT'
    case 'google': return 'Google AI'
    default: return provider
  }
}

const getApiKeyPlaceholder = (provider: string) => {
  switch (provider.toLowerCase()) {
    case 'anthropic': return 'sk-ant-api03-...'
    case 'openai': return 'sk-proj-...'
    case 'google': return 'AIza...'
    default: return 'API 키를 입력하세요'
  }
}

// API 키 검증 함수
const validateApiKey = async () => {
  if (!keyForm.value.api_key || !keyForm.value.provider) {
    ElMessage.warning('프로바이더와 API 키를 모두 입력해주세요')
    return
  }

  try {
    validatingKey.value = true
    keyValidation.value = { message: '', type: '', data: null }
    
    const response = await fetch('/api/admin/validate-api-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider: keyForm.value.provider,
        api_key: keyForm.value.api_key
      })
    })
    
    const data = await response.json()
    
    if (data.success) {
      keyValidation.value = {
        message: 'API 키가 유효합니다',
        type: 'success',
        data: {
          total_credits: data.total_credits,
          remaining_credits: data.remaining_credits,
          plan: data.plan,
          current_usage: data.current_usage,
          rate_limits: data.rate_limits,
          usage_by_agent: data.usage_by_agent,
          api_status: data.api_status,
          last_checked: data.last_checked
        }
      }
    } else {
      keyValidation.value = {
        message: data.error || 'API 키 검증에 실패했습니다',
        type: 'error',
        data: null
      }
    }
  } catch (error) {
    console.error('API key validation error:', error)
    keyValidation.value = {
      message: 'API 키 검증 중 오류가 발생했습니다',
      type: 'error',
      data: null
    }
  } finally {
    validatingKey.value = false
  }
}

// API 키 마스킹
const maskApiKey = (apiKey: string) => {
  if (!apiKey) return ''
  if (apiKey.length <= 8) return apiKey
  return apiKey.substring(0, 8) + '...' + apiKey.substring(apiKey.length - 4)
}

// 크레딧 관련 함수들
const getCreditUsagePercentage = (key: any) => {
  const total = key.total_credits || 0
  const remaining = key.remaining_credits || 0
  if (total === 0) return 0
  return Math.max(0, Math.min(100, ((total - remaining) / total) * 100))
}

const getCreditColorClass = (remaining: number, total: number) => {
  const percentage = (remaining / total) * 100
  if (percentage < 10) return 'credit-critical'
  if (percentage < 25) return 'credit-warning'
  return 'credit-normal'
}

// 사용량 백분율 계산
const getDailyUsagePercentage = (key: any) => {
  const usage = key?.daily_usage || 0
  const limit = key?.daily_limit || 1
  if (!limit) return 0
  return Math.min((usage / limit) * 100, 100)
}

const getMonthlyUsagePercentage = (key: any) => {
  const usage = key?.monthly_usage || 0
  const limit = key?.monthly_limit || 1
  if (!limit) return 0
  return Math.min((usage / limit) * 100, 100)
}

// 진행 바 색상
const getProgressColor = (percentage: number) => {
  if (percentage < 50) return '#67c23a'
  if (percentage < 80) return '#e6a23c'
  return '#f56c6c'
}

// CRUD 기능들
const saveKey = async () => {
  if (!formRef.value) return
  
  // API 키 검증이 완료되지 않은 경우 확인
  if (!keyValidation.value.data) {
    ElMessage.warning('API 키 검증을 먼저 완료해주세요')
    return
  }
  
  try {
    await formRef.value.validate()
    saving.value = true
    
    const url = editingKey.value ? `/api/admin/api-keys/${editingKey.value.id}` : '/api/admin/api-keys'
    const method = editingKey.value ? 'PUT' : 'POST'
    
    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...keyForm.value,
        total_credits: keyValidation.value.data.total_credits,
        remaining_credits: keyValidation.value.data.remaining_credits
      })
    })
    
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success(editingKey.value ? 'API 키가 수정되었습니다' : 'API 키가 추가되었습니다')
      showAddDialog.value = false
      await refreshData()
    } else {
      throw new Error(data.error || '저장 실패')
    }
  } catch (error) {
    console.error('Failed to save API key:', error)
    ElMessage.error('API 키 저장에 실패했습니다')
  } finally {
    saving.value = false
  }
}

// 상세보기 함수들
const viewKeyDetails = async (key: any) => {
  currentDetailKey.value = key
  showDetailsDialog.value = true
  await refreshAgentUsage()
  await fetchRecentUsage()
}

const refreshAgentUsage = async () => {
  if (!currentDetailKey.value) return
  
  try {
    loadingAgentUsage.value = true
    const response = await fetch(`/api/admin/api-keys/${currentDetailKey.value.id}/agent-usage`)
    const data = await response.json()
    
    if (data.success) {
      agentUsageData.value = data.agent_usage || []
    } else {
      // 샘플 데이터로 대체
      agentUsageData.value = [
        {
          agent_name: 'Document Processor',
          task_type: 'PDF 처리',
          requests_count: 45,
          tokens_used: 12500,
          cost: 8.75,
          last_used: new Date().toISOString(),
          description: 'PDF 문서에서 문제와 학습자료 추출'
        },
        {
          agent_name: 'Content Analyzer',
          task_type: '내용 분석',
          requests_count: 23,
          tokens_used: 7800,
          cost: 5.46,
          last_used: new Date(Date.now() - 86400000).toISOString(),
          description: '추출된 내용의 품질 검증 및 분류'
        },
        {
          agent_name: 'Question Generator',
          task_type: '문제 생성',
          requests_count: 31,
          tokens_used: 9200,
          cost: 6.44,
          last_used: new Date(Date.now() - 3600000).toISOString(),
          description: '학습자료 기반 추가 문제 생성'
        }
      ]
    }
  } catch (error) {
    console.error('Failed to fetch agent usage:', error)
    ElMessage.error('에이전트 사용량을 가져오는데 실패했습니다')
  } finally {
    loadingAgentUsage.value = false
  }
}

const fetchRecentUsage = async () => {
  if (!currentDetailKey.value) return
  
  try {
    const response = await fetch(`/api/admin/api-keys/${currentDetailKey.value.id}/recent-usage`)
    const data = await response.json()
    
    if (data.success) {
      recentUsageData.value = data.recent_usage || []
    } else {
      // 샘플 데이터로 대체
      recentUsageData.value = [
        {
          timestamp: new Date().toISOString(),
          agent_name: 'Document Processor',
          task: 'PDF 텍스트 추출',
          tokens: 1250,
          cost: 0.875,
          status: 'success'
        },
        {
          timestamp: new Date(Date.now() - 1800000).toISOString(),
          agent_name: 'Content Analyzer',
          task: '문제 유형 분류',
          tokens: 890,
          cost: 0.623,
          status: 'success'
        },
        {
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          agent_name: 'Question Generator',
          task: '객관식 문제 생성',
          tokens: 1456,
          cost: 1.019,
          status: 'success'
        }
      ]
    }
  } catch (error) {
    console.error('Failed to fetch recent usage:', error)
  }
}

const editKey = (key: any) => {
  editingKey.value = key
  keyForm.value = {
    name: key.name,
    provider: key.provider,
    api_key: key.api_key,
    description: key.description || '',
    is_active: key.is_active
  }
  // 기존 키의 경우 검증 데이터 설정
  keyValidation.value = {
    message: '기존 API 키입니다',
    type: 'success',
    data: {
      total_credits: key.total_credits,
      remaining_credits: key.remaining_credits
    }
  }
  showAddDialog.value = true
}

const deleteKey = async (key: any) => {
  try {
    await ElMessageBox.confirm(
      `API 키 "${key.name}"을 정말 삭제하시겠습니까?`,
      '삭제 확인',
      {
        confirmButtonText: '삭제',
        cancelButtonText: '취소',
        type: 'warning',
      }
    )
    
    const response = await fetch(`/api/admin/api-keys/${key.id}`, {
      method: 'DELETE'
    })
    
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success('API 키가 삭제되었습니다')
      await refreshData()
    } else {
      throw new Error(data.error || '삭제 실패')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete API key:', error)
      ElMessage.error('API 키 삭제에 실패했습니다')
    }
  }
}

const resetForm = () => {
  editingKey.value = null
  keyForm.value = {
    name: '',
    provider: '',
    api_key: '',
    description: '',
    is_active: true
  }
  keyValidation.value = { message: '', type: '', data: null }
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

const resetDetails = () => {
  currentDetailKey.value = null
  agentUsageData.value = []
  recentUsageData.value = []
}

// 날짜 형식 함수들
const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleDateString('ko-KR')
}

const formatDateTime = (dateString: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('ko-KR')
}

// 데이터 새로고침
const refreshData = async () => {
  await fetchApiKeys()
  await fetchSystemStats()
}

// 컴포넌트 마운트 시 데이터 로드
onMounted(() => {
  refreshData()
})
</script>

<style scoped>
.api-keys-view {
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
  margin-bottom: 24px;
}

.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 0;
  padding: 32px 24px;
  color: white;
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

.action-buttons {
  display: flex;
  gap: 12px;
  align-items: center;
}

.action-buttons .el-button {
  border-radius: 8px;
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* API 키 컨테이너 */
.api-keys-container {
  margin: 0 16px 16px 16px;
}

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
  color: #606266;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.loading-container .el-icon {
  margin-right: 8px;
  font-size: 18px;
}

.empty-container {
  padding: 60px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  text-align: center;
}

.api-keys-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}

/* API 키 카드 스타일 */
.api-key-card {
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  transition: all 0.3s ease;
}

.api-key-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
}

.api-key-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.api-key-card :deep(.el-card__body) {
  padding: 24px;
}

.key-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.key-info {
  flex: 1;
}

.key-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.key-tags {
  display: flex;
  gap: 8px;
}

.key-actions {
  display: flex;
  gap: 8px;
}

.key-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* API 키 프리뷰 */
.key-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #f1f5f9;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.key-label {
  font-size: 14px;
  font-weight: 500;
  color: #64748b;
}

.key-text {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #1e293b;
  font-weight: 500;
}

/* 크레딧 정보 */
.credit-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.credit-item {
  text-align: center;
  padding: 16px 12px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.credit-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.credit-value {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
}

.credit-normal {
  color: #059669;
}

.credit-warning {
  color: #d97706;
}

.credit-critical {
  color: #dc2626;
}

/* 크레딧 사용 현황 */
.credit-usage {
  padding: 16px;
  background: #fefefe;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.usage-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.usage-text {
  font-size: 12px;
  color: #6b7280;
  text-align: center;
  margin-top: 8px;
}

/* 사용 통계 */
.usage-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.usage-item {
  text-align: center;
  padding: 12px 8px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.usage-number {
  display: block;
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 2px;
}

.usage-label {
  font-size: 11px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* API 키 입력 그룹 */
.api-key-input-group {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.api-key-input-group .el-input {
  flex: 1;
}

.validation-message {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 14px;
}

.validation-message.success {
  background: #f0f9ff;
  color: #059669;
  border: 1px solid #a7f3d0;
}

.validation-message.error {
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.credit-validation-info {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  padding: 16px;
  background: #f0f9ff;
  border-radius: 8px;
  border: 1px solid #bae6fd;
}

.credit-validation-info .credit-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.credit-validation-info .credit-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.credit-validation-info .credit-amount {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

/* API 검증 정보 스타일 */
.api-validation-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.validation-section {
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.validation-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
}

.usage-info,
.rate-limits-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.usage-item,
.rate-limit-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
}

.usage-label,
.rate-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.usage-value,
.rate-value {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
}

.agent-usage-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.agent-usage-item {
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.agent-name {
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 6px;
}

.agent-stats {
  display: flex;
  gap: 12px;
  font-size: 11px;
  color: #64748b;
}

.agent-stats span {
  padding: 2px 6px;
  background: #f1f5f9;
  border-radius: 4px;
}

/* 상세보기 다이얼로그 */
.key-details {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-section {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.detail-section :deep(.el-card__header) {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.detail-section h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.usage-overview {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  padding: 20px 0;
}

.usage-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;
}

.usage-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.usage-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.usage-info {
  flex: 1;
}

.usage-value {
  font-size: 24px;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
  margin-bottom: 4px;
}

/* 환경 변수 및 시스템 통계 카드 */
.env-status-card, .system-stats-card {
  margin: 0 16px 16px 16px;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.env-status-card :deep(.el-card__header),
.system-stats-card :deep(.el-card__header) {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-bottom: 1px solid #e2e8f0;
  padding: 20px 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #1e293b;
}

.current-key-item {
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.key-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.key-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.key-name {
  margin: 0;
  color: #303133;
  font-size: 18px;
}

.key-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f5f7fa;
  padding: 8px 12px;
  border-radius: 6px;
  font-family: 'Courier New', monospace;
}

.key-text {
  color: #409eff;
  font-weight: 500;
}

.key-stats {
  margin-top: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
}

.stat-item {
  background: white;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.stat-label {
  display: block;
  color: #606266;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-value {
  display: block;
  font-weight: 500;
  margin-bottom: 8px;
  color: #303133;
}

.recent-usage h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.usage-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.usage-item {
  text-align: center;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.usage-number {
  display: block;
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 4px;
}

.usage-label {
  font-size: 12px;
  color: #909399;
}

.env-status {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.env-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.env-name {
  font-weight: 500;
  color: #303133;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-box {
  display: flex;
  align-items: center;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 10px;
  border: 1px solid #e4e7ed;
}

.stat-icon {
  font-size: 24px;
  margin-right: 12px;
}

.stat-content {
  flex: 1;
}

.stat-number {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.stat-desc {
  font-size: 12px;
  color: #909399;
}
</style>