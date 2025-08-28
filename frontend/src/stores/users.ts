import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { User, UserCreate, UserUpdate, PaginatedResponse } from '@/types'
import apiService from '@/services/api'

export const useUsersStore = defineStore('users', () => {
  // State
  const users = ref<User[]>([])
  const currentUser = ref<User | null>(null)
  const isLoading = ref(false)
  const totalUsers = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)

  // Actions
  const fetchUsers = async (page = 1, size = 20, search?: string): Promise<void> => {
    try {
      isLoading.value = true
      const params = new URLSearchParams({
        skip: ((page - 1) * size).toString(),
        limit: size.toString(),
      })
      
      if (search) {
        params.append('search', search)
      }

      const response = await apiService.get<{users: User[], total: number, skip: number, limit: number}>(`/api/users?${params}`)
      
      users.value = response.users
      totalUsers.value = response.total
      currentPage.value = page
      pageSize.value = size
    } catch (error) {
      console.error('Failed to fetch users:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const fetchUser = async (userId: number): Promise<User> => {
    try {
      const user = await apiService.get<User>(`/api/users/${userId}`)
      currentUser.value = user
      return user
    } catch (error) {
      console.error('Failed to fetch user:', error)
      throw error
    }
  }

  const createUser = async (userData: UserCreate): Promise<User> => {
    try {
      const response = await apiService.post<{success: boolean, user: User, message: string}>('/api/users', userData)
      if (response.success && response.user) {
        users.value.unshift(response.user)
        totalUsers.value += 1
        return response.user
      } else {
        throw new Error(response.message || 'Failed to create user')
      }
    } catch (error) {
      console.error('Failed to create user:', error)
      throw error
    }
  }

  const updateUser = async (userId: number, userData: UserUpdate): Promise<User> => {
    try {
      const response = await apiService.put<{success: boolean, user: User, message: string}>(`/api/users/${userId}`, userData)
      if (response.success && response.user) {
        // Update users list
        const index = users.value.findIndex(u => u.id === userId)
        if (index !== -1) {
          users.value[index] = response.user
        }
        
        // Update current user if it's the same user
        if (currentUser.value?.id === userId) {
          currentUser.value = response.user
        }
        
        return response.user
      } else {
        throw new Error(response.message || 'Failed to update user')
      }
    } catch (error) {
      console.error('Failed to update user:', error)
      // Re-throw the error with more context
      const errorMessage = error?.response?.data?.detail || error?.response?.data?.message || error?.message || 'Failed to update user'
      throw new Error(errorMessage)
    }
  }

  const deleteUser = async (userId: number): Promise<void> => {
    try {
      const response = await apiService.delete<{success: boolean, message: string}>(`/api/users/${userId}`)
      if (response.success) {
        users.value = users.value.filter(u => u.id !== userId)
        totalUsers.value -= 1
        
        if (currentUser.value?.id === userId) {
          currentUser.value = null
        }
      } else {
        throw new Error(response.message || 'Failed to delete user')
      }
    } catch (error) {
      console.error('Failed to delete user:', error)
      throw error
    }
  }

  const toggleUserStatus = async (userId: number): Promise<User> => {
    try {
      const response = await apiService.patch<{success: boolean, user: User, message: string}>(`/api/users/${userId}/toggle-status`)
      if (response.success && response.user) {
        const index = users.value.findIndex(u => u.id === userId)
        if (index !== -1) {
          users.value[index] = response.user
        }
        
        if (currentUser.value?.id === userId) {
          currentUser.value = response.user
        }
        
        return response.user
      } else {
        throw new Error(response.message || 'Failed to toggle user status')
      }
    } catch (error) {
      console.error('Failed to toggle user status:', error)
      throw error
    }
  }

  const clearCurrentUser = (): void => {
    currentUser.value = null
  }

  return {
    // State
    users: readonly(users),
    currentUser,
    isLoading: readonly(isLoading),
    totalUsers: readonly(totalUsers),
    currentPage: readonly(currentPage),
    pageSize: readonly(pageSize),
    
    // Actions
    fetchUsers,
    fetchUser,
    createUser,
    updateUser,
    deleteUser,
    toggleUserStatus,
    clearCurrentUser,
  }
})