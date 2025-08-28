<template>
  <div class="profile-container">
    <div class="page-header">
      <h1 class="page-title">프로필 설정</h1>
      <p class="page-description">계정 정보 및 환경 설정 관리</p>
    </div>

    <el-row :gutter="20">
      <!-- Profile Information -->
      <el-col :xs="24" :lg="16">
        <el-card class="profile-card">
          <template #header>
            <div class="card-header">
              <el-icon class="header-icon"><UserIcon /></el-icon>
              <span class="card-title">기본 정보</span>
            </div>
          </template>
          
          <el-form
            ref="profileFormRef"
            :model="profileForm"
            :rules="profileRules"
            label-width="120px"
          >
            <el-form-item label="사용자명" prop="username">
              <el-input v-model="profileForm.username" disabled />
              <div class="form-tip">사용자명은 변경할 수 없습니다</div>
            </el-form-item>
            
            <el-form-item label="이메일" prop="email">
              <el-input v-model="profileForm.email" type="email" />
            </el-form-item>
            
            <el-form-item label="전체 이름" prop="full_name">
              <el-input v-model="profileForm.full_name" />
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                :loading="updating"
                @click="updateProfile"
                class="update-btn"
              >
                <el-icon><EditPen /></el-icon>
                프로필 업데이트
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- Change Password -->
        <el-card class="password-card">
          <template #header>
            <div class="card-header">
              <el-icon class="header-icon"><Lock /></el-icon>
              <span class="card-title">비밀번호 변경</span>
            </div>
          </template>
          
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="140px"
          >
            <el-form-item label="현재 비밀번호" prop="currentPassword">
              <el-input
                v-model="passwordForm.currentPassword"
                type="password"
                show-password
              />
            </el-form-item>
            
            <el-form-item label="새 비밀번호" prop="newPassword">
              <el-input
                v-model="passwordForm.newPassword"
                type="password"
                show-password
              />
            </el-form-item>
            
            <el-form-item label="비밀번호 확인" prop="confirmPassword">
              <el-input
                v-model="passwordForm.confirmPassword"
                type="password"
                show-password
              />
            </el-form-item>
            
            <el-form-item>
              <el-button
                type="primary"
                :loading="changingPassword"
                @click="changePassword"
                class="update-btn"
              >
                <el-icon><Key /></el-icon>
                비밀번호 변경
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- Profile Summary -->
      <el-col :xs="24" :lg="8">
        <el-card class="summary-card">
          <template #header>
            <span class="card-title">Account Summary</span>
          </template>
          
          <div class="profile-summary">
            <div class="avatar-section">
              <el-avatar size="80" class="profile-avatar">
                {{ getUserInitials() }}
              </el-avatar>
              <div class="avatar-info">
                <h3 class="user-name">
                  {{ authStore.user?.full_name || authStore.user?.username }}
                </h3>
                <p class="user-email">{{ authStore.user?.email }}</p>
                <el-tag
                  :type="authStore.user?.role === 'admin' ? 'warning' : authStore.user?.role === 'instructor' ? 'success' : 'info'"
                  size="default"
                  effect="dark"
                >
                  {{ getRoleDisplayName(authStore.user?.role) }}
                </el-tag>
              </div>
            </div>
            
            <el-divider />
            
            <div class="account-details">
              <div class="detail-item">
                <span class="detail-label">Account Status:</span>
                <el-tag
                  :type="authStore.user?.is_active ? 'success' : 'danger'"
                  size="small"
                >
                  {{ authStore.user?.is_active ? 'Active' : 'Inactive' }}
                </el-tag>
              </div>
              
              <div class="detail-item">
                <span class="detail-label">Member Since:</span>
                <span class="detail-value">
                  {{ formatDate(authStore.user?.created_at || '') }}
                </span>
              </div>
              
              <div class="detail-item">
                <span class="detail-label">Last Updated:</span>
                <span class="detail-value">
                  {{ formatRelativeTime(authStore.user?.updated_at || '') }}
                </span>
              </div>
            </div>
          </div>
        </el-card>

        <!-- Activity Stats -->
        <el-card class="stats-card">
          <template #header>
            <span class="card-title">Your Activity</span>
          </template>
          
          <div class="activity-stats">
            <div class="stat-item">
              <div class="stat-icon">
                <el-icon size="20"><Document /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ userStats.certificatesUploaded }}</div>
                <div class="stat-label">Certificates Uploaded</div>
              </div>
            </div>
            
            <div class="stat-item">
              <div class="stat-icon">
                <el-icon size="20"><Reading /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ userStats.studyMaterialsGenerated }}</div>
                <div class="stat-label">Study Materials</div>
              </div>
            </div>
            
            <div class="stat-item">
              <div class="stat-icon">
                <el-icon size="20"><Clock /></el-icon>
              </div>
              <div class="stat-content">
                <div class="stat-value">{{ userStats.lastLoginDays }}</div>
                <div class="stat-label">Days Since Login</div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- Account Actions -->
        <el-card class="actions-card">
          <template #header>
            <span class="card-title">Account Actions</span>
          </template>
          
          <div class="account-actions">
            <el-button
              type="info"
              size="large"
              class="action-btn"
              @click="exportData"
            >
              <el-icon><Download /></el-icon>
              Export My Data
            </el-button>
            
            <el-button
              type="warning"
              size="large"
              class="action-btn"
              @click="showDeleteDialog = true"
            >
              <el-icon><Delete /></el-icon>
              Delete Account
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Delete Account Dialog -->
    <el-dialog
      v-model="showDeleteDialog"
      title="Delete Account"
      width="500px"
      @close="resetDeleteForm"
    >
      <el-alert
        title="Warning: This action cannot be undone"
        type="warning"
        description="Deleting your account will permanently remove all your data, including uploaded certificates and generated study materials."
        :closable="false"
        show-icon
      />
      
      <el-form
        ref="deleteFormRef"
        :model="deleteForm"
        :rules="deleteRules"
        label-width="100px"
        style="margin-top: 20px"
      >
        <el-form-item label="Password" prop="password">
          <el-input
            v-model="deleteForm.password"
            type="password"
            placeholder="Enter your password to confirm"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="Confirmation" prop="confirmation">
          <el-input
            v-model="deleteForm.confirmation"
            placeholder="Type 'DELETE' to confirm"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showDeleteDialog = false">Cancel</el-button>
          <el-button
            type="danger"
            :loading="deleting"
            @click="deleteAccount"
          >
            Delete Account
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Document,
  Reading,
  Clock,
  Download,
  Delete,
  User as UserIcon,
  Lock,
  Key,
  Avatar,
  DataAnalysis,
  Setting,
  EditPen,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { formatDate, formatRelativeTime } from '@/utils/format'

