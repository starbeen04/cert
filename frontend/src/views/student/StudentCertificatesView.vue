<template>
  <div class="student-certificates">
    <!-- Page Header -->
    <div class="page-header">
      <div>
        <h1 class="page-title">자격증 선택</h1>
        <p class="page-description">
          학습하고 싶은 자격증을 선택하세요. AI가 맞춤형 학습 계획을 제공해드립니다.
        </p>
      </div>
      <el-button type="primary" @click="loadCertificates">
        <el-icon><Refresh /></el-icon>
        새로고침
      </el-button>
    </div>

    <!-- 자격증 목록 -->
    <el-card class="certificates-card">
      <template #header>
        <div class="card-header">
          <span>사용 가능한 자격증</span>
          <div class="header-controls">
            <el-input
              v-model="searchQuery"
              placeholder="자격증 검색..."
              :prefix-icon="Search"
              clearable
              @input="handleSearch"
              style="width: 200px; margin-right: 12px;"
            />
            <el-select
              v-model="selectedCategory"
              placeholder="분야"
              clearable
              @change="handleCategoryFilter"
              style="width: 120px; margin-right: 12px;"
            >
              <el-option label="전체" value="" />
              <el-option label="Cloud" value="Cloud" />
              <el-option label="Security" value="Security" />
              <el-option label="IT" value="IT" />
            </el-select>
            <el-select
              v-model="selectedDifficulty"
              placeholder="난이도"
              clearable
              @change="handleDifficultyFilter"
              style="width: 120px"
            >
              <el-option label="전체" value="" />
              <el-option label="초급" value="Beginner" />
              <el-option label="중급" value="intermediate" />
              <el-option label="고급" value="advanced" />
              <el-option label="전문가" value="Expert" />
            </el-select>
          </div>
        </div>
      </template>

        <div v-if="filteredCertificates.length === 0 && !loading" class="empty-container">
          <el-empty description="검색 조건에 맞는 자격증이 없습니다">
            <el-button type="primary" @click="clearFilters">
              필터 초기화
            </el-button>
          </el-empty>
        </div>

        <div v-else class="certificates-list">
          <div
            v-for="cert in filteredCertificates"
            :key="cert.id"
            class="cert-item"
            @click="selectCertificate(cert)"
          >
            <div class="cert-header">
              <div class="cert-info">
                <h4 class="cert-name">{{ cert.title }}</h4>
                <div class="cert-tags">
                  <el-tag :type="getDifficultyColor(cert.difficulty_level)" size="small">
                    {{ getDifficultyLabel(cert.difficulty_level) }}
                  </el-tag>
                  <el-tag type="info" size="small">{{ cert.category }}</el-tag>
                  <el-tag
                    v-if="isEnrolled(cert.id)"
                    type="success"
                    size="small"
                  >
                    학습중
                  </el-tag>
                  <el-tag
                    v-else-if="isCompleted(cert.id)"
                    type="primary"
                    size="small"
                  >
                    완료
                  </el-tag>
                </div>
              </div>
            </div>

            <div class="cert-description">
              <p>{{ cert.description }}</p>
            </div>

            <div class="cert-details">
              <div class="detail-group">
                <span class="detail-label">발급기관:</span>
                <span class="detail-value">{{ cert.issuer }}</span>
              </div>
              <div class="detail-group">
                <span class="detail-label">시험시간:</span>
                <span class="detail-value">{{ cert.exam_duration_minutes || 120 }}분</span>
              </div>
              <div class="detail-group">
                <span class="detail-label">합격점수:</span>
                <span class="detail-value">{{ cert.passing_score || 60 }}%</span>
              </div>
              <div class="detail-group">
                <span class="detail-label">총 문제수:</span>
                <span class="detail-value">{{ cert.total_questions || '-' }}</span>
              </div>
            </div>

            <div class="cert-actions">
              <el-button
                v-if="isEnrolled(cert.id)"
                type="primary"
                size="small"
                @click.stop="startLearning(cert)"
              >
                학습 계속하기
              </el-button>
              <el-button
                v-else-if="isCompleted(cert.id)"
                type="success"
                size="small"
                @click.stop="startLearning(cert)"
              >
                복습하기
              </el-button>
              <el-button
                v-else
                type="primary"
                size="small"
                @click.stop="startLearning(cert)"
              >
                학습 시작하기
              </el-button>
              <el-button
                type="text"
                size="small"
                @click.stop="selectCertificate(cert)"
              >
                상세보기
              </el-button>
            </div>
          </div>
        </div>
    </el-card>

    <!-- Certificate Detail Modal -->
    <el-dialog
      v-model="showDetailModal"
      :title="selectedCert?.title"
      width="600px"
    >
      <div v-if="selectedCert" class="cert-detail-content">
        <div class="detail-header">
          <div class="detail-icon">🏆</div>
          <div class="detail-info">
            <h2>{{ selectedCert.title }}</h2>
            <p>{{ selectedCert.description }}</p>
            <div class="detail-meta">
              <el-tag :type="getDifficultyColor(selectedCert.difficulty_level)">
                {{ getDifficultyLabel(selectedCert.difficulty_level) }}
              </el-tag>
              <span class="meta-text">{{ selectedCert.category }} | {{ selectedCert.issuer }}</span>
            </div>
          </div>
        </div>
        
        <div class="detail-stats">
          <div class="stat-box">
            <div class="stat-icon">⏱️</div>
            <div class="stat-content">
              <div class="stat-number">{{ selectedCert.exam_duration_minutes || 120 }}분</div>
              <div class="stat-desc">시험 시간</div>
            </div>
          </div>
          <div class="stat-box">
            <div class="stat-icon">🎯</div>
            <div class="stat-content">
              <div class="stat-number">{{ selectedCert.passing_score || 60 }}%</div>
              <div class="stat-desc">합격 점수</div>
            </div>
          </div>
          <div class="stat-box">
            <div class="stat-icon">📝</div>
            <div class="stat-content">
              <div class="stat-number">{{ selectedCert.total_questions || '-' }}</div>
              <div class="stat-desc">총 문제수</div>
            </div>
          </div>
        </div>
        
        <div class="detail-description">
          <h3>자격증 소개</h3>
          <p>{{ selectedCert.description }}</p>
          
          <h3>학습 내용</h3>
          <ul>
            <li>핵심 개념과 이론 학습</li>
            <li>실무 중심의 문제 해결 능력 향상</li>
            <li>모의고사를 통한 시험 준비</li>
            <li>AI 기반 맞춤형 학습 가이드</li>
          </ul>
        </div>
      </div>
      
      <template #footer>
        <div class="modal-actions">
          <el-button @click="showDetailModal = false">닫기</el-button>
          <el-button
            type="primary"
            @click="startLearning(selectedCert)"
          >
            {{ isEnrolled(selectedCert?.id) ? '학습 계속하기' : '학습 시작하기' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Search,
  Refresh,
} from '@element-plus/icons-vue'

const router = useRouter()

// State
const loading = ref(false)
const certificates = ref<any[]>([])
const searchQuery = ref('')
const selectedCategory = ref('')
const selectedDifficulty = ref('')
const viewMode = ref('grid')
const showDetailModal = ref(false)
const selectedCert = ref<any>(null)

// Mock enrolled certificates
const enrolledCertificates = ref([1, 2]) // IDs of enrolled certificates
const completedCertificates = ref([]) // IDs of completed certificates

// Computed
const filteredCertificates = computed(() => {
  let filtered = certificates.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(cert =>
      cert.title.toLowerCase().includes(query) ||
      cert.description.toLowerCase().includes(query) ||
      cert.issuer.toLowerCase().includes(query)
    )
  }

  if (selectedCategory.value) {
    filtered = filtered.filter(cert => cert.category === selectedCategory.value)
  }

  if (selectedDifficulty.value) {
    filtered = filtered.filter(cert => cert.difficulty_level === selectedDifficulty.value)
  }

  return filtered
})

