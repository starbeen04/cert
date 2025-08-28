<template>
  <div class="student-profile">
    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">프로필 & 설정</h1>
        <p class="page-description">
          계정 정보와 학습 환경을 관리하세요
        </p>
      </div>
      <el-button type="primary" @click="refreshData">
        <el-icon><Refresh /></el-icon>
        새로고침
      </el-button>
    </div>

    <!-- Navigation Tabs -->
    <el-card class="navigation-card">
      <template #header>
        <div class="card-header">
          <span>설정 메뉴</span>
        </div>
      </template>
      
      <div class="nav-tabs">
        <el-button-group>
          <el-button
            :type="activeSection === 'profile' ? 'primary' : ''"
            @click="switchSection('profile')"
          >
            <el-icon><User /></el-icon>
            프로필 정보
          </el-button>
          <el-button
            :type="activeSection === 'settings' ? 'primary' : ''"
            @click="switchSection('settings')"
          >
            <el-icon><Setting /></el-icon>
            학습 설정
          </el-button>
          <el-button
            :type="activeSection === 'notifications' ? 'primary' : ''"
            @click="switchSection('notifications')"
          >
            <el-icon><Bell /></el-icon>
            알림 설정
          </el-button>
          <el-button
            :type="activeSection === 'security' ? 'primary' : ''"
            @click="switchSection('security')"
          >
            <el-icon><Lock /></el-icon>
            보안 설정
          </el-button>
          <el-button
            :type="activeSection === 'achievements' ? 'primary' : ''"
            @click="switchSection('achievements')"
          >
            <el-icon><Trophy /></el-icon>
            성취 배지
          </el-button>
          <el-button
            :type="activeSection === 'statistics' ? 'primary' : ''"
            @click="switchSection('statistics')"
          >
            <el-icon><DataAnalysis /></el-icon>
            학습 통계
          </el-button>
        </el-button-group>
      </div>
    </el-card>

    <!-- Profile Content -->
    <div class="content-section">
      <!-- Profile Information -->
      <el-card v-if="activeSection === 'profile'" class="content-card">
        <template #header>
          <div class="card-header">
            <span>프로필 정보</span>
          </div>
        </template>
            
            <div class="profile-info">
              <!-- Avatar Section -->
              <div class="avatar-section">
                <div class="avatar-container">
                  <el-avatar
                    :size="100"
                    :src="userProfile.avatar"
                    class="profile-avatar"
                  >
                    {{ userProfile.username?.charAt(0).toUpperCase() }}
                  </el-avatar>
                  <el-upload
                    class="avatar-uploader"
                    action="#"
                    :show-file-list="false"
                    :on-change="handleAvatarChange"
                    :auto-upload="false"
                  >
                    <el-button size="small" :icon="Camera">
                      변경
                    </el-button>
                  </el-upload>
                </div>
                
                <div class="profile-basic">
                  <h3>{{ userProfile.username }}</h3>
                  <p class="user-email">{{ userProfile.email }}</p>
                  <el-tag type="primary" size="small">
                    {{ userProfile.role === 'student' ? '학습자' : '관리자' }}
                  </el-tag>
                </div>
              </div>

              <!-- Profile Form -->
              <el-form
                :model="userProfile"
                :rules="profileRules"
                label-width="120px"
                class="profile-form"
              >
                <el-form-item label="사용자명" prop="username">
                  <el-input v-model="userProfile.username" />
                </el-form-item>
                
                <el-form-item label="이메일" prop="email">
                  <el-input v-model="userProfile.email" type="email" />
                </el-form-item>
                
                <el-form-item label="전화번호" prop="phone">
                  <el-input v-model="userProfile.phone" />
                </el-form-item>
                
                <el-form-item label="생년월일" prop="birth_date">
                  <el-date-picker
                    v-model="userProfile.birth_date"
                    type="date"
                    placeholder="생년월일 선택"
                    style="width: 100%"
                  />
                </el-form-item>
                
                <el-form-item label="관심 분야">
                  <el-select
                    v-model="userProfile.interests"
                    multiple
                    placeholder="관심 있는 자격증 분야를 선택하세요"
                    style="width: 100%"
                  >
                    <el-option label="클라우드 컴퓨팅" value="cloud" />
                    <el-option label="보안" value="security" />
                    <el-option label="네트워킹" value="networking" />
                    <el-option label="데이터베이스" value="database" />
                    <el-option label="프로그래밍" value="programming" />
                    <el-option label="AI/ML" value="ai_ml" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="자기소개">
                  <el-input
                    v-model="userProfile.bio"
                    type="textarea"
                    :rows="4"
                    placeholder="간단한 자기소개를 작성해보세요"
                  />
                </el-form-item>
                
                <el-form-item>
                  <el-button type="primary" @click="saveProfile">
                    프로필 저장
                  </el-button>
                  <el-button @click="resetProfile">
                    초기화
                  </el-button>
                </el-form-item>
              </el-form>
            </div>
      </el-card>

      <!-- Learning Settings -->
      <el-card v-else-if="activeSection === 'settings'" class="content-card">
        <template #header>
          <div class="card-header">
            <span>학습 설정</span>
          </div>
        </template>
            
            <el-form :model="learningSettings" label-width="150px">
              <el-form-item label="일일 학습 목표">
                <el-slider
                  v-model="learningSettings.daily_goal_minutes"
                  :min="15"
                  :max="240"
                  :step="15"
                  :format-tooltip="formatTimeTooltip"
                  show-input
                  input-size="small"
                />
                <span class="setting-desc">매일 학습할 목표 시간을 설정하세요</span>
              </el-form-item>
              
              <el-form-item label="학습 알림">
                <el-switch
                  v-model="learningSettings.study_reminders"
                  active-text="활성화"
                  inactive-text="비활성화"
                />
                <span class="setting-desc">설정한 시간에 학습 알림을 받습니다</span>
              </el-form-item>
              
              <el-form-item 
                v-if="learningSettings.study_reminders"
                label="알림 시간"
              >
                <el-time-picker
                  v-model="learningSettings.reminder_time"
                  placeholder="알림 시간 선택"
                  format="HH:mm"
                  value-format="HH:mm"
                />
              </el-form-item>
              
              <el-form-item label="자동 저장">
                <el-switch
                  v-model="learningSettings.auto_save"
                  active-text="활성화"
                  inactive-text="비활성화"
                />
                <span class="setting-desc">학습 진도를 자동으로 저장합니다</span>
              </el-form-item>
              
              <el-form-item label="문제 풀이 모드">
                <el-radio-group v-model="learningSettings.practice_mode">
                  <el-radio value="immediate">즉시 정답 확인</el-radio>
                  <el-radio value="end">마지막에 일괄 확인</el-radio>
                </el-radio-group>
              </el-form-item>
              
              <el-form-item label="난이도 조절">
                <el-switch
                  v-model="learningSettings.adaptive_difficulty"
                  active-text="활성화"
                  inactive-text="비활성화"
                />
                <span class="setting-desc">학습 성과에 따라 문제 난이도를 자동 조절합니다</span>
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="saveLearningSettings">
                  설정 저장
                </el-button>
              </el-form-item>
            </el-form>
      </el-card>

      <!-- Notification Settings -->
      <el-card v-else-if="activeSection === 'notifications'" class="content-card">
        <template #header>
          <div class="card-header">
            <span>알림 설정</span>
          </div>
        </template>
            
            <el-form :model="notificationSettings" label-width="180px">
              <el-form-item label="이메일 알림">
                <el-switch
                  v-model="notificationSettings.email_enabled"
                  active-text="활성화"
                  inactive-text="비활성화"
                />
              </el-form-item>
              
              <div v-if="notificationSettings.email_enabled" class="notification-options">
                <el-form-item label="학습 진도 알림">
                  <el-checkbox v-model="notificationSettings.progress_updates">
                    주간 학습 진도 리포트
                  </el-checkbox>
                </el-form-item>
                
                <el-form-item label="시험 일정 알림">
                  <el-checkbox v-model="notificationSettings.exam_reminders">
                    자격증 시험 일정 알림
                  </el-checkbox>
                </el-form-item>
                
                <el-form-item label="새 기능 알림">
                  <el-checkbox v-model="notificationSettings.feature_updates">
                    새로운 기능 및 업데이트 알림
                  </el-checkbox>
                </el-form-item>
                
                <el-form-item label="마케팅 이메일">
                  <el-checkbox v-model="notificationSettings.marketing_emails">
                    할인 및 프로모션 정보
                  </el-checkbox>
                </el-form-item>
              </div>
              
              <el-form-item label="브라우저 알림">
                <el-switch
                  v-model="notificationSettings.browser_enabled"
                  active-text="활성화"
                  inactive-text="비활성화"
                />
              </el-form-item>
              
              <el-form-item label="모바일 알림">
                <el-switch
                  v-model="notificationSettings.mobile_enabled"
                  active-text="활성화"
                  inactive-text="비활성화"
                />
              </el-form-item>
              
              <el-form-item>
                <el-button type="primary" @click="saveNotificationSettings">
                  알림 설정 저장
                </el-button>
              </el-form-item>
            </el-form>
      </el-card>

      <!-- Security Settings -->
      <el-card v-else-if="activeSection === 'security'" class="content-card">
        <template #header>
          <div class="card-header">
            <span>보안 설정</span>
          </div>
        </template>
            
            <div class="security-sections">
              <!-- Password Change -->
              <div class="security-section">
                <h3>비밀번호 변경</h3>
                <el-form
                  :model="passwordForm"
                  :rules="passwordRules"
                  label-width="120px"
                  class="password-form"
                >
                  <el-form-item label="현재 비밀번호" prop="current_password">
                    <el-input
                      v-model="passwordForm.current_password"
                      type="password"
                      show-password
                    />
                  </el-form-item>
                  
                  <el-form-item label="새 비밀번호" prop="new_password">
                    <el-input
                      v-model="passwordForm.new_password"
                      type="password"
                      show-password
                    />
                  </el-form-item>
                  
                  <el-form-item label="비밀번호 확인" prop="confirm_password">
                    <el-input
                      v-model="passwordForm.confirm_password"
                      type="password"
                      show-password
                    />
                  </el-form-item>
                  
                  <el-form-item>
                    <el-button type="primary" @click="changePassword">
                      비밀번호 변경
                    </el-button>
                  </el-form-item>
                </el-form>
              </div>

              <!-- Two-Factor Authentication -->
              <div class="security-section">
                <h3>2단계 인증</h3>
                <div class="two-factor-status">
                  <div class="status-info">
                    <el-icon :class="twoFactorEnabled ? 'enabled' : 'disabled'">
                      <component :is="twoFactorEnabled ? 'SuccessFilled' : 'WarningFilled'" />
                    </el-icon>
                    <span>{{ twoFactorEnabled ? '활성화됨' : '비활성화됨' }}</span>
                  </div>
                  
                  <el-button
                    :type="twoFactorEnabled ? 'danger' : 'primary'"
                    @click="toggleTwoFactor"
                  >
                    {{ twoFactorEnabled ? '비활성화' : '활성화' }}
                  </el-button>
                </div>
                <p class="security-desc">
                  2단계 인증을 활성화하여 계정 보안을 강화하세요
                </p>
              </div>

              <!-- Session Management -->
              <div class="security-section">
                <h3>세션 관리</h3>
                <div class="active-sessions">
                  <div
                    v-for="session in activeSessions"
                    :key="session.id"
                    class="session-item"
                  >
                    <div class="session-info">
                      <div class="session-device">
                        <el-icon><Monitor /></el-icon>
                        <span>{{ session.device }}</span>
                      </div>
                      <div class="session-details">
                        <span class="session-location">{{ session.location }}</span>
                        <span class="session-time">{{ formatSessionTime(session.last_active) }}</span>
                      </div>
                    </div>
                    
                    <el-button
                      v-if="!session.current"
                      type="text"
                      @click="terminateSession(session.id)"
                    >
                      종료
                    </el-button>
                    <el-tag v-else type="success" size="small">현재 세션</el-tag>
                  </div>
                </div>
                
                <el-button type="danger" @click="terminateAllSessions">
                  모든 세션 종료
                </el-button>
              </div>
            </div>
      </el-card>

      <!-- Achievements -->
      <el-card v-else-if="activeSection === 'achievements'" class="content-card">
        <template #header>
          <div class="card-header">
            <span>성취 및 배지</span>
          </div>
        </template>
            
            <div class="achievements-overview">
              <div class="achievement-stats">
                <div class="stat-card">
                  <div class="stat-icon">🏆</div>
                  <div class="stat-info">
                    <div class="stat-number">{{ achievements.total_badges }}</div>
                    <div class="stat-label">획득한 배지</div>
                  </div>
                </div>
                
                <div class="stat-card">
                  <div class="stat-icon">📚</div>
                  <div class="stat-info">
                    <div class="stat-number">{{ achievements.completed_courses }}</div>
                    <div class="stat-label">완료한 학습</div>
                  </div>
                </div>
                
                <div class="stat-card">
                  <div class="stat-icon">🎯</div>
                  <div class="stat-info">
                    <div class="stat-number">{{ achievements.study_streak }}</div>
                    <div class="stat-label">연속 학습일</div>
                  </div>
                </div>
              </div>
              
              <div class="badges-grid">
                <div
                  v-for="badge in badges"
                  :key="badge.id"
                  :class="['badge-item', { earned: badge.earned }]"
                >
                  <div class="badge-icon">{{ badge.icon }}</div>
                  <div class="badge-info">
                    <h4>{{ badge.name }}</h4>
                    <p>{{ badge.description }}</p>
                    <div v-if="badge.earned" class="badge-earned">
                      <el-icon><Check /></el-icon>
                      <span>{{ formatDate(badge.earned_date) }}에 획득</span>
                    </div>
                    <div v-else class="badge-progress">
                      <el-progress
                        :percentage="badge.progress"
                        :color="badge.progress >= 100 ? '#67c23a' : '#409eff'"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
      </el-card>

      <!-- Statistics -->
      <el-card v-else-if="activeSection === 'statistics'" class="content-card">
        <template #header>
          <div class="card-header">
            <span>학습 통계</span>
          </div>
        </template>
            
            <div class="statistics-overview">
              <!-- Overview Cards -->
              <div class="stats-cards">
                <div class="stats-card">
                  <div class="card-header">
                    <h3>총 학습 시간</h3>
                    <el-icon><Clock /></el-icon>
                  </div>
                  <div class="card-value">{{ statistics.total_study_time }}시간</div>
                  <div class="card-change positive">
                    +12% 지난달 대비
                  </div>
                </div>
                
                <div class="stats-card">
                  <div class="card-header">
                    <h3>문제 해결</h3>
                    <el-icon><EditPen /></el-icon>
                  </div>
                  <div class="card-value">{{ statistics.problems_solved }}문제</div>
                  <div class="card-change positive">
                    +8% 지난달 대비
                  </div>
                </div>
                
                <div class="stats-card">
                  <div class="card-header">
                    <h3>평균 정확도</h3>
                    <el-icon><TrendCharts /></el-icon>
                  </div>
                  <div class="card-value">{{ statistics.average_accuracy }}%</div>
                  <div class="card-change positive">
                    +5% 지난달 대비
                  </div>
                </div>
                
                <div class="stats-card">
                  <div class="card-header">
                    <h3>학습 연속일</h3>
                    <el-icon><Calendar /></el-icon>
                  </div>
                  <div class="card-value">{{ statistics.current_streak }}일</div>
                  <div class="card-change">
                    최고 기록: {{ statistics.longest_streak }}일
                  </div>
                </div>
              </div>
              
              <!-- Weekly Progress Chart -->
              <div class="chart-section">
                <h3>주간 학습 진도</h3>
                <div class="chart-placeholder">
                  <p>📊 학습 진도 차트가 여기에 표시됩니다</p>
                  <small>차트 라이브러리 연동 예정</small>
                </div>
              </div>
              
              <!-- Learning Calendar -->
              <div class="calendar-section">
                <h3>학습 캘린더</h3>
                <div class="calendar-placeholder">
                  <p>📅 학습 캘린더가 여기에 표시됩니다</p>
                  <small>달력 컴포넌트 연동 예정</small>
                </div>
              </div>
            </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  User,
  Setting,
  Bell,
  Lock,
  Trophy,
  DataAnalysis,
  Camera,
  Check,
  Monitor,
  Clock,
  EditPen,
  TrendCharts,
  Calendar,
  Refresh
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { formatDate } from '@/utils/format'

