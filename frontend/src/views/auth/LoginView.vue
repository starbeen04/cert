<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1 class="login-title">CertFast Admin</h1>
        <p class="login-subtitle">Sign in to your account</p>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="Username or Email"
            size="large"
            :prefix-icon="User"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="Password"
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="rememberMe" class="remember-me">
            로그인 유지
          </el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="authStore.isLoading"
            @click="handleLogin"
            native-type="button"
          >
            {{ authStore.isLoading ? 'Signing in...' : 'Sign In' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <p class="footer-text">
          © 2024 CertFast. All rights reserved.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import type { LoginCredentials } from '@/types'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// Form ref
const loginFormRef = ref<FormInstance>()

// Form data
const loginForm = reactive<LoginCredentials>({
  username: '',
  password: '',
})

// Remember me
const rememberMe = ref(false)

// Form validation rules
const loginRules: FormRules = {
  username: [
    { required: true, message: 'Please enter your username or email', trigger: 'blur' },
    { min: 3, message: 'Username must be at least 3 characters', trigger: 'blur' },
  ],
  password: [
    { required: true, message: 'Please enter your password', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' },
  ],
}

// Methods
const handleLogin = async (event?: Event) => {
  console.log('🔥 handleLogin called!', event)
  
  // Prevent any form submission
  if (event) {
    event.preventDefault()
    event.stopPropagation()
  }
  
  if (!loginFormRef.value) {
    console.log('❌ loginFormRef is null')
    return
  }

  try {
    // Validate form first
    const isValid = await loginFormRef.value.validate()
    if (!isValid) return
    
    console.log('🚀 Starting login process...')
    
    // Attempt login with remember me option
    await authStore.login(loginForm, rememberMe.value)
    
    console.log('✅ Login function completed')
    console.log('🔒 Auth store state after login:', {
      isAuthenticated: authStore.isAuthenticated,
      hasToken: !!authStore.token,
      hasUser: !!authStore.user,
      userRole: authStore.user?.role
    })
    
    // Save remember me preference
    if (rememberMe.value) {
      localStorage.setItem('remember_me', 'true')
      localStorage.setItem('saved_username', loginForm.username)
    } else {
      localStorage.removeItem('remember_me')
      localStorage.removeItem('saved_username')
    }
    
    ElMessage.success('로그인 성공!')
    
    // Small delay to ensure message is shown
    await new Promise(resolve => setTimeout(resolve, 100))
    
    // Redirect based on user role
    const userRole = authStore.user?.role
    let redirectTo: string
    
    if (route.query.redirect) {
      redirectTo = route.query.redirect as string
    } else if (userRole === 'admin') {
      redirectTo = '/admin'
    } else if (userRole === 'instructor') {
      redirectTo = '/instructor'
    } else {
      redirectTo = '/student'
    }
    
    console.log('Redirecting to:', redirectTo)
    await router.push(redirectTo)
    
  } catch (error: any) {
    console.error('Login failed:', error)
    
    // Show specific error message based on response
    let errorMessage = 'Login failed. Please try again.'
    
    if (error.response) {
      // Server responded with error status
      const status = error.response.status
      const data = error.response.data
      
      console.log('Error response:', { status, data }) // Debug log
      
      if (status === 401) {
        errorMessage = '아이디 또는 비밀번호가 올바르지 않습니다.'
      } else if (status === 422) {
        errorMessage = '입력 정보를 다시 확인해주세요.'
      } else if (status === 500) {
        errorMessage = '서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.'
      } else if (status === 0 || status >= 400) {
        errorMessage = '서버에 연결할 수 없습니다. 네트워크 상태를 확인해주세요.'
      } else if (data && data.detail) {
        errorMessage = data.detail
      }
    } else if (error.request) {
      // Request made but no response received
      errorMessage = '서버에 연결할 수 없습니다. 네트워크 상태를 확인해주세요.'
    } else if (error.message) {
      errorMessage = error.message
    }
    
    // Show error message with longer duration to prevent disappearing
    ElMessage({
      message: errorMessage,
      type: 'error',
      duration: 0, // Don't auto-close
      showClose: true
    })
    
    // Also log to console for debugging
    console.error('Detailed error info:', {
      error,
      response: error?.response,
      status: error?.response?.status,
      data: error?.response?.data
    })
  }
}

// Load saved login data
onMounted(() => {
  const savedRememberMe = localStorage.getItem('remember_me')
  const savedUsername = localStorage.getItem('saved_username')
  
  if (savedRememberMe === 'true' && savedUsername) {
    rememberMe.value = true
    loginForm.username = savedUsername
  }
})
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
  position: relative;
  overflow: hidden;
}

.login-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-title {
  font-size: 28px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 8px 0;
}

.login-subtitle {
  font-size: 16px;
  color: #7f8c8d;
  margin: 0;
}

.login-form {
  margin-bottom: 24px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 20px;
}

.login-form :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.remember-me {
  width: 100%;
}

.login-button {
  width: 100%;
  height: 48px;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: transform 0.2s, box-shadow 0.2s;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.login-button:active {
  transform: translateY(0);
}

.login-footer {
  text-align: center;
  margin-top: 24px;
}

.footer-text {
  font-size: 14px;
  color: #95a5a6;
  margin: 0;
}

/* Responsive design */
@media (max-width: 480px) {
  .login-container {
    padding: 16px;
  }
  
  .login-card {
    padding: 24px;
  }
  
  .login-title {
    font-size: 24px;
  }
}

/* Animation for card entrance */
@keyframes slideInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-card {
  animation: slideInUp 0.6s ease-out;
}
</style>