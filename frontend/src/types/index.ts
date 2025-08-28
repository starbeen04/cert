// User types
export interface User {
  id: number
  email: string
  username: string
  full_name: string
  is_active: boolean
  role: string // 'admin', 'instructor', 'student'
}

export interface UserCreate {
  email: string
  username: string
  password: string
  full_name?: string
  role?: string
}

export interface UserUpdate {
  email?: string
  username?: string
  full_name?: string
  is_active?: boolean
  role?: string
}

// Auth types
export interface LoginCredentials {
  username: string
  password: string
}

export interface AuthTokens {
  access_token: string
  token_type: string
  user: User
}

// Certificate types
export interface Certificate {
  id: number
  name: string
  description?: string
  category?: string
  difficulty_level?: string
  estimated_study_hours?: number
  is_active: boolean
  created_at: string
}

export interface CertificateCreate {
  name: string
  description?: string
}

export interface CertificateUpdate {
  name?: string
  description?: string
}

// Study Material types
export interface StudyMaterial {
  id: number
  certificate_id: number
  title: string
  content: string
  content_type: 'text' | 'question' | 'answer'
  order_index: number
  created_at: string
  updated_at: string
}

// AI Agent types
export interface AIAgent {
  id: number
  name: string
  description?: string
  model_name: string
  system_prompt: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface AIAgentCreate {
  name: string
  description?: string
  model_name: string
  system_prompt: string
  is_active?: boolean
}

export interface AIAgentUpdate {
  name?: string
  description?: string
  model_name?: string
  system_prompt?: string
  is_active?: boolean
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface ApiError {
  detail: string
}

// Dashboard Statistics
export interface DashboardStats {
  total_users: number
  total_certificates: number
  total_study_materials: number
  active_ai_agents: number
  recent_uploads: number
  processing_queue: number
}

// File upload types
export interface FileUploadProgress {
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
}

// Navigation types
export interface MenuItem {
  name: string
  path: string
  icon: string
  children?: MenuItem[]
  meta?: {
    title: string
    requiresAuth?: boolean
    roles?: string[]
  }
}