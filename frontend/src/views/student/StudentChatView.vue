<template>
  <div class="student-chat">
    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">AI 학습 도우미</h1>
        <p class="page-description">
          궁금한 점을 언제든지 AI에게 물어보세요. 자격증 관련 질문부터 학습 전략까지 도움드릴게요!
        </p>
      </div>
      <el-button type="primary" @click="loadCertificates">
        <el-icon><Refresh /></el-icon>
        새로고침
      </el-button>
    </div>

    <div class="chat-layout">
      <!-- Chat Main Area -->
      <el-card class="chat-card">
        <template #header>
          <div class="card-header">
            <div class="ai-info">
              <div class="ai-avatar">🤖</div>
              <div class="ai-details">
                <span>CertFast AI</span>
                <span class="ai-status">온라인</span>
              </div>
            </div>
            
            <div class="header-controls">
              <el-select
                v-model="selectedCertificate"
                placeholder="자격증 선택"
                size="small"
                style="width: 200px; margin-right: 8px;"
                @change="changeCertificateContext"
              >
                <el-option
                  v-for="cert in availableCertificates"
                  :key="cert.id"
                  :label="cert.title"
                  :value="cert.id"
                />
              </el-select>
              
              <el-button @click="clearChat" size="small">
                <el-icon><Delete /></el-icon>
                대화 지우기
              </el-button>
            </div>
          </div>
        </template>

        <!-- Messages Area -->
        <div ref="messagesContainer" class="messages-area" v-loading="isLoading">
          <!-- Welcome Message -->
          <div v-if="messages.length === 0" class="welcome-message">
            <div class="ai-avatar large">🤖</div>
            <h3>안녕하세요! CertFast AI입니다</h3>
            <p>자격증 학습에 관한 모든 질문을 도와드릴게요. 어떤 도움이 필요하신가요?</p>
            
            <div class="quick-questions">
              <h4>자주 묻는 질문:</h4>
              <div class="question-chips">
                <el-tag
                  v-for="question in quickQuestions"
                  :key="question"
                  class="question-chip"
                  @click="sendQuickQuestion(question)"
                >
                  {{ question }}
                </el-tag>
              </div>
            </div>
          </div>

          <!-- Chat Messages -->
          <div class="messages-list">
            <div
              v-for="message in messages"
              :key="message.id"
              :class="['message', message.sender]"
            >
              <div v-if="message.sender === 'ai'" class="ai-avatar small">🤖</div>
              
              <div class="message-content">
                <div class="message-bubble">
                  <div v-if="message.type === 'text'" class="message-text">
                    <div v-html="formatMessage(message.content)"></div>
                  </div>
                  
                  <div v-else-if="message.type === 'code'" class="message-code">
                    <pre><code>{{ message.content }}</code></pre>
                  </div>
                  
                  <div v-else-if="message.type === 'suggestions'" class="message-suggestions">
                    <p>{{ message.content }}</p>
                    <div class="suggestion-buttons">
                      <el-button
                        v-for="suggestion in message.suggestions"
                        :key="suggestion"
                        size="small"
                        @click="sendQuickQuestion(suggestion)"
                      >
                        {{ suggestion }}
                      </el-button>
                    </div>
                  </div>
                </div>
                
                <div class="message-meta">
                  <span class="message-time">{{ formatTime(message.timestamp) }}</span>
                  <div v-if="message.sender === 'ai'" class="message-actions">
                    <el-button
                      type="text"
                      size="small"
                      :icon="CopyDocument"
                      @click="copyMessage(message.content)"
                    >
                      복사
                    </el-button>
                    <el-button
                      type="text"
                      size="small"
                      :icon="message.liked ? 'SuccessFilled' : 'Success'"
                      @click="toggleLike(message)"
                    >
                      {{ message.liked ? '좋아요' : '도움됨' }}
                    </el-button>
                  </div>
                </div>
              </div>
              
              <div v-if="message.sender === 'user'" class="user-avatar">
                {{ userStore.user?.username?.charAt(0).toUpperCase() }}
              </div>
            </div>
          </div>

          <!-- Typing Indicator -->
          <div v-if="isTyping" class="typing-indicator">
            <div class="ai-avatar small">🤖</div>
            <div class="typing-animation">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>

        <!-- Input Area -->
        <div class="input-area">
          <div class="input-container">
            <el-input
              v-model="currentMessage"
              type="textarea"
              :rows="2"
              placeholder="궁금한 점을 입력하세요..."
              :disabled="isLoading"
              @keydown.enter.prevent="handleKeyPress"
              resize="none"
              maxlength="1000"
              show-word-limit
            />
            
            <div class="input-actions">
              <el-button
                type="text"
                :icon="PaperClip"
                @click="attachFile"
                :disabled="isLoading"
              >
                파일
              </el-button>
              
              <el-button
                type="primary"
                :icon="Promotion"
                @click="sendMessage"
                :disabled="!currentMessage.trim() || isLoading"
                :loading="isLoading"
              >
                전송
              </el-button>
            </div>
          </div>
          
          <div class="input-hint">
            <span>Enter로 전송, Shift+Enter로 줄바꿈</span>
          </div>
        </div>
      </el-card>

      <!-- Sidebar -->
      <div class="chat-sidebar">
        <!-- Current Context -->
        <el-card class="sidebar-card">
          <template #header>
            <div class="card-header">
              <span>현재 학습 맥락</span>
            </div>
          </template>
          
          <div v-if="selectedCertificate" class="context-content">
            <h4 class="cert-name">{{ getSelectedCertificateName() }}</h4>
            <p class="cert-desc">{{ getSelectedCertificateDescription() }}</p>
            
            <div class="context-stats">
              <div class="stat-item">
                <span class="stat-label">학습 진도:</span>
                <span class="stat-value">75%</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">최근 정확도:</span>
                <span class="stat-value">85%</span>
              </div>
            </div>
          </div>
          
          <div v-else class="empty-context">
            <el-empty description="자격증을 선택하면 더 정확한 답변을 받을 수 있어요!" :image-size="60" />
          </div>
        </el-card>

        <!-- AI Features -->
        <el-card class="sidebar-card">
          <template #header>
            <div class="card-header">
              <span>AI 기능</span>
            </div>
          </template>
          
          <div class="features-list">
            <div class="feature-item" @click="requestStudyPlan">
              <el-icon><Calendar /></el-icon>
              <span>학습 계획 생성</span>
            </div>
            
            <div class="feature-item" @click="requestWeakAnalysis">
              <el-icon><TrendCharts /></el-icon>
              <span>약점 분석</span>
            </div>
            
            <div class="feature-item" @click="requestTips">
              <el-icon><Lightbulb /></el-icon>
              <span>학습 팁 요청</span>
            </div>
            
            <div class="feature-item" @click="requestMockTest">
              <el-icon><EditPen /></el-icon>
              <span>모의고사 추천</span>
            </div>
          </div>
        </el-card>

        <!-- Chat History -->
        <el-card class="sidebar-card">
          <template #header>
            <div class="card-header">
              <span>최근 대화</span>
            </div>
          </template>
          
          <div v-if="chatHistory.length === 0" class="empty-container">
            <el-empty description="대화 기록이 없습니다" :image-size="60" />
          </div>
          
          <div v-else class="history-list">
            <div
              v-for="chat in chatHistory"
              :key="chat.id"
              class="history-item"
              @click="loadChatHistory(chat)"
            >
              <div class="history-content">
                <h5 class="history-title">{{ chat.title }}</h5>
                <div class="history-meta">
                  <span class="history-date">{{ formatDate(chat.date) }}</span>
                  <span class="history-count">{{ chat.message_count }}개 메시지</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Delete,
  CopyDocument,
  PaperClip,
  Promotion,
  Calendar,
  TrendCharts,
  Lightbulb,
  EditPen,
  Refresh,
} from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { formatDate } from '@/utils/format'

