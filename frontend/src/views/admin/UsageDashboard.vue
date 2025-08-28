<template>
  <div class="usage-dashboard">
    <!-- 페이지 헤더 -->
    <div class="page-header">
      <h1 class="page-title">실시간 사용량 대시보드</h1>
      <p class="page-description">API 사용량과 비용을 실시간으로 모니터링하고 최적화 제안을 확인하세요</p>
      <div class="header-actions">
        <el-button @click="refreshDashboard" :loading="loading">
          <el-icon><Refresh /></el-icon>
          새로고침
        </el-button>
        <el-switch
          v-model="autoRefresh"
          active-text="자동 새로고침"
          @change="toggleAutoRefresh"
        />
      </div>
    </div>

    <!-- 실시간 통계 카드 -->
    <div class="stats-cards">
      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon requests">
            <el-icon><DataBoard /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatNumber(realtimeStats.total_requests) }}</div>
            <div class="stat-label">총 요청 수</div>
            <div class="stat-change" :class="getChangeClass(realtimeStats.requests_change)">
              {{ formatChange(realtimeStats.requests_change) }}
            </div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon cost">
            <el-icon><Money /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">${{ formatCurrency(realtimeStats.total_cost) }}</div>
            <div class="stat-label">총 비용</div>
            <div class="stat-change" :class="getChangeClass(realtimeStats.cost_change)">
              {{ formatChange(realtimeStats.cost_change) }}
            </div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon tokens">
            <el-icon><Coin /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ formatNumber(realtimeStats.total_tokens) }}</div>
            <div class="stat-label">총 토큰 수</div>
            <div class="stat-change" :class="getChangeClass(realtimeStats.tokens_change)">
              {{ formatChange(realtimeStats.tokens_change) }}
            </div>
          </div>
        </div>
      </el-card>

      <el-card class="stat-card">
        <div class="stat-content">
          <div class="stat-icon agents">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ realtimeStats.active_agents }}</div>
            <div class="stat-label">활성 에이전트</div>
            <div class="stat-change" :class="getChangeClass(realtimeStats.agents_change)">
              {{ formatChange(realtimeStats.agents_change) }}
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 차트 섹션 -->
    <div class="charts-section">
      <!-- 실시간 사용량 추이 -->
      <el-card class="chart-card">
        <template #header>
          <div class="card-header">
            <span>실시간 사용량 추이 (최근 24시간)</span>
            <el-radio-group v-model="chartType" size="small">
              <el-radio value="requests">요청</el-radio>
              <el-radio value="cost">비용</el-radio>
              <el-radio value="tokens">토큰</el-radio>
            </el-radio-group>
          </div>
        </template>
        <div id="usage-trend-chart" style="height: 300px;"></div>
      </el-card>

      <!-- 에이전트별 사용량 -->
      <el-card class="chart-card">
        <template #header>
          <span>에이전트별 사용량 분석</span>
        </template>
        <div id="agent-usage-chart" style="height: 300px;"></div>
      </el-card>

      <!-- API별 사용량 -->
      <el-card class="chart-card">
        <template #header>
          <span>API별 사용량 분석</span>
        </template>
        <div id="api-usage-chart" style="height: 300px;"></div>
      </el-card>
    </div>

    <!-- 최적화 제안 -->
    <el-card class="optimization-card" v-if="optimizationSuggestions.length > 0">
      <template #header>
        <div class="card-header">
          <span>비용 최적화 제안</span>
          <el-tag type="warning">{{ optimizationSuggestions.length }}개 제안</el-tag>
        </div>
      </template>
      <div class="suggestions-list">
        <div 
          v-for="(suggestion, index) in optimizationSuggestions" 
          :key="index" 
          class="suggestion-item"
          :class="suggestion.priority"
        >
          <div class="suggestion-header">
            <el-icon :class="getSuggestionIcon(suggestion.priority)">
              <component :is="getSuggestionIconComponent(suggestion.priority)" />
            </el-icon>
            <h4>{{ suggestion.title }}</h4>
            <el-tag :type="getSuggestionTagType(suggestion.priority)" size="small">
              {{ suggestion.priority === 'high' ? '높음' : suggestion.priority === 'medium' ? '보통' : '낮음' }}
            </el-tag>
          </div>
          <p class="suggestion-description">{{ suggestion.description }}</p>
          <div class="suggestion-impact">
            <span>예상 절약: <strong>${{ formatCurrency(suggestion.potential_savings) }}/월</strong></span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 알림 및 경고 -->
    <el-card class="alerts-card" v-if="alerts.length > 0">
      <template #header>
        <span>실시간 알림</span>
      </template>
      <div class="alerts-list">
        <el-alert
          v-for="(alert, index) in alerts"
          :key="index"
          :title="alert.title"
          :type="alert.type"
          :description="alert.description"
          show-icon
          :closable="false"
          class="alert-item"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Refresh, DataBoard, Money, Coin, User, 
  Warning, InfoFilled, SuccessFilled 
} from '@element-plus/icons-vue'
import { formatNumber, formatCurrency } from '@/utils/format'
import * as echarts from 'echarts'

