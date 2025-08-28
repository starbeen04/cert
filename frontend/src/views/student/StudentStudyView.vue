<template>
  <div class="student-study">
    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">{{ currentCertificate?.title || 'AWS Solutions Architect' }}</h1>
        <p class="page-description">
          학습 진도: {{ completedModules }}/{{ totalModules }} 모듈 완료 ({{ studyProgress }}%)
        </p>
      </div>
      <div class="header-actions">
        <el-button type="success" @click="goToPractice">
          <el-icon><Edit /></el-icon>
          문제 풀이
        </el-button>
        <el-button type="info" @click="goToChat">
          <el-icon><ChatDotRound /></el-icon>
          AI 도우미
        </el-button>
        <el-button type="primary" @click="loadStudyData">
          <el-icon><Refresh /></el-icon>
          새로고침
        </el-button>
      </div>
    </div>

    <!-- Study Navigation -->
    <el-card class="navigation-card">
      <template #header>
        <div class="card-header">
          <span>학습 메뉴</span>
          <div class="progress-display">
            <el-progress 
              :percentage="studyProgress" 
              :stroke-width="6"
              :color="getProgressColor(studyProgress)"
            />
            <span class="progress-text">{{ studyProgress }}% 완료</span>
          </div>
        </div>
      </template>
      
      <div class="nav-buttons">
        <el-button-group>
          <el-button 
            :type="studyMode === 'modules' ? 'primary' : ''" 
            @click="studyMode = 'modules'"
          >
            <el-icon><Reading /></el-icon>
            학습 모듈
          </el-button>
          <el-button 
            :type="studyMode === 'roadmap' ? 'primary' : ''" 
            @click="studyMode = 'roadmap'"
          >
            <el-icon><Location /></el-icon>
            학습 로드맵
          </el-button>
          <el-button 
            :type="studyMode === 'notes' ? 'primary' : ''" 
            @click="studyMode = 'notes'"
          >
            <el-icon><Document /></el-icon>
            내 노트
          </el-button>
        </el-button-group>
      </div>
    </el-card>

    <!-- Study Content -->
    <div class="study-content">
      <!-- Study Modules View -->
      <el-card v-if="studyMode === 'modules'" class="content-card">
        <template #header>
          <div class="card-header">
            <span>학습 모듈</span>
          </div>
        </template>
        
        <div class="modules-list">
          <div 
            v-for="module in studyModules" 
            :key="module.id"
            class="module-item"
            :class="{ 'completed': module.completed, 'locked': module.locked, 'current': module.current }"
            @click="selectModule(module)"
          >
            <div class="module-header">
              <div class="module-info">
                <div class="module-icon">
                  <el-icon v-if="module.completed"><Check /></el-icon>
                  <el-icon v-else-if="module.locked"><Lock /></el-icon>
                  <span v-else>{{ module.order }}</span>
                </div>
                <div class="module-details">
                  <h4 class="module-title">{{ module.title }}</h4>
                  <p class="module-description">{{ module.description }}</p>
                </div>
              </div>
              <div class="module-status">
                <el-tag v-if="module.completed" type="success" size="small">완료</el-tag>
                <el-tag v-else-if="module.locked" type="info" size="small">잠김</el-tag>
                <el-tag v-else-if="module.current" type="primary" size="small">진행중</el-tag>
              </div>
            </div>
            
            <div class="module-meta">
              <div class="meta-group">
                <span class="meta-label">소요시간:</span>
                <span class="meta-value">{{ module.estimatedTime }}분</span>
              </div>
              <div class="meta-group">
                <span class="meta-label">레슨수:</span>
                <span class="meta-value">{{ module.lessons }}개</span>
              </div>
              <div v-if="module.progress > 0" class="meta-group">
                <span class="meta-label">진도:</span>
                <span class="meta-value">{{ module.progress }}%</span>
              </div>
            </div>
            
            <div v-if="module.progress > 0" class="module-progress">
              <el-progress 
                :percentage="module.progress" 
                :stroke-width="4"
                :color="module.completed ? '#67c23a' : '#409eff'"
              />
            </div>
            
            <div class="module-actions">
              <el-button 
                v-if="!module.locked"
                :type="module.current ? 'primary' : 'text'"
                size="small"
                @click.stop="startModule(module)"
              >
                {{ module.completed ? '복습하기' : module.current ? '계속하기' : '시작하기' }}
              </el-button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- Learning Roadmap View -->
      <el-card v-else-if="studyMode === 'roadmap'" class="content-card">
        <template #header>
          <div class="card-header">
            <span>학습 로드맵</span>
          </div>
        </template>
        
        <div class="roadmap-list">
          <div
            v-for="(phase, index) in learningRoadmap"
            :key="phase.id"
            class="roadmap-item"
            :class="phase.status"
          >
            <div class="roadmap-header">
              <div class="roadmap-info">
                <h4 class="roadmap-title">{{ phase.title }}</h4>
                <div class="roadmap-tags">
                  <el-tag :type="getPhaseTagType(phase.status)" size="small">
                    {{ getPhaseStatusText(phase.status) }}
                  </el-tag>
                  <span class="roadmap-timeframe">{{ phase.timeframe }}</span>
                </div>
              </div>
            </div>
            
            <div class="roadmap-content">
              <p class="roadmap-description">{{ phase.description }}</p>
              
              <div class="roadmap-topics">
                <h5>주요 학습 내용:</h5>
                <ul>
                  <li v-for="topic in phase.topics" :key="topic">{{ topic }}</li>
                </ul>
              </div>
            </div>
            
            <div class="roadmap-actions">
              <el-button 
                v-if="phase.status !== 'locked'"
                :type="phase.status === 'current' ? 'primary' : 'text'"
                size="small"
                @click="goToPhase(phase)"
              >
                {{ phase.status === 'completed' ? '복습하기' : '학습하기' }}
              </el-button>
            </div>
          </div>
        </div>
      </el-card>

      <!-- My Notes View -->
      <el-card v-else-if="studyMode === 'notes'" class="content-card">
        <template #header>
          <div class="card-header">
            <span>내 학습 노트</span>
            <el-button type="primary" size="small" @click="showNoteModal = true">
              <el-icon><Plus /></el-icon>
              새 노트 작성
            </el-button>
          </div>
        </template>
        
        <div v-if="studyNotes.length === 0" class="empty-container">
          <el-empty description="아직 작성한 노트가 없습니다">
            <el-button type="primary" @click="showNoteModal = true">
              첫 노트 작성하기
            </el-button>
          </el-empty>
        </div>
        
        <div v-else class="notes-list">
          <div 
            v-for="note in studyNotes" 
            :key="note.id"
            class="note-item"
            @click="editNote(note)"
          >
            <div class="note-header">
              <div class="note-info">
                <h4 class="note-title">{{ note.title }}</h4>
                <div class="note-tags">
                  <el-tag size="small">{{ note.module }}</el-tag>
                  <span class="note-date">{{ note.date }}</span>
                </div>
              </div>
            </div>
            
            <div class="note-content">
              <p>{{ note.content }}</p>
            </div>
            
            <div class="note-actions">
              <el-button type="text" size="small" @click.stop="editNote(note)">
                <el-icon><Edit /></el-icon>
                수정
              </el-button>
              <el-button type="text" size="small" @click.stop="deleteNote(note.id)">
                <el-icon><Delete /></el-icon>
                삭제
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- Study Module Detail Modal -->
    <el-dialog
      v-model="showModuleModal"
      :title="selectedModule?.title"
      width="800px"
      custom-class="module-detail-modal"
    >
      <div v-if="selectedModule" class="module-detail">
        <div class="module-overview">
          <div class="overview-stats">
            <div class="stat-item">
              <el-icon><Clock /></el-icon>
              <span>{{ selectedModule.estimatedTime }}분 소요</span>
            </div>
            <div class="stat-item">
              <el-icon><Document /></el-icon>
              <span>{{ selectedModule.lessons }}개 레슨</span>
            </div>
            <div class="stat-item">
              <el-icon><TrendCharts /></el-icon>
              <span>중급 난이도</span>
            </div>
          </div>
          
          <p class="module-full-description">{{ selectedModule.description }}</p>
        </div>
        
        <div class="module-lessons">
          <h3>레슨 목록</h3>
          <div class="lessons-list">
            <div 
              v-for="lesson in selectedModule.lessons_detail" 
              :key="lesson.id"
              class="lesson-item"
              :class="{ 'completed': lesson.completed }"
            >
              <div class="lesson-icon">
                <el-icon v-if="lesson.completed"><Check /></el-icon>
                <el-icon v-else><VideoPlay /></el-icon>
              </div>
              <div class="lesson-content">
                <h4>{{ lesson.title }}</h4>
                <p>{{ lesson.description }}</p>
                <span class="lesson-duration">{{ lesson.duration }}분</span>
              </div>
              <div class="lesson-actions">
                <el-button 
                  :type="lesson.completed ? 'success' : 'primary'" 
                  size="small"
                  @click="startLesson(lesson)"
                >
                  {{ lesson.completed ? '복습' : '학습' }}
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <template #footer>
        <div class="modal-actions">
          <el-button @click="showModuleModal = false">닫기</el-button>
          <el-button 
            type="primary" 
            @click="startModule(selectedModule)"
          >
            {{ selectedModule?.completed ? '복습 시작' : '학습 시작' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- Note Modal -->
    <el-dialog
      v-model="showNoteModal"
      :title="editingNote ? '노트 수정' : '새 노트 작성'"
      width="600px"
    >
      <el-form :model="noteForm" label-width="80px">
        <el-form-item label="제목">
          <el-input v-model="noteForm.title" placeholder="노트 제목을 입력하세요" />
        </el-form-item>
        <el-form-item label="모듈">
          <el-select v-model="noteForm.moduleId" placeholder="관련 모듈 선택">
            <el-option 
              v-for="module in studyModules" 
              :key="module.id"
              :label="module.title"
              :value="module.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="내용">
          <el-input 
            v-model="noteForm.content" 
            type="textarea" 
            :rows="8"
            placeholder="학습 내용이나 중요한 포인트를 기록하세요"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="modal-actions">
          <el-button @click="closeNoteModal">취소</el-button>
          <el-button type="primary" @click="saveNote">
            {{ editingNote ? '수정' : '저장' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Reading,
  Location,
  Document,
  Edit,
  ChatDotRound,
  Check,
  Lock,
  Clock,
  TrendCharts,
  VideoPlay,
  Plus,
  Delete,
  Timer,
  Refresh
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

// State
const currentCertificate = ref<any>(null)
const studyMode = ref('modules')
const showModuleModal = ref(false)
const showNoteModal = ref(false)
const selectedModule = ref<any>(null)
const editingNote = ref<any>(null)

// Study Progress
const studyProgress = ref(65)
const completedModules = ref(4)
const totalModules = ref(8)

// Study Modules Data
const studyModules = ref([
  {
    id: 1,
    order: 1,
    title: 'AWS 기초 개념',
    description: 'AWS 클라우드의 기본 개념과 핵심 서비스를 학습합니다.',
    estimatedTime: 45,
    lessons: 6,
    progress: 100,
    completed: true,
    locked: false,
    current: false,
    lessons_detail: [
      { id: 1, title: 'AWS 클라우드란?', description: 'AWS 클라우드의 기본 개념', duration: 8, completed: true },
      { id: 2, title: 'AWS 글로벌 인프라', description: '리전과 가용영역의 이해', duration: 10, completed: true },
      { id: 3, title: '핵심 서비스 개요', description: 'EC2, S3, RDS 등 주요 서비스', duration: 12, completed: true },
      { id: 4, title: 'IAM 기초', description: '보안과 권한 관리', duration: 15, completed: true }
    ]
  },
  {
    id: 2,
    order: 2,
    title: 'EC2 인스턴스 관리',
    description: 'Amazon EC2 인스턴스의 생성, 설정, 관리 방법을 학습합니다.',
    estimatedTime: 60,
    lessons: 8,
    progress: 75,
    completed: false,
    locked: false,
    current: true,
    lessons_detail: [
      { id: 5, title: 'EC2 인스턴스 유형', description: 'CPU, 메모리, 스토리지 최적화', duration: 10, completed: true },
      { id: 6, title: 'AMI 생성과 관리', description: '커스텀 이미지 만들기', duration: 12, completed: true },
      { id: 7, title: '보안 그룹 설정', description: '네트워크 방화벽 구성', duration: 15, completed: false },
      { id: 8, title: '키 페어 관리', description: 'SSH 접근 키 관리', duration: 8, completed: false }
    ]
  },
  {
    id: 3,
    order: 3,
    title: 'VPC 네트워킹',
    description: 'Virtual Private Cloud의 구성과 네트워크 설계를 학습합니다.',
    estimatedTime: 75,
    lessons: 10,
    progress: 0,
    completed: false,
    locked: false,
    current: false,
    lessons_detail: [
      { id: 9, title: 'VPC 기본 개념', description: 'Virtual Private Cloud 이해', duration: 12, completed: false },
      { id: 10, title: '서브넷 설계', description: '퍼블릭/프라이빗 서브넷', duration: 15, completed: false },
      { id: 11, title: '라우팅 테이블', description: '네트워크 트래픽 라우팅', duration: 18, completed: false }
    ]
  },
  {
    id: 4,
    order: 4,
    title: 'S3 스토리지',
    description: 'Amazon S3 객체 스토리지 서비스를 학습합니다.',
    estimatedTime: 50,
    lessons: 7,
    progress: 0,
    completed: false,
    locked: true,
    current: false,
    lessons_detail: []
  }
])

// Learning Roadmap Data
const learningRoadmap = ref([
  {
    id: 1,
    title: '1단계: AWS 기초',
    description: 'AWS 클라우드의 기본 개념과 핵심 서비스를 이해합니다.',
    status: 'completed',
    timeframe: '1-2주',
    topics: [
      'AWS 클라우드 기본 개념',
      '글로벌 인프라 구조',
      '핵심 서비스 소개',
      'IAM 기초'
    ]
  },
  {
    id: 2,
    title: '2단계: 컴퓨팅 서비스',
    description: 'EC2를 중심으로 한 컴퓨팅 서비스를 마스터합니다.',
    status: 'current',
    timeframe: '2-3주',
    topics: [
      'EC2 인스턴스 관리',
      '로드 밸런서',
      'Auto Scaling',
      'Lambda 서버리스'
    ]
  },
  {
    id: 3,
    title: '3단계: 네트워킹',
    description: 'VPC를 통한 네트워크 아키텍처 설계를 학습합니다.',
    status: 'locked',
    timeframe: '3-4주',
    topics: [
      'VPC 설계',
      '서브넷과 라우팅',
      'VPN과 DirectConnect',
      'CloudFront CDN'
    ]
  },
  {
    id: 4,
    title: '4단계: 스토리지와 데이터베이스',
    description: '다양한 스토리지 옵션과 데이터베이스 서비스를 학습합니다.',
    status: 'locked',
    timeframe: '4-5주',
    topics: [
      'S3 객체 스토리지',
      'EBS 블록 스토리지',
      'RDS 관계형 데이터베이스',
      'DynamoDB NoSQL'
    ]
  }
])

// Study Notes Data
const studyNotes = ref([
  {
    id: 1,
    title: 'IAM 정책 작성 요점',
    content: 'IAM 정책 작성 시 최소 권한 원칙을 적용하고, 조건부 접근을 활용하여 보안을 강화해야 함.',
    module: 'AWS 기초 개념',
    date: '2024-01-15'
  },
  {
    id: 2,
    title: 'EC2 인스턴스 유형 선택 기준',
    content: '워크로드 특성에 따라 CPU 최적화, 메모리 최적화, 스토리지 최적화 인스턴스를 적절히 선택.',
    module: 'EC2 인스턴스 관리',
    date: '2024-01-18'
  }
])

// Note Form
const noteForm = reactive({
  title: '',
  content: '',
  moduleId: null
})

// Computed
const getProgressColor = computed(() => (progress: number) => {
  if (progress >= 80) return '#67c23a'
  if (progress >= 60) return '#e6a23c'
  return '#f56c6c'
})

// Methods
const loadStudyData = async () => {
  try {
    const certId = route.params.id
    if (certId) {
      // 특정 자격증 학습 데이터 로드
      // const response = await fetch(`/api/student/study/${certId}`)
      // currentCertificate.value = await response.json()
    }
  } catch (error) {
    console.error('Failed to load study data:', error)
    ElMessage.error('학습 데이터를 불러오는데 실패했습니다')
  }
}

const selectModule = (module: any) => {
  if (module.locked) {
    ElMessage.warning('이전 모듈을 완료한 후 학습할 수 있습니다')
    return
  }
  selectedModule.value = module
  showModuleModal.value = true
}

const startModule = (module: any) => {
  if (!module) return
  
  showModuleModal.value = false
  ElMessage.success(`${module.title} 학습을 시작합니다`)
  // 실제 학습 페이지로 이동
  // router.push(`/student/study/module/${module.id}`)
}

const startLesson = (lesson: any) => {
  ElMessage.success(`${lesson.title} 레슨을 시작합니다`)
  // 실제 레슨 페이지로 이동
}

const goToPhase = (phase: any) => {
  ElMessage.info(`${phase.title} 단계로 이동합니다`)
}

const getPhaseTagType = (status: string) => {
  switch (status) {
    case 'completed': return 'success'
    case 'current': return 'primary'
    case 'locked': return 'info'
    default: return 'info'
  }
}

const getPhaseStatusText = (status: string) => {
  switch (status) {
    case 'completed': return '완료'
    case 'current': return '진행중'
    case 'locked': return '잠김'
    default: return '대기'
  }
}

const editNote = (note: any) => {
  editingNote.value = note
  noteForm.title = note.title
  noteForm.content = note.content
  noteForm.moduleId = studyModules.value.find(m => m.title === note.module)?.id || null
  showNoteModal.value = true
}

const closeNoteModal = () => {
  showNoteModal.value = false
  editingNote.value = null
  noteForm.title = ''
  noteForm.content = ''
  noteForm.moduleId = null
}

const saveNote = () => {
  if (!noteForm.title || !noteForm.content) {
    ElMessage.warning('제목과 내용을 입력해주세요')
    return
  }

  const module = studyModules.value.find(m => m.id === noteForm.moduleId)
  const now = new Date().toISOString().split('T')[0]

  if (editingNote.value) {
    // 기존 노트 수정
    const index = studyNotes.value.findIndex(n => n.id === editingNote.value.id)
    if (index !== -1) {
      studyNotes.value[index] = {
        ...studyNotes.value[index],
        title: noteForm.title,
        content: noteForm.content,
        module: module?.title || '',
        date: now
      }
    }
    ElMessage.success('노트가 수정되었습니다')
  } else {
    // 새 노트 추가
    const newNote = {
      id: Date.now(),
      title: noteForm.title,
      content: noteForm.content,
      module: module?.title || '',
      date: now
    }
    studyNotes.value.unshift(newNote)
    ElMessage.success('노트가 저장되었습니다')
  }

  closeNoteModal()
}

const deleteNote = async (noteId: number) => {
  try {
    await ElMessageBox.confirm('이 노트를 삭제하시겠습니까?', '확인', {
      confirmButtonText: '삭제',
      cancelButtonText: '취소',
      type: 'warning'
    })
    
    studyNotes.value = studyNotes.value.filter(note => note.id !== noteId)
    ElMessage.success('노트가 삭제되었습니다')
  } catch {
    // 취소
  }
}

const goToPractice = () => {
  router.push('/student/practice')
}

const goToChat = () => {
  router.push('/student/chat')
}

// Initialize
onMounted(() => {
  loadStudyData()
})
</script>

<style scoped>
.student-study {
  max-width: 1200px;
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

.header-actions {
  display: flex;
  gap: 8px;
}

.navigation-card, .content-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-display {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 200px;
}

.progress-text {
  font-size: 14px;
  color: #606266;
  white-space: nowrap;
}

.nav-buttons {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}

.empty-container {
  padding: 40px;
}

/* Modules List */
.modules-list {
  
}

.module-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.2s;
}

.module-item:hover {
  background: #f0f9ff;
  border-color: #409eff;
}

.module-item.completed {
  border-color: #67c23a;
  background: #f0f9ff;
}

.module-item.current {
  border-color: #409eff;
  background: #f0f9ff;
}

.module-item.locked {
  opacity: 0.6;
  cursor: not-allowed;
}

.module-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.module-info {
  display: flex;
  gap: 12px;
  flex: 1;
}

.module-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f7fa;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  flex-shrink: 0;
}

.module-details {
  flex: 1;
}

.module-title {
  margin: 0 0 4px 0;
  color: #303133;
  font-size: 16px;
}

.module-description {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.4;
}

.module-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.meta-group {
  display: flex;
  gap: 4px;
  font-size: 14px;
}

.meta-label {
  color: #909399;
}

.meta-value {
  color: #303133;
  font-weight: 500;
}

.module-progress {
  margin-bottom: 12px;
}

.module-actions {
  display: flex;
  justify-content: flex-end;
}

/* Roadmap List */
.roadmap-list {
  
}

.roadmap-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  background: #fafafa;
}

.roadmap-item.completed {
  border-color: #67c23a;
  background: #f0f9ff;
}

.roadmap-item.current {
  border-color: #409eff;
  background: #f0f9ff;
}

.roadmap-item.locked {
  opacity: 0.6;
}

.roadmap-header {
  margin-bottom: 12px;
}

.roadmap-info {
  
}

.roadmap-title {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 16px;
}

.roadmap-tags {
  display: flex;
  align-items: center;
  gap: 12px;
}

.roadmap-timeframe {
  color: #909399;
  font-size: 14px;
}

.roadmap-content {
  margin-bottom: 16px;
}

.roadmap-description {
  color: #606266;
  margin: 0 0 12px 0;
  line-height: 1.5;
}

.roadmap-topics h5 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 14px;
}

.roadmap-topics ul {
  margin: 0;
  padding-left: 20px;
  color: #606266;
}

.roadmap-topics li {
  margin: 4px 0;
}

.roadmap-actions {
  display: flex;
  justify-content: flex-end;
}

/* Notes List */
.notes-list {
  
}

.note-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.2s;
}