const userStore = useAuthStore()

// State
const isLoading = ref(false)
const isTyping = ref(false)
const currentMessage = ref('')
const selectedCertificate = ref<number | null>(null)
const availableCertificates = ref<any[]>([])
const messagesContainer = ref<HTMLElement>()

// Messages
const messages = ref<any[]>([])
let messageIdCounter = 1

// Quick Questions
const quickQuestions = [
  "AWS의 핵심 서비스는 무엇인가요?",
  "자격증 시험 일정은 어떻게 되나요?",
  "효과적인 학습 방법을 알려주세요",
  "모의고사는 언제 보는 게 좋을까요?",
  "취약점을 어떻게 개선하나요?"
]

// Chat History (Mock)
const chatHistory = ref([
  {
    id: 1,
    title: "AWS 보안 서비스 질문",
    date: new Date(Date.now() - 2 * 60 * 60 * 1000),
    message_count: 8
  },
  {
    id: 2,
    title: "시험 준비 전략 상담",
    date: new Date(Date.now() - 24 * 60 * 60 * 1000),
    message_count: 12
  }
])

// Methods
const loadCertificates = async () => {
  try {
    const response = await fetch('http://localhost:8100/api/admin/certificates/list')
    const data = await response.json()
    
    if (data.success) {
      availableCertificates.value = data.certificates || []
    }
  } catch (error) {
    console.error('Failed to load certificates:', error)
  }
}