// 반응형 데이터
const loading = ref(false)
const autoRefresh = ref(true)
const chartType = ref('requests')
const realtimeStats = ref({
  total_requests: 0,
  total_cost: 0,
  total_tokens: 0,
  active_agents: 0,
  requests_change: 0,
  cost_change: 0,
  tokens_change: 0,
  agents_change: 0
})
const optimizationSuggestions = ref<any[]>([])
const alerts = ref<any[]>([])
const chartData = ref({
  usage_trend: [],
  agent_usage: [],
  api_usage: []
})

let refreshInterval: NodeJS.Timeout | null = null
let usageTrendChart: echarts.ECharts | null = null
let agentUsageChart: echarts.ECharts | null = null
let apiUsageChart: echarts.ECharts | null = null

// 실시간 데이터 가져오기
const fetchRealtimeData = async () => {
  try {
    loading.value = true
    const response = await fetch('http://localhost:8100/api/admin/real-time-usage')
    const data = await response.json()
    
    if (data.success) {
      realtimeStats.value = data.stats
      optimizationSuggestions.value = data.optimization_suggestions || []
      alerts.value = data.alerts || []
      chartData.value = data.charts || { usage_trend: [], agent_usage: [], api_usage: [] }
      
      // 차트 업데이트
      updateCharts()
    } else {
      throw new Error(data.error || 'API 호출 실패')
    }
  } catch (error) {
    console.error('Failed to fetch realtime data:', error)
    ElMessage.error('실시간 데이터를 가져오는데 실패했습니다')
  } finally {
    loading.value = false
  }
}

// 차트 업데이트
const updateCharts = () => {
  updateUsageTrendChart()
  updateAgentUsageChart()
  updateApiUsageChart()
}

// 사용량 추이 차트 업데이트
const updateUsageTrendChart = () => {
  if (!usageTrendChart || !chartData.value.usage_trend) return

  const data = chartData.value.usage_trend
  const option = {
    title: {
      text: '실시간 사용량 추이',
      textStyle: { fontSize: 14, color: '#303133' }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      textStyle: { color: '#303133' }
    },
    xAxis: {
      type: 'category',
      data: data.map((item: any) => item.time),
      axisLabel: { color: '#606266' }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#606266' }
    },
    series: [{
      data: data.map((item: any) => item[chartType.value]),
      type: 'line',
      smooth: true,
      itemStyle: { color: '#409EFF' },
      areaStyle: { color: 'rgba(64, 158, 255, 0.1)' }
    }],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    }
  }

  usageTrendChart.setOption(option)
}

// 에이전트 사용량 차트 업데이트
const updateAgentUsageChart = () => {
  if (!agentUsageChart || !chartData.value.agent_usage) return

  const data = chartData.value.agent_usage
  const option = {
    title: {
      text: '에이전트별 사용량',
      textStyle: { fontSize: 14, color: '#303133' }
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      textStyle: { color: '#303133' }
    },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      data: data.map((item: any) => ({
        value: item.usage,
        name: item.name
      })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }]
  }

  agentUsageChart.setOption(option)
}

// API 사용량 차트 업데이트
const updateApiUsageChart = () => {
  if (!apiUsageChart || !chartData.value.api_usage) return

  const data = chartData.value.api_usage
  const option = {
    title: {
      text: 'API별 사용량',
      textStyle: { fontSize: 14, color: '#303133' }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      textStyle: { color: '#303133' }
    },
    xAxis: {
      type: 'category',
      data: data.map((item: any) => item.api),
      axisLabel: { color: '#606266', rotate: 45 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#606266' }
    },
    series: [{
      data: data.map((item: any) => item.usage),
      type: 'bar',
      itemStyle: { color: '#67C23A' }
    }],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '20%',
      containLabel: true
    }
  }

  apiUsageChart.setOption(option)
}

