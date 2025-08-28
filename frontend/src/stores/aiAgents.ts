import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { AIAgent, AIAgentCreate, AIAgentUpdate, PaginatedResponse } from '@/types'
import apiService from '@/services/api'

export const useAIAgentsStore = defineStore('aiAgents', () => {
  // State
  const aiAgents = ref<AIAgent[]>([])
  const currentAgent = ref<AIAgent | null>(null)
  const isLoading = ref(false)
  const totalAgents = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)

  // Actions
  const fetchAIAgents = async (page = 1, size = 20, search?: string): Promise<void> => {
    try {
      isLoading.value = true
      
      // 실제 백엔드 API 사용
      const response = await fetch('/api/admin/usage-stats')
      const data = await response.json()
      
      if (data.success) {
        // AI 에이전트 데이터 매핑
        aiAgents.value = data.ai_agents.details || []
        totalAgents.value = data.ai_agents.total || 0
        currentPage.value = page
        pageSize.value = size
      } else {
        throw new Error(data.error || 'Failed to fetch AI agents')
      }
    } catch (error) {
      console.error('Failed to fetch AI agents:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const fetchAIAgent = async (agentId: number): Promise<AIAgent> => {
    try {
      // 새로운 AI 에이전트 상세 조회 API
      const agent = await apiService.get<AIAgent>(`/api/ai-agents/${agentId}`)
      currentAgent.value = agent
      return agent
    } catch (error) {
      console.error('Failed to fetch AI agent:', error)
      throw error
    }
  }

  const createAIAgent = async (agentData: AIAgentCreate): Promise<any> => {
    try {
      // 실제 백엔드 API 사용
      const response = await fetch('/api/admin/ai-agents', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(agentData)
      })
      
      const data = await response.json()
      
      if (data.success) {
        // 생성 후 목록을 새로고침
        await fetchAIAgents(currentPage.value, pageSize.value)
        return data
      } else {
        throw new Error(data.error || 'Failed to create AI agent')
      }
    } catch (error) {
      console.error('Failed to create AI agent:', error)
      throw error
    }
  }

  const updateAIAgent = async (agentId: number, agentData: AIAgentUpdate): Promise<any> => {
    try {
      // 실제 백엔드 API 사용
      const response = await fetch(`/api/admin/ai-agents/${agentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(agentData)
      })
      
      const data = await response.json()
      
      if (data.success) {
        // 업데이트 후 목록을 새로고침
        await fetchAIAgents(currentPage.value, pageSize.value)
        return data
      } else {
        throw new Error(data.error || 'Failed to update AI agent')
      }
    } catch (error) {
      console.error('Failed to update AI agent:', error)
      throw error
    }
  }

  const deleteAIAgent = async (agentId: number): Promise<any> => {
    try {
      // 실제 백엔드 API 사용
      const response = await fetch(`/api/admin/ai-agents/${agentId}`, {
        method: 'DELETE'
      })
      
      const data = await response.json()
      
      if (data.success) {
        // 삭제 후 목록을 새로고침
        await fetchAIAgents(currentPage.value, pageSize.value)
        return data
      } else {
        throw new Error(data.error || 'Failed to delete AI agent')
      }
    } catch (error) {
      console.error('Failed to delete AI agent:', error)
      throw error
    }
  }

  const toggleAgentStatus = async (agentId: number): Promise<AIAgent> => {
    const agent = aiAgents.value.find(a => a.id === agentId)
    if (!agent) {
      throw new Error('AI agent not found')
    }

    return updateAIAgent(agentId, { is_active: !agent.is_active })
  }

  const testAIAgent = async (agentId: number, prompt: string): Promise<string> => {
    try {
      const response = await apiService.post<{ response: string }>(`/api/ai-management/agents/${agentId}/test`, {
        prompt,
      })
      return response.response
    } catch (error) {
      console.error('Failed to test AI agent:', error)
      throw error
    }
  }

  const clearCurrentAgent = (): void => {
    currentAgent.value = null
  }

  const getAvailableModels = async (): Promise<string[]> => {
    try {
      // 실제 백엔드 API에서 사용 가능한 모델 목록을 가져오거나 기본값 반환
      return [
        'claude-3-5-sonnet-20241022',
        'claude-3-5-haiku-20241022', 
        'claude-3-opus-20240229',
        'gpt-4o',
        'gpt-4o-mini',
        'gpt-3.5-turbo'
      ]
    } catch (error) {
      console.error('Failed to fetch available models:', error)
      // Return default models if API fails
      return ['claude-3-5-sonnet-20241022', 'gpt-4o']
    }
  }

  const getAgentStats = async (): Promise<any> => {
    try {
      const response = await apiService.get('/api/ai-agents/admin/stats')
      return response
    } catch (error) {
      console.error('Failed to fetch agent stats:', error)
      throw error
    }
  }

  const getAgentUsageStats = async (agentId: number, days: number = 30): Promise<any> => {
    try {
      const response = await apiService.get(`/api/ai-agents/${agentId}/usage/stats?days=${days}`)
      return response
    } catch (error) {
      console.error('Failed to fetch agent usage stats:', error)
      throw error
    }
  }

  const getUsageOverview = async (days: number = 7): Promise<any> => {
    try {
      const response = await apiService.get(`/api/ai-agents/usage/overview?days=${days}`)
      return response
    } catch (error) {
      console.error('Failed to fetch usage overview:', error)
      throw error
    }
  }

  return {
    // State
    aiAgents: readonly(aiAgents),
    currentAgent: readonly(currentAgent),
    isLoading: readonly(isLoading),
    totalAgents: readonly(totalAgents),
    currentPage: readonly(currentPage),
    pageSize: readonly(pageSize),
    
    // Actions
    fetchAIAgents,
    fetchAIAgent,
    createAIAgent,
    updateAIAgent,
    deleteAIAgent,
    toggleAgentStatus,
    testAIAgent,
    clearCurrentAgent,
    getAvailableModels,
    // New admin functions
    getAgentStats,
    getAgentUsageStats,
    getUsageOverview,
  }
})