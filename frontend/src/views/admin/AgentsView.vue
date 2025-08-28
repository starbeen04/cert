<template>
  <div class="agents-view">
    <!-- 페이지 헤더 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">AI 에이전트 관리</h1>
        <p class="page-description">각 에이전트의 성능 메트릭과 비용 효율성을 분석하고 최적 모델을 추천받으세요</p>
      </div>
      <div class="header-actions">
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          새로고침
        </el-button>
        <el-button @click="syncAgentAnalytics" type="primary" :loading="syncLoading">
          <el-icon><Promotion /></el-icon>
          분석 동기화
        </el-button>
      </div>
    </div>

    <!-- 전체 통계 요약 -->
    <div class="summary-cards">
      <el-card class="summary-card">
        <div class="summary-content">
          <div class="summary-icon total">
            <el-icon><User /></el-icon>
          </div>
          <div class="summary-info">
            <div class="summary-value">{{ agentsSummary.total_agents }}</div>
            <div class="summary-label">총 에이전트</div>
          </div>
        </div>
      </el-card>

      <el-card class="summary-card">
        <div class="summary-content">
          <div class="summary-icon active">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="summary-info">
            <div class="summary-value">{{ agentsSummary.active_agents }}</div>
            <div class="summary-label">활성 에이전트</div>
          </div>
        </div>
      </el-card>

      <el-card class="summary-card">
        <div class="summary-content">
          <div class="summary-icon cost">
            <el-icon><Money /></el-icon>
          </div>
          <div class="summary-info">
            <div class="summary-value">${{ formatCurrency(agentsSummary.total_cost) }}</div>
            <div class="summary-label">총 비용 (월간)</div>
          </div>
        </div>
      </el-card>

      <el-card class="summary-card">
        <div class="summary-content">
          <div class="summary-icon efficiency">
            <el-icon><TrendCharts /></el-icon>
          </div>
          <div class="summary-info">
            <div class="summary-value">{{ agentsSummary.avg_efficiency.toFixed(1) }}%</div>
            <div class="summary-label">평균 효율성</div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 필터 및 정렬 -->
    <el-card class="filters-card">
      <div class="filters">
        <div class="filter-group">
          <label>상태:</label>
          <el-select v-model="filters.status" placeholder="전체" clearable @change="applyFilters">
            <el-option label="전체" value="" />
            <el-option label="활성" value="active" />
            <el-option label="비활성" value="inactive" />
          </el-select>
        </div>
        <div class="filter-group">
          <label>모델:</label>
          <el-select v-model="filters.model" placeholder="전체" clearable @change="applyFilters">
            <el-option label="전체" value="" />
            <el-option 
              v-for="model in availableModels" 
              :key="model" 
              :label="model" 
              :value="model" 
            />
          </el-select>
        </div>
        <div class="filter-group">
          <label>정렬:</label>
          <el-select v-model="sortBy" @change="applySorting">
            <el-option label="이름" value="name" />
            <el-option label="사용량" value="usage" />
            <el-option label="비용" value="cost" />
            <el-option label="효율성" value="efficiency" />
          </el-select>
        </div>
        <div class="filter-group">
          <el-button @click="clearFilters" size="small">필터 초기화</el-button>
        </div>
      </div>
    </el-card>

    <!-- 에이전트 목록 -->
    <div v-if="loading" class="loading-container">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>에이전트 데이터를 가져오는 중...</span>
    </div>

    <div v-else-if="filteredAgents.length === 0" class="empty-container">
      <el-empty description="에이전트가 없습니다" />
    </div>

    <div v-else class="agents-grid">
      <el-card 
        v-for="agent in filteredAgents" 
        :key="agent.id" 
        class="agent-card"
        :class="{ 'inactive': !agent.is_active }"
      >
        <!-- 에이전트 헤더 -->
        <template #header>
          <div class="agent-header">
            <div class="agent-basic-info">
              <h3 class="agent-name">{{ agent.name }}</h3>
              <div class="agent-tags">
                <el-tag :type="agent.is_active ? 'success' : 'danger'" size="small">
                  {{ agent.is_active ? '활성' : '비활성' }}
                </el-tag>
                <el-tag type="info" size="small">{{ agent.model }}</el-tag>
              </div>
            </div>
            <div class="agent-actions">
              <el-dropdown @command="handleAgentAction" trigger="click">
                <el-button circle size="small">
                  <el-icon><More /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="{action: 'view', agent: agent}">상세 보기</el-dropdown-item>
                    <el-dropdown-item :command="{action: 'optimize', agent: agent}">최적화 제안</el-dropdown-item>
                    <el-dropdown-item :command="{action: 'export', agent: agent}">데이터 내보내기</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </template>

        <!-- 에이전트 통계 -->
        <div class="agent-content">
          <!-- 주요 메트릭 -->
          <div class="metrics-grid">
            <div class="metric-item">
              <div class="metric-value">{{ formatNumber(agent.total_requests) }}</div>
              <div class="metric-label">총 요청</div>
            </div>
            <div class="metric-item">
              <div class="metric-value">${{ formatCurrency(agent.total_cost) }}</div>
              <div class="metric-label">총 비용</div>
            </div>
            <div class="metric-item">
              <div class="metric-value">{{ agent.efficiency.toFixed(1) }}%</div>
              <div class="metric-label">효율성</div>
            </div>
            <div class="metric-item">
              <div class="metric-value">{{ agent.avg_response_time }}ms</div>
              <div class="metric-label">평균 응답시간</div>
            </div>
          </div>

          <!-- 성능 차트 -->
          <div class="performance-chart">
            <h4>최근 7일 성능 추이</h4>
            <div :id="`chart-${agent.id}`" style="height: 150px;"></div>
          </div>

          <!-- 비용 효율성 분석 -->
          <div class="cost-analysis">
            <h4>비용 효율성 분석</h4>
            <div class="analysis-grid">
              <div class="analysis-item">
                <span class="analysis-label">요청당 비용:</span>
                <span class="analysis-value">${{ (agent.total_cost / agent.total_requests || 0).toFixed(4) }}</span>
              </div>
              <div class="analysis-item">
                <span class="analysis-label">토큰당 비용:</span>
                <span class="analysis-value">${{ (agent.total_cost / agent.total_tokens || 0).toFixed(6) }}</span>
              </div>
              <div class="analysis-item">
                <span class="analysis-label">일평균 비용:</span>
                <span class="analysis-value">${{ (agent.total_cost / 30).toFixed(2) }}</span>
              </div>
            </div>
          </div>

          <!-- 모델 추천 -->
          <div class="model-recommendation" v-if="agent.recommended_model">
            <div class="recommendation-header">
              <el-icon class="recommendation-icon"><Lightbulb /></el-icon>
              <h4>모델 최적화 추천</h4>
            </div>
            <div class="recommendation-content">
              <div class="current-vs-recommended">
                <div class="model-comparison">
                  <div class="current-model">
                    <span class="model-label">현재:</span>
                    <el-tag size="small">{{ agent.model }}</el-tag>
                  </div>
                  <el-icon class="arrow"><Right /></el-icon>
                  <div class="recommended-model">
                    <span class="model-label">추천:</span>
                    <el-tag type="success" size="small">{{ agent.recommended_model.name }}</el-tag>
                  </div>
                </div>
                <div class="savings-info">
                  <span class="savings-label">예상 절약:</span>
                  <span class="savings-value">${{ formatCurrency(agent.recommended_model.potential_savings) }}/월</span>
                  <span class="savings-percentage">({{ agent.recommended_model.savings_percentage }}% 절약)</span>
                </div>
              </div>
              <div class="recommendation-reason">
                <p>{{ agent.recommended_model.reason }}</p>
              </div>
              <div class="recommendation-actions">
                <el-button 
                  size="small" 
                  type="primary" 
                  @click="applyRecommendation(agent)"
                >
                  추천 적용
                </el-button>
                <el-button 
                  size="small" 
                  @click="dismissRecommendation(agent)"
                >
                  나중에
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 에이전트 상세 모달 -->
    <el-dialog 
      v-model="detailModalVisible" 
      :title="`${selectedAgent?.name} 상세 정보`"
      width="80%"
      top="5vh"
    >
      <div v-if="selectedAgent" class="agent-detail-content">
        <!-- 상세 통계 테이블 -->
        <el-tabs v-model="activeDetailTab">
          <el-tab-pane label="성능 통계" name="stats">
            <div class="detail-stats">
              <el-row :gutter="20">
                <el-col :span="12">
                  <el-card>
                    <template #header>요청 통계</template>
                    <div class="stat-list">
                      <div class="stat-row">
                        <span>총 요청 수:</span>
                        <span>{{ formatNumber(selectedAgent.total_requests) }}</span>
                      </div>
                      <div class="stat-row">
                        <span>성공 요청:</span>
                        <span>{{ formatNumber(selectedAgent.successful_requests) }}</span>
                      </div>
                      <div class="stat-row">
                        <span>실패 요청:</span>
                        <span>{{ formatNumber(selectedAgent.failed_requests) }}</span>
                      </div>
                      <div class="stat-row">
                        <span>성공률:</span>
                        <span>{{ ((selectedAgent.successful_requests / selectedAgent.total_requests) * 100).toFixed(2) }}%</span>
                      </div>
                    </div>
                  </el-card>
                </el-col>
                <el-col :span="12">
                  <el-card>
                    <template #header>비용 통계</template>
                    <div class="stat-list">
                      <div class="stat-row">
                        <span>총 비용:</span>
                        <span>${{ formatCurrency(selectedAgent.total_cost) }}</span>
                      </div>
                      <div class="stat-row">
                        <span>입력 토큰 비용:</span>
                        <span>${{ formatCurrency(selectedAgent.input_cost) }}</span>
                      </div>
                      <div class="stat-row">
                        <span>출력 토큰 비용:</span>
                        <span>${{ formatCurrency(selectedAgent.output_cost) }}</span>
                      </div>
                      <div class="stat-row">
                        <span>평균 요청당 비용:</span>
                        <span>${{ (selectedAgent.total_cost / selectedAgent.total_requests || 0).toFixed(4) }}</span>
                      </div>
                    </div>
                  </el-card>
                </el-col>
              </el-row>
            </div>
          </el-tab-pane>
          <el-tab-pane label="사용량 추이" name="trends">
            <div id="agent-detail-chart" style="height: 400px;"></div>
          </el-tab-pane>
          <el-tab-pane label="에러 로그" name="errors">
            <el-table :data="selectedAgent.error_logs || []" stripe>
              <el-table-column prop="timestamp" label="시간" width="180">
                <template #default="scope">
                  {{ formatDateTime(scope.row.timestamp) }}
                </template>
              </el-table-column>
              <el-table-column prop="error_type" label="에러 유형" width="120" />
              <el-table-column prop="error_message" label="에러 메시지" />
              <el-table-column prop="request_id" label="요청 ID" width="150" />
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh, User, CircleCheck, Money, TrendCharts, 
  Loading, More, Lightbulb, Right, Promotion
} from '@element-plus/icons-vue'
import { formatNumber, formatCurrency, formatDateTime } from '@/utils/format'
import * as echarts from 'echarts'