const userStore = useAuthStore()

// State
const activeSection = ref('profile')

// User Profile
const userProfile = reactive({
  username: 'test_student',
  email: 'student@example.com',
  phone: '',
  birth_date: null,
  interests: ['cloud', 'security'],
  bio: '',
  avatar: '',
  role: 'student'
})

const originalProfile = reactive({ ...userProfile })

// Learning Settings
const learningSettings = reactive({
  daily_goal_minutes: 60,
  study_reminders: true,
  reminder_time: '20:00',
  auto_save: true,
  practice_mode: 'immediate',
  adaptive_difficulty: true
})

// Notification Settings
const notificationSettings = reactive({
  email_enabled: true,
  progress_updates: true,
  exam_reminders: true,
  feature_updates: false,
  marketing_emails: false,
  browser_enabled: true,
  mobile_enabled: false
})

// Security
const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: ''
})

const twoFactorEnabled = ref(false)

const activeSessions = ref([
  {
    id: 1,
    device: 'Chrome on Windows',
    location: '서울, 대한민국',
    last_active: new Date(),
    current: true
  },
  {
    id: 2,
    device: 'Safari on iPhone',
    location: '서울, 대한민국',
    last_active: new Date(Date.now() - 2 * 60 * 60 * 1000),
    current: false
  }
])

