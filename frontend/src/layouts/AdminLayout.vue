<template>
  <div class="admin-layout" :class="{ 'sidebar-collapsed': isCollapsed }">
    <!-- Sidebar -->
    <nav class="sidebar" :class="{ 'collapsed': isCollapsed }">
      <div class="sidebar-header">
        <div v-if="!isCollapsed" class="logo">
          <h2>CertFast</h2>
        </div>
        <div v-else class="logo-collapsed">
          <span>CF</span>
        </div>
      </div>
      
      <el-menu
        :default-active="currentRoute"
        :collapse="isCollapsed"
        :unique-opened="false"
        background-color="#2c3e50"
        text-color="#ecf0f1"
        active-text-color="#3498db"
        router
        class="sidebar-menu"
      >
        <el-menu-item
          v-for="route in menuRoutes"
          :key="route.path"
          :index="route.path"
          @click="navigateTo(route.path)"
        >
          <el-icon>
            <component :is="route.meta?.icon || 'Menu'" />
          </el-icon>
          <template #title>{{ route.meta?.title }}</template>
        </el-menu-item>
      </el-menu>
    </nav>

    <!-- Main Area -->
    <div class="main-area">
      <!-- Header -->
      <header class="header">
        <div class="header-left">
          <el-button
            type="text"
            @click="toggleSidebar"
            class="sidebar-toggle"
          >
            <el-icon size="20">
              <component :is="isCollapsed ? 'Expand' : 'Fold'" />
            </el-icon>
          </el-button>
          
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item
              v-for="item in breadcrumbs"
              :key="item.path"
              :to="item.path"
            >
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <!-- User Info -->
          <el-dropdown trigger="click">
            <span class="user-dropdown">
              <el-avatar size="small" class="user-avatar">
                {{ userInitials }}
              </el-avatar>
              <span class="username">{{ authStore.user?.full_name || authStore.user?.username }}</span>
              <el-icon class="el-icon--right">
                <ArrowDown />
              </el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="goToProfile">
                  <el-icon><User /></el-icon>
                  프로필
                </el-dropdown-item>
                <el-dropdown-item divided @click="logout">
                  <el-icon><SwitchButton /></el-icon>
                  로그아웃
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <!-- Main Content -->
      <main class="content">
        <div class="content-wrapper">
          <router-view :key="$route.fullPath" />
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowDown,
  User,
  SwitchButton,
  Expand,
  Fold,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { getMenuRoutes } from '@/router'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// Sidebar state
const isCollapsed = ref(false)

// Menu routes
const menuRoutes = getMenuRoutes()

// Current route for menu highlighting
const currentRoute = computed(() => {
  // For child routes, highlight the parent
  if (route.matched.length > 1) {
    return route.matched[route.matched.length - 2].path
  }
  return route.path
})

// Breadcrumbs
const breadcrumbs = computed(() => {
  const items = []
  
  for (let i = 0; i < route.matched.length; i++) {
    const matched = route.matched[i]
    if (matched.meta?.title && !matched.meta?.hideInMenu) {
      items.push({
        path: matched.path,
        title: matched.meta.title,
      })
    }
  }
  
  return items
})

// User initials
const userInitials = computed(() => {
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
})

// Methods
const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
  localStorage.setItem('sidebar-collapsed', String(isCollapsed.value))
}

const navigateTo = (path: string) => {
  router.push(path)
}

const goToProfile = () => {
  router.push('/admin/profile')
}

const logout = async () => {
  try {
    await ElMessageBox.confirm(
      '정말 로그아웃 하시겠습니까?',
      '로그아웃 확인',
      {
        confirmButtonText: '로그아웃',
        cancelButtonText: '취소',
        type: 'warning',
      }
    )
    
    authStore.logout()
    ElMessage.success('성공적으로 로그아웃되었습니다')
    router.push('/login')
  } catch {
    // User cancelled
  }
}

// Initialize sidebar state
onMounted(() => {
  const saved = localStorage.getItem('sidebar-collapsed')
  if (saved !== null) {
    isCollapsed.value = saved === 'true'
  }
})
</script>

