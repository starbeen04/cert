<template>
  <div class="instructor-collaboration">
    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">강사 협업</h1>
        <p class="page-description">
          같은 자격증 분야의 강사들과 정보를 공유하고 협업하세요.
        </p>
      </div>
      <div class="header-actions">
        <el-button type="success" @click="showNewDiscussionModal = true">
          <el-icon><ChatDotRound /></el-icon>
          새 토론 시작
        </el-button>
        <el-button type="primary" @click="showResourceModal = true">
          <el-icon><Share /></el-icon>
          자료 공유
        </el-button>
      </div>
    </div>

    <div class="collaboration-content">
      <!-- 좌측: 토론 목록 -->
      <div class="discussions-section">
        <el-card class="discussions-card">
          <template #header>
            <div class="card-header">
              <span>토론 목록</span>
              <el-select
                v-model="selectedCategory"
                placeholder="자격증 선택"
                size="small"
                style="width: 180px;"
              >
                <el-option label="모든 자격증" value="" />
                <el-option 
                  v-for="cert in certificates" 
                  :key="cert.id" 
                  :label="cert.name" 
                  :value="cert.id" 
                />
              </el-select>
            </div>
          </template>

          <div class="discussions-list">
            <div 
              v-for="discussion in filteredDiscussions" 
              :key="discussion.id"
              class="discussion-item"
              :class="{ active: selectedDiscussion?.id === discussion.id }"
              @click="selectDiscussion(discussion)"
            >
              <div class="discussion-header">
                <div class="discussion-title">{{ discussion.title }}</div>
                <div class="discussion-time">{{ formatTime(discussion.lastActivity) }}</div>
              </div>
              <div class="discussion-meta">
                <span class="author">{{ discussion.author }}</span>
                <el-tag :type="getCategoryType(discussion.category)" size="small">
                  {{ discussion.categoryName }}
                </el-tag>
                <span class="replies">{{ discussion.replyCount }}개 답변</span>
              </div>
              <div class="discussion-preview">{{ discussion.preview }}</div>
              <div v-if="discussion.isNew" class="new-badge">
                <el-tag type="danger" size="small">NEW</el-tag>
              </div>
            </div>
          </div>

          <div v-if="filteredDiscussions.length === 0" class="empty-state">
            <el-empty description="토론이 없습니다" />
          </div>
        </el-card>
      </div>

      <!-- 우측: 토론 상세 및 댓글 -->
      <div class="discussion-detail-section">
        <el-card v-if="!selectedDiscussion" class="welcome-card">
          <div class="welcome-content">
            <el-icon size="64" color="#c0c4cc">
              <ChatDotRound />
            </el-icon>
            <h3>토론을 선택하세요</h3>
            <p>좌측에서 토론을 선택하여 내용을 확인하고 참여하세요.</p>
          </div>
        </el-card>

        <div v-else class="discussion-detail">
          <!-- 토론 헤더 -->
          <el-card class="discussion-header-card">
            <div class="discussion-info">
              <div class="discussion-title-section">
                <h2 class="discussion-title">{{ selectedDiscussion.title }}</h2>
                <div class="discussion-tags">
                  <el-tag :type="getCategoryType(selectedDiscussion.category)">
                    {{ selectedDiscussion.categoryName }}
                  </el-tag>
                  <el-tag v-if="selectedDiscussion.isPinned" type="warning" size="small">
                    📌 고정됨
                  </el-tag>
                </div>
              </div>
              <div class="discussion-meta">
                <div class="author-info">
                  <el-avatar :size="32">{{ selectedDiscussion.author.charAt(0) }}</el-avatar>
                  <div class="author-details">
                    <div class="author-name">{{ selectedDiscussion.author }}</div>
                    <div class="post-time">{{ formatDateTime(selectedDiscussion.createdAt) }}</div>
                  </div>
                </div>
                <div class="discussion-actions">
                  <el-button size="small" @click="likeDiscussion">
                    <el-icon><Like /></el-icon>
                    {{ selectedDiscussion.likes }}
                  </el-button>
                  <el-button size="small" @click="shareDiscussion">
                    <el-icon><Share /></el-icon>
                    공유
                  </el-button>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 토론 내용 -->
          <el-card class="discussion-content-card">
            <div class="discussion-content" v-html="selectedDiscussion.content"></div>
            
            <!-- 첨부 파일 -->
            <div v-if="selectedDiscussion.attachments" class="attachments">
              <h4>첨부 파일</h4>
              <div class="attachment-list">
                <div 
                  v-for="file in selectedDiscussion.attachments" 
                  :key="file.id"
                  class="attachment-item"
                >
                  <el-icon><Document /></el-icon>
                  <span class="filename">{{ file.name }}</span>
                  <el-button type="text" size="small" @click="downloadFile(file)">
                    다운로드
                  </el-button>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 댓글 목록 -->
          <el-card class="replies-card">
            <template #header>
              <span>댓글 ({{ selectedDiscussion.replies.length }})</span>
            </template>

            <div class="replies-list">
              <div 
                v-for="reply in selectedDiscussion.replies" 
                :key="reply.id"
                class="reply-item"
              >
                <div class="reply-header">
                  <el-avatar :size="28">{{ reply.author.charAt(0) }}</el-avatar>
                  <div class="reply-info">
                    <span class="reply-author">{{ reply.author }}</span>
                    <span class="reply-time">{{ formatTime(reply.createdAt) }}</span>
                  </div>
                  <div class="reply-actions">
                    <el-button type="text" size="small" @click="likeReply(reply)">
                      <el-icon><Like /></el-icon>
                      {{ reply.likes }}
                    </el-button>
                  </div>
                </div>
                <div class="reply-content">{{ reply.content }}</div>
              </div>
            </div>

            <!-- 댓글 작성 -->
            <div class="reply-form">
              <el-input
                v-model="newReply"
                type="textarea"
                :rows="3"
                placeholder="댓글을 입력하세요..."
                resize="none"
              />
              <div class="reply-form-actions">
                <el-button size="small" @click="newReply = ''">취소</el-button>
                <el-button type="primary" size="small" @click="submitReply">
                  댓글 작성
                </el-button>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </div>

    <!-- 새 토론 시작 모달 -->
    <el-dialog
      v-model="showNewDiscussionModal"
      title="새 토론 시작"
      width="600px"
    >
      <el-form :model="newDiscussionForm" label-width="100px">
        <el-form-item label="자격증" required>
          <el-select v-model="newDiscussionForm.category" placeholder="자격증을 선택하세요">
            <el-option 
              v-for="cert in certificates" 
              :key="cert.id" 
              :label="cert.name" 
              :value="cert.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="제목" required>
          <el-input v-model="newDiscussionForm.title" placeholder="토론 제목을 입력하세요" />
        </el-form-item>
        <el-form-item label="내용" required>
          <el-input
            v-model="newDiscussionForm.content"
            type="textarea"
            :rows="6"
            placeholder="토론 내용을 입력하세요..."
          />
        </el-form-item>
        <el-form-item label="파일 첨부">
          <el-upload
            drag
            action="/api/upload"
            multiple
            :on-success="handleFileUpload"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              클릭하거나 파일을 드래그하여 업로드
            </div>
          </el-upload>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showNewDiscussionModal = false">취소</el-button>
          <el-button type="primary" @click="createDiscussion">
            토론 시작
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 자료 공유 모달 -->
    <el-dialog
      v-model="showResourceModal"
      title="자료 공유"
      width="500px"
    >
      <el-form :model="resourceForm" label-width="80px">
        <el-form-item label="제목" required>
          <el-input v-model="resourceForm.title" placeholder="자료 제목" />
        </el-form-item>
        <el-form-item label="설명">
          <el-input
            v-model="resourceForm.description"
            type="textarea"
            :rows="3"
            placeholder="자료에 대한 설명을 입력하세요"
          />
        </el-form-item>
        <el-form-item label="자격증" required>
          <el-select v-model="resourceForm.category" placeholder="관련 자격증">
            <el-option 
              v-for="cert in certificates" 
              :key="cert.id" 
              :label="cert.name" 
              :value="cert.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="파일" required>
          <el-upload
            drag
            action="/api/upload"
            :on-success="handleResourceUpload"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              공유할 파일을 업로드하세요
            </div>
          </el-upload>
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showResourceModal = false">취소</el-button>
          <el-button type="primary" @click="shareResource">
            공유하기
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ChatDotRound,
  Share,
  Like,
  Document,
  UploadFilled
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 상태
const selectedCategory = ref('')
const selectedDiscussion = ref(null)
const newReply = ref('')
const showNewDiscussionModal = ref(false)
const showResourceModal = ref(false)

