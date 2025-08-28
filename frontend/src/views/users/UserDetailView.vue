<template>
  <div class="user-detail-container">
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack" class="back-btn">돌아가기</el-button>
        <div class="header-info">
          <h1 class="page-title">사용자 상세정보</h1>
          <p class="page-description">사용자 정보 보기 및 관리</p>
        </div>
      </div>
      <div class="header-actions" v-if="!isCurrentUser(usersStore.currentUser)">
        <el-button type="primary" :icon="Edit" @click="showEditDialog = true" class="edit-btn">
          정보 수정
        </el-button>
      </div>
    </div>

    <div v-if="usersStore.currentUser" class="user-content">
      <!-- User Profile Card -->
      <el-row :gutter="24">
        <el-col :xs="24" :lg="8">
          <el-card class="profile-card">
            <div class="profile-header">
              <div class="avatar-section">
                <el-avatar :size="120" class="profile-avatar">
                  {{ getUserInitials(usersStore.currentUser) }}
                </el-avatar>
                <div class="avatar-overlay" v-if="isCurrentUser(usersStore.currentUser)">
                  <el-icon class="camera-icon"><Camera /></el-icon>
                </div>
              </div>
              <div class="profile-info">
                <h3 class="profile-name">
                  {{ usersStore.currentUser.full_name || usersStore.currentUser.username }}
                </h3>
                <p class="profile-username">@{{ usersStore.currentUser.username }}</p>
                <p class="profile-email">{{ usersStore.currentUser.email }}</p>
                <div class="profile-tags">
                  <el-tag
                    :type="usersStore.currentUser.is_active ? 'success' : 'danger'"
                    size="default"
                    effect="dark"
                  >
                    {{ usersStore.currentUser.is_active ? '활성' : '비활성' }}
                  </el-tag>
                  <el-tag
                    :type="usersStore.currentUser.role === 'admin' ? 'warning' : usersStore.currentUser.role === 'instructor' ? 'success' : 'info'"
                    size="default"
                    effect="dark"
                  >
                    {{ getRoleDisplayName(usersStore.currentUser.role) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </el-card>

          <!-- User Stats -->
          <el-card class="stats-card" v-loading="statsLoading">
            <template #header>
              <div class="card-header">
                <el-icon class="header-icon"><DataAnalysis /></el-icon>
                <span class="card-title">활동 통계</span>
              </div>
            </template>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-info">
                  <div class="stat-icon certificate">
                    <el-icon><Document /></el-icon>
                  </div>
                  <div class="stat-content">
                    <div class="stat-value">{{ userStats.certificates_count || 0 }}</div>
                    <div class="stat-label">자격증</div>
                  </div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-info">
                  <div class="stat-icon materials">
                    <el-icon><Reading /></el-icon>
                  </div>
                  <div class="stat-content">
                    <div class="stat-value">{{ userStats.study_materials_count || 0 }}</div>
                    <div class="stat-label">학습자료</div>
                  </div>
                </div>
              </div>
              <div class="stat-item">
                <div class="stat-info">
                  <div class="stat-icon activity">
                    <el-icon><Clock /></el-icon>
                  </div>
                  <div class="stat-content">
                    <div class="stat-value">{{ getActiveDays() }}</div>
                    <div class="stat-label">활동일수</div>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="16">
          <!-- User Information -->
          <el-card class="info-card">
            <template #header>
              <div class="card-header">
                <el-icon class="header-icon"><UserIcon /></el-icon>
                <span class="card-title">기본 정보</span>
              </div>
            </template>
            <div class="info-grid">
              <div class="info-item">
                <div class="info-content">
                  <div class="info-label">사용자 ID</div>
                  <div class="info-value">#{{ String(usersStore.currentUser.id).padStart(4, '0') }}</div>
                </div>
              </div>
              <div class="info-item">
                <div class="info-content">
                  <div class="info-label">사용자명</div>
                  <div class="info-value">{{ usersStore.currentUser.username }}</div>
                </div>
              </div>
              <div class="info-item">
                <div class="info-content">
                  <div class="info-label">이메일</div>
                  <div class="info-value">{{ usersStore.currentUser.email }}</div>
                </div>
              </div>
              <div class="info-item">
                <div class="info-content">
                  <div class="info-label">전체 이름</div>
                  <div class="info-value">{{ usersStore.currentUser.full_name || '미설정' }}</div>
                </div>
              </div>
              <div class="info-item">
                <div class="info-content">
                  <div class="info-label">상태</div>
                  <div class="info-value">
                    <el-tag
                      :type="usersStore.currentUser.is_active ? 'success' : 'danger'"
                      size="small"
                      effect="light"
                    >
                      {{ usersStore.currentUser.is_active ? '활성' : '비활성' }}
                    </el-tag>
                  </div>
                </div>
              </div>
              <div class="info-item">
                <div class="info-content">
                  <div class="info-label">역할</div>
                  <div class="info-value">
                    <el-tag
                      :type="usersStore.currentUser.role === 'admin' ? 'warning' : usersStore.currentUser.role === 'instructor' ? 'success' : 'info'"
                      size="small"
                      effect="light"
                    >
                      {{ getRoleDisplayName(usersStore.currentUser.role) }}
                    </el-tag>
                  </div>
                </div>
              </div>
              <div class="info-item">
                <div class="info-content">
                  <div class="info-label">가입일</div>
                  <div class="info-value">{{ formatDate(usersStore.currentUser.created_at) }}</div>
                </div>
              </div>
              <div class="info-item">
                <div class="info-content">
                  <div class="info-label">마지막 업데이트</div>
                  <div class="info-value">{{ formatDate(usersStore.currentUser.updated_at) }}</div>
                </div>
              </div>
            </div>
          </el-card>

          <!-- Recent Activity -->
          <el-card class="activity-card" v-loading="activityLoading">
            <template #header>
              <div class="card-header">
                <el-icon class="header-icon"><Clock /></el-icon>
                <span class="card-title">최근 활동</span>
              </div>
            </template>
            <div class="activity-content">
              <el-timeline v-if="recentActivities.length > 0">
                <el-timeline-item
                  v-for="activity in recentActivities"
                  :key="activity.id"
                  :timestamp="formatDateTime(activity.created_at)"
                  :type="getActivityType(activity.type)"
                >
                  <div class="timeline-content">
                    <h4 class="activity-title">{{ activity.title }}</h4>
                    <p class="activity-description">{{ activity.description }}</p>
                  </div>
                </el-timeline-item>
              </el-timeline>
              <el-empty v-else description="최근 활동이 없습니다" :image-size="100" />
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- Loading State -->
    <div v-else-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- Error State -->
    <div v-else class="error-container">
      <el-empty description="User not found" />
    </div>

    <!-- Edit User Dialog -->
    <el-dialog
      v-model="showEditDialog"
      title="사용자 정보 수정"
      width="500px"
      @close="resetEditForm"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="120px"
      >
        <el-form-item label="사용자명" prop="username">
          <el-input v-model="editForm.username" disabled />
          <div class="form-tip">사용자명은 변경할 수 없습니다</div>
        </el-form-item>
        
        <el-form-item label="이메일" prop="email">
          <el-input v-model="editForm.email" type="email" />
        </el-form-item>
        
        <el-form-item label="전체 이름" prop="full_name">
          <el-input v-model="editForm.full_name" />
        </el-form-item>
        
        <el-form-item label="상태" prop="is_active">
          <el-switch
            v-model="editForm.is_active"
            active-text="활성"
            inactive-text="비활성"
          />
        </el-form-item>
        
        <el-form-item label="역할" prop="role">
          <el-select v-model="editForm.role" placeholder="역할 선택">
            <el-option label="학생" value="student" />
            <el-option label="강사" value="instructor" />
            <el-option label="관리자" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">취소</el-button>
          <el-button type="primary" @click="handleUpdateUser" :loading="loading">
            사용자 정보 수정
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { ArrowLeft, Edit, User as UserIcon, DataAnalysis, Document, Reading, Clock, Camera } from '@element-plus/icons-vue'
import { useUsersStore } from '@/stores/users'
import type { User, UserUpdate } from '@/types'
import { formatDate } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const usersStore = useUsersStore()

// State
const loading = ref(false)
const statsLoading = ref(false)
const activityLoading = ref(false)
const showEditDialog = ref(false)
const editFormRef = ref<FormInstance>()

// User stats (will be fetched from API)
const userStats = reactive({
  certificates_count: 0,
  study_materials_count: 0,
  login_count: 0,
})

// Recent activities (will be fetched from API)
const recentActivities = ref<any[]>([])

// Edit form
const editForm = reactive<UserUpdate & { id: number }>({
  id: 0,
  username: '',
  email: '',
  full_name: '',
  is_active: true,
  role: 'student',
})

// Form validation rules
const editRules: FormRules = {
  username: [
    { required: true, message: 'Please enter username', trigger: 'blur' },
    { min: 3, max: 50, message: 'Length should be 3 to 50', trigger: 'blur' },
  ],
  email: [
    { required: true, message: 'Please enter email', trigger: 'blur' },
    { type: 'email', message: 'Please enter a valid email', trigger: 'blur' },
  ],
}

// Computed
const userId = computed(() => parseInt(route.params.id as string))

// Methods
const goBack = () => {
  console.log('goBack called - navigating to /admin/users')
  
  // First try router navigation
  router.replace('/admin/users').catch((error) => {
    console.error('Router navigation failed:', error)
    // Fallback to direct location change
    window.location.href = '/admin/users'
  })
  
  console.log('router.replace executed')
}

const getRoleDisplayName = (role: string): string => {
  const roleMap: { [key: string]: string } = {
    'admin': '관리자',
    'instructor': '강사',
    'student': '학생',
  }
  return roleMap[role] || role
}

const getUserInitials = (user: User): string => {
  if (user.full_name) {
    return user.full_name
      .split(' ')
      .map(name => name.charAt(0))
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }
  return user.username.charAt(0).toUpperCase()
}

const handleUpdateUser = async () => {
  if (!editFormRef.value) return

  try {
    await editFormRef.value.validate()
    const { id, ...updateData } = editForm
    
    // Update user
    await usersStore.updateUser(id, updateData)
    
    ElMessage.success('사용자 정보가 성공적으로 업데이트되었습니다')
    showEditDialog.value = false
    
    // Reload all user data to reflect changes
    await loadUserData()
  } catch (error) {
    console.error('Failed to update user:', error)
    const errorMessage = error?.response?.data?.detail || error?.message || 'Failed to update user'
    ElMessage.error(`사용자 정보 업데이트에 실패했습니다: ${errorMessage}`)
  }
}

const resetEditForm = () => {
  if (usersStore.currentUser) {
    editForm.id = usersStore.currentUser.id
    editForm.username = usersStore.currentUser.username
    editForm.email = usersStore.currentUser.email
    editForm.full_name = usersStore.currentUser.full_name || ''
    editForm.is_active = usersStore.currentUser.is_active
    editForm.role = usersStore.currentUser.role || 'student'
  }
  editFormRef.value?.resetFields()
}

const isCurrentUser = (user: User | null): boolean => {
  if (!user) return false
  const currentUserId = localStorage.getItem('currentUserId') || '2' // fallback to admin
  return user.id.toString() === currentUserId
}

const formatDateTime = (dateString: string): string => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleString('ko-KR')
}

const getActiveDays = (): number => {
  if (!usersStore.currentUser?.created_at) return 0
  const createdDate = new Date(usersStore.currentUser.created_at)
  const today = new Date()
  const diffTime = Math.abs(today.getTime() - createdDate.getTime())
  return Math.ceil(diffTime / (1000 * 60 * 60 * 24))
}

const getActivityType = (type: string): string => {
  const typeMap: { [key: string]: string } = {
    'login': 'primary',
    'upload': 'success', 
    'update': 'info',
    'create': 'warning'
  }
  return typeMap[type] || 'info'
}

const fetchUserStats = async () => {
  if (!usersStore.currentUser) return
  
  try {
    statsLoading.value = true
    // Fetch real user stats from API
    const response = await fetch(`/api/users/${usersStore.currentUser.id}/stats`)
    if (response.ok) {
      const stats = await response.json()
      // Use actual data, fallback to 0 for null values
      userStats.certificates_count = stats.certificates_count || 0
      userStats.study_materials_count = stats.study_materials_count || 0
      userStats.login_count = stats.practice_sessions || 0
    } else {
      // Fallback to 0 values if API fails
      userStats.certificates_count = 0
      userStats.study_materials_count = 0
      userStats.login_count = 0
    }
  } catch (error) {
    // Set to 0 on error (silently handle)
    userStats.certificates_count = 0
    userStats.study_materials_count = 0  
    userStats.login_count = 0
  } finally {
    statsLoading.value = false
  }
}

const fetchRecentActivity = async () => {
  if (!usersStore.currentUser) return
  
  try {
    activityLoading.value = true
    // Simulated activity - in real app, fetch from API
    const activities = [
      {
        id: 1,
        title: '로그인',
        description: '시스템에 로그인했습니다',
        created_at: new Date().toISOString(),
        type: 'login'
      },
      {
        id: 2, 
        title: '프로필 업데이트',
        description: '프로필 정보를 업데이트했습니다',
        created_at: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
        type: 'update'
      }
    ]
    recentActivities.value = activities
  } catch (error) {
    console.error('Failed to fetch recent activity:', error)
  } finally {
    activityLoading.value = false
  }
}

// Initialize
onMounted(async () => {
  await loadUserData()
})

// Cleanup on unmount
onBeforeUnmount(() => {
  // Clear current user to prevent state issues when navigating to other pages
  usersStore.clearCurrentUser()
  
  // Clear any pending operations
  loading.value = false
  statsLoading.value = false
  activityLoading.value = false
  showEditDialog.value = false
})

// Load user data function for reuse
const loadUserData = async () => {
  try {
    loading.value = true
    
    // Validate user ID
    if (!userId.value || isNaN(userId.value)) {
      throw new Error('Invalid user ID')
    }
    
    await usersStore.fetchUser(userId.value)
    
    // Only proceed if user was successfully fetched
    if (usersStore.currentUser) {
      resetEditForm()
      
      // Fetch additional data
      await Promise.all([
        fetchUserStats().catch(err => console.warn('Failed to fetch user stats:', err)),
        fetchRecentActivity().catch(err => console.warn('Failed to fetch recent activity:', err))
      ])
    }
  } catch (error) {
    console.error('Failed to fetch user:', error)
    ElMessage.error('사용자 상세 정보를 불러오는데 실패했습니다')
    
    // Navigate back to users list if user not found
    if (error?.response?.status === 404) {
      setTimeout(() => goBack(), 2000)
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ===== 전체 컨테이너 ===== */
.user-detail-container {
  padding: 0;
  margin: 0;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

/* ===== 페이지 헤더 ===== */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  color: white;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.back-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  backdrop-filter: blur(10px);
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

.header-info .page-title {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: white;
}

.header-info .page-description {
  font-size: 16px;
  margin: 0;
  color: rgba(255, 255, 255, 0.9);
}

.edit-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  backdrop-filter: blur(10px);
  font-weight: 500;
}

.edit-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

/* ===== 프로필 카드 ===== */
.profile-card {
  margin-bottom: 24px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.profile-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 20px;
  padding: 32px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.avatar-section {
  position: relative;
  display: inline-block;
}

.profile-avatar {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-size: 36px;
  font-weight: 700;
  border: 4px solid white;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.avatar-overlay {
  position: absolute;
  bottom: 8px;
  right: 8px;
  width: 32px;
  height: 32px;
  background: #409eff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border: 2px solid white;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.camera-icon {
  color: white;
  font-size: 16px;
}

.profile-name {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: #2c3e50;
}

.profile-username {
  margin: 4px 0;
  font-size: 16px;
  color: #667eea;
  font-weight: 500;
}

.profile-email {
  margin: 4px 0 16px 0;
  color: #6c757d;
  font-size: 16px;
}

.profile-tags {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

/* ===== 통계 카드 ===== */
.stats-card {
  margin-bottom: 24px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-icon {
  font-size: 18px;
  color: #667eea;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
}

.stat-item {
  padding: 20px;
  border-right: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

.stat-item:last-child {
  border-right: none;
}

.stat-item:hover {
  background: #f8f9fa;
  transform: translateY(-2px);
}

.stat-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stat-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #667eea;
  font-size: 16px;
  flex-shrink: 0;
}

.stat-icon.certificate {
  background: #f0f9ff;
  color: #0369a1;
}

.stat-icon.materials {
  background: #fef3f2;
  color: #dc2626;
}

.stat-icon.activity {
  background: #f0fdf4;
  color: #16a34a;
}

.stat-content {
  flex: 1;
  min-width: 0;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 2px;
  line-height: 1.2;
}

.stat-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
}

/* ===== 정보 카드 ===== */
.info-card {
  margin-bottom: 24px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0;
}

.info-item {
  padding: 16px 20px;
  border-right: 1px solid #e9ecef;
  border-bottom: 1px solid #e9ecef;
  transition: background-color 0.3s ease;
}

.info-item:nth-child(even) {
  border-right: none;
}

.info-item:nth-last-child(-n+2) {
  border-bottom: none;
}

.info-item:hover {
  background: #f8f9fa;
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.025em;
}

.info-value {
  font-size: 14px;
  color: #2c3e50;
  font-weight: 500;
  min-height: 20px;
  display: flex;
  align-items: center;
}

/* ===== 활동 카드 ===== */
.activity-card {
  margin-bottom: 24px;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.activity-content {
  padding: 8px;
}

.timeline-content {
  padding-left: 16px;
}

.activity-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.activity-description {
  margin: 0;
  font-size: 14px;
  color: #6c757d;
  line-height: 1.5;
}

/* ===== 로딩 및 에러 상태 ===== */
.loading-container,
.error-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.dialog-footer {
  display: flex;
  gap: 12px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* ===== 반응형 디자인 ===== */
@media (max-width: 1024px) {
  .user-detail-container {
    padding: 0 16px;
  }
  
  .page-header {
    padding: 20px;
  }
  
  .header-info .page-title {
    font-size: 28px;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .stat-item {
    border-right: none;
    border-bottom: 1px solid #e9ecef;
    padding: 16px;
  }
  
  .stat-item:last-child {
    border-bottom: none;
  }
  
  .stat-info {
    gap: 10px;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .info-item {
    border-right: none;
    padding: 12px 16px;
  }
}

@media (max-width: 768px) {
  .user-detail-container {
    padding: 0 12px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
    padding: 16px;
  }
  
  .header-left {
    flex-direction: column;
    gap: 12px;
  }
  
  .header-info .page-title {
    font-size: 24px;
  }
  
  .profile-header {
    padding: 24px 16px;
  }
  
  .profile-name {
    font-size: 24px;
  }
  
  .profile-tags {
    flex-direction: column;
    align-items: center;
    gap: 8px;
  }
  
  .stat-item {
    padding: 20px 16px;
  }
  
  .info-item {
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .user-detail-container {
    padding: 0 8px;
  }
  
  .page-header {
    border-radius: 12px;
    padding: 12px;
  }
  
  .header-info .page-title {
    font-size: 20px;
  }
  
  .header-info .page-description {
    font-size: 14px;
  }
  
  .profile-header {
    padding: 20px 12px;
  }
  
  .profile-avatar {
    width: 100px !important;
    height: 100px !important;
    font-size: 30px;
  }
  
  .profile-name {
    font-size: 20px;
  }
  
  .stat-value {
    font-size: 24px;
  }
  
  .activity-title {
    font-size: 14px;
  }
}

/* ===== Element Plus 컴포넌트 스타일 오버라이드 ===== */
:deep(.el-card) {
  border: none;
}

:deep(.el-card__header) {
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
  padding: 16px 24px;
}

:deep(.el-card__body) {
  padding: 0;
}

:deep(.el-timeline) {
  padding: 16px 24px;
}

:deep(.el-timeline-item__timestamp) {
  color: #6c757d;
  font-size: 12px;
}

:deep(.el-empty) {
  padding: 40px 20px;
}

:deep(.el-tag) {
  font-weight: 500;
  border-radius: 8px;
  padding: 4px 12px;
}
</style>