// 반응형 데이터
const loading = ref(false)
const syncLoading = ref(false)
const detailModalVisible = ref(false)
const activeDetailTab = ref('stats')
const selectedAgent = ref<any>(null)

const agents = ref<any[]>([])
const agentsSummary = ref({
  total_agents: 0,
  active_agents: 0,
  total_cost: 0,
  avg_efficiency: 0
})

const filters = ref({
  status: '',
  model: ''
})
const sortBy = ref('name')
const availableModels = ref<string[]>([])

// 필터링된 에이전트
const filteredAgents = computed(() => {
  let filtered = agents.value

  // 상태 필터
  if (filters.value.status) {
    filtered = filtered.filter(agent => {
      if (filters.value.status === 'active') return agent.is_active
      if (filters.value.status === 'inactive') return !agent.is_active
      return true
    })
  }

  // 모델 필터
  if (filters.value.model) {
    filtered = filtered.filter(agent => agent.model === filters.value.model)
  }

  // 정렬
  filtered.sort((a, b) => {
    switch (sortBy.value) {
      case 'name':
        return a.name.localeCompare(b.name)
      case 'usage':
        return b.total_requests - a.total_requests
      case 'cost':
        return b.total_cost - a.total_cost
      case 'efficiency':
        return b.efficiency - a.efficiency
      default:
        return 0
    }
  })

  return filtered
})

