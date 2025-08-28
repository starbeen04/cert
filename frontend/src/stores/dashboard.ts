import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { DashboardStats } from '@/types'
import apiService from '@/services/api'

export const useDashboardStore = defineStore('dashboard', () => {
  // State
  const stats = ref<DashboardStats>({
    total_users: 0,
    total_certificates: 0,
    total_study_materials: 0,
    active_ai_agents: 0,
    recent_uploads: 0,
    processing_queue: 0,
  })
  const isLoading = ref(false)
  const lastUpdated = ref<Date | null>(null)

  // Actions
  const fetchDashboardStats = async (): Promise<void> => {
    try {
      isLoading.value = true
      const response = await apiService.get<DashboardStats>('/api/dashboard/stats')
      stats.value = response
      lastUpdated.value = new Date()
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const refreshStats = async (): Promise<void> => {
    await fetchDashboardStats()
  }

  return {
    // State
    stats: readonly(stats),
    isLoading: readonly(isLoading),
    lastUpdated: readonly(lastUpdated),
    
    // Actions
    fetchDashboardStats,
    refreshStats,
  }
})