const sendMessage = async () => {
  if (!currentMessage.value.trim() || isLoading.value) return

  const userMessage = {
    id: messageIdCounter++,
    sender: 'user',
    type: 'text',
    content: currentMessage.value.trim(),
    timestamp: new Date()
  }

  messages.value.push(userMessage)
  const messageToSend = currentMessage.value.trim()
  currentMessage.value = ''

  await scrollToBottom()
  
  // Simulate AI response
  await simulateAIResponse(messageToSend)
}

const simulateAIResponse = async (userMessage: string) => {
  isLoading.value = true
  isTyping.value = true

  // Simulate typing delay
  await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000))

  isTyping.value = false

  // Generate AI response based on message
  const aiResponse = generateAIResponse(userMessage)
  
  const aiMessage = {
    id: messageIdCounter++,
    sender: 'ai',
    type: aiResponse.type || 'text',
    content: aiResponse.content,
    suggestions: aiResponse.suggestions,
    timestamp: new Date(),
    liked: false
  }

  messages.value.push(aiMessage)
  isLoading.value = false

  await scrollToBottom()
}

const generateAIResponse = (userMessage: string) => {
  const message = userMessage.toLowerCase()
  
  if (message.includes('aws') || message.includes('아마존')) {
    return {
      type: 'text',
      content: `AWS(Amazon Web Services)에 대해 질문해주셨네요! 🌟

AWS는 아마존에서 제공하는 클라우드 컴퓨팅 플랫폼으로, 다음과 같은 핵심 서비스들을 제공합니다:

**컴퓨팅 서비스:**
• EC2 (Elastic Compute Cloud) - 가상 서버
• Lambda - 서버리스 컴퓨팅
• ECS/EKS - 컨테이너 서비스

**스토리지 서비스:**
• S3 (Simple Storage Service) - 객체 스토리지
• EBS (Elastic Block Store) - 블록 스토리지
• EFS (Elastic File System) - 파일 스토리지

**데이터베이스 서비스:**
• RDS (Relational Database Service)
• DynamoDB - NoSQL 데이터베이스
• ElastiCache - 인메모리 캐싱

더 궁금한 AWS 서비스가 있으시면 언제든 물어보세요!`,
      suggestions: ["AWS 보안 서비스는?", "EC2 인스턴스 유형", "S3 스토리지 클래스"]
    }
  }
  
  if (message.includes('학습') || message.includes('공부')) {
    return {
      type: 'suggestions',
      content: '효과적인 자격증 학습을 위한 몇 가지 팁을 드릴게요:',
      suggestions: ["학습 계획 세우기", "약점 파악하기", "모의고사 활용", "복습 전략"]
    }
  }
  
  if (message.includes('시험') || message.includes('일정')) {
    return {
      type: 'text',
      content: `자격증 시험 준비에 대해 궁금하시군요! 📅

**일반적인 시험 준비 일정:**
• 2-3개월: 기초 학습 및 개념 정리
• 1개월: 집중 문제 풀이 및 약점 보완
• 1-2주: 최종 복습 및 모의고사

**시험 신청 팁:**
• 충분한 준비 기간 확보
• 본인의 학습 속도 고려
• 시험 일정 미리 확인

어떤 자격증을 준비하고 계신지 알려주시면 더 구체적인 조언을 드릴 수 있어요!`
    }
  }

  // Default response
  return {
    type: 'text',
    content: `좋은 질문이네요! 😊 

"${userMessage}"에 대해 더 자세히 알려드리고 싶습니다. 

현재 학습 중인 자격증을 선택해주시면 더 맞춤형 답변을 드릴 수 있어요. 

다른 궁금한 점이 있으시면 언제든 말씀해주세요!`,
    suggestions: ["학습 방법 추천", "시험 팁 요청", "약점 분석"]
  }
}