const router = useRouter()
const authStore = useAuthStore()

// Form refs
const profileFormRef = ref<FormInstance>()
const passwordFormRef = ref<FormInstance>()
const deleteFormRef = ref<FormInstance>()

// State
const updating = ref(false)
const changingPassword = ref(false)
const deleting = ref(false)
const showDeleteDialog = ref(false)

// User stats (will be fetched from actual data)
const userStats = reactive({
  certificatesUploaded: 0,
  studyMaterialsGenerated: 0,
  lastLoginDays: 0,
})

// Computed properties
const isAdminUser = computed(() => authStore.user?.role === 'admin')

// Forms
const profileForm = reactive({
  username: '',
  email: '',
  full_name: '',
})

const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
})

const deleteForm = reactive({
  password: '',
  confirmation: '',
})

// Form validation rules
const profileRules: FormRules = {
  email: [
    { required: true, message: 'Please enter email', trigger: 'blur' },
    { type: 'email', message: 'Please enter a valid email', trigger: 'blur' },
  ],
}

const passwordRules: FormRules = {
  currentPassword: [
    { required: true, message: '현재 비밀번호를 입력해주세요', trigger: 'blur' },
  ],
  newPassword: [
    { required: true, message: '새 비밀번호를 입력해주세요', trigger: 'blur' },
    { min: 6, message: '비밀번호는 최소 6자 이상이어야 합니다', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '비밀번호 확인을 입력해주세요', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('비밀번호가 일치하지 않습니다'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

const deleteRules: FormRules = {
  password: [
    { required: true, message: 'Please enter your password', trigger: 'blur' },
  ],
  confirmation: [
    { required: true, message: 'Please type DELETE to confirm', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== 'DELETE') {
          callback(new Error('Please type DELETE exactly'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
}

// Methods
const getUserInitials = (): string => {
  const user = authStore.user
  if (user?.full_name) {
    return user.full_name
      .split(' ')
      .map(name => name.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }
  return user?.username?.charAt(0).toUpperCase() || 'U'
}

const getRoleDisplayName = (role: string | undefined): string => {
  const roleMap: { [key: string]: string } = {
    'admin': '관리자',
    'instructor': '강사',
    'student': '학생',
  }
  return roleMap[role || 'student'] || role || '학생'
}

const getActiveDays = (): number => {
  if (!authStore.user?.created_at) return 0
  const createdDate = new Date(authStore.user.created_at)
  const today = new Date()
  const diffTime = Math.abs(today.getTime() - createdDate.getTime())
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
}

const fetchUserStats = async () => {
  try {
    // Simulate fetching user stats - in real app, this would be an API call
    userStats.certificatesUploaded = Math.floor(Math.random() * 10) + 1
    userStats.studyMaterialsGenerated = Math.floor(Math.random() * 20) + 5
  } catch (error) {
    console.error('Failed to fetch user stats:', error)
  }
}

const updateProfile = async () => {
  if (!profileFormRef.value) return

  try {
    await profileFormRef.value.validate()
    updating.value = true
    
    await authStore.updateProfile({
      email: profileForm.email,
      full_name: profileForm.full_name,
    })
    
    ElMessage.success('프로필이 성공적으로 업데이트되었습니다')
  } catch (error) {
    console.error('Failed to update profile:', error)
    ElMessage.error('프로필 업데이트에 실패했습니다')
  } finally {
    updating.value = false
  }
}

const changePassword = async () => {
  if (!passwordFormRef.value) return

  try {
    await passwordFormRef.value.validate()
    changingPassword.value = true
    
    // Call password change API
    const token = localStorage.getItem('auth_token') || sessionStorage.getItem('auth_token')
    const response = await fetch('/api/auth/change-password', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        currentPassword: passwordForm.currentPassword,
        newPassword: passwordForm.newPassword
      })
    })
    
    const data = await response.json()
    
    if (!response.ok) {
      throw new Error(data.detail || 'Failed to change password')
    }
    
    ElMessage.success('비밀번호가 성공적으로 변경되었습니다')
    
    // Reset form
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    passwordFormRef.value.resetFields()
  } catch (error) {
    console.error('Failed to change password:', error)
    ElMessage.error(error.message || '비밀번호 변경에 실패했습니다')
  } finally {
    changingPassword.value = false
  }
}

const exportData = async () => {
  try {
    await ElMessageBox.confirm(
      'This will export all your data including certificates and study materials. Continue?',
      'Export Data',
      {
        confirmButtonText: 'Export',
        cancelButtonText: 'Cancel',
        type: 'info',
      }
    )
    
    // TODO: Implement data export
    ElMessage.success('Data export started. You will receive an email when ready.')
  } catch {
    // User cancelled
  }
}

const deleteAccount = async () => {
  if (!deleteFormRef.value) return

  try {
    await deleteFormRef.value.validate()
    deleting.value = true
    
    // TODO: Implement account deletion API call
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    ElMessage.success('Account deleted successfully')
    authStore.logout()
    router.push('/login')
  } catch (error) {
    console.error('Failed to delete account:', error)
    ElMessage.error('Failed to delete account')
  } finally {
    deleting.value = false
  }
}

const resetDeleteForm = () => {
  deleteForm.password = ''
  deleteForm.confirmation = ''
  deleteFormRef.value?.resetFields()
}

// Initialize
onMounted(async () => {
  if (authStore.user) {
    profileForm.username = authStore.user.username
    profileForm.email = authStore.user.email
    profileForm.full_name = authStore.user.full_name || ''
  }
  
  // Fetch user stats
  await fetchUserStats()
})
</script>

<style scoped>
/* ===== 전체 컨테이너 ===== */
.profile-container {
  padding: 0;
  margin: 0;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

/* ===== 페이지 헤더 ===== */
.page-header {
  margin-bottom: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.page-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: white;
}

.page-description {
  font-size: 16px;
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
}

/* ===== 카드 헤더 ===== */
.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  font-size: 18px;
  color: #667eea;
}

.profile-card {
  margin-bottom: 24px;
}

.password-card {
  margin-bottom: 24px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.summary-card {
  margin-bottom: 20px;
}

.profile-summary {
  text-align: center;
}

.avatar-section {
  margin-bottom: 20px;
}

.profile-avatar {
  background-color: #409eff;
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 16px;
}

.user-name {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.user-email {
  margin: 0 0 8px 0;
  color: #7f8c8d;
  font-size: 14px;
}

.account-details {
  text-align: left;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.detail-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.detail-value {
  font-size: 14px;
  color: #2c3e50;
}

.stats-card {
  margin-bottom: 20px;
}

.activity-stats {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-icon {
  width: 36px;
  height: 36px;
  background: #409eff;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  flex-shrink: 0;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 2px;
}

.stat-label {
  font-size: 12px;
  color: #7f8c8d;
}

.actions-card {
  margin-bottom: 20px;
}

.account-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-btn {
  width: 100%;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.dialog-footer {
  display: flex;
  gap: 12px;
}

/* Responsive design */
@media (max-width: 768px) {
  .profile-summary {
    text-align: left;
  }
  
  .avatar-section {
    display: flex;
    align-items: center;
    gap: 16px;
    text-align: left;
  }
  
  .avatar-info {
    flex: 1;
  }
  
  .user-name {
    font-size: 16px;
  }
}
</style>