<template>
  <div class="comprehensive-report">
    <!-- 페이지 헤더 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">종합 보고서</h1>
        <p class="page-description">모든 API 사용량과 비용 데이터를 종합 분석하고 최적화 인사이트를 확인하세요</p>
      </div>
      <div class="header-actions">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="~"
          start-placeholder="시작일"
          end-placeholder="종료일"
          @change="onDateRangeChange"
        />
        <el-button @click="refreshReport" :loading="loading">
          <el-icon><Refresh /></el-icon>
          보고서 새로고침
        </el-button>
        <el-button @click="exportReport" type="primary">
          <el-icon><Download /></el-icon>
          PDF 내보내기
        </el-button>
      </div>
    </div>

    <!-- 종합 통계 요약 -->
    <div class="executive-summary">
      <el-card class="summary-overview">
        <template #header>
          <div class="card-header">
            <span>요약</span>
            <el-tag :type="getSummaryTagType(reportData.summary?.trend)" size="small">
              {{ reportData.summary?.period }}
            </el-tag>
          </div>
        </template>
        
        <div class="summary-grid">
          <div class="summary-metric">
            <div class="metric-icon total-cost">
              <el-icon><Money /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">${{ formatCurrency(reportData.summary?.total_cost || 0) }}</div>
              <div class="metric-label">총 비용</div>
              <div class="metric-change" :class="getTrendClass(reportData.summary?.cost_change)">
                {{ formatChange(reportData.summary?.cost_change) }}
              </div>
            </div>
          </div>

          <div class="summary-metric">
            <div class="metric-icon total-requests">
              <el-icon><DataBoard /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ formatNumber(reportData.summary?.total_requests || 0) }}</div>
              <div class="metric-label">총 요청 수</div>
              <div class="metric-change" :class="getTrendClass(reportData.summary?.requests_change)">
                {{ formatChange(reportData.summary?.requests_change) }}
              </div>
            </div>
          </div>

          <div class="summary-metric">
            <div class="metric-icon efficiency">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">{{ (reportData.summary?.avg_efficiency || 0).toFixed(1) }}%</div>
              <div class="metric-label">평균 효율성</div>
              <div class="metric-change" :class="getTrendClass(reportData.summary?.efficiency_change)">
                {{ formatChange(reportData.summary?.efficiency_change) }}
              </div>
            </div>
          </div>

          <div class="summary-metric">
            <div class="metric-icon cost-per-request">
              <el-icon><Calculator /></el-icon>
            </div>
            <div class="metric-content">
              <div class="metric-value">${{ formatCurrency(reportData.summary?.cost_per_request || 0) }}</div>
              <div class="metric-label">요청당 평균 비용</div>
              <div class="metric-change" :class="getTrendClass(reportData.summary?.cost_per_request_change)">
                {{ formatChange(reportData.summary?.cost_per_request_change) }}
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 차트 섹션 -->
    <div class="charts-section">
      <div class="chart-row">
        <!-- 시간별 트렌드 차트 -->
        <el-card class="chart-card large">
          <template #header>
            <div class="card-header">
              <span>시간별 사용량 트렌드</span>
              <el-radio-group v-model="trendChartType" size="small" @change="updateTrendChart">
                <el-radio value="cost">비용</el-radio>
                <el-radio value="requests">요청</el-radio>
                <el-radio value="tokens">토큰</el-radio>
              </el-radio-group>
            </div>
          </template>
          <div id="trend-chart" style="height: 400px;"></div>
        </el-card>
      </div>

      <div class="chart-row">
        <!-- 에이전트별 분석 -->
        <el-card class="chart-card medium">
          <template #header>
            <span>에이전트별 비용 분석</span>
          </template>
          <div id="agent-cost-chart" style="height: 300px;"></div>
        </el-card>

        <!-- 모델별 분석 -->
        <el-card class="chart-card medium">
          <template #header>
            <span>모델별 사용량 분석</span>
          </template>
          <div id="model-usage-chart" style="height: 300px;"></div>
        </el-card>
      </div>

      <div class="chart-row">
        <!-- 시간대별 패턴 -->
        <el-card class="chart-card medium">
          <template #header>
            <span>시간대별 사용 패턴</span>
          </template>
          <div id="hourly-pattern-chart" style="height: 300px;"></div>
        </el-card>

        <!-- 일별 효율성 추이 -->
        <el-card class="chart-card medium">
          <template #header>
            <span>일별 효율성 추이</span>
          </template>
          <div id="daily-efficiency-chart" style="height: 300px;"></div>
        </el-card>
      </div>
    </div>

    <!-- 상세 분석 테이블 -->
    <div class="detailed-analysis">
      <el-card class="analysis-table-card">
        <template #header>
          <div class="card-header">
            <span>상세 분석</span>
            <div class="table-controls">
              <el-input
                v-model="searchQuery"
                placeholder="검색..."
                style="width: 200px;"
                clearable
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <el-select v-model="analysisFilter" placeholder="필터" style="width: 120px;">
                <el-option label="전체" value="" />
                <el-option label="에이전트" value="agent" />
                <el-option label="모델" value="model" />
                <el-option label="API 키" value="api_key" />
              </el-select>
            </div>
          </div>
        </template>

        <el-table
          :data="filteredAnalysisData"
          stripe
          style="width: 100%"
          :loading="loading"
          @sort-change="onSortChange"
        >
          <el-table-column prop="name" label="이름" width="200" sortable="custom">
            <template #default="scope">
              <div class="name-cell">
                <el-tag :type="getEntityTagType(scope.row.type)" size="small">
                  {{ scope.row.type }}
                </el-tag>
                <span class="entity-name">{{ scope.row.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="total_requests" label="총 요청" width="120" sortable="custom">
            <template #default="scope">
              {{ formatNumber(scope.row.total_requests) }}
            </template>
          </el-table-column>
          <el-table-column prop="total_cost" label="총 비용" width="120" sortable="custom">
            <template #default="scope">
              ${{ formatCurrency(scope.row.total_cost) }}
            </template>
          </el-table-column>
          <el-table-column prop="avg_cost_per_request" label="요청당 비용" width="140" sortable="custom">
            <template #default="scope">
              ${{ formatCurrency(scope.row.avg_cost_per_request) }}
            </template>
          </el-table-column>
          <el-table-column prop="efficiency" label="효율성" width="100" sortable="custom">
            <template #default="scope">
              <el-progress
                :percentage="scope.row.efficiency"
                :color="getEfficiencyColor(scope.row.efficiency)"
                :stroke-width="8"
                :show-text="false"
              />
              <span class="efficiency-text">{{ scope.row.efficiency.toFixed(1) }}%</span>
            </template>
          </el-table-column>
          <el-table-column prop="trend" label="트렌드" width="120">
            <template #default="scope">
              <div class="trend-cell">
                <el-icon :class="getTrendIconClass(scope.row.trend)">
                  <component :is="getTrendIcon(scope.row.trend)" />
                </el-icon>
                <span :class="getTrendClass(scope.row.trend_value)">
                  {{ formatChange(scope.row.trend_value) }}
                </span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="last_activity" label="마지막 활동" width="180">
            <template #default="scope">
              {{ formatDateTime(scope.row.last_activity) }}
            </template>
          </el-table-column>
          <el-table-column label="액션" width="120" fixed="right">
            <template #default="scope">
              <el-button size="small" @click="viewEntityDetails(scope.row)">
                상세보기
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 최적화 인사이트 -->
    <div class="optimization-insights">
      <el-card class="insights-card">
        <template #header>
          <div class="card-header">
            <span>비용 최적화 인사이트</span>
            <el-tag type="info" size="small">{{ optimizationInsights.length }}개의 인사이트</el-tag>
          </div>
        </template>

        <div class="insights-grid">
          <div 
            v-for="(insight, index) in optimizationInsights" 
            :key="index"
            class="insight-card"
            :class="insight.impact"
          >
            <div class="insight-header">
              <div class="insight-icon" :class="insight.impact">
                <el-icon>
                  <component :is="getInsightIcon(insight.impact)" />
                </el-icon>
              </div>
              <div class="insight-title">
                <h4>{{ insight.title }}</h4>
                <el-tag :type="getImpactTagType(insight.impact)" size="small">
                  {{ getImpactText(insight.impact) }}
                </el-tag>
              </div>
            </div>
            
            <div class="insight-content">
              <p class="insight-description">{{ insight.description }}</p>
              
              <div class="insight-metrics">
                <div class="metric-item">
                  <span class="metric-label">예상 절약:</span>
                  <span class="metric-value savings">${{ formatCurrency(insight.potential_savings) }}/월</span>
                </div>
                <div class="metric-item" v-if="insight.implementation_effort">
                  <span class="metric-label">구현 난이도:</span>
                  <span class="metric-value effort" :class="insight.implementation_effort">
                    {{ getEffortText(insight.implementation_effort) }}
                  </span>
                </div>
              </div>

              <div class="insight-actions">
                <el-button size="small" type="primary" @click="implementInsight(insight)">
                  적용하기
                </el-button>
                <el-button size="small" @click="viewInsightDetails(insight)">
                  자세히 보기
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 상세 인사이트 모달 -->
    <el-dialog 
      v-model="insightModalVisible" 
      :title="selectedInsight?.title"
      width="60%"
      top="5vh"
    >
      <div v-if="selectedInsight" class="insight-detail-content">
        <div class="insight-detail-header">
          <div class="detail-impact" :class="selectedInsight.impact">
            <el-icon>
              <component :is="getInsightIcon(selectedInsight.impact)" />
            </el-icon>
            <span>{{ getImpactText(selectedInsight.impact) }} 영향</span>
          </div>
        </div>

        <div class="insight-detail-body">
          <div class="detail-section">
            <h4>상세 설명</h4>
            <p>{{ selectedInsight.detailed_description }}</p>
          </div>

          <div class="detail-section" v-if="selectedInsight.affected_entities">
            <h4>영향 받는 요소</h4>
            <el-tag 
              v-for="entity in selectedInsight.affected_entities"
              :key="entity"
              size="small"
              class="entity-tag"
            >
              {{ entity }}
            </el-tag>
          </div>

          <div class="detail-section">
            <h4>구현 단계</h4>
            <ol class="implementation-steps">
              <li v-for="step in selectedInsight.implementation_steps" :key="step">
                {{ step }}
              </li>
            </ol>
          </div>

          <div class="detail-section">
            <h4>예상 결과</h4>
            <div class="expected-results">
              <div class="result-item">
                <span class="result-label">월간 비용 절약:</span>
                <span class="result-value">${{ formatCurrency(selectedInsight.potential_savings) }}</span>
              </div>
              <div class="result-item">
                <span class="result-label">연간 비용 절약:</span>
                <span class="result-value">${{ formatCurrency(selectedInsight.potential_savings * 12) }}</span>
              </div>
              <div class="result-item" v-if="selectedInsight.roi">
                <span class="result-label">투자 대비 수익률:</span>
                <span class="result-value">{{ selectedInsight.roi }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="insightModalVisible = false">닫기</el-button>
          <el-button type="primary" @click="implementSelectedInsight">
            구현하기
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Refresh, Download, Money, DataBoard, TrendCharts, Calculator,
  Search, ArrowUp, ArrowDown, Minus, Warning, InfoFilled, 
  SuccessFilled, CircleCheck
} from '@element-plus/icons-vue'
import { formatNumber, formatCurrency, formatDateTime } from '@/utils/format'
import * as echarts from 'echarts'

// 반응형 데이터
const loading = ref(false)
const dateRange = ref<[Date, Date]>([
  new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // 30일 전
  new Date() // 오늘
])
const trendChartType = ref('cost')
const searchQuery = ref('')
const analysisFilter = ref('')
const insightModalVisible = ref(false)
const selectedInsight = ref<any>(null)

const reportData = ref<any>({
  summary: {},
  charts: {
    trend_data: [],
    agent_cost_data: [],
    model_usage_data: [],
    hourly_pattern_data: [],
    daily_efficiency_data: []
  },
  detailed_analysis: [],
  optimization_insights: []
})

const optimizationInsights = computed(() => reportData.value.optimization_insights || [])

// 차트 인스턴스들
let trendChart: echarts.ECharts | null = null
let agentCostChart: echarts.ECharts | null = null
let modelUsageChart: echarts.ECharts | null = null
let hourlyPatternChart: echarts.ECharts | null = null
let dailyEfficiencyChart: echarts.ECharts | null = null

// 필터링된 분석 데이터
const filteredAnalysisData = computed(() => {
  let data = reportData.value.detailed_analysis || []
  
  // 검색 필터
  if (searchQuery.value) {
    data = data.filter((item: any) => 
      item.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }
  
  // 타입 필터
  if (analysisFilter.value) {
    data = data.filter((item: any) => item.type === analysisFilter.value)
  }
  
  return data
})

// 종합 보고서 데이터 가져오기
const fetchComprehensiveReport = async () => {
  try {
    loading.value = true
    const startDate = dateRange.value[0].toISOString().split('T')[0]
    const endDate = dateRange.value[1].toISOString().split('T')[0]
    
    const response = await fetch(
      `http://localhost:8100/api/admin/comprehensive-report?start_date=${startDate}&end_date=${endDate}`
    )
    const data = await response.json()
    
    if (data.success) {
      reportData.value = data.report
      
      // 차트 업데이트
      nextTick(() => {
        initializeCharts()
        updateAllCharts()
      })
      
      ElMessage.success('종합 보고서를 성공적으로 가져왔습니다')
    } else {
      throw new Error(data.error || 'API 호출 실패')
    }
  } catch (error) {
    console.error('Failed to fetch comprehensive report:', error)
    ElMessage.error('종합 보고서를 가져오는데 실패했습니다')
  } finally {
    loading.value = false
  }
}

// 차트 초기화
const initializeCharts = () => {
  trendChart = echarts.init(document.getElementById('trend-chart'))
  agentCostChart = echarts.init(document.getElementById('agent-cost-chart'))
  modelUsageChart = echarts.init(document.getElementById('model-usage-chart'))
  hourlyPatternChart = echarts.init(document.getElementById('hourly-pattern-chart'))
  dailyEfficiencyChart = echarts.init(document.getElementById('daily-efficiency-chart'))

  // 윈도우 리사이즈 이벤트 핸들러
  window.addEventListener('resize', () => {
    trendChart?.resize()
    agentCostChart?.resize()
    modelUsageChart?.resize()
    hourlyPatternChart?.resize()
    dailyEfficiencyChart?.resize()
  })
}

// 모든 차트 업데이트
const updateAllCharts = () => {
  updateTrendChart()
  updateAgentCostChart()
  updateModelUsageChart()
  updateHourlyPatternChart()
  updateDailyEfficiencyChart()
}

// 트렌드 차트 업데이트
const updateTrendChart = () => {
  if (!trendChart || !reportData.value.charts?.trend_data) return

  const data = reportData.value.charts.trend_data
  const option = {
    title: {
      text: `${trendChartType.value === 'cost' ? '비용' : trendChartType.value === 'requests' ? '요청 수' : '토큰 수'} 추이`,
      textStyle: { fontSize: 16, color: '#303133' }
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e4e7ed',
      textStyle: { color: '#303133' }
    },
    legend: {
      data: ['실제값', '예측값'],
      top: 40
    },
    xAxis: {
      type: 'category',
      data: data.map((item: any) => item.date),
      axisLabel: { color: '#606266' }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#606266' }
    },
    series: [
      {
        name: '실제값',
        data: data.map((item: any) => item[trendChartType.value]),
        type: 'line',
        smooth: true,
        itemStyle: { color: '#409EFF' },
        areaStyle: { color: 'rgba(64, 158, 255, 0.1)' }
      },
      {
        name: '예측값',
        data: data.slice(-7).map((item: any) => item[`${trendChartType.value}_prediction`]),
        type: 'line',
        smooth: true,
        itemStyle: { color: '#E6A23C' },
        lineStyle: { type: 'dashed' }
      }
    ],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: 80,
      containLabel: true
    }
  }

  trendChart.setOption(option)
}

// 에이전트 비용 차트 업데이트
const updateAgentCostChart = () => {
  if (!agentCostChart || !reportData.value.charts?.agent_cost_data) return

  const data = reportData.value.charts.agent_cost_data
  const option = {
    title: {
      text: '에이전트별 비용 분석',
      textStyle: { fontSize: 14, color: '#303133' }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: ${c} ({d}%)'
    },
    series: [{
      name: '비용',
      type: 'pie',
      radius: ['50%', '80%'],
      center: ['50%', '60%'],
      data: data.map((item: any) => ({
        value: item.cost,
        name: item.agent_name
      })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      label: {
        show: true,
        formatter: '{b}\n${c}'
      }
    }]
  }

  agentCostChart.setOption(option)
}

// 모델 사용량 차트 업데이트
const updateModelUsageChart = () => {
  if (!modelUsageChart || !reportData.value.charts?.model_usage_data) return

  const data = reportData.value.charts.model_usage_data
  const option = {
    title: {
      text: '모델별 사용량',
      textStyle: { fontSize: 14, color: '#303133' }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    xAxis: {
      type: 'category',
      data: data.map((item: any) => item.model),
      axisLabel: { 
        color: '#606266',
        rotate: 45,
        interval: 0
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#606266' }
    },
    series: [{
      data: data.map((item: any) => item.usage_count),
      type: 'bar',
      itemStyle: { 
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#67C23A' },
          { offset: 1, color: '#95d475' }
        ])
      },
      label: {
        show: true,
        position: 'top'
      }
    }],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '25%',
      top: 60,
      containLabel: true
    }
  }

  modelUsageChart.setOption(option)
}

// 시간대별 패턴 차트 업데이트
const updateHourlyPatternChart = () => {
  if (!hourlyPatternChart || !reportData.value.charts?.hourly_pattern_data) return

  const data = reportData.value.charts.hourly_pattern_data
  const option = {
    title: {
      text: '시간대별 사용 패턴',
      textStyle: { fontSize: 14, color: '#303133' }
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: Array.from({length: 24}, (_, i) => `${i}시`),
      axisLabel: { color: '#606266' }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#606266' }
    },
    series: [{
      data: data,
      type: 'bar',
      itemStyle: { 
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#409EFF' },
          { offset: 1, color: '#79bbff' }
        ])
      }
    }],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: 60,
      containLabel: true
    }
  }

  hourlyPatternChart.setOption(option)
}

