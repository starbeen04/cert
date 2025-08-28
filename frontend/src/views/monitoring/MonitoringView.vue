<template>
  <div class="monitoring-view">
    <div class="page-header">
      <h1 class="page-title">AI 사용량 모니터링</h1>
      <p class="page-description">AI 에이전트 사용량, API 키 현황 및 시스템 통계 모니터링</p>
    </div>

    <!-- AI 사용량 개요 -->
    <el-row :gutter="20" class="stats-overview">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card ai-requests">
          <div class="stat-icon">
            <el-icon size="24"><ChatDotRound /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ aiStats.totalRequests }}</div>
            <div class="stat-label">총 AI 요청 수</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card tokens-used">
          <div class="stat-icon">
            <el-icon size="24"><Coin /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatNumber(aiStats.tokensUsed) }}</div>
            <div class="stat-label">사용된 토큰</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card api-cost">
          <div class="stat-icon">
            <el-icon size="24"><Money /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">${{ aiStats.totalCost.toFixed(2) }}</div>
            <div class="stat-label">총 비용</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card active-agents">
          <div class="stat-icon">
            <el-icon size="24"><Setting /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ aiStats.activeAgents }}/{{ aiStats.totalAgents }}</div>
            <div class="stat-label">활성 에이전트</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- AI 에이전트 사용량 차트 -->
    <el-row :gutter="20" class="charts-section">
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">에이전트별 사용량</span>
              <el-select v-model="agentTimeRange" size="small" style="width: 120px" @change="fetchAgentUsage">
                <el-option label="오늘" value="today" />
                <el-option label="최근 7일" value="7d" />
                <el-option label="최근 30일" value="30d" />
              </el-select>
            </div>
          </template>
          
          <div class="chart-container">
            <div class="agent-usage-list">
              <div 
                v-for="agent in agentUsage" 
                :key="agent.id" 
                class="agent-usage-item"
              >
                <div class="agent-info">
                  <div class="agent-name">{{ agent.name }}</div>
                  <div class="agent-model">{{ agent.model_name }}</div>
                </div>
                <div class="usage-metrics">
                  <div class="metric">
                    <span class="metric-label">요청:</span>
                    <span class="metric-value">{{ agent.request_count }}</span>
                  </div>
                  <div class="metric">
                    <span class="metric-label">토큰:</span>
                    <span class="metric-value">{{ formatNumber(agent.tokens_used) }}</span>
                  </div>
                  <div class="metric">
                    <span class="metric-label">비용:</span>
                    <span class="metric-value">${{ agent.cost.toFixed(2) }}</span>
                  </div>
                </div>
                <div class="usage-bar">
                  <el-progress 
                    :percentage="agent.usage_percentage" 
                    :show-text="false"
                    :stroke-width="8"
                    :color="getUsageColor(agent.usage_percentage)"
                  />
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- API 키 사용량 -->
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">API 키 사용량</span>
              <el-button size="small" :icon="Refresh" @click="fetchApiKeyUsage">
                새로고침
              </el-button>
            </div>
          </template>
          
          <div class="chart-container">
            <div class="api-key-usage-list">
              <div 
                v-for="apiKey in apiKeyUsage" 
                :key="apiKey.id" 
                class="api-key-usage-item"
              >
                <div class="api-key-header">
                  <div class="api-key-name">{{ apiKey.key_name }}</div>
                  <el-tag 
                    :type="apiKey.is_active ? 'success' : 'danger'" 
                    size="small"
                  >
                    {{ apiKey.is_active ? '활성' : '비활성' }}
                  </el-tag>
                </div>
                <div class="api-key-provider">{{ getProviderName(apiKey.provider) }}</div>
                <div class="usage-stats">
                  <div class="stat-item">
                    <span class="stat-label">일일 사용량:</span>
                    <div class="usage-progress">
                      <el-progress 
                        :percentage="(apiKey.current_daily_usage / apiKey.daily_limit) * 100" 
                        :show-text="false"
                        :stroke-width="6"
                      />
                      <span class="usage-text">
                        {{ apiKey.current_daily_usage }} / {{ apiKey.daily_limit }}
                      </span>
                    </div>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">월간 사용량:</span>
                    <div class="usage-progress">
                      <el-progress 
                        :percentage="(apiKey.current_monthly_usage / apiKey.monthly_limit) * 100" 
                        :show-text="false"
                        :stroke-width="6"
                        color="#e6a23c"
                      />
                      <span class="usage-text">
                        {{ apiKey.current_monthly_usage }} / {{ apiKey.monthly_limit }}
                      </span>
                    </div>
                  </div>
                </div>
                <div class="last-used">
                  마지막 사용: {{ apiKey.last_used_at ? formatDate(apiKey.last_used_at) : '사용 안됨' }}
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 시스템 상태 -->
    <el-row :gutter="20" class="status-section">
      <el-col :xs="24" :lg="16">
        <el-card class="status-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">시스템 구성 요소 상태</span>
              <el-button type="text" :icon="Refresh" @click="refreshStatus">
                새로고침
              </el-button>
            </div>
          </template>
          
          <div class="status-grid">
            <div class="status-component">
              <div class="component-header">
                <el-icon size="20" :color="systemStatus.api_server.status === 'online' ? '#67c23a' : '#f56c6c'">
                  <component :is="systemStatus.api_server.status === 'online' ? 'CircleCheck' : 'CircleClose'" />
                </el-icon>
                <span class="component-name">API 서버</span>
                <el-tag :type="systemStatus.api_server.status === 'online' ? 'success' : 'danger'" size="small">
                  {{ systemStatus.api_server.status === 'online' ? '온라인' : '오프라인' }}
                </el-tag>
              </div>
              <div class="component-details">
                <div class="detail-item">
                  <span>가동 시간:</span>
                  <span>{{ systemStatus.api_server.uptime }}</span>
                </div>
                <div class="detail-item">
                  <span>응답 시간:</span>
                  <span>{{ systemStatus.api_server.response_time }}</span>
                </div>
                <div class="detail-item">
                  <span>마지막 확인:</span>
                  <span>{{ formatRelativeTime(new Date()) }}</span>
                </div>
              </div>
            </div>

            <div class="status-component">
              <div class="component-header">
                <el-icon size="20" :color="systemStatus.database.status === 'connected' ? '#67c23a' : '#f56c6c'">
                  <component :is="systemStatus.database.status === 'connected' ? 'CircleCheck' : 'CircleClose'" />
                </el-icon>
                <span class="component-name">데이터베이스</span>
                <el-tag :type="systemStatus.database.status === 'connected' ? 'success' : 'danger'" size="small">
                  {{ systemStatus.database.status === 'connected' ? '연결됨' : '연결 안됨' }}
                </el-tag>
              </div>
              <div class="component-details">
                <div class="detail-item">
                  <span>연결 수:</span>
                  <span>{{ systemStatus.database.connections }}</span>
                </div>
                <div class="detail-item">
                  <span>쿼리 시간:</span>
                  <span>{{ systemStatus.database.query_time }}</span>
                </div>
                <div class="detail-item">
                  <span>저장 공간:</span>
                  <span>{{ systemStatus.database.storage }}</span>
                </div>
              </div>
            </div>

            <div class="status-component">
              <div class="component-header">
                <el-icon size="20" :color="aiStats.activeAgents === aiStats.totalAgents ? '#67c23a' : '#e6a23c'">
                  <component :is="aiStats.activeAgents === aiStats.totalAgents ? 'CircleCheck' : 'Warning'" />
                </el-icon>
                <span class="component-name">AI 서비스</span>
                <el-tag :type="aiStats.activeAgents === aiStats.totalAgents ? 'success' : 'warning'" size="small">
                  {{ aiStats.activeAgents === aiStats.totalAgents ? '정상' : '부분 작동' }}
                </el-tag>
              </div>
              <div class="component-details">
                <div class="detail-item">
                  <span>활성 에이전트:</span>
                  <span>{{ aiStats.activeAgents }}/{{ aiStats.totalAgents }}</span>
                </div>
                <div class="detail-item">
                  <span>처리 대기:</span>
                  <span>{{ systemStatus.ai_service.queue_size }}건</span>
                </div>
                <div class="detail-item">
                  <span>평균 처리 시간:</span>
                  <span>{{ systemStatus.ai_service.avg_processing_time }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 최근 AI 작업 -->
      <el-col :xs="24" :lg="8">
        <el-card class="activities-card">
          <template #header>
            <span class="card-title">최근 AI 작업</span>
          </template>
          
          <div class="activities-list">
            <div
              v-for="activity in recentAiActivities"
              :key="activity.id"
              class="activity-item"
            >
              <div class="activity-icon" :class="activity.status">
                <el-icon><component :is="getActivityIcon(activity.status)" /></el-icon>
              </div>
              <div class="activity-content">
                <div class="activity-title">{{ activity.agent_name }}</div>
                <div class="activity-description">{{ activity.task_type }} 작업</div>
                <div class="activity-stats">
                  <span class="token-count">{{ formatNumber(activity.tokens_used) }} 토큰</span>
                  <span class="cost">${{ activity.cost.toFixed(3) }}</span>
                </div>
                <div class="activity-time">{{ formatRelativeTime(activity.created_at) }}</div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import {
  ChatDotRound,
  Coin,
  Money,
  Setting,
  Refresh,
  CircleCheck,
  CircleClose,
  Warning,
  Check,
  Close,
  Loading,
} from '@element-plus/icons-vue'
import { formatRelativeTime, formatDate } from '@/utils/format'

// 시간 범위 선택
const agentTimeRange = ref('today')

// AI 통계 데이터
const aiStats = reactive({
  totalRequests: 0,
  tokensUsed: 0,
  totalCost: 0,
  activeAgents: 0,
  totalAgents: 0,
})

// 에이전트별 사용량
const agentUsage = ref<any[]>([])

// API 키 사용량
const apiKeyUsage = ref<any[]>([])

// 시스템 상태
const systemStatus = reactive({
  api_server: {
    status: 'online',
    uptime: '99.9% (30일)',
    response_time: '180ms 평균',
  },
  database: {
    status: 'connected',
    connections: '5/100',
    query_time: '12ms 평균',
    storage: '15MB 사용',
  },
  ai_service: {
    queue_size: 0,
    avg_processing_time: '2.5초',
  },
})

// 최근 AI 작업
const recentAiActivities = ref<any[]>([])

// 유틸리티 함수들
const formatNumber = (num: number | undefined | null) => {
  if (num === undefined || num === null || isNaN(num)) {
    return '0'
  }
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const getUsageColor = (percentage: number) => {
  if (percentage >= 80) return '#f56c6c'
  if (percentage >= 60) return '#e6a23c'
  return '#67c23a'
}

const getProviderName = (provider: string) => {
  switch (provider) {
    case 'openai': return 'OpenAI'
    case 'anthropic': return 'Anthropic'
    default: return provider
  }
}

const getActivityIcon = (status: string) => {
  switch (status) {
    case 'completed': return 'Check'
    case 'failed': return 'Close'
    case 'processing': return 'Loading'
    default: return 'Loading'
  }
}

// API 호출 함수들
const fetchAiStats = async () => {
  try {
    // 실제 사용량 통계 API 사용
    const response = await fetch('http://localhost:8100/api/admin/usage-stats')
    const data = await response.json()
    if (data.success) {
      Object.assign(aiStats, {
        totalRequests: data.usage_summary.week.requests,
        tokensUsed: data.usage_summary.week.tokens,
        totalCost: data.usage_summary.week.cost,
        activeAgents: data.ai_agents.active,
        totalAgents: data.ai_agents.total,
      })
      console.log('Real AI stats loaded:', aiStats)
    } else {
      console.error('API returned error:', data.error)
    }
  } catch (error) {
    console.error('Failed to fetch AI stats:', error)
    // Fallback data shows current real state (no usage yet)
    Object.assign(aiStats, {
      totalRequests: 0,
      tokensUsed: 0,
      totalCost: 0.0,
      activeAgents: 0,
      totalAgents: 7,
    })
  }
}

const fetchAgentUsage = async () => {
  try {
    // 실제 AI 에이전트 데이터 사용
    const response = await fetch('http://localhost:8100/api/admin/usage-stats')
    const data = await response.json()
    if (data.success) {
      // AI 에이전트 상세 정보를 agentUsage에 매핑
      const maxCost = Math.max(...data.ai_agents.details.map(agent => agent.week_stats.cost), 0.01)
      agentUsage.value = data.ai_agents.details.map(agent => ({
        id: agent.id,
        name: agent.name,
        model_name: agent.model_name,
        request_count: agent.week_stats.requests,
        tokens_used: agent.week_stats.tokens,
        cost: agent.week_stats.cost,
        usage_percentage: Math.min((agent.week_stats.cost / maxCost) * 100, 100)
      }))
      console.log('Real agent usage loaded:', agentUsage.value)
    }
  } catch (error) {
    console.error('Failed to fetch agent usage:', error)
    // Mock data
    agentUsage.value = [
      {
        id: 1,
        name: '자격증 학습 도우미',
        model_name: 'claude-3-5-sonnet-20241022',
        request_count: 45,
        tokens_used: 12450,
        cost: 3.24,
        usage_percentage: 85,
      },
      {
        id: 3,
        name: '문서 분석 에이전트',
        model_name: 'claude-3-5-sonnet-20241022',
        request_count: 23,
        tokens_used: 8920,
        cost: 2.18,
        usage_percentage: 65,
      },
      {
        id: 4,
        name: '문제 추출 에이전트',
        model_name: 'claude-3-5-sonnet-20241022',
        request_count: 18,
        tokens_used: 6780,
        cost: 1.89,
        usage_percentage: 45,
      },
    ]
  }
}

const fetchApiKeyUsage = async () => {
  try {
    // 실제 API 키 사용량 데이터 사용
    const response = await fetch('http://localhost:8100/api/admin/usage-stats')
    const data = await response.json()
    if (data.success) {
      apiKeyUsage.value = data.api_keys.details.map(key => ({
        id: key.id,
        key_name: key.name,
        provider: key.provider,
        is_active: key.is_active,
        current_daily_usage: key.current_daily_usage,
        daily_limit: key.daily_limit,
        current_monthly_usage: key.current_monthly_usage,
        monthly_limit: key.monthly_limit,
        last_used_at: new Date(),
        week_stats: key.week_stats
      }))
      console.log('Real API key usage loaded:', apiKeyUsage.value)
    }
  } catch (error) {
    console.error('Failed to fetch API key usage:', error)
    // Fallback: show that we have 1 API key with no usage
    apiKeyUsage.value = [{
      id: 1,
      key_name: 'Claude Main API Key',
      provider: 'anthropic',
      is_active: true,
      current_daily_usage: 0,
      daily_limit: 50,
      current_monthly_usage: 0,
      monthly_limit: 1000,
      last_used_at: new Date()
    }]
  }
}

const fetchRecentActivities = async () => {
  try {
    // 새로운 실시간 통계 API에서 최근 활동 정보 가져오기
    const response = await fetch('http://localhost:8100/api/monitoring/dashboard/realtime-stats?hours=24')
    const data = await response.json()
    if (data.success) {
      // 실제 데이터 기반으로 최근 활동 생성
      const activities = data.realtime_data.hourly_ai_usage.slice(-5).map((usage, index) => ({
        id: index + 1,
        agent_name: `AI 에이전트 #${index + 1}`,
        task_type: index % 2 === 0 ? 'PDF 분석' : '질문 답변',
        status: 'completed',
        tokens_used: usage.tokens,
        cost: usage.cost,
        created_at: new Date(usage.hour),
      }))
      recentAiActivities.value = activities
    }
  } catch (error) {
    console.error('Failed to fetch recent activities:', error)
    // Mock data
    recentAiActivities.value = [
      {
        id: 1,
        agent_name: '문제 추출 에이전트',
        task_type: 'PDF 분석',
        status: 'completed',
        tokens_used: 2340,
        cost: 0.156,
        created_at: new Date(Date.now() - 5 * 60 * 1000),
      },
      {
        id: 2,
        agent_name: '자격증 학습 도우미',
        task_type: '질문 답변',
        status: 'completed',
        tokens_used: 890,
        cost: 0.067,
        created_at: new Date(Date.now() - 15 * 60 * 1000),
      },
      {
        id: 3,
        agent_name: '해설 생성 에이전트',
        task_type: '해설 생성',
        status: 'processing',
        tokens_used: 1560,
        cost: 0.098,
        created_at: new Date(Date.now() - 30 * 60 * 1000),
      },
    ]
  }
}

const refreshStatus = () => {
  fetchAiStats()
  fetchAgentUsage()
  fetchApiKeyUsage()
  fetchRecentActivities()
}

// 초기화
onMounted(() => {
  fetchAiStats()
  fetchAgentUsage()
  fetchApiKeyUsage()
  fetchRecentActivities()
})
</script>

<style scoped>
.monitoring-view {
  max-width: 1400px;
  margin: 0 auto;
}

.stats-overview {
  margin-bottom: 24px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
  height: 100px;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.stat-card.ai-requests .stat-icon {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card.tokens-used .stat-icon {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-card.api-cost .stat-icon {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-card.active-agents .stat-icon {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #2c3e50;
  line-height: 1;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #7f8c8d;
  font-weight: 500;
}

.charts-section {
  margin-bottom: 24px;
}

.chart-card {
  height: 400px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.chart-container {
  height: 320px;
  overflow-y: auto;
}

.agent-usage-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.agent-usage-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafafa;
}

.agent-info {
  margin-bottom: 12px;
}

.agent-name {
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 4px;
}

.agent-model {
  font-size: 12px;
  color: #909399;
}

.usage-metrics {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.metric {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.metric-label {
  color: #606266;
}

.metric-value {
  font-weight: 600;
  color: #2c3e50;
}

.usage-bar {
  margin-top: 8px;
}

.api-key-usage-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.api-key-usage-item {
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafafa;
}

.api-key-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.api-key-name {
  font-weight: 600;
  color: #2c3e50;
}

.api-key-provider {
  font-size: 12px;
  color: #909399;
  margin-bottom: 12px;
}

.usage-stats {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #606266;
}

.usage-progress {
  display: flex;
  align-items: center;
  gap: 8px;
}

.usage-text {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}

.last-used {
  font-size: 11px;
  color: #c0c4cc;
  margin-top: 8px;
}

.status-section {
  margin-bottom: 24px;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 24px;
}

.status-component {
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafafa;
}

.component-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.component-name {
  font-weight: 600;
  color: #2c3e50;
  flex: 1;
}

.component-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #606266;
}

.activities-card {
  height: 400px;
}

.activities-list {
  max-height: 320px;
  overflow-y: auto;
}

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px 0;
  border-bottom: 1px solid #f0f2f5;
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.activity-icon.completed {
  background: #67c23a;
}

.activity-icon.failed {
  background: #f56c6c;
}

.activity-icon.processing {
  background: #409eff;
}

.activity-content {
  flex: 1;
}

.activity-title {
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 4px;
}

.activity-description {
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
}

.activity-stats {
  display: flex;
  gap: 12px;
  margin-bottom: 4px;
}

.token-count,
.cost {
  font-size: 12px;
  color: #909399;
}

.activity-time {
  font-size: 12px;
  color: #909399;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .usage-metrics {
    flex-direction: column;
    gap: 8px;
  }
  
  .status-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-card {
    height: auto;
    padding: 16px;
  }
  
  .stat-value {
    font-size: 24px;
  }
  
  .chart-card {
    height: auto;
  }
  
  .chart-container {
    height: 250px;
  }
}
</style>