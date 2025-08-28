import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8100'

class ApiService {
  private instance: AxiosInstance

  constructor() {
    this.instance = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor
    this.instance.interceptors.request.use(
      (config) => {
        const authStore = useAuthStore()
        const token = authStore.token

        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        return config
      },
      (error) => {
        return Promise.reject(error)
      }
    )

    // Response interceptor
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => {
        return response
      },
      (error) => {
        const authStore = useAuthStore()

        if (error.response?.status === 401) {
          authStore.logout()
          ElMessage.error('Authentication expired. Please login again.')
          window.location.href = '/login'
        } else if (error.response?.status === 403) {
          ElMessage.error('Access denied.')
        } else if (error.response?.status >= 500) {
          ElMessage.error('Server error. Please try again later.')
        } else if (error.response?.data?.detail) {
          ElMessage.error(error.response.data.detail)
        } else if (error.message) {
          ElMessage.error(error.message)
        }

        return Promise.reject(error)
      }
    )
  }

  // Generic request methods
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get<T>(url, config)
    return response.data
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post<T>(url, data, config)
    return response.data
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.put<T>(url, data, config)
    return response.data
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.patch<T>(url, data, config)
    return response.data
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete<T>(url, config)
    return response.data
  }

  // File upload method
  async upload<T = any>(url: string, file: File, onProgress?: (progress: number) => void): Promise<T> {
    const formData = new FormData()
    formData.append('file', file)

    const config: AxiosRequestConfig = {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    }

    const response = await this.instance.post<T>(url, formData, config)
    return response.data
  }
}

export const apiService = new ApiService()
export default apiService