.note-item:hover {
  background: #f0f9ff;
  border-color: #409eff;
}

.note-header {
  margin-bottom: 12px;
}

.note-info {
  
}

.note-title {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 16px;
}

.note-tags {
  display: flex;
  align-items: center;
  gap: 12px;
}

.note-date {
  color: #909399;
  font-size: 14px;
}

.note-content {
  margin-bottom: 16px;
}

.note-content p {
  margin: 0;
  color: #606266;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.note-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

/* Modal Styles */
.module-detail {
  padding: 20px 0;
}

.module-overview {
  margin-bottom: 24px;
}

.overview-stats {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 14px;
}

.module-full-description {
  color: #606266;
  line-height: 1.6;
  margin: 0;
}

.module-lessons h3 {
  margin: 0 0 16px 0;
  color: #303133;
}

.lessons-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.lesson-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
  transition: all 0.2s;
}

.lesson-item:hover {
  background: #eef2f6;
}

.lesson-item.completed {
  background: #f0f9ff;
  border: 1px solid #67c23a;
}

.lesson-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lesson-item.completed .lesson-icon {
  background: #67c23a;
}

.lesson-content {
  flex: 1;
}

.lesson-content h4 {
  margin: 0 0 4px 0;
  color: #303133;
  font-size: 14px;
}

.lesson-content p {
  margin: 0 0 4px 0;
  color: #606266;
  font-size: 13px;
}

.lesson-duration {
  font-size: 12px;
  color: #909399;
}

.lesson-actions {
  display: flex;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .progress-display {
    flex-direction: column;
    align-items: flex-start;
    min-width: auto;
  }
  
  .nav-buttons {
    overflow-x: auto;
  }
  
  .module-info {
    flex-direction: column;
    gap: 8px;
  }
  
  .module-icon {
    align-self: flex-start;
  }
  
  .module-meta {
    flex-direction: column;
    gap: 8px;
  }
  
  .overview-stats {
    flex-direction: column;
    gap: 12px;
  }
  
  .lesson-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>