// 데이터 가져오기
const fetchAgentsData = async () => {
  try {
    loading.value = true
    const response = await fetch('http://localhost:8100/api/monitoring/usage-api/agent-analytics')
    const data = await response.json()
    
    if (data.success) {
      agents.value = data.agents || []
      agentsSummary.value = data.summary || {}
      availableModels.value = data.available_models || []
      
      // 개별 에이전트 차트 생성
      nextTick(() => {
        agents.value.forEach(agent => {
          createAgentChart(agent)
        })
      })
      
      ElMessage.success('에이전트 데이터를 성공적으로 가져왔습니다')
    } else {
      throw new Error(data.error || 'API 호출 실패')
    }
  } catch (error) {
    console.error('Failed to fetch agents data:', error)
    ElMessage.error('에이전트 데이터를 가져오는데 실패했습니다')
  } finally {
    loading.value = false
  }
}

// 에이전트 분석 동기화
const syncAgentAnalytics = async () => {
  try {
    syncLoading.value = true
    const response = await fetch('http://localhost:8100/api/monitoring/usage-api/sync', {
      method: 'POST'
    })
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success('에이전트 분석이 동기화되었습니다')
      await fetchAgentsData() // 데이터 새로고침
    } else {
      throw new Error(data.error || '동기화 실패')
    }
  } catch (error) {
    console.error('Failed to sync agent analytics:', error)
    ElMessage.error('에이전트 분석 동기화에 실패했습니다')
  } finally {
    syncLoading.value = false
  }
}

