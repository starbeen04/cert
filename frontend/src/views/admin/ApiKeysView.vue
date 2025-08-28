<template>
  <div class="api-keys-view">
    <div class="page-header">
      <h1 class="page-title">API 키 관리</h1>
      <p class="page-description">실제 사용 중인 API 키와 사용량 정보를 확인하세요</p>
      <div class="header-actions">
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          새로고침
        </el-button>
        <el-button type="primary" @click="syncExternalApis" :loading="syncLoading">
          <el-icon><Connection /></el-icon>
          외부 API 동기화
        </el-button>
      </div>
    </div>

    <!-- API 키 목록 -->
    <el-card class="api-keys-card">
      <template #header>
        <div class="card-header">
          <span>현재 API 키 정보</span>
        </div>
      </template>

      <div v-if="loading" class="loading-container">
        <el-icon class="is-loading"><Loading /></el-icon>
        <span>API 키 정보를 가져오는 중...</span>
      </div>

      <div v-else-if="apiKeys.length === 0" class="empty-container">
        <el-empty description="등록된 API 키가 없습니다" />
      </div>

      <div v-else class="api-keys-list">
        <div v-for="key in apiKeys" :key="key.id" class="api-key-item">
          <div class="api-key-header">
            <div class="api-key-info">
              <h3 class="api-key-name">{{ key.name }}</h3>
              <el-tag :type="key.provider === 'anthropic' ? 'success' : 'primary'" size="small">
                {{ key.provider }}
              </el-tag>
              <el-tag :type="key.is_active ? 'success' : 'danger'" size="small">
                {{ key.is_active ? '활성' : '비활성' }}
              </el-tag>
            </div>
          </div>

          <div class="api-key-details">
            <!-- 외부 API 사용량 정보 -->
            <div class="external-usage" v-if="key.external_usage">
              <h4>실제 사용량 (외부 API 기준)</h4>
              <div class="external-stats">
                <div class="external-stat-item">
                  <el-icon class="stat-icon"><TrendCharts /></el-icon>
                  <div class="stat-content">
                    <span class="stat-label">오늘 사용량:</span>
                    <span class="stat-value">${{ formatCurrency(key.external_usage.today_cost) }}</span>
                    <span class="stat-tokens">({{ formatNumber(key.external_usage.today_tokens) }} 토큰)</span>
                  </div>
                </div>
                <div class="external-stat-item">
                  <el-icon class="stat-icon"><InfoFilled /></el-icon>
                  <div class="stat-content">
                    <span class="stat-label">이번 달 사용량:</span>
                    <span class="stat-value">${{ formatCurrency(key.external_usage.month_cost) }}</span>
                    <span class="stat-tokens">({{ formatNumber(key.external_usage.month_tokens) }} 토큰)</span>
                  </div>
                </div>
                <div class="external-stat-item sync-status">
                  <el-icon class="stat-icon" :class="key.external_usage.sync_status">
                    <component :is="getSyncStatusIcon(key.external_usage.sync_status)" />
                  </el-icon>
                  <div class="stat-content">
                    <span class="stat-label">동기화 상태:</span>
                    <span class="stat-value" :class="key.external_usage.sync_status">
                      {{ getSyncStatusText(key.external_usage.sync_status) }}
                    </span>
                    <span class="sync-time" v-if="key.external_usage.last_sync">
                      ({{ formatDateTime(key.external_usage.last_sync) }})
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="usage-stats">
              <div class="stat-item">
                <span class="stat-label">일일 사용량</span>
                <span class="stat-value">{{ key.current_daily_usage }} / {{ key.daily_limit }}</span>
                <el-progress 
                  :percentage="getDailyUsagePercentage(key)" 
                  :color="getProgressColor(getDailyUsagePercentage(key))"
                  :stroke-width="6"
                />
              </div>
              
              <div class="stat-item">
                <span class="stat-label">월간 사용량</span>
                <span class="stat-value">{{ key.current_monthly_usage }} / {{ key.monthly_limit }}</span>
                <el-progress 
                  :percentage="getMonthlyUsagePercentage(key)" 
                  :color="getProgressColor(getMonthlyUsagePercentage(key))"
                  :stroke-width="6"
                />
              </div>
            </div>

            <div class="week-stats" v-if="key.week_stats">
              <h4>최근 7일 사용량</h4>
              <div class="stats-grid">
                <div class="stat-box">
                  <div class="stat-number">{{ key.week_stats.requests }}</div>
                  <div class="stat-desc">요청 수</div>
                </div>
                <div class="stat-box">
                  <div class="stat-number">${{ key.week_stats.cost.toFixed(4) }}</div>
                  <div class="stat-desc">비용</div>
                </div>
                <div class="stat-box">
                  <div class="stat-number">{{ formatNumber(key.week_stats.tokens) }}</div>
                  <div class="stat-desc">토큰</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 외부 API 동기화 상태 -->
    <el-card class="sync-status-card" v-if="lastSyncTime">
      <template #header>
        <div class="card-header">
          <span>외부 API 동기화 상태</span>
          <el-tag type="info" size="small">마지막 동기화: {{ formatDateTime(lastSyncTime) }}</el-tag>
        </div>
      </template>
      <div class="sync-summary">
        <div class="sync-item">
          <el-icon class="sync-icon success"><CircleCheck /></el-icon>
          <span>OpenAI API 연동 완료</span>
        </div>
        <div class="sync-item">
          <el-icon class="sync-icon success"><CircleCheck /></el-icon>
          <span>Anthropic API 연동 완료</span>
        </div>
        <div class="sync-item">
          <el-icon class="sync-icon warning"><WarningFilled /></el-icon>
          <span>일부 API 키의 사용량 정보 업데이트 지연</span>
        </div>
      </div>
    </el-card>

    <!-- 실시간 시스템 상태 -->
    <el-card class="system-status-card">
      <template #header>
        <div class="card-header">
          <span>시스템 상태</span>
        </div>
      </template>

      <div v-if="systemStatus" class="system-status">
        <div class="status-item">
          <span class="status-label">총 API 키:</span>
          <span class="status-value">{{ systemStatus.api_keys.total }}</span>
        </div>
        <div class="status-item">
          <span class="status-label">활성 API 키:</span>
          <span class="status-value">{{ systemStatus.api_keys.active }}</span>
        </div>
        <div class="status-item">
          <span class="status-label">총 AI 에이전트:</span>
          <span class="status-value">{{ systemStatus.ai_agents.total }}</span>
        </div>
        <div class="status-item">
          <span class="status-label">활성 AI 에이전트:</span>
          <span class="status-value">{{ systemStatus.ai_agents.active }}</span>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Loading, Connection, TrendCharts, InfoFilled, WarningFilled, CircleCheck } from '@element-plus/icons-vue'