<style scoped>
/* ===== 새로운 CSS Grid 기반 레이아웃 ===== */
.admin-layout {
  display: grid;
  grid-template-columns: 250px 1fr;
  height: 100vh;
  width: 100%;
  transition: grid-template-columns 0.3s ease;
}

.admin-layout.sidebar-collapsed {
  grid-template-columns: 64px 1fr;
}

/* ===== 사이드바 ===== */
.sidebar {
  background-color: #2c3e50;
  border-right: 1px solid #34495e;
  overflow-y: auto;
  transition: all 0.3s ease;
  grid-row: 1;
}

.sidebar-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #34495e;
  color: #ecf0f1;
}

.logo h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.logo-collapsed span {
  font-size: 18px;
  font-weight: bold;
}

.sidebar-menu {
  border: none;
  height: calc(100vh - 60px);
}

/* ===== 메인 영역 ===== */
.main-area {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  grid-row: 1;
}

/* ===== 헤더 ===== */
.header {
  background-color: #ffffff;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 60px;
  flex-shrink: 0;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.sidebar-toggle {
  color: #606266;
  font-size: 20px;
}

.breadcrumb {
  margin-left: 20px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-dropdown:hover {
  background-color: #f5f7fa;
}

.user-avatar {
  background-color: #409eff;
}

.username {
  font-size: 14px;
  color: #303133;
}

/* ===== 콘텐츠 영역 ===== */
.content {
  background-color: #f5f7fa;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.content-wrapper {
  padding: 20px;
  min-height: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

/* ===== 메뉴 스타일 ===== */
:deep(.sidebar-menu) {
  border: none;
}

:deep(.sidebar-menu .el-menu-item) {
  color: #ecf0f1 !important;
}

:deep(.sidebar-menu .el-menu-item:hover) {
  background-color: #34495e !important;
}

:deep(.sidebar-menu .el-menu-item.is-active) {
  background-color: #3498db !important;
  color: #ffffff !important;
}

/* ===== 반응형 디자인 ===== */

/* 태블릿 (768px ~ 1024px) */
@media (max-width: 1024px) and (min-width: 769px) {
  .admin-layout {
    grid-template-columns: 200px 1fr;
  }
  
  .admin-layout.sidebar-collapsed {
    grid-template-columns: 64px 1fr;
  }
  
  .content-wrapper {
    padding: 16px;
  }
}

/* 모바일 (768px 이하) */
@media (max-width: 768px) {
  .admin-layout {
    grid-template-columns: 1fr;
    position: relative;
  }
  
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    width: 250px;
    height: 100vh;
    z-index: 1000;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
  }
  
  .sidebar.show {
    transform: translateX(0);
  }
  
  .main-area {
    grid-column: 1;
  }
  
  .content-wrapper {
    padding: 16px 12px;
  }
  
  .breadcrumb {
    display: none;
  }
  
  .header-left {
    gap: 10px;
  }
  
  .username {
    display: none;
  }
}

/* 아주 작은 모바일 (480px 이하) */
@media (max-width: 480px) {
  .sidebar {
    width: 100vw;
  }
  
  .content-wrapper {
    padding: 12px 8px;
  }
  
  .header {
    padding: 0 12px;
  }
  
  .header-left {
    gap: 8px;
  }
  
  .breadcrumb {
    display: none;
  }
}

/* ===== 트랜지션 ===== */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ===== 스크롤바 스타일링 ===== */
.sidebar::-webkit-scrollbar {
  width: 6px;
}

.sidebar::-webkit-scrollbar-track {
  background: #34495e;
}

.sidebar::-webkit-scrollbar-thumb {
  background: #5a6c7d;
  border-radius: 3px;
}

.sidebar::-webkit-scrollbar-thumb:hover {
  background: #4a5a6b;
}

.content::-webkit-scrollbar {
  width: 8px;
}

.content::-webkit-scrollbar-track {
  background: #f1f1f1;
}

.content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 4px;
}

.content::-webkit-scrollbar-thumb:hover {
  background: #a1a1a1;
}
</style>