const sendQuickQuestion = (question: string) => {
  currentMessage.value = question
  sendMessage()
}

const handleKeyPress = (event: KeyboardEvent) => {
  if (event.shiftKey) {
    // Shift+Enter: Add line break (handled by textarea naturally)
    return
  } else {
    // Enter: Send message
    event.preventDefault()
    sendMessage()
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const clearChat = () => {
  messages.value = []
  ElMessage.success('대화가 초기화되었습니다')
}

const changeCertificateContext = (certificateId: number) => {
  // Add context change message
  const contextMessage = {
    id: messageIdCounter++,
    sender: 'ai',
    type: 'text',
    content: `${getSelectedCertificateName()} 맥락으로 전환되었습니다. 이제 해당 자격증에 특화된 질문과 답변을 제공해드릴게요! 🎯`,
    timestamp: new Date(),
    liked: false
  }
  
  messages.value.push(contextMessage)
  scrollToBottom()
}

const getSelectedCertificateName = () => {
  const cert = availableCertificates.value.find(c => c.id === selectedCertificate.value)
  return cert?.title || ''
}

const getSelectedCertificateDescription = () => {
  const cert = availableCertificates.value.find(c => c.id === selectedCertificate.value)
  return cert?.description || ''
}

const formatMessage = (content: string) => {
  // Simple markdown-like formatting
  return content
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
    .replace(/•/g, '•')
}

const formatTime = (timestamp: Date) => {
  return timestamp.toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}

const copyMessage = async (content: string) => {
  try {
    await navigator.clipboard.writeText(content)
    ElMessage.success('메시지가 복사되었습니다')
  } catch (error) {
    ElMessage.error('복사에 실패했습니다')
  }
}

const toggleLike = (message: any) => {
  message.liked = !message.liked
  ElMessage.success(message.liked ? '피드백 감사합니다!' : '피드백이 취소되었습니다')
}

const attachFile = () => {
  ElMessage.info('파일 첨부 기능은 곧 제공될 예정입니다')
}

const loadChatHistory = (chat: any) => {
  ElMessage.info('대화 기록 불러오기 기능은 곧 제공될 예정입니다')
}

// AI Feature Functions
const requestStudyPlan = () => {
  sendQuickQuestion("개인 맞춤 학습 계획을 세워주세요")
}

const requestWeakAnalysis = () => {
  sendQuickQuestion("제 약점을 분석해주세요")
}

const requestTips = () => {
  sendQuickQuestion("효과적인 학습 팁을 알려주세요")
}

const requestMockTest = () => {
  sendQuickQuestion("모의고사 일정을 추천해주세요")
}

// Initialize
onMounted(() => {
  loadCertificates()
})
</script>

<style scoped>
.student-chat {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  height: calc(100vh - 140px);
  display: flex;
  flex-direction: column;
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

.chat-layout {
  display: flex;
  gap: 24px;
  flex: 1;
  min-height: 0;
}

.chat-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.ai-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.ai-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #409eff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  color: white;
}

.ai-avatar.large {
  width: 48px;
  height: 48px;
  font-size: 24px;
  margin-bottom: 16px;
}

.ai-avatar.small {
  width: 28px;
  height: 28px;
  font-size: 14px;
}

.ai-details {
  display: flex;
  flex-direction: column;
  font-size: 14px;
}

.ai-status {
  font-size: 12px;
  color: #67c23a;
}

.ai-status::before {
  content: "●";
  margin-right: 4px;
}

.header-controls {
  display: flex;
  align-items: center;
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  min-height: 400px;
}

.welcome-message {
  text-align: center;
  padding: 40px 20px;
  color: #606266;
}

.welcome-message h3 {
  margin: 0 0 12px 0;
  color: #303133;
}

.welcome-message p {
  margin: 0 0 32px 0;
  line-height: 1.6;
}

.quick-questions h4 {
  margin: 0 0 16px 0;
  color: #303133;
}

.question-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
}

.question-chip {
  cursor: pointer;
  transition: all 0.2s;
}

.question-chip:hover {
  background: #409eff;
  color: white;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message {
  display: flex;
  gap: 12px;
  max-width: 80%;
}

.message.user {
  flex-direction: row-reverse;
  margin-left: auto;
}

.message.ai {
  margin-right: auto;
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #409eff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 12px;
}

.message-content {
  flex: 1;
}

.message-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  background: #f5f7fa;
  margin-bottom: 4px;
  border: 1px solid #e4e7ed;
}

.message.user .message-bubble {
  background: #409eff;
  color: white;
  border-color: #409eff;
}

.message-text {
  line-height: 1.6;
}

.message-code {
  background: #303133;
  color: #fff;
  border-radius: 8px;
  overflow-x: auto;
}

.message-code pre {
  margin: 0;
  padding: 12px;
}

.message-suggestions p {
  margin: 0 0 12px 0;
}

.suggestion-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.message-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #909399;
}