import { formatNumber, formatCurrency, safeToFixed } from '@/utils/format'

// 반응형 데이터
const loading = ref(false)
const syncLoading = ref(false)
const apiKeys = ref<any[]>([])
const systemStatus = ref<any>(null)
const externalUsageData = ref<any[]>([])
const lastSyncTime = ref<string | null>(null)

// API 키 데이터 가져오기
const fetchApiKeys = async () => {
  try {
    loading.value = true
    const response = await fetch('http://localhost:8100/api/admin/usage-stats')
    const data = await response.json()
    
    if (data.success) {
      apiKeys.value = data.api_keys.details
      systemStatus.value = {
        api_keys: data.api_keys,
        ai_agents: data.ai_agents,
        usage_summary: data.usage_summary
      }
      externalUsageData.value = data.external_usage || []
      lastSyncTime.value = data.last_sync_time || null
      ElMessage.success('API 키 정보를 성공적으로 가져왔습니다')
    } else {
      throw new Error(data.error || 'API 호출 실패')
    }
  } catch (error) {
    console.error('Failed to fetch API keys:', error)
    ElMessage.error('API 키 정보를 가져오는데 실패했습니다')
  } finally {
    loading.value = false
  }
}

// 사용량 백분율 계산
const getDailyUsagePercentage = (key: any) => {
  if (!key.daily_limit) return 0
  return Math.min((key.current_daily_usage / key.daily_limit) * 100, 100)
}

const getMonthlyUsagePercentage = (key: any) => {
  if (!key.monthly_limit) return 0
  return Math.min((key.current_monthly_usage / key.monthly_limit) * 100, 100)
}

// 진행 바 색상
const getProgressColor = (percentage: number) => {
  if (percentage < 50) return '#67c23a'
  if (percentage < 80) return '#e6a23c'
  return '#f56c6c'
}

