<template>
  <div class="users-container">
    <div class="page-header">
      <h1 class="page-title">사용자 관리</h1>
      <p class="page-description">시스템 사용자 및 권한을 관리합니다</p>
    </div>

    <!-- Actions Bar -->
    <div class="actions-bar">
      <div class="search-section">
        <el-input
          v-model="searchQuery"
          placeholder="사용자 검색..."
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
          class="search-input"
        />
      </div>
      
      <div class="action-buttons">
        <el-button
          type="primary"
          :icon="Plus"
          @click="showCreateDialog = true"
          class="main-action-btn"
        >
          <span class="btn-text">사용자 추가</span>
        </el-button>
        <el-button
          :icon="Refresh"
          @click="refreshUsers"
          class="secondary-action-btn"
        >
          <span class="btn-text">새로고침</span>
        </el-button>
      </div>
    </div>

    <!-- Desktop Table View -->
    <el-card class="table-card desktop-table" v-loading="usersStore.isLoading">
      <el-table
        :data="usersStore.users"
        stripe
        @sort-change="handleSortChange"
        table-layout="auto"
      >
        <el-table-column label="번호" width="80" align="center">
          <template #default="scope">
            <span class="row-number">{{ scope.$index + 1 }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="username" label="사용자명" min-width="150" sortable>
          <template #default="scope">
            <div class="user-info">
              <el-avatar size="small" class="user-avatar">
                {{ getUserInitials(scope.row) }}
              </el-avatar>
              <span class="username">{{ scope.row.username }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="email" label="이메일" min-width="200" sortable>
          <template #default="scope">
            <span class="email-text">{{ scope.row.email }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="full_name" label="전체 이름" min-width="150">
          <template #default="scope">
            <span class="full-name-text">{{ scope.row.full_name || '-' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="is_active" label="상태" width="120" align="center">
          <template #default="scope">
            <div class="status-wrapper">
              <el-switch
                v-model="scope.row.is_active"
                size="small"
                :active-text="scope.row.is_active ? '활성' : '비활성'"
                @change="toggleUserStatus(scope.row)"
              />
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="role" label="역할" width="120" align="center">
          <template #default="scope">
            <el-tag
              :type="scope.row.role === 'admin' ? 'warning' : scope.row.role === 'instructor' ? 'success' : 'info'"
              size="small"
            >
              {{ getRoleDisplayName(scope.row.role) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="등록일" width="120" sortable>
          <template #default="scope">
            <span class="date-text">{{ formatDate(scope.row.created_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="작업" min-width="200" align="center" class-name="action-column">
          <template #default="scope">
            <div class="action-controls">
              <div class="action-buttons">
                <el-tooltip content="상세보기" placement="top">
                  <el-button class="action-btn" type="info" :icon="View" @click="viewUser(scope.row)" circle />
                </el-tooltip>
                <el-tooltip content="편집" placement="top">
                  <el-button class="action-btn" type="primary" :icon="Edit" @click="editUser(scope.row)" circle />
                </el-tooltip>
                <el-tooltip content="삭제" placement="top">
                  <el-button 
                    class="action-btn" 
                    type="danger" 
                    :icon="Delete" 
                    @click="deleteUser(scope.row)" 
                    :disabled="isCurrentUser(scope.row)"
                    circle 
                  />
                </el-tooltip>
              </div>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="usersStore.totalUsers"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- Mobile Cards View -->
    <div class="mobile-cards" v-loading="usersStore.isLoading">
      <div class="empty-state" v-if="usersStore.users.length === 0">
        <el-empty description="사용자가 없습니다" />
      </div>
      
      <div v-else>
        <div v-for="(user, index) in usersStore.users" :key="user.id" class="user-card">
          <div class="card-header">
            <div class="card-title">
              <div class="card-number">{{ index + 1 }}</div>
              <el-avatar size="small" class="card-avatar">
                {{ getUserInitials(user) }}
              </el-avatar>
              <span class="card-username">{{ user.username }}</span>
            </div>
            <div class="card-status">
              <el-switch
                v-model="user.is_active"
                size="small"
                @change="toggleUserStatus(user)"
              />
            </div>
          </div>
          
          <div class="card-content">
            <div class="card-row">
              <span class="card-label">이메일:</span>
              <span class="card-value email-text">{{ user.email }}</span>
            </div>
            
            <div class="card-row" v-if="user.full_name">
              <span class="card-label">전체 이름:</span>
              <span class="card-value">{{ user.full_name }}</span>
            </div>
            
            <div class="card-row">
              <span class="card-label">역할:</span>
              <el-tag
                :type="user.role === 'admin' ? 'warning' : user.role === 'instructor' ? 'success' : 'info'"
                size="small"
              >
                {{ getRoleDisplayName(user.role) }}
              </el-tag>
            </div>
            
            <div class="card-row">
              <span class="card-label">등록일:</span>
              <span class="card-value date-text">{{ formatDate(user.created_at) }}</span>
            </div>
          </div>
          
          <div class="card-actions">
            <el-button class="mobile-action-btn" type="info" :icon="View" @click="viewUser(user)">
              상세보기
            </el-button>
            <el-button class="mobile-action-btn" type="primary" :icon="Edit" @click="editUser(user)">
              편집
            </el-button>
            <el-button 
              class="mobile-action-btn" 
              type="danger" 
              :icon="Delete" 
              @click="deleteUser(user)"
              :disabled="isCurrentUser(user)"
            >
              삭제
            </el-button>
          </div>
        </div>
        
        <!-- Mobile Pagination -->
        <div class="mobile-pagination">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :page-sizes="[10, 20, 50]"
            :total="usersStore.totalUsers"
            layout="prev, pager, next"
            small
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </div>
    </div>

    <!-- Create User Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      title="Create New User"
      width="500px"
      @close="resetCreateForm"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="120px"
      >
        <el-form-item label="Username" prop="username">
          <el-input v-model="createForm.username" />
        </el-form-item>
        
        <el-form-item label="Email" prop="email">
          <el-input v-model="createForm.email" type="email" />
        </el-form-item>
        
        <el-form-item label="Password" prop="password">
          <el-input v-model="createForm.password" type="password" show-password />
        </el-form-item>
        
        <el-form-item label="Full Name" prop="full_name">
          <el-input v-model="createForm.full_name" />
        </el-form-item>
        
        <el-form-item label="Role" prop="role">
          <el-select v-model="createForm.role" placeholder="Select role">
            <el-option label="Student" value="student" />
            <el-option label="Instructor" value="instructor" />
            <el-option label="Administrator" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">Cancel</el-button>
          <el-button type="primary" @click="handleCreateUser">
            Create User
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Edit User Dialog -->
    <el-dialog
      v-model="showEditDialog"
      title="Edit User"
      width="500px"
      @close="resetEditForm"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="120px"
      >
        <el-form-item label="Username" prop="username">
          <el-input v-model="editForm.username" />
        </el-form-item>
        
        <el-form-item label="Email" prop="email">
          <el-input v-model="editForm.email" type="email" />
        </el-form-item>
        
        <el-form-item label="Full Name" prop="full_name">
          <el-input v-model="editForm.full_name" />
        </el-form-item>
        
        <el-form-item label="Status" prop="is_active">
          <el-switch
            v-model="editForm.is_active"
            active-text="Active"
            inactive-text="Inactive"
          />
        </el-form-item>
        
        <el-form-item label="Role" prop="role">
          <el-select 
            v-model="editForm.role" 
            placeholder="Select role"
            :disabled="authStore.user?.id === editForm.id"
          >
            <el-option label="학생" value="student" />
            <el-option label="강사" value="instructor" />
            <el-option label="관리자" value="admin" />
          </el-select>
          <div v-if="authStore.user?.id === editForm.id" class="role-note">
            자기 자신의 역할은 변경할 수 없습니다
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">Cancel</el-button>
          <el-button type="primary" @click="handleUpdateUser">
            Update User
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  Search,
  Plus,
  Refresh,
  View,
  Edit,
  Delete,
} from '@element-plus/icons-vue'
import { useUsersStore } from '@/stores/users'
import { useAuthStore } from '@/stores/auth'
import type { User, UserCreate, UserUpdate } from '@/types'
import { formatDate } from '@/utils/format'

const router = useRouter()
const usersStore = useUsersStore()
const authStore = useAuthStore()

// Search and pagination
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

// Dialog states
const showCreateDialog = ref(false)
const showEditDialog = ref(false)

// Form refs
const createFormRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()

// Forms
const createForm = reactive<UserCreate>({
  username: '',
  email: '',
  password: '',
  full_name: '',
  role: 'student',
})

const editForm = reactive<UserUpdate & { id: number }>({
  id: 0,
  username: '',
  email: '',
  full_name: '',
  is_active: true,
  role: 'student',
})

// Form validation rules
const createRules: FormRules = {
  username: [
    { required: true, message: 'Please enter username', trigger: 'blur' },
    { min: 3, max: 50, message: 'Length should be 3 to 50', trigger: 'blur' },
  ],
  email: [
    { required: true, message: 'Please enter email', trigger: 'blur' },
    { type: 'email', message: 'Please enter a valid email', trigger: 'blur' },
  ],
  password: [
    { required: true, message: 'Please enter password', trigger: 'blur' },
    { min: 6, message: 'Password must be at least 6 characters', trigger: 'blur' },
  ],
}

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

// Methods
const fetchUsers = () => {
  usersStore.fetchUsers(currentPage.value, pageSize.value, searchQuery.value)
}

const handleSearch = () => {
  currentPage.value = 1
  fetchUsers()
}

const handleSortChange = () => {
  // Implement sorting logic if needed
  fetchUsers()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchUsers()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchUsers()
}

const refreshUsers = () => {
  fetchUsers()
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

const getRoleDisplayName = (role: string): string => {
  const roleMap: { [key: string]: string } = {
    'admin': '관리자',
    'instructor': '강사',
    'student': '학생',
  }
  return roleMap[role] || role
}

const toggleUserStatus = async (user: User) => {
  try {
    await usersStore.toggleUserStatus(user.id)
    ElMessage.success(`사용자 상태가 ${user.is_active ? '활성' : '비활성'}으로 변경되었습니다`)
  } catch (error) {
    console.error('Failed to toggle user status:', error)
    ElMessage.error('사용자 상태 변경에 실패했습니다')
    // Revert the switch state
    user.is_active = !user.is_active
  }
}

const viewUser = (user: User) => {
  router.push(`/admin/users/${user.id}`)
}

const editUser = (user: User) => {
  editForm.id = user.id
  editForm.username = user.username
  editForm.email = user.email
  editForm.full_name = user.full_name || ''
  editForm.is_active = user.is_active
  editForm.role = user.role || 'student'
  showEditDialog.value = true
}

const isCurrentUser = (user: User): boolean => {
  return authStore.user?.id === user.id
}

const deleteUser = async (user: User) => {
  // Prevent deleting current user
  if (isCurrentUser(user)) {
    ElMessage.warning('자기 자신은 삭제할 수 없습니다')
    return
  }

  try {
    await ElMessageBox.confirm(
      `정말로 사용자 "${user.username}"을(를) 삭제하시겠습니까?`,
      '삭제 확인',
      {
        confirmButtonText: '삭제',
        cancelButtonText: '취소',
        type: 'warning',
      }
    )

    await usersStore.deleteUser(user.id)
    ElMessage.success('사용자가 성공적으로 삭제되었습니다')
    fetchUsers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete user:', error)
      ElMessage.error('사용자 삭제에 실패했습니다')
    }
  }
}

const handleCreateUser = async () => {
  if (!createFormRef.value) return

  try {
    await createFormRef.value.validate()
    await usersStore.createUser(createForm)
    ElMessage.success('User created successfully')
    showCreateDialog.value = false
    resetCreateForm()
    fetchUsers()
  } catch (error) {
    console.error('Failed to create user:', error)
    ElMessage.error('Failed to create user')
  }
}

const handleUpdateUser = async () => {
  if (!editFormRef.value) return

  try {
    await editFormRef.value.validate()
    const { id, ...updateData } = editForm
    await usersStore.updateUser(id, updateData)
    ElMessage.success('User updated successfully')
    showEditDialog.value = false
    resetEditForm()
    fetchUsers()
  } catch (error) {
    console.error('Failed to update user:', error)
    ElMessage.error('Failed to update user')
  }
}

const resetCreateForm = () => {
  Object.assign(createForm, {
    username: '',
    email: '',
    password: '',
    full_name: '',
    role: 'student',
  })
  createFormRef.value?.resetFields()
}

const resetEditForm = () => {
  Object.assign(editForm, {
    id: 0,
    username: '',
    email: '',
    full_name: '',
    is_active: true,
    role: 'student',
  })
  editFormRef.value?.resetFields()
}

// Initialize
onMounted(() => {
  fetchUsers()
})
</script>

<style scoped>
/* ===== 새로운 CSS Grid 기반 반응형 레이아웃 ===== */
.users-container {
  padding: 0;
  margin: 0;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.page-header {
  margin-bottom: 24px;
  padding: 0 4px;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px 0;
}

.page-description {
  font-size: 14px;
  color: #909399;
  margin: 0;
}

/* ===== Actions Bar ===== */
.actions-bar {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 20px;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: #ffffff;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.search-section {
  min-width: 0;
}

.search-input {
  max-width: 400px;
  width: 100%;
}

.action-buttons {
  display: flex;
  gap: 12px;
  flex-shrink: 0;
}

.main-action-btn {
  min-width: 120px;
  height: 40px;
  font-weight: 500;
}

.secondary-action-btn {
  min-width: 100px;
  height: 40px;
}

.btn-text {
  font-size: 14px;
}

/* ===== Desktop Table ===== */
.desktop-table {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.row-number {
  font-weight: 600;
  color: #606266;
  font-size: 14px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 0;
}

.user-avatar {
  background: linear-gradient(135deg, #409eff 0%, #6bb6ff 100%);
  font-size: 12px;
  font-weight: 600;
}

.username {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.email-text {
  color: #606266;
  font-size: 13px;
}

.full-name-text {
  color: #606266;
  font-size: 13px;
}

.date-text {
  color: #909399;
  font-size: 12px;
}

.status-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* ===== Action Controls ===== */
.action-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 8px 4px;
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-btn {
  width: 32px !important;
  height: 32px !important;
  min-width: 32px !important;
  padding: 0 !important;
  border-radius: 50% !important;
  display: inline-flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: all 0.2s ease !important;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

/* ===== Pagination ===== */
.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
  padding: 16px 0;
}

/* ===== Mobile Cards ===== */
.mobile-cards {
  display: none;
}

.user-card {
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
  margin-bottom: 16px;
  overflow: hidden;
  transition: all 0.2s ease;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.user-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}

.card-header {
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e4e7ed;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.card-number {
  background: #409eff;
  color: white;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 12px;
  min-width: 24px;
  text-align: center;
}

.card-avatar {
  background: linear-gradient(135deg, #409eff 0%, #6bb6ff 100%);
  font-size: 12px;
  font-weight: 600;
}

.card-username {
  font-weight: 600;
  color: #303133;
  font-size: 16px;
}

.card-status {
  flex-shrink: 0;
}

.card-content {
  padding: 16px;
}

.card-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #f5f7fa;
}

.card-row:last-child {
  margin-bottom: 0;
  border-bottom: none;
}

.card-label {
  font-weight: 500;
  color: #606266;
  font-size: 13px;
  min-width: 80px;
}

.card-value {
  color: #303133;
  font-size: 13px;
  text-align: right;
  word-break: break-all;
}

.card-actions {
  background: #f8f9fa;
  padding: 16px;
  display: flex;
  gap: 8px;
  border-top: 1px solid #e4e7ed;
}

.mobile-action-btn {
  flex: 1;
  height: 36px;
  font-size: 13px;
  font-weight: 500;
}

.mobile-pagination {
  display: flex;
  justify-content: center;
  padding: 20px 0;
  margin-top: 16px;
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
}

.dialog-footer {
  display: flex;
  gap: 12px;
}

.role-note {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
  font-style: italic;
}

/* ===== 반응형 디자인 ===== */

/* 큰 데스크탑 (1200px 이상) */
@media (min-width: 1200px) {
  .users-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
  }
  
  .action-btn {
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
  }
  
  .actions-bar {
    padding: 20px;
  }
}

/* 중간 데스크탑 (769px ~ 1199px) */
@media (max-width: 1199px) and (min-width: 769px) {
  .users-container {
    padding: 0 16px;
  }
  
  .action-btn {
    width: 30px !important;
    height: 30px !important;
    min-width: 30px !important;
  }
  
  .actions-bar {
    padding: 16px;
    gap: 16px;
  }
  
  .main-action-btn {
    min-width: 100px;
    height: 36px;
  }
  
  .secondary-action-btn {
    min-width: 90px;
    height: 36px;
  }
}

/* 태블릿 (481px ~ 768px) */
@media (max-width: 768px) and (min-width: 481px) {
  .users-container {
    padding: 0 12px;
  }
  
  .desktop-table {
    display: none;
  }
  
  .mobile-cards {
    display: block;
  }
  
  .actions-bar {
    grid-template-columns: 1fr;
    gap: 16px;
    padding: 16px;
  }
  
  .action-buttons {
    justify-content: center;
    width: 100%;
  }
  
  .main-action-btn,
  .secondary-action-btn {
    flex: 1;
    max-width: 150px;
    height: 40px;
  }
  
  .page-title {
    font-size: 24px;
  }
  
  .user-card {
    border-radius: 10px;
  }
  
  .mobile-action-btn {
    height: 40px;
    font-size: 14px;
  }
}

/* 작은 모바일 (480px 이하) */
@media (max-width: 480px) {
  .users-container {
    padding: 0 8px;
  }
  
  .desktop-table {
    display: none;
  }
  
  .mobile-cards {
    display: block;
  }
  
  .actions-bar {
    grid-template-columns: 1fr;
    gap: 12px;
    padding: 12px;
  }
  
  .action-buttons {
    flex-direction: column;
    width: 100%;
    gap: 8px;
  }
  
  .main-action-btn,
  .secondary-action-btn {
    width: 100%;
    height: 44px;
    font-size: 16px;
  }
  
  .btn-text {
    font-size: 16px;
  }
  
  .page-title {
    font-size: 22px;
  }
  
  .page-description {
    font-size: 13px;
  }
  
  .user-card {
    border-radius: 8px;
    margin-bottom: 12px;
  }
  
  .card-header {
    padding: 12px;
  }
  
  .card-content {
    padding: 12px;
  }
  
  .card-actions {
    padding: 12px;
    flex-direction: column;
    gap: 8px;
  }
  
  .mobile-action-btn {
    width: 100%;
    height: 44px;
    font-size: 16px;
  }
  
  .card-username {
    font-size: 15px;
  }
  
  .card-number {
    font-size: 11px;
    padding: 3px 6px;
  }
}

/* ===== Element Plus 컴포넌트 스타일 오버라이드 ===== */
:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table .el-table__cell) {
  padding: 12px 0;
  border-bottom: 1px solid #f0f2f5;
}

:deep(.el-table .el-table__header-wrapper) {
  background: #fafafa;
}

:deep(.el-table th.el-table__cell) {
  background: #fafafa;
  font-weight: 600;
  color: #303133;
  border-bottom: 2px solid #e4e7ed;
}

:deep(.el-table .el-table__row:hover) {
  background-color: #f8f9ff;
}

:deep(.el-table .action-column) {
  padding: 8px 0;
}

:deep(.el-switch.is-checked .el-switch__core) {
  background-color: #409eff;
}

:deep(.el-tag) {
  font-weight: 500;
  border-radius: 6px;
}

:deep(.el-pagination) {
  justify-content: center;
}

:deep(.el-dialog) {
  border-radius: 12px;
  overflow: hidden;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #303133;
}

/* ===== 스크롤바 스타일링 ===== */
.users-container::-webkit-scrollbar {
  width: 8px;
}

.users-container::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.users-container::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.users-container::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}
</style>