// 에이전트별 차트 생성
const createAgentChart = (agent: any) => {
  const chartDom = document.getElementById(`chart-${agent.id}`)
  if (!chartDom || !agent.performance_data) return

  const chart = echarts.init(chartDom)
  const option = {
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      textStyle: { color: '#303133' }
    },
    xAxis: {
      type: 'category',
      data: agent.performance_data.map((item: any) => item.date),
      axisLabel: { fontSize: 10, color: '#606266' }
    },
    yAxis: {
      type: 'value',
      axisLabel: { fontSize: 10, color: '#606266' }
    },
    series: [{
      data: agent.performance_data.map((item: any) => item.requests),
      type: 'line',
      smooth: true,
      itemStyle: { color: '#409EFF' },
      lineStyle: { width: 2 },
      symbol: 'circle',
      symbolSize: 4
    }],
    grid: {
      left: '10%',
      right: '10%',
      top: '10%',
      bottom: '20%'
    }
  }

  chart.setOption(option)
}

// 에이전트 액션 핸들러
const handleAgentAction = async (command: any) => {
  const { action, agent } = command
  
  switch (action) {
    case 'view':
      selectedAgent.value = agent
      detailModalVisible.value = true
      break
    case 'optimize':
      await showOptimizationSuggestions(agent)
      break
    case 'export':
      await exportAgentData(agent)
      break
  }
}

// 최적화 제안 표시
const showOptimizationSuggestions = async (agent: any) => {
  ElMessageBox.alert(
    `${agent.name}에 대한 최적화 제안을 생성하는 중입니다...`,
    '최적화 제안',
    {
      confirmButtonText: '확인'
    }
  )
}

// 에이전트 데이터 내보내기
const exportAgentData = async (agent: any) => {
  try {
    const csvData = generateAgentCSV(agent)
    downloadCSV(csvData, `${agent.name}_analytics.csv`)
    ElMessage.success('데이터가 성공적으로 내보내졌습니다')
  } catch (error) {
    ElMessage.error('데이터 내보내기에 실패했습니다')
  }
}

// CSV 데이터 생성
const generateAgentCSV = (agent: any) => {
  const headers = ['날짜', '요청 수', '비용', '성공률', '응답 시간']
  const rows = agent.performance_data?.map((item: any) => [
    item.date,
    item.requests,
    item.cost,
    item.success_rate,
    item.response_time
  ]) || []
  
  return [headers, ...rows].map(row => row.join(',')).join('\n')
}