// 외부 API 동기화
const syncExternalApis = async () => {
  try {
    syncLoading.value = true
    const response = await fetch('http://localhost:8100/api/monitoring/usage-api/sync', {
      method: 'POST'
    })
    const data = await response.json()
    
    if (data.success) {
      lastSyncTime.value = new Date().toISOString()
      ElMessage.success('외부 API 동기화가 완료되었습니다')
      // 동기화 후 데이터 새로고침
      await fetchApiKeys()
    } else {
      throw new Error(data.error || '동기화 실패')
    }
  } catch (error) {
    console.error('Failed to sync external APIs:', error)
    ElMessage.error('외부 API 동기화에 실패했습니다')
  } finally {
    syncLoading.value = false
  }
}

// 동기화 상태 아이콘 반환
const getSyncStatusIcon = (status: string) => {
  switch (status) {
    case 'success': return 'CircleCheck'
    case 'warning': return 'WarningFilled'
    case 'error': return 'CircleClose'
    default: return 'InfoFilled'
  }
}

// 동기화 상태 텍스트 반환
const getSyncStatusText = (status: string) => {
  switch (status) {
    case 'success': return '정상'
    case 'warning': return '주의'
    case 'error': return '오류'
    default: return '알 수 없음'
  }
}

// 날짜 시간 포맷팅
const formatDateTime = (dateString: string) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('ko-KR')
}

// 데이터 새로고침
const refreshData = () => {
  fetchApiKeys()
}

// 컴포넌트 마운트 시 데이터 로드
onMounted(() => {
  fetchApiKeys()
})
</script>

<style scoped>
.api-keys-view {
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

.api-keys-card, .system-status-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.loading-container {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #606266;
}

.loading-container .el-icon {
  margin-right: 8px;
  font-size: 18px;
}

.empty-container {
  padding: 40px;
}

.api-key-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  background: #fafafa;
}

.api-key-header {
  margin-bottom: 16px;
}

.api-key-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.api-key-name {
  margin: 0;
  color: #303133;
}

.usage-stats {
  margin-bottom: 20px;
}

.stat-item {
  margin-bottom: 12px;
}

.stat-label {
  display: inline-block;
  width: 120px;
  color: #606266;
}

.stat-value {
  margin-left: 12px;
  font-weight: 500;
}

.week-stats h4 {
  margin: 0 0 12px 0;
  color: #303133;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-box {
  text-align: center;
  padding: 16px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.stat-number {
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 4px;
}

.stat-desc {
  font-size: 12px;
  color: #909399;
}

.system-status {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.status-label {
  color: #606266;
}

.status-value {
  font-weight: 500;
  color: #303133;
}

/* 헤더 액션 스타일 */
.header-actions {
  display: flex;
  gap: 12px;
}

/* 외부 사용량 스타일 */
.external-usage {
  margin-bottom: 20px;
  padding: 16px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.external-usage h4 {
  margin: 0 0 16px 0;
  color: #1e293b;
  font-size: 14px;
  font-weight: 600;
}

.external-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.external-stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}

.external-stat-item.sync-status {
  border-left: 4px solid #3b82f6;
}

.external-stat-item .stat-icon {
  font-size: 16px;
  color: #64748b;
}

.external-stat-item .stat-content {
  flex: 1;
}

.external-stat-item .stat-label {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
}

.external-stat-item .stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-right: 8px;
}

.external-stat-item .stat-tokens {
  font-size: 12px;
  color: #6b7280;
}

.external-stat-item .sync-time {
  font-size: 11px;
  color: #9ca3af;
  margin-left: 8px;
}

.external-stat-item .stat-value.success {
  color: #059669;
}

.external-stat-item .stat-value.warning {
  color: #d97706;
}

.external-stat-item .stat-value.error {
  color: #dc2626;
}

/* 동기화 상태 카드 */
.sync-status-card {
  margin-bottom: 24px;
}

.sync-summary {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sync-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #f8fafc;
  border-radius: 6px;
  font-size: 14px;
}

.sync-icon {
  font-size: 16px;
}

.sync-icon.success {
  color: #059669;
}

.sync-icon.warning {
  color: #d97706;
}

.sync-icon.error {
  color: #dc2626;
}
</style>