import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { requiresAuth: false, hideInMenu: true },
  },
  {
    path: '/',
    name: 'Home',
    beforeEnter: () => {
      // 홈페이지는 라우터 가드에서 처리
      return '/student'
    }
  },
  {
    path: '/student',
    component: () => import('@/layouts/StudentLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'StudentDashboard',
        component: () => import('@/views/student/StudentDashboardView.vue'),
        meta: { title: '대시보드', icon: 'HomeFilled' },
      },
      {
        path: 'certificates',
        name: 'StudentCertificates',
        component: () => import('@/views/student/StudentCertificatesView.vue'),
        meta: { title: '자격증 선택', icon: 'Document' },
      },
      {
        path: 'certificates/:id',
        name: 'StudentCertificateDetail',
        component: () => import('@/views/student/StudentCertificateDetailView.vue'),
        meta: { title: '자격증 상세', hideInMenu: true },
      },
      {
        path: 'study',
        name: 'StudentStudy',
        component: () => import('@/views/student/StudentStudyView.vue'),
        meta: { title: '학습하기', icon: 'Reading' },
      },
      {
        path: 'study/:id',
        name: 'StudentStudyDetail',
        component: () => import('@/views/student/StudentStudyDetailView.vue'),
        meta: { title: '자격증 학습', hideInMenu: true },
      },
      {
        path: 'practice',
        name: 'StudentPractice',
        component: () => import('@/views/student/StudentPracticeView.vue'),
        meta: { title: '문제 풀이', icon: 'EditPen' },
      },
      {
        path: 'practice/:id',
        name: 'StudentPracticeDetail',
        component: () => import('@/views/student/StudentPracticeDetailView.vue'),
        meta: { title: '문제 풀이 세션', hideInMenu: true },
      },
      {
        path: 'chat',
        name: 'StudentChat',
        component: () => import('@/views/student/StudentChatView.vue'),
        meta: { title: 'AI 도우미', icon: 'ChatDotRound' },
      },
      {
        path: 'progress',
        name: 'StudentProgress',
        component: () => import('@/views/student/StudentProgressView.vue'),
        meta: { title: '학습 진도', hideInMenu: true },
      },
      {
        path: 'profile',
        name: 'StudentProfile',
        component: () => import('@/views/student/StudentProfileView.vue'),
        meta: { title: '프로필', hideInMenu: true },
      },
      {
        path: 'settings',
        name: 'StudentSettings',
        component: () => import('@/views/student/StudentSettingsView.vue'),
        meta: { title: '설정', hideInMenu: true },
      },
    ],
  },
  {
    path: '/instructor',
    component: () => import('@/layouts/InstructorLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'InstructorDashboard',
        component: () => import('@/views/instructor/InstructorDashboardView.vue'),
        meta: { title: '대시보드', icon: 'HomeFilled' },
      },
      {
        path: 'students',
        name: 'InstructorStudents',
        component: () => import('@/views/instructor/InstructorStudentsView.vue'),
        meta: { title: '학습자 관리', icon: 'User' },
      },
      {
        path: 'students/:id',
        name: 'InstructorStudentDetail',
        component: () => import('@/views/instructor/InstructorStudentDetailView.vue'),
        meta: { title: '학습자 상세', hideInMenu: true },
      },
      {
        path: 'content',
        name: 'InstructorContent',
        component: () => import('@/views/instructor/InstructorContentView.vue'),
        meta: { title: '학습 자료 관리', icon: 'Document' },
      },
      {
        path: 'reports',
        name: 'InstructorReports',
        component: () => import('@/views/instructor/InstructorReportsView.vue'),
        meta: { title: '신고 관리', icon: 'Warning' },
      },
      {
        path: 'collaboration',
        name: 'InstructorCollaboration',
        component: () => import('@/views/instructor/InstructorCollaborationView.vue'),
        meta: { title: '강사 협업', icon: 'ChatDotRound' },
      },
      {
        path: 'analytics',
        name: 'InstructorAnalytics',
        component: () => import('@/views/instructor/InstructorAnalyticsView.vue'),
        meta: { title: '학습 분석', icon: 'DataAnalysis' },
      },
      {
        path: 'profile',
        name: 'InstructorProfile',
        component: () => import('@/views/instructor/InstructorProfileView.vue'),
        meta: { title: '프로필', hideInMenu: true },
      },
    ],
  },
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/dashboard/DashboardView.vue'),
        meta: { title: '대시보드', icon: 'Dashboard' },
      },
      {
        path: 'users',
        name: 'Users',
        component: () => import('@/views/users/UsersView.vue'),
        meta: { title: '사용자 관리', icon: 'User' },
      },
      {
        path: 'users/:id',
        name: 'UserDetail',
        component: () => import('@/views/users/UserDetailView.vue'),
        meta: { title: '사용자 상세', hideInMenu: true },
      },
      {
        path: 'certificates',
        name: 'Certificates',
        component: () => import('@/views/certificates/CertificatesView.vue'),
        meta: { title: '자격증 관리', icon: 'Document' },
      },
      {
        path: 'certificates/:id',
        name: 'CertificateDetail',
        component: () => import('@/views/certificates/CertificateDetailView.vue'),
        meta: { title: '자격증 상세', hideInMenu: true },
      },
      {
        path: 'upload',
        name: 'Upload',
        component: () => import('@/views/upload/UploadView.vue'),
        meta: { title: 'PDF 업로드', icon: 'Upload' },
      },
      {
        path: 'documents',
        name: 'Documents',
        component: () => import('@/views/documents/DocumentsView.vue'),
        meta: { title: '처리된 문서', icon: 'Document' },
      },
      {
        path: 'ai-agents',
        name: 'AIAgents',
        component: () => import('@/views/ai-agents/AIAgentsView.vue'),
        meta: { title: 'AI 에이전트 관리', icon: 'Setting' },
      },
      {
        path: 'ai-agents/:id',
        name: 'AIAgentDetail',
        component: () => import('@/views/ai-agents/AIAgentDetailView.vue'),
        meta: { title: 'AI 에이전트 상세', hideInMenu: true },
      },
      {
        path: 'api-keys',
        name: 'APIKeys',
        component: () => import('@/views/api-keys/ApiKeysView.vue'),
        meta: { title: 'API 키 관리', icon: 'Key' },
      },
      {
        path: 'monitoring',
        name: 'Monitoring',
        component: () => import('@/views/monitoring/MonitoringView.vue'),
        meta: { title: '통계 및 모니터링', icon: 'DataAnalysis' },
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/profile/ProfileView.vue'),
        meta: { title: '프로필 설정', hideInMenu: true },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/error/NotFoundView.vue'),
    meta: { hideInMenu: true },
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// Navigation guards
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)

  console.log('Router guard:', {
    to: to.path,
    from: from.path,
    isAuthenticated: authStore.isAuthenticated,
    userRole: authStore.user?.role,
    requiresAuth
  })

  // Clear stores when navigating away from detail pages to avoid state conflicts
  if (from.path.includes('/users/') && !to.path.includes('/users/')) {
    // Import users store dynamically to avoid circular imports
    import('@/stores/users').then(({ useUsersStore }) => {
      const usersStore = useUsersStore()
      usersStore.clearCurrentUser()
    })
  }

  if (requiresAuth && !authStore.isAuthenticated) {
    console.log('Redirecting to login - not authenticated')
    next({
      path: '/login',
      query: { redirect: to.fullPath },
    })
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    // 사용자 역할에 따라 리디렉션
    const userRole = authStore.user?.role
    console.log('Already authenticated, redirecting from login to:', userRole)
    if (userRole === 'admin') {
      next({ path: '/admin' })
    } else if (userRole === 'instructor') {
      next({ path: '/instructor' })
    } else {
      next({ path: '/student' })
    }
  } else if (to.path === '/' && authStore.isAuthenticated) {
    // 루트 경로에서도 역할에 따라 리디렉션
    const userRole = authStore.user?.role
    console.log('Root path redirect to:', userRole)
    if (userRole === 'admin') {
      next({ path: '/admin' })
    } else if (userRole === 'instructor') {
      next({ path: '/instructor' })
    } else {
      next({ path: '/student' })
    }
  } else if (to.path.startsWith('/admin') && authStore.isAuthenticated) {
    // 관리자 페이지 접근 권한 검증
    const userRole = authStore.user?.role
    if (userRole !== 'admin') {
      console.log('Access denied - not admin, redirecting to appropriate dashboard')
      if (userRole === 'instructor') {
        next({ path: '/instructor' })
      } else if (userRole === 'student') {
        next({ path: '/student' })
      } else {
        next({ path: '/login' })
      }
      return
    }
    console.log('Admin access granted')
    next()
  } else if (to.path.startsWith('/instructor') && authStore.isAuthenticated) {
    // 강사 페이지 접근 권한 검증
    const userRole = authStore.user?.role
    if (userRole !== 'instructor') {
      console.log('Access denied - not instructor, redirecting to appropriate dashboard')
      if (userRole === 'admin') {
        next({ path: '/admin' })
      } else if (userRole === 'student') {
        next({ path: '/student' })
      } else {
        next({ path: '/login' })
      }
      return
    }
    console.log('Instructor access granted')
    next()
  } else {
    console.log('Normal navigation')
    next()
  }
})

export default router

// Export route helpers for navigation
export const getMenuRoutes = () => {
  const adminRoute = routes.find(route => route.path === '/admin')
  if (!adminRoute?.children) return []
  
  return adminRoute.children
    .filter(route => !route.meta?.hideInMenu)
    .map(route => ({
      ...route,
      path: route.path === '' ? '/admin' : `/admin/${route.path}`
    }))
}

export const findRouteByName = (name: string) => {
  const findRoute = (routes: RouteRecordRaw[]): RouteRecordRaw | undefined => {
    for (const route of routes) {
      if (route.name === name) return route
      if (route.children) {
        const found = findRoute(route.children)
        if (found) return found
      }
    }
  }
  
  return findRoute(routes)
}