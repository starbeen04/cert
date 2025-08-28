import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Certificate, CertificateCreate, CertificateUpdate, PaginatedResponse } from '@/types'
import apiService from '@/services/api'

export const useCertificatesStore = defineStore('certificates', () => {
  // State
  const certificates = ref<Certificate[]>([])
  const currentCertificate = ref<Certificate | null>(null)
  const isLoading = ref(false)
  const isUploading = ref(false)
  const uploadProgress = ref(0)
  const totalCertificates = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(20)

  // Actions
  const fetchCertificates = async (page = 1, size = 20, search?: string): Promise<void> => {
    try {
      isLoading.value = true
      
      // 실제 백엔드 API 사용
      const response = await fetch('http://localhost:8100/api/admin/certificates/list')
      const data = await response.json()
      
      if (data.success) {
        // title 필드를 name으로 매핑하고 등록자 정보 추가
        const mappedCertificates = (data.certificates || []).map(cert => ({
          ...cert,
          name: cert.title, // title -> name 매핑
          is_active: cert.status === 'active',
          user: {
            id: 1,
            username: 'admin',
            full_name: 'Administrator'
          }
        }))
        
        certificates.value = mappedCertificates
        totalCertificates.value = mappedCertificates.length
        currentPage.value = page
        pageSize.value = size
      } else {
        throw new Error(data.error || 'Failed to fetch certificates')
      }
    } catch (error) {
      console.error('Failed to fetch certificates:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  const fetchCertificate = async (certificateId: number): Promise<Certificate> => {
    try {
      const certificate = await apiService.get<Certificate>(`/api/certificates/${certificateId}`)
      currentCertificate.value = certificate
      return certificate
    } catch (error) {
      console.error('Failed to fetch certificate:', error)
      throw error
    }
  }

  const uploadCertificate = async (file: File, uploadData: any): Promise<any> => {
    try {
      isUploading.value = true
      uploadProgress.value = 0

      // Create FormData for file upload
      const formData = new FormData()
console.log("Creating FormData with file:", file);      console.log("File type:", typeof file);      console.log("File name:", file?.name);      console.log("File size:", file?.size);
      formData.append('file', file)
      formData.append('name', uploadData.name)
      formData.append('certificate_id', uploadData.certificate_id.toString())
      formData.append('file_type', uploadData.file_type)
      if (uploadData.description) {
        formData.append('description', uploadData.description)
console.log("FormData contents:");      for (let [key, value] of formData.entries()) {        console.log(key, value);      }
      }

// Use apiService for proper base URL and headers
      const result = await apiService.post("/api/upload/pdf", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        onUploadProgress: (progressEvent: any) => {
          if (progressEvent.total) {
            uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          }
        }
      })
      
      uploadProgress.value = 100
      return result
    } catch (error) {
      console.error("Failed to upload certificate:", error);
      console.error("Error details:", error.response?.data);
      console.error("Error status:", error.response?.status);
      console.error("Error message:", error.message);
      throw error
    } finally {
      isUploading.value = false
      uploadProgress.value = 0
    }
  }

  const updateCertificate = async (certificateId: number, data: CertificateUpdate): Promise<Certificate> => {
    try {
      const updatedCertificate = await apiService.put<Certificate>(`/api/certificates/${certificateId}`, data)
      
      const index = certificates.value.findIndex(c => c.id === certificateId)
      if (index !== -1) {
        certificates.value[index] = updatedCertificate
      }
      
      if (currentCertificate.value?.id === certificateId) {
        currentCertificate.value = updatedCertificate
      }
      
      return updatedCertificate
    } catch (error) {
      console.error('Failed to update certificate:', error)
      throw error
    }
  }

  const deleteCertificate = async (certificateId: number): Promise<void> => {
    try {
      await apiService.delete(`/api/certificates/${certificateId}`)
      
      certificates.value = certificates.value.filter(c => c.id !== certificateId)
      totalCertificates.value -= 1
      
      if (currentCertificate.value?.id === certificateId) {
        currentCertificate.value = null
      }
    } catch (error) {
      console.error('Failed to delete certificate:', error)
      throw error
    }
  }

  const processCertificate = async (certificateId: number): Promise<void> => {
    try {
      await apiService.post(`/api/certificates/${certificateId}/process`)
      
      // Refresh the certificate data
      await fetchCertificate(certificateId)
    } catch (error) {
      console.error('Failed to process certificate:', error)
      throw error
    }
  }

  const downloadCertificate = async (certificateId: number): Promise<void> => {
    try {
      const response = await apiService.get(`/api/certificates/${certificateId}/download`, {
        responseType: 'blob',
      })
      
      // Create download link
      const blob = new Blob([response])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      
      // Get certificate name for filename
      const certificate = certificates.value.find(c => c.id === certificateId)
      link.download = certificate?.name || `certificate-${certificateId}.pdf`
      
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Failed to download certificate:', error)
      throw error
    }
  }

  const clearCurrentCertificate = (): void => {
    currentCertificate.value = null
  }

  const fetchUploadedFiles = async (): Promise<any[]> => {
    try {
      const response = await apiService.get<{files: any[], total: number}>('/api/upload/files')
      return response.files
    } catch (error) {
      console.error('Failed to fetch uploaded files:', error)
      throw error
    }
  }

  const fetchCertificatesInfo = async (): Promise<any[]> => {
    try {
      // 실제 백엔드 API 사용
      const response = await fetch('http://localhost:8100/api/admin/certificates/list')
      const data = await response.json()
      
      if (data.success) {
        return data.certificates || []
      } else {
        throw new Error(data.error || 'Failed to fetch certificates info')
      }
    } catch (error) {
      console.error('Failed to fetch certificates info:', error)
      throw error
    }
  }

  const createCertificate = async (certificateData: {
    title: string;
    description?: string;
    issuer?: string;
    category?: string;
    difficulty_level?: string;
    exam_duration_minutes?: number;
    passing_score?: number;
    tags?: string[];
  }): Promise<any> => {
    try {
      const response = await apiService.post('/api/certificates/admin/create', certificateData)
      
      // 생성 후 목록을 새로고침
      await fetchCertificates(currentPage.value, pageSize.value)
      
      return response
    } catch (error) {
      console.error('Failed to create certificate:', error)
      throw error
    }
  }

  const updateCertificateAdmin = async (certificateId: number, updateData: any): Promise<any> => {
    try {
      const response = await apiService.put(`/api/certificates/admin/${certificateId}/update`, updateData)
      
      // 업데이트 후 목록을 새로고침
      await fetchCertificates(currentPage.value, pageSize.value)
      
      return response
    } catch (error) {
      console.error('Failed to update certificate:', error)
      throw error
    }
  }

  const deleteCertificateAdmin = async (certificateId: number): Promise<any> => {
    try {
      const response = await apiService.delete(`/api/certificates/admin/${certificateId}/delete`)
      
      // 삭제 후 목록을 새로고침
      await fetchCertificates(currentPage.value, pageSize.value)
      
      return response
    } catch (error) {
      console.error('Failed to delete certificate:', error)
      throw error
    }
  }

  const getCertificateStats = async (): Promise<any> => {
    try {
      const response = await apiService.get('/api/certificates/admin/stats')
      return response
    } catch (error) {
      console.error('Failed to fetch certificate stats:', error)
      throw error
    }
  }

  return {
    // State
    certificates: readonly(certificates),
    currentCertificate: readonly(currentCertificate),
    isLoading: readonly(isLoading),
    isUploading: readonly(isUploading),
    uploadProgress: readonly(uploadProgress),
    totalCertificates: readonly(totalCertificates),
    currentPage: readonly(currentPage),
    pageSize: readonly(pageSize),
    
    // Actions
    fetchCertificates,
    fetchCertificate,
    uploadCertificate,
    updateCertificate,
    deleteCertificate,
    processCertificate,
    downloadCertificate,
    clearCurrentCertificate,
    fetchUploadedFiles,
    fetchCertificatesInfo,
    // New admin functions
    createCertificate,
    updateCertificateAdmin,
    deleteCertificateAdmin,
    getCertificateStats,
  }
})