.message.user .message-meta {
  flex-direction: row-reverse;
}

.message-actions {
  display: flex;
  gap: 4px;
}

.typing-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}

.typing-animation {
  display: flex;
  gap: 4px;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 12px;
  border: 1px solid #e4e7ed;
}

.typing-animation span {
  width: 6px;
  height: 6px;
  background: #909399;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-animation span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-animation span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
    opacity: 0.5;
  }
  30% {
    transform: translateY(-10px);
    opacity: 1;
  }
}

.input-area {
  padding: 20px;
  border-top: 1px solid #e4e7ed;
}

.input-container {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-container .el-textarea {
  flex: 1;
}

.input-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-hint {
  margin-top: 8px;
  text-align: center;
  font-size: 12px;
  color: #909399;
}

.chat-sidebar {
  width: 300px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sidebar-card {
  margin-bottom: 0;
}

.empty-container {
  padding: 20px;
}

.empty-context {
  padding: 20px;
}

.context-content {
  
}

.cert-name {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 16px;
}

.cert-desc {
  margin: 0 0 16px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.4;
}

.context-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
}

.stat-label {
  color: #909399;
}

.stat-value {
  font-weight: 500;
  color: #303133;
}

.features-list {
  
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: #606266;
  border: 1px solid transparent;
  margin-bottom: 8px;
}

.feature-item:hover {
  background: #f0f9ff;
  color: #409eff;
  border-color: #409eff;
}

.history-list {
  max-height: 300px;
  overflow-y: auto;
}

.history-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 8px;
  border: 1px solid #e4e7ed;
  background: #fafafa;
}

.history-item:hover {
  background: #f0f9ff;
  border-color: #409eff;
}

.history-content {
  
}

.history-title {
  margin: 0 0 4px 0;
  color: #303133;
  font-size: 14px;
  font-weight: 500;
}

.history-meta {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

/* 반응형 디자인 */
@media (max-width: 1024px) {
  .chat-layout {
    flex-direction: column;
  }
  
  .chat-sidebar {
    width: 100%;
    order: -1;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 16px;
  }
  
  .student-chat {
    height: auto;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .header-controls {
    width: 100%;
    justify-content: space-between;
  }
  
  .message {
    max-width: 95%;
  }
  
  .input-container {
    flex-direction: column;
    align-items: stretch;
  }
  
  .input-actions {
    flex-direction: row;
    justify-content: space-between;
  }
  
  .chat-sidebar {
    grid-template-columns: 1fr;
  }
}
</style>