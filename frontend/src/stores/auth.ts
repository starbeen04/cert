import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { User, LoginCredentials, AuthTokens } from '@/types'
import apiService from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  // State
  const token = ref<string | null>(null)
  const user = ref<User | null>(null)
  const isLoading = ref(false)

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  // Actions
  const login = async (credentials: LoginCredentials, rememberMe: boolean = false): Promise<void> => {
    try {
      console.log('🔐 Starting login process...')
      isLoading.value = true
      
      const formData = `username=${encodeURIComponent(credentials.username)}&password=${encodeURIComponent(credentials.password)}`

      console.log('📤 Sending login request for username:', credentials.username)
      
      // First get token from /api/auth/token
      const tokenResponse = await apiService.post<{access_token: string, token_type: string}>('/api/auth/token', formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })
      
      console.log('🎟️ Token response received:', tokenResponse)

      if (!tokenResponse.access_token) {
        throw new Error('No access token received')
      }

      // Set token first
      token.value = tokenResponse.access_token
      console.log('✅ Token set in store:', !!token.value)

      // Then get user info from /api/auth/me
      console.log('👤 Fetching user info...')
      const userResponse = await apiService.get<User>('/api/auth/me')
      
      if (!userResponse) {
        throw new Error('No user data received')
      }
      
      user.value = userResponse
      console.log('👤 User data set:', userResponse)

      // Save to localStorage or sessionStorage based on rememberMe
      if (rememberMe) {
        localStorage.setItem('auth_token', tokenResponse.access_token)
        localStorage.setItem('auth_user', JSON.stringify(userResponse))
      } else {
        sessionStorage.setItem('auth_token', tokenResponse.access_token)
        sessionStorage.setItem('auth_user', JSON.stringify(userResponse))
      }
      
      console.log('💾 Data saved to localStorage')
      console.log('🎉 Login completed successfully!')
      console.log('🔒 Auth state - isAuthenticated:', isAuthenticated.value, 'user role:', user.value?.role)
    } catch (error: any) {
      console.error('Login failed:', error)
      
      // Clear any existing auth data on error
      token.value = null
      user.value = null
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
      sessionStorage.removeItem('auth_token')
      sessionStorage.removeItem('auth_user')
      
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const logout = (): void => {
    token.value = null
    user.value = null

    // Clear both localStorage and sessionStorage
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
    sessionStorage.removeItem('auth_token')
    sessionStorage.removeItem('auth_user')
  }

  const initializeAuth = (): void => {
    // Check localStorage first (remember me), then sessionStorage
    let savedToken = localStorage.getItem('auth_token')
    let savedUser = localStorage.getItem('auth_user')
    
    if (!savedToken) {
      savedToken = sessionStorage.getItem('auth_token')
      savedUser = sessionStorage.getItem('auth_user')
    }

    if (savedToken && savedUser) {
      try {
        token.value = savedToken
        user.value = JSON.parse(savedUser)
      } catch (error) {
        console.error('Failed to parse saved user data:', error)
        logout()
      }
    }
  }

  const fetchCurrentUser = async (): Promise<void> => {
    try {
      const currentUser = await apiService.get<User>('/api/auth/me')
      user.value = currentUser
      
      // Update user data in the storage where it exists
      if (localStorage.getItem('auth_token')) {
        localStorage.setItem('auth_user', JSON.stringify(currentUser))
      } else if (sessionStorage.getItem('auth_token')) {
        sessionStorage.setItem('auth_user', JSON.stringify(currentUser))
      }
    } catch (error) {
      console.error('Failed to fetch current user:', error)
      logout()
      throw error
    }
  }

  const updateProfile = async (userData: Partial<User>): Promise<void> => {
    try {
      const updatedUser = await apiService.put<User>('/api/auth/me', userData)
      user.value = updatedUser
      
      // Update user data in the storage where it exists
      if (localStorage.getItem('auth_token')) {
        localStorage.setItem('auth_user', JSON.stringify(updatedUser))
      } else if (sessionStorage.getItem('auth_token')) {
        sessionStorage.setItem('auth_user', JSON.stringify(updatedUser))
      }
    } catch (error) {
      console.error('Failed to update profile:', error)
      throw error
    }
  }

  return {
    // State (expose raw refs for API interceptor access)
    token,
    user,
    isLoading: readonly(isLoading),
    
    // Getters
    isAuthenticated,
    isAdmin,
    
    // Actions
    login,
    logout,
    initializeAuth,
    fetchCurrentUser,
    updateProfile,
  }
})