// 일별 효율성 차트 업데이트
const updateDailyEfficiencyChart = () => {
  if (!dailyEfficiencyChart || !reportData.value.charts?.daily_efficiency_data) return

  const data = reportData.value.charts.daily_efficiency_data
  const option = {
    title: {
      text: '일별 효율성 추이',
      textStyle: { fontSize: 14, color: '#303133' }
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: data.map((item: any) => item.date),
      axisLabel: { color: '#606266' }
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { 
        color: '#606266',
        formatter: '{value}%'
      }
    },
    series: [{
      data: data.map((item: any) => item.efficiency),
      type: 'line',
      smooth: true,
      itemStyle: { color: '#F56C6C' },
      areaStyle: { color: 'rgba(245, 108, 108, 0.1)' },
      markLine: {
        data: [{
          type: 'average',
          name: '평균값'
        }]
      }
    }],
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: 60,
      containLabel: true
    }
  }

  dailyEfficiencyChart.setOption(option)
}

// 유틸리티 함수들
const formatChange = (value: number) => {
  if (value === undefined || value === null) return '0%'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value.toFixed(1)}%`
}

const getTrendClass = (value: number) => {
  if (value > 0) return 'positive'
  if (value < 0) return 'negative'
  return 'neutral'
}

const getTrendIcon = (trend: string) => {
  switch (trend) {
    case 'up': return ArrowUp
    case 'down': return ArrowDown
    default: return Minus
  }
}

const getTrendIconClass = (trend: string) => {
  return `trend-icon ${trend}`
}

const getSummaryTagType = (trend: string) => {
  switch (trend) {
    case 'improving': return 'success'
    case 'declining': return 'warning'
    default: return 'info'
  }
}

const getEntityTagType = (type: string) => {
  switch (type) {
    case 'agent': return 'primary'
    case 'model': return 'success'
    case 'api_key': return 'warning'
    default: return 'info'
  }
}

const getEfficiencyColor = (efficiency: number) => {
  if (efficiency >= 80) return '#67C23A'
  if (efficiency >= 60) return '#E6A23C'
  return '#F56C6C'
}

const getInsightIcon = (impact: string) => {
  switch (impact) {
    case 'high': return Warning
    case 'medium': return InfoFilled
    default: return SuccessFilled
  }
}

const getImpactTagType = (impact: string) => {
  switch (impact) {
    case 'high': return 'danger'
    case 'medium': return 'warning'
    default: return 'success'
  }
}

const getImpactText = (impact: string) => {
  switch (impact) {
    case 'high': return '높음'
    case 'medium': return '보통'
    default: return '낮음'
  }
}

const getEffortText = (effort: string) => {
  switch (effort) {
    case 'low': return '쉬움'
    case 'medium': return '보통'
    default: return '어려움'
  }
}

// 이벤트 핸들러들
const onDateRangeChange = () => {
  fetchComprehensiveReport()
}

const onSortChange = (sortInfo: any) => {
  // 정렬 로직 구현
  console.log('Sort change:', sortInfo)
}

const refreshReport = () => {
  fetchComprehensiveReport()
}

const exportReport = async () => {
  try {
    ElMessage.info('보고서를 PDF로 내보내는 중...')
    // PDF 내보내기 로직 구현
    await new Promise(resolve => setTimeout(resolve, 2000)) // 시뮬레이션
    ElMessage.success('보고서가 성공적으로 내보내졌습니다')
  } catch (error) {
    ElMessage.error('보고서 내보내기에 실패했습니다')
  }
}

const viewEntityDetails = (entity: any) => {
  ElMessage.info(`${entity.name}의 상세 정보를 표시합니다`)
}

const viewInsightDetails = (insight: any) => {
  selectedInsight.value = insight
  insightModalVisible.value = true
}

const implementInsight = async (insight: any) => {
  try {
    const confirm = await ElMessageBox.confirm(
      `"${insight.title}" 최적화를 적용하시겠습니까?`,
      '최적화 적용 확인',
      {
        confirmButtonText: '적용',
        cancelButtonText: '취소',
        type: 'warning'
      }
    )

    if (confirm) {
      ElMessage.success('최적화가 성공적으로 적용되었습니다')
    }
  } catch (error) {
    // 사용자가 취소한 경우
  }
}

const implementSelectedInsight = () => {
  if (selectedInsight.value) {
    implementInsight(selectedInsight.value)
    insightModalVisible.value = false
  }
}

// 컴포넌트 마운트
onMounted(() => {
  fetchComprehensiveReport()
})
</script>

<style scoped>
.comprehensive-report {
  max-width: 1600px;
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
  align-items: center;
  gap: 16px;
}

/* 종합 통계 스타일 */
.executive-summary {
  margin-bottom: 24px;
}

.summary-overview {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.summary-overview :deep(.el-card__header) {
  background: transparent;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.summary-overview :deep(.el-card__header .card-header span) {
  color: white;
  font-size: 18px;
  font-weight: 600;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
  padding: 20px 0;
}

.summary-metric {
  display: flex;
  align-items: center;
  gap: 16px;
}

.metric-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
}

.metric-content {
  flex: 1;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 4px;
}

.metric-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 4px;
}

.metric-change {
  font-size: 12px;
  font-weight: 500;
}

.metric-change.positive { color: #4ade80; }
.metric-change.negative { color: #f87171; }
.metric-change.neutral { color: #a1a1aa; }

/* 차트 섹션 스타일 */
.charts-section {
  margin-bottom: 32px;
}

.chart-row {
  display: grid;
  gap: 20px;
  margin-bottom: 20px;
}

.chart-row:first-child {
  grid-template-columns: 1fr;
}

.chart-row:not(:first-child) {
  grid-template-columns: 1fr 1fr;
}

.chart-card.large {
  grid-column: 1 / -1;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* 상세 분석 테이블 스타일 */
.detailed-analysis {
  margin-bottom: 32px;
}

.table-controls {
  display: flex;
  gap: 12px;
}

.name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.entity-name {
  font-weight: 500;
}

.efficiency-text {
  font-size: 12px;
  color: #606266;
  margin-left: 8px;
}

.trend-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.trend-icon {
  font-size: 14px;
}

.trend-icon.up { color: #67C23A; }
.trend-icon.down { color: #F56C6C; }
.trend-icon.stable { color: #909399; }

/* 최적화 인사이트 스타일 */
.optimization-insights {
  margin-bottom: 32px;
}

.insights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}

.insight-card {
  padding: 20px;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  background: white;
  transition: all 0.3s ease;
}

.insight-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.insight-card.high {
  border-left: 4px solid #F56C6C;
  background: linear-gradient(135deg, #fef2f2 0%, #fef8f8 100%);
}

.insight-card.medium {
  border-left: 4px solid #E6A23C;
  background: linear-gradient(135deg, #fffbeb 0%, #fefcf3 100%);
}

.insight-card.low {
  border-left: 4px solid #67C23A;
  background: linear-gradient(135deg, #f0f9ff 0%, #f8fafc 100%);
}

.insight-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.insight-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  color: white;
}

.insight-icon.high { background: #F56C6C; }
.insight-icon.medium { background: #E6A23C; }
.insight-icon.low { background: #67C23A; }

.insight-title {
  flex: 1;
}

.insight-title h4 {
  margin: 0 0 4px 0;
  color: #303133;
  font-size: 16px;
}

.insight-description {
  margin: 0 0 16px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.insight-metrics {
  margin-bottom: 16px;
}

.metric-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
}

.metric-label {
  color: #606266;
}

.metric-value.savings {
  color: #67C23A;
  font-weight: 600;
}

.metric-value.effort.low { color: #67C23A; }
.metric-value.effort.medium { color: #E6A23C; }
.metric-value.effort.high { color: #F56C6C; }

.insight-actions {
  display: flex;
  gap: 8px;
}

/* 인사이트 상세 모달 */
.insight-detail-content {
  max-height: 60vh;
  overflow-y: auto;
}

.insight-detail-header {
  margin-bottom: 20px;
}

.detail-impact {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 8px;
  font-weight: 500;
}

.detail-impact.high {
  background: #fef2f2;
  color: #dc2626;
}

.detail-impact.medium {
  background: #fffbeb;
  color: #d97706;
}

.detail-impact.low {
  background: #f0f9ff;
  color: #2563eb;
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section h4 {
  margin: 0 0 12px 0;
  color: #303133;
  font-size: 16px;
  border-bottom: 1px solid #e4e7ed;
  padding-bottom: 8px;
}

.entity-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.implementation-steps {
  margin: 0;
  padding-left: 20px;
}

.implementation-steps li {
  margin-bottom: 8px;
  line-height: 1.5;
}

.expected-results {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.result-label {
  color: #606266;
  font-size: 14px;
}

.result-value {
  font-weight: 600;
  color: #303133;
}

/* 반응형 디자인 */
@media (max-width: 1200px) {
  .chart-row:not(:first-child) {
    grid-template-columns: 1fr;
  }
  
  .insights-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .summary-grid {
    grid-template-columns: 1fr;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .header-actions {
    width: 100%;
    flex-wrap: wrap;
    justify-content: flex-end;
  }
  
  .table-controls {
    flex-direction: column;
    gap: 8px;
  }
}
</style>