// Achievements
const achievements = reactive({
  total_badges: 8,
  completed_courses: 12,
  study_streak: 15
})

const badges = ref([
  {
    id: 1,
    name: '첫 걸음',
    description: '첫 번째 학습 완료',
    icon: '🎯',
    earned: true,
    earned_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
    progress: 100
  },
  {
    id: 2,
    name: '꾸준함의 힘',
    description: '7일 연속 학습',
    icon: '🔥',
    earned: true,
    earned_date: new Date(Date.now() - 15 * 24 * 60 * 60 * 1000),
    progress: 100
  },
  {
    id: 3,
    name: '문제 해결사',
    description: '100문제 해결',
    icon: '🧩',
    earned: false,
    progress: 75
  },
  {
    id: 4,
    name: '시험 마스터',
    description: '첫 모의고사 80점 이상',
    icon: '📝',
    earned: false,
    progress: 50
  }
])

// Statistics
const statistics = reactive({
  total_study_time: 48,
  problems_solved: 324,
  average_accuracy: 82,
  current_streak: 15,
  longest_streak: 23
})

// Form Rules
const profileRules = {
  username: [
    { required: true, message: '사용자명을 입력해주세요', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '이메일을 입력해주세요', trigger: 'blur' },
    { type: 'email', message: '올바른 이메일 형식을 입력해주세요', trigger: 'blur' }
  ]
}