// 폼 데이터
const newDiscussionForm = ref({
  category: '',
  title: '',
  content: '',
  attachments: []
})

const resourceForm = ref({
  title: '',
  description: '',
  category: '',
  file: null
})

// 자격증 목록
const certificates = ref([
  { id: 1, name: 'AWS Solutions Architect Associate' },
  { id: 2, name: 'Google Cloud Professional Cloud Architect' },
  { id: 3, name: 'Microsoft Azure Fundamentals' },
  { id: 4, name: 'CompTIA Security+' },
  { id: 5, name: 'CISSP' }
])

// 토론 데이터 (실제로는 API에서 가져올 예정)
const discussions = ref([
  {
    id: 1,
    title: 'AWS 자격증 문제 출제 방향 논의',
    author: '김강사',
    category: 1,
    categoryName: 'AWS Solutions Architect Associate',
    content: `<p>안녕하세요 강사님들,</p>
              <p>AWS 자격증 시험의 최신 동향을 반영하여 문제 출제 방향을 논의하고 싶습니다.</p>
              <p>특히 다음 영역에 대해 의견을 나누고 싶어요:</p>
              <ul>
                <li>서버리스 아키텍처 (Lambda, API Gateway)</li>
                <li>컨테이너 서비스 (ECS, EKS)</li>
                <li>최신 보안 서비스들</li>
              </ul>
              <p>각자의 경험과 인사이트를 공유해주시면 감사하겠습니다!</p>`,
    preview: 'AWS 자격증 시험의 최신 동향을 반영하여 문제 출제 방향을 논의하고 싶습니다...',
    createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000),
    lastActivity: new Date(Date.now() - 30 * 60 * 1000),
    replyCount: 8,
    likes: 12,
    isPinned: true,
    isNew: false,
    attachments: [
      { id: 1, name: 'AWS_출제_가이드.pdf', url: '/files/aws-guide.pdf' }
    ],
    replies: [
      {
        id: 1,
        author: '이교수',
        content: '좋은 주제네요! 저는 최근 서버리스 분야의 문제를 많이 출제하고 있는데, 학습자들의 반응이 좋습니다.',
        createdAt: new Date(Date.now() - 90 * 60 * 1000),
        likes: 5
      },
      {
        id: 2,
        author: '박강사',
        content: '컨테이너 서비스 관련해서는 실제 실습 경험을 바탕으로 한 문제가 효과적인 것 같아요. 실습 환경을 어떻게 구성하고 계신가요?',
        createdAt: new Date(Date.now() - 60 * 60 * 1000),
        likes: 3
      }
    ]
  },
  {
    id: 2,
    title: '클라우드 보안 최신 동향 공유',
    author: '이교수',
    category: 1,
    categoryName: 'AWS Solutions Architect Associate',
    content: `<p>클라우드 보안 분야의 최신 동향을 공유드립니다.</p>
              <p>Zero Trust 아키텍처와 관련된 내용이 최근 많이 출제되고 있는 것 같아요.</p>`,
    preview: '클라우드 보안 분야의 최신 동향을 공유드립니다. Zero Trust 아키텍처와 관련된...',
    createdAt: new Date(Date.now() - 4 * 60 * 60 * 1000),
    lastActivity: new Date(Date.now() - 45 * 60 * 1000),
    replyCount: 5,
    likes: 8,
    isPinned: false,
    isNew: true,
    attachments: null,
    replies: [
      {
        id: 3,
        author: '정강사',
        content: 'Zero Trust 관련 자료가 있으시면 공유 부탁드려요!',
        createdAt: new Date(Date.now() - 45 * 60 * 1000),
        likes: 2
      }
    ]
  },
  {
    id: 3,
    title: 'CompTIA Security+ 실습 환경 구축',
    author: '정강사',
    category: 4,
    categoryName: 'CompTIA Security+',
    content: `<p>보안 실습을 위한 가상 환경 구축 방법을 공유합니다.</p>
              <p>VMware를 활용한 안전한 실습 환경 설정법을 정리했어요.</p>`,
    preview: '보안 실습을 위한 가상 환경 구축 방법을 공유합니다...',
    createdAt: new Date(Date.now() - 24 * 60 * 60 * 1000),
    lastActivity: new Date(Date.now() - 2 * 60 * 60 * 1000),
    replyCount: 3,
    likes: 6,
    isPinned: false,
    isNew: false,
    attachments: null,
    replies: []
  }
])