// Methods
const loadCertificates = async () => {
  try {
    loading.value = true
    
    // 실제 백엔드 API 사용
    const response = await fetch('http://localhost:8100/api/admin/certificates/list')
    const data = await response.json()
    
    if (data.success) {
      certificates.value = data.certificates || []
    } else {
      throw new Error(data.error || 'Failed to load certificates')
    }
  } catch (error) {
    console.error('Failed to load certificates:', error)
    ElMessage.error('자격증 목록을 불러오는데 실패했습니다')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  // Search is reactive through computed property
}

const handleCategoryFilter = () => {
  // Filter is reactive through computed property
}

const handleDifficultyFilter = () => {
  // Filter is reactive through computed property
}

const handleViewModeChange = () => {
  // View mode change
}

const clearFilters = () => {
  searchQuery.value = ''
  selectedCategory.value = ''
  selectedDifficulty.value = ''
}

const selectCertificate = (cert: any) => {
  selectedCert.value = cert
  showDetailModal.value = true
}

const startLearning = (cert: any) => {
  if (!cert) return
  
  showDetailModal.value = false
  router.push(`/student/study/${cert.id}`)
}

const isEnrolled = (certId: number) => {
  return enrolledCertificates.value.includes(certId)
}

const isCompleted = (certId: number) => {
  return completedCertificates.value.includes(certId)
}

const getDifficultyColor = (difficulty: string) => {
  switch (difficulty) {
    case 'Beginner': return 'success'
    case 'intermediate': return 'warning'
    case 'advanced': return 'danger'
    case 'Expert': return 'danger'
    default: return 'info'
  }
}

const getDifficultyLabel = (difficulty: string) => {
  switch (difficulty) {
    case 'Beginner': return '초급'
    case 'intermediate': return '중급'
    case 'advanced': return '고급'
    case 'Expert': return '전문가'
    default: return difficulty
  }
}

// Initialize
onMounted(() => {
  loadCertificates()
})
</script>

<style scoped>
.student-certificates {
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

.certificates-card {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-controls {
  display: flex;
  align-items: center;
}

.empty-container {
  padding: 40px;
}

.certificates-list {
  
}

.cert-item {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 16px;
  background: #fafafa;
  cursor: pointer;
  transition: all 0.2s;
}

.cert-item:hover {
  background: #f0f9ff;
  border-color: #409eff;
}

.cert-header {
  margin-bottom: 16px;
}

.cert-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cert-name {
  margin: 0;
  color: #303133;
}

.cert-tags {
  display: flex;
  gap: 8px;
}

.cert-description {
  margin-bottom: 16px;
}

.cert-description p {
  margin: 0;
  color: #606266;
  line-height: 1.5;
}

.cert-details {
  margin-bottom: 16px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.detail-group {
  display: flex;
  font-size: 14px;
}

.detail-label {
  color: #909399;
  min-width: 80px;
}

.detail-value {
  color: #303133;
  font-weight: 500;
}

.cert-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}


.cert-detail-content {
  padding: 20px 0;
}

.detail-header {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
}

.detail-icon {
  font-size: 48px;
  background: linear-gradient(135deg, #ffd700, #ffed4e);
  width: 80px;
  height: 80px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-info h2 {
  margin: 0 0 8px 0;
  color: #2c3e50;
}

.detail-info p {
  margin: 0 0 12px 0;
  color: #606266;
}

.detail-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.meta-text {
  color: #909399;
  font-size: 14px;
}

.detail-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
}

.stat-box {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-box .stat-icon {
  font-size: 24px;
}

.stat-box .stat-number {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.stat-box .stat-desc {
  font-size: 12px;
  color: #909399;
}

.detail-description h3 {
  margin: 20px 0 12px 0;
  color: #2c3e50;
}

.detail-description p {
  color: #606266;
  line-height: 1.6;
}

.detail-description ul {
  color: #606266;
  line-height: 1.8;
}

.modal-actions {
  display: flex;
  gap: 12px;
}

/* 반응형 디자인 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .header-controls {
    flex-direction: column;
    width: 100%;
    gap: 8px;
  }
  
  .header-controls .el-input,
  .header-controls .el-select {
    width: 100% !important;
  }
  
  .cert-details {
    grid-template-columns: 1fr;
  }
  
  .detail-header {
    flex-direction: column;
    text-align: center;
  }
  
  .detail-stats {
    flex-direction: column;
  }
}
</style>