const passwordRules = {
  current_password: [
    { required: true, message: '현재 비밀번호를 입력해주세요', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '새 비밀번호를 입력해주세요', trigger: 'blur' },
    { min: 6, message: '비밀번호는 최소 6자리 이상이어야 합니다', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '비밀번호 확인을 입력해주세요', trigger: 'blur' },
    {
      validator: (rule: any, value: string, callback: Function) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('비밀번호가 일치하지 않습니다'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// Methods
const refreshData = () => {
  ElMessage.success('데이터를 새로고침했습니다')
}

const switchSection = (section: string) => {
  activeSection.value = section
}

const handleAvatarChange = (file: any) => {
  ElMessage.info('아바타 업로드 기능은 곧 제공될 예정입니다')
}

const saveProfile = () => {
  ElMessage.success('프로필이 저장되었습니다')
}

const resetProfile = () => {
  Object.assign(userProfile, originalProfile)
  ElMessage.info('프로필이 초기화되었습니다')
}

const saveLearningSettings = () => {
  ElMessage.success('학습 설정이 저장되었습니다')
}

const saveNotificationSettings = () => {
  ElMessage.success('알림 설정이 저장되었습니다')
}

const changePassword = () => {
  if (!passwordForm.current_password || !passwordForm.new_password || !passwordForm.confirm_password) {
    ElMessage.warning('모든 필드를 입력해주세요')
    return
  }
  
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    ElMessage.error('새 비밀번호가 일치하지 않습니다')
    return
  }
  
  ElMessage.success('비밀번호가 변경되었습니다')
  Object.assign(passwordForm, {
    current_password: '',
    new_password: '',
    confirm_password: ''
  })
}

const toggleTwoFactor = () => {
  twoFactorEnabled.value = !twoFactorEnabled.value
  ElMessage.success(
    twoFactorEnabled.value 
      ? '2단계 인증이 활성화되었습니다' 
      : '2단계 인증이 비활성화되었습니다'
  )
}

const terminateSession = (sessionId: number) => {
  activeSessions.value = activeSessions.value.filter(s => s.id !== sessionId)
  ElMessage.success('세션이 종료되었습니다')
}

const terminateAllSessions = async () => {
  try {
    await ElMessageBox.confirm(
      '현재 세션을 제외한 모든 세션이 종료됩니다. 계속하시겠습니까?',
      '확인',
      {
        confirmButtonText: '종료',
        cancelButtonText: '취소',
        type: 'warning'
      }
    )
    
    activeSessions.value = activeSessions.value.filter(s => s.current)
    ElMessage.success('모든 세션이 종료되었습니다')
  } catch {
    // 취소
  }
}

const formatTimeTooltip = (value: number) => {
  const hours = Math.floor(value / 60)
  const minutes = value % 60
  return hours > 0 ? `${hours}시간 ${minutes}분` : `${minutes}분`
}

const formatSessionTime = (time: Date) => {
  const now = new Date()
  const diff = now.getTime() - time.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  
  if (minutes < 1) return '방금 전'
  if (minutes < 60) return `${minutes}분 전`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}시간 전`
  
  const days = Math.floor(hours / 24)
  return `${days}일 전`
}

// Initialize
onMounted(() => {
  // Load user data if needed
})
</script>

<style scoped>
.student-profile {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  margin: 0;
  color: #303133;
}

.page-description {
  margin: 8px 0 0 0;
  color: #606266;
}

.navigation-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-tabs {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}

.content-section {
  
}

.content-card {
  margin-bottom: 24px;
}

.profile-info {
  
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e4e7ed;
}

.avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.profile-avatar {
  background: #409eff;
  color: white;
  font-size: 36px;
  font-weight: 600;
}

.profile-basic h3 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 20px;
}

.user-email {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 14px;
}

.profile-form {
  max-width: 600px;
}

.setting-desc {
  display: block;
  font-size: 13px;
  color: #909399;
  margin-top: 4px;
}

.notification-options {
  margin-left: 20px;
  padding-left: 20px;
  border-left: 2px solid #e4e7ed;
}

.security-sections {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.security-section {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.security-section h3 {
  margin: 0 0 16px 0;
  color: #303133;
}

.password-form {
  max-width: 400px;
}

.two-factor-status {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-info .enabled {
  color: #67c23a;
}

.status-info .disabled {
  color: #f56c6c;
}

.security-desc {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.active-sessions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.session-device {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #303133;
}

.session-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: #909399;
}

.achievements-overview {
  
}

.achievement-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.stat-icon {
  font-size: 24px;
}

.stat-number {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 14px;
  color: #606266;
}

.badges-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

.badge-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  background: #fafafa;
  transition: all 0.2s;
}

.badge-item.earned {
  border-color: #67c23a;
  background: #f0f9ff;
}

.badge-item:not(.earned) {
  opacity: 0.7;
}

.badge-icon {
  font-size: 24px;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  border-radius: 8px;
}

.badge-item.earned .badge-icon {
  background: #67c23a;
  color: white;
}

.badge-info {
  flex: 1;
}

.badge-info h4 {
  margin: 0 0 4px 0;
  color: #303133;
  font-size: 14px;
}

.badge-info p {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 13px;
}

.badge-earned {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #67c23a;
}

.badge-progress {
  margin-top: 8px;
}

.statistics-overview {
  
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stats-card {
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
}

.stats-card .card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.stats-card .card-header h3 {
  margin: 0;
  color: #303133;
  font-size: 14px;
}

.card-value {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 6px;
}

.card-change {
  font-size: 12px;
  color: #606266;
}

.card-change.positive {
  color: #67c23a;
}

.chart-section,
.calendar-section {
  margin-bottom: 24px;
}

.chart-section h3,
.calendar-section h3 {
  margin: 0 0 16px 0;
  color: #303133;
}

.chart-placeholder,
.calendar-placeholder {
  height: 200px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #606266;
}

.chart-placeholder small,
.calendar-placeholder small {
  margin-top: 8px;
  color: #909399;
}

/* 반응형 디자인 */
@media (max-width: 1024px) {
  .nav-tabs {
    overflow-x: auto;
    justify-content: flex-start;
  }
  
  .nav-tabs .el-button-group {
    display: flex;
    white-space: nowrap;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .nav-tabs .el-button-group {
    flex-direction: column;
    width: 100%;
  }
  
  .avatar-section {
    flex-direction: column;
    text-align: center;
  }
  
  .achievement-stats {
    grid-template-columns: 1fr;
  }
  
  .badges-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-cards {
    grid-template-columns: 1fr;
  }
  
  .session-item {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .two-factor-status {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>