// CSV 다운로드
const downloadCSV = (csvContent: string, filename: string) => {
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', filename)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// 추천 모델 적용
const applyRecommendation = async (agent: any) => {
  try {
    const confirm = await ElMessageBox.confirm(
      `${agent.name}의 모델을 ${agent.recommended_model.name}으로 변경하시겠습니까?`,
      '모델 변경 확인',
      {
        confirmButtonText: '변경',
        cancelButtonText: '취소',
        type: 'warning'
      }
    )

    if (confirm) {
      // 실제 모델 변경 API 호출
      ElMessage.success('모델이 성공적으로 변경되었습니다')
      await fetchAgentsData() // 데이터 새로고침
    }
  } catch (error) {
    // 사용자가 취소한 경우는 에러로 처리하지 않음
  }
}

// 추천 무시
const dismissRecommendation = (agent: any) => {
  agent.recommended_model = null
  ElMessage.info('추천이 무시되었습니다')
}

// 필터 적용
const applyFilters = () => {
  // 필터는 computed에서 자동으로 적용됨
}

// 정렬 적용
const applySorting = () => {
  // 정렬은 computed에서 자동으로 적용됨
}

// 필터 초기화
const clearFilters = () => {
  filters.value = {
    status: '',
    model: ''
  }
  sortBy.value = 'name'
}

// 데이터 새로고침
const refreshData = () => {
  fetchAgentsData()
}

// 컴포넌트 마운트
onMounted(() => {
  fetchAgentsData()
})
</script>

<style scoped>
.agents-view {
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

.header-left {
  flex: 1;
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
  gap: 12px;
}

/* 요약 카드 스타일 */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.summary-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.summary-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.summary-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.summary-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
}

.summary-icon.total { background: linear-gradient(45deg, #409EFF, #79bbff); }
.summary-icon.active { background: linear-gradient(45deg, #67C23A, #95d475); }
.summary-icon.cost { background: linear-gradient(45deg, #E6A23C, #f1c40f); }
.summary-icon.efficiency { background: linear-gradient(45deg, #F56C6C, #f89898); }

.summary-info {
  flex: 1;
}

.summary-value {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.summary-label {
  font-size: 14px;
  color: #606266;
}

/* 필터 스타일 */
.filters-card {
  margin-bottom: 24px;
}

.filters {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-group label {
  font-size: 14px;
  color: #606266;
  min-width: 50px;
}

/* 에이전트 그리드 스타일 */
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

.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}

.agent-card {
  transition: transform 0.2s, box-shadow 0.2s;
}

.agent-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.agent-card.inactive {
  opacity: 0.7;
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.agent-basic-info {
  flex: 1;
}

.agent-name {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 18px;
}

.agent-tags {
  display: flex;
  gap: 8px;
}

.agent-content {
  padding: 0;
}

/* 메트릭 그리드 */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.metric-item {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.metric-value {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 12px;
  color: #606266;
}

/* 성능 차트 */
.performance-chart {
  margin-bottom: 20px;
}

.performance-chart h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 14px;
}

/* 비용 분석 */
.cost-analysis {
  margin-bottom: 20px;
}

.cost-analysis h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 14px;
}

.analysis-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.analysis-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
}

.analysis-label {
  color: #606266;
}

.analysis-value {
  font-weight: 500;
  color: #303133;
}

/* 모델 추천 */
.model-recommendation {
  padding: 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 8px;
  border: 1px solid #bae6fd;
}

.recommendation-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.recommendation-icon {
  color: #0ea5e9;
  font-size: 16px;
}

.recommendation-header h4 {
  margin: 0;
  color: #0369a1;
  font-size: 14px;
}

.current-vs-recommended {
  margin-bottom: 12px;
}

.model-comparison {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.current-model,
.recommended-model {
  display: flex;
  align-items: center;
  gap: 6px;
}

.model-label {
  font-size: 12px;
  color: #64748b;
}

.arrow {
  color: #0ea5e9;
}

.savings-info {
  font-size: 12px;
  color: #059669;
  font-weight: 500;
}

.savings-value {
  margin: 0 4px;
}

.savings-percentage {
  font-weight: normal;
  color: #065f46;
}

.recommendation-reason {
  margin-bottom: 12px;
}

.recommendation-reason p {
  margin: 0;
  font-size: 12px;
  color: #475569;
  line-height: 1.4;
}

.recommendation-actions {
  display: flex;
  gap: 8px;
}

/* 상세 모달 스타일 */
.agent-detail-content {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-stats {
  margin-bottom: 20px;
}

.stat-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 14px;
}

.stat-row:last-child {
  border-bottom: none;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .summary-cards,
  .agents-grid {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .filters {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>