// 필터된 토론 목록
const filteredDiscussions = computed(() => {
  if (!selectedCategory.value) {
    return discussions.value
  }
  return discussions.value.filter(d => d.category === selectedCategory.value)
})

// 메서드
const selectDiscussion = (discussion) => {
  selectedDiscussion.value = discussion
}

const getCategoryType = (categoryId) => {
  // 자격증별 색상 구분
  const colors = ['primary', 'success', 'warning', 'danger', 'info']
  return colors[categoryId % colors.length]
}

const formatTime = (date) => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / (1000 * 60))
  
  if (minutes < 1) return '방금 전'
  if (minutes < 60) return `${minutes}분 전`
  
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}시간 전`
  
  const days = Math.floor(hours / 24)
  return `${days}일 전`
}

const formatDateTime = (date) => {
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const likeDiscussion = () => {
  if (selectedDiscussion.value) {
    selectedDiscussion.value.likes++
    ElMessage.success('좋아요를 눌렸습니다')
  }
}

const shareDiscussion = () => {
  ElMessage.info('공유 기능을 구현 중입니다')
}

const likeReply = (reply) => {
  reply.likes++
}

const submitReply = () => {
  if (!newReply.value.trim()) {
    ElMessage.warning('댓글을 입력해주세요')
    return
  }

  const reply = {
    id: Date.now(),
    author: authStore.user?.full_name || authStore.user?.username || '익명',
    content: newReply.value,
    createdAt: new Date(),
    likes: 0
  }

  selectedDiscussion.value.replies.push(reply)
  selectedDiscussion.value.replyCount++
  newReply.value = ''
  ElMessage.success('댓글이 작성되었습니다')
}

const createDiscussion = () => {
  if (!newDiscussionForm.value.title || !newDiscussionForm.value.content || !newDiscussionForm.value.category) {
    ElMessage.warning('모든 필수 항목을 입력해주세요')
    return
  }

  const discussion = {
    id: Date.now(),
    title: newDiscussionForm.value.title,
    author: authStore.user?.full_name || authStore.user?.username || '익명',
    category: newDiscussionForm.value.category,
    categoryName: certificates.value.find(c => c.id === newDiscussionForm.value.category)?.name || '',
    content: `<p>${newDiscussionForm.value.content}</p>`,
    preview: newDiscussionForm.value.content.substring(0, 100) + '...',
    createdAt: new Date(),
    lastActivity: new Date(),
    replyCount: 0,
    likes: 0,
    isPinned: false,
    isNew: true,
    attachments: newDiscussionForm.value.attachments,
    replies: []
  }

  discussions.value.unshift(discussion)
  showNewDiscussionModal.value = false
  newDiscussionForm.value = {
    category: '',
    title: '',
    content: '',
    attachments: []
  }
  ElMessage.success('새 토론이 시작되었습니다')
}

const shareResource = () => {
  if (!resourceForm.value.title || !resourceForm.value.category) {
    ElMessage.warning('모든 필수 항목을 입력해주세요')
    return
  }

  // TODO: 실제 자료 공유 로직
  showResourceModal.value = false
  resourceForm.value = {
    title: '',
    description: '',
    category: '',
    file: null
  }
  ElMessage.success('자료가 공유되었습니다')
}

const handleFileUpload = (response, file) => {
  newDiscussionForm.value.attachments.push({
    id: Date.now(),
    name: file.name,
    url: response.url
  })
}

const handleResourceUpload = (response, file) => {
  resourceForm.value.file = {
    name: file.name,
    url: response.url
  }
}

const downloadFile = (file) => {
  // TODO: 파일 다운로드 로직
  ElMessage.info('파일 다운로드를 시작합니다')
}

onMounted(() => {
  // 첫 번째 토론을 기본 선택
  if (discussions.value.length > 0) {
    selectedDiscussion.value = discussions.value[0]
  }
})
</script>

<style scoped>
.instructor-collaboration {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e4e7ed;
}

.page-title {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.page-description {
  margin: 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.collaboration-content {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 24px;
  height: calc(100vh - 200px);
}

.discussions-section {
  height: 100%;
}

.discussions-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.discussions-list {
  flex: 1;
  overflow-y: auto;
  max-height: calc(100vh - 300px);
}

.discussion-item {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.discussion-item:hover {
  background-color: #f8f9fa;
}

.discussion-item.active {
  background-color: #e6f7ff;
  border-left: 4px solid #409eff;
}

.discussion-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.discussion-title {
  font-weight: 600;
  color: #303133;
  font-size: 15px;
}

.discussion-time {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
  margin-left: 8px;
}

.discussion-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.author {
  font-size: 13px;
  color: #606266;
}

.replies {
  font-size: 12px;
  color: #909399;
}

.discussion-preview {
  font-size: 13px;
  color: #909399;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.new-badge {
  position: absolute;
  top: 8px;
  right: 8px;
}

.discussion-detail-section {
  height: 100%;
  overflow-y: auto;
}

.welcome-card {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.welcome-content {
  text-align: center;
  color: #909399;
}

.welcome-content h3 {
  margin: 16px 0 8px 0;
  color: #606266;
}

.discussion-detail {
  display: flex;
  flex-direction: column;
  gap: 16px;
  height: 100%;
}

.discussion-header-card {
  flex-shrink: 0;
}

.discussion-info .discussion-title-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.discussion-info .discussion-title {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  flex: 1;
}

.discussion-tags {
  display: flex;
  gap: 8px;
  margin-left: 16px;
}

.discussion-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.author-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.author-details {
  display: flex;
  flex-direction: column;
}

.author-name {
  font-weight: 500;
  color: #303133;
}

.post-time {
  font-size: 12px;
  color: #909399;
}

.discussion-actions {
  display: flex;
  gap: 8px;
}

.discussion-content-card {
  flex-shrink: 0;
}

.discussion-content {
  color: #606266;
  line-height: 1.6;
  margin-bottom: 16px;
}

.attachments h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #303133;
}

.attachment-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attachment-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #f8f9fa;
  border-radius: 4px;
}

.filename {
  flex: 1;
  font-size: 14px;
  color: #606266;
}

.replies-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.replies-list {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 16px;
}

.reply-item {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
}

.reply-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.reply-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.reply-author {
  font-weight: 500;
  color: #303133;
  font-size: 14px;
}

.reply-time {
  font-size: 12px;
  color: #909399;
}

.reply-actions {
  display: flex;
  gap: 8px;
}

.reply-content {
  color: #606266;
  line-height: 1.5;
  padding-left: 36px;
}

.reply-form {
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
  margin-top: 16px;
}

.reply-form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

@media (max-width: 1200px) {
  .collaboration-content {
    grid-template-columns: 1fr;
    height: auto;
  }
  
  .discussions-section {
    height: auto;
  }
  
  .discussions-list {
    max-height: 400px;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: flex-start;
  }
  
  .discussion-info .discussion-title-section {
    flex-direction: column;
    gap: 12px;
  }
  
  .discussion-tags {
    margin-left: 0;
  }
  
  .discussion-meta {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
}
</style>