// 차트 초기화
const initCharts = () => {
  usageTrendChart = echarts.init(document.getElementById('usage-trend-chart'))
  agentUsageChart = echarts.init(document.getElementById('agent-usage-chart'))
  apiUsageChart = echarts.init(document.getElementById('api-usage-chart'))

  // 윈도우 리사이즈 이벤트 핸들러
  window.addEventListener('resize', () => {
    usageTrendChart?.resize()
    agentUsageChart?.resize()
    apiUsageChart?.resize()
  })
}

// 유틸리티 함수들
const formatChange = (value: number) => {
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(1)}%`
}

const getChangeClass = (value: number) => {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return 'neutral'
}

const getSuggestionIcon = (priority: string) => {
  return `suggestion-icon ${priority}`
}

const getSuggestionIconComponent = (priority: string) => {
  switch (priority) {
    case 'high': return Warning
    case 'medium': return InfoFilled
    default: return SuccessFilled
  }
}

const getSuggestionTagType = (priority: string) => {
  switch (priority) {
    case 'high': return 'danger'
    case 'medium': return 'warning'
    default: return 'info'
  }
}

// 자동 새로고침 토글
const toggleAutoRefresh = () => {
  if (autoRefresh.value) {
    refreshInterval = setInterval(fetchRealtimeData, 30000) // 30초마다 새로고침
  } else {
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  }
}

// 대시보드 새로고침
const refreshDashboard = () => {
  fetchRealtimeData()
}

// 차트 타입 변경 시 차트 업데이트
watch(chartType, () => {
  updateUsageTrendChart()
})

// 컴포넌트 마운트
onMounted(() => {
  fetchRealtimeData()
  
  // DOM이 렌더링된 후 차트 초기화
  setTimeout(() => {
    initCharts()
    updateCharts()
  }, 100)

  // 자동 새로고침 시작
  if (autoRefresh.value) {
    toggleAutoRefresh()
  }
})

// 컴포넌트 언마운트
onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
  
  // 차트 정리
  usageTrendChart?.dispose()
  agentUsageChart?.dispose()
  apiUsageChart?.dispose()
})
</script>

<style scoped>
.usage-dashboard {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.page-title {
  margin: 0;
  color: #303133;
  font-size: 28px;
}

.page-description {
  margin: 8px 0 0 0;
  color: #606266;
  font-size: 14px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 통계 카드 스타일 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.requests { background: linear-gradient(45deg, #409EFF, #79bbff); }
.stat-icon.cost { background: linear-gradient(45deg, #E6A23C, #f1c40f); }
.stat-icon.tokens { background: linear-gradient(45deg, #67C23A, #95d475); }
.stat-icon.agents { background: linear-gradient(45deg, #F56C6C, #f89898); }

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 4px;
}

.stat-change {
  font-size: 12px;
  font-weight: 500;
}

.stat-change.positive { color: #67C23A; }
.stat-change.negative { color: #F56C6C; }
.stat-change.neutral { color: #909399; }

/* 차트 섹션 스타일 */
.charts-section {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  margin-bottom: 24px;
}

.chart-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 최적화 제안 스타일 */
.optimization-card {
  margin-bottom: 24px;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.suggestion-item {
  padding: 16px;
  border-radius: 8px;
  border-left: 4px solid;
}

.suggestion-item.high {
  background: #fef0f0;
  border-color: #F56C6C;
}

.suggestion-item.medium {
  background: #fdf6ec;
  border-color: #E6A23C;
}

.suggestion-item.low {
  background: #f0f9ff;
  border-color: #409EFF;
}

.suggestion-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.suggestion-header h4 {
  margin: 0;
  color: #303133;
  font-size: 16px;
  flex: 1;
}

.suggestion-description {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.suggestion-impact {
  font-size: 14px;
  color: #303133;
}

.suggestion-impact strong {
  color: #67C23A;
}

/* 알림 스타일 */
.alerts-card {
  margin-bottom: 24px;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.alert-item {
  margin-bottom: 0;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: space-between;
  }
}
</style>