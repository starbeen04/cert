<template>
  <div class="certificates-view">
    <div class="page-header">
      <h1 class="page-title">자격증 관리</h1>
      <p class="page-description">자격증을 등록하고 관리할 수 있습니다</p>
    </div>

    <!-- Actions Bar -->
    <div class="actions-bar">
      <div class="search-section">
        <el-input
          v-model="searchQuery"
          placeholder="Search certificates..."
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
          style="width: 300px"
        />
        <el-select
          v-model="statusFilter"
          placeholder="Filter by status"
          clearable
          @change="handleSearch"
          style="width: 150px; margin-left: 12px"
        >
          <el-option label="전체" value="" />
          <el-option label="활성" value="active" />
          <el-option label="비활성" value="inactive" />
        </el-select>
      </div>
      
      <div class="action-buttons">
        <el-button
          type="primary"
          :icon="Plus"
          @click="showCreateDialog = true"
        >
          자격증 등록
        </el-button>
        <el-button
          type="success"
          :icon="Setting"
          @click="showIssuersDialog = true"
        >
          발행기관 관리
        </el-button>
        <el-button
          :icon="Refresh"
          @click="refreshCertificates"
        >
          새로고침
        </el-button>
      </div>
    </div>

    <!-- Certificates Table -->
    <el-card class="table-card">
      <!-- 데스크톱/태블릿 뷰 -->
      <el-table
        v-loading="certificatesStore.isLoading"
        :data="certificatesStore.certificates"
        stripe
        @sort-change="handleSortChange"
        class="responsive-table"
      >
        <el-table-column
          label="번호"
          width="80"
          align="center"
        >
          <template #default="scope">
            {{ scope.$index + 1 }}
          </template>
        </el-table-column>
        
        <el-table-column
          prop="name"
          label="자격증명"
          min-width="200"
          sortable
        >
          <template #default="scope">
            <div class="certificate-info">
              <div class="certificate-icon">
                <el-icon size="20"><Document /></el-icon>
              </div>
              <div>
                <div class="certificate-name">{{ scope.row.name }}</div>
                <div class="certificate-description">
                  {{ scope.row.description || 'No description' }}
                </div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column
          label="발행기관"
          min-width="140"
        >
          <template #default="scope">
            <div v-if="scope.row.issuer" class="issuer-info">
              <div class="issuer-name">{{ scope.row.issuer }}</div>
              <div class="issuer-code">{{ getIssuerCode(scope.row.issuer) }}</div>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column
          label="설명"
          min-width="200"
          show-overflow-tooltip
        >
          <template #default="scope">
            <span v-if="scope.row.description" class="description-text">
              {{ scope.row.description }}
            </span>
            <span v-else class="no-description">설명 없음</span>
          </template>
        </el-table-column>

        <el-table-column
          prop="user"
          label="등록자"
          min-width="120"
        >
          <template #default="scope">
            <div v-if="scope.row.user" class="user-info">
              <el-avatar size="small" class="user-avatar">
                {{ getUserInitials(scope.row.user) }}
              </el-avatar>
              <span class="username">{{ scope.row.user.username }}</span>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>


        <el-table-column
          label="상태"
          width="100"
          align="center"
        >
          <template #default="scope">
            <el-tag
              :type="scope.row.is_active ? 'success' : 'danger'"
              size="small"
            >
              {{ scope.row.is_active ? '활성' : '비활성' }}
            </el-tag>
          </template>
        </el-table-column>


        <el-table-column
          prop="upload_date"
          label="등록일"
          min-width="110"
          sortable
          class-name="date-column"
        >
          <template #default="scope">
            <div class="date-cell">
              {{ formatDate(scope.row.upload_date) }}
            </div>
          </template>
        </el-table-column>

        <el-table-column
          label="작업"
          min-width="200"
          align="center"
          class-name="action-column"
        >
          <template #default="scope">
            <div class="action-controls">
              <div class="status-switch">
                <el-switch
                  v-model="scope.row.is_active"
                  size="small"
                  @change="toggleCertificateStatus(scope.row)"
                />
              </div>
              <div class="action-buttons">
                <el-tooltip content="편집" placement="top">
                  <el-button
                    class="action-btn"
                    type="primary"
                    :icon="Edit"
                    @click="editCertificate(scope.row)"
                    circle
                  />
                </el-tooltip>
                <el-tooltip content="삭제" placement="top">
                  <el-button
                    class="action-btn"
                    type="danger"
                    :icon="Delete"
                    @click="deleteCertificate(scope.row)"
                    circle
                  />
                </el-tooltip>
              </div>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 모바일 카드 뷰 -->
      <div class="mobile-cards" v-if="certificatesStore.certificates.length > 0">
        <div 
          v-for="(certificate, index) in certificatesStore.certificates" 
          :key="certificate.id" 
          class="certificate-card"
        >
          <div class="card-header">
            <div class="card-title">
              <div class="card-number">{{ index + 1 }}</div>
              <el-icon class="card-icon"><Document /></el-icon>
              <span>{{ certificate.name }}</span>
            </div>
            <div class="card-status">
              <el-tag 
                :type="certificate.is_active ? 'success' : 'danger'" 
                size="small"
              >
                {{ certificate.is_active ? '활성' : '비활성' }}
              </el-tag>
            </div>
          </div>
          
          <div class="card-content">
            <div class="card-info">
              <div class="info-item">
                <span class="info-label">발행기관:</span>
                <span class="info-value">{{ certificate.issuer || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">설명:</span>
                <span class="info-value">{{ certificate.description || '설명 없음' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">등록일:</span>
                <span class="info-value">{{ formatDate(certificate.upload_date) }}</span>
              </div>
            </div>
            
            <div class="card-actions">
              <div class="action-switch">
                <el-switch
                  v-model="certificate.is_active"
                  size="small"
                  @change="toggleCertificateStatus(certificate)"
                />
              </div>
              <div class="action-buttons-mobile">
                <el-button
                  class="mobile-btn"
                  type="primary"
                  :icon="Edit"
                  @click="editCertificate(certificate)"
                  size="small"
                >
                  편집
                </el-button>
                <el-button
                  class="mobile-btn"
                  type="danger"
                  :icon="Delete"
                  @click="deleteCertificate(certificate)"
                  size="small"
                >
                  삭제
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="certificatesStore.totalCertificates"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- Edit Certificate Dialog -->
    <el-dialog
      v-model="showEditDialog"
      title="자격증 편집"
      width="600px"
      @close="resetEditForm"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="120px"
      >
        <el-form-item label="자격증명" prop="name">
          <el-input v-model="editForm.name" placeholder="자격증명을 입력하세요" />
        </el-form-item>
        
        <el-form-item label="발행기관" prop="issuing_authority">
          <el-select v-model="editForm.issuing_authority" placeholder="발행기관을 선택하세요" style="width: 100%">
            <el-option 
              v-for="issuer in issuers.filter(i => i.active)" 
              :key="issuer.id" 
              :label="issuer.name" 
              :value="issuer.name" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="분야" prop="category">
          <el-select v-model="editForm.category" placeholder="분야를 선택하세요" style="width: 100%">
            <el-option label="IT/컴퓨터" value="IT" />
            <el-option label="경영/사무" value="Business" />
            <el-option label="건설/토목" value="Construction" />
            <el-option label="기계/자동차" value="Mechanical" />
            <el-option label="전기/전자" value="Electrical" />
            <el-option label="화학/섬유" value="Chemical" />
            <el-option label="디자인" value="Design" />
            <el-option label="서비스업" value="Service" />
            <el-option label="기타" value="Others" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="난이도" prop="difficulty_level">
          <el-select v-model="editForm.difficulty_level" placeholder="난이도를 선택하세요" style="width: 100%">
            <el-option label="초급" value="Beginner" />
            <el-option label="중급" value="Intermediate" />
            <el-option label="고급" value="Advanced" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="설명" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="4"
            placeholder="자격증에 대한 상세 설명을 입력하세요"
          />
        </el-form-item>
        
        <el-form-item label="상태">
          <el-switch 
            v-model="editForm.is_active" 
            active-text="활성" 
            inactive-text="비활성"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">취소</el-button>
          <el-button type="primary" @click="handleUpdateCertificate">
            저장
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Create Certificate Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      title="자격증 등록"
      width="600px"
      @close="resetCreateForm"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="120px"
      >
        <el-form-item label="자격증 이름" prop="name">
          <el-input v-model="createForm.name" placeholder="자격증 이름을 입력하세요" />
        </el-form-item>
        
        <el-form-item label="발급기관" prop="issuing_authority">
          <el-select v-model="createForm.issuing_authority" placeholder="발급기관을 선택하세요" style="width: 100%">
            <el-option 
              v-for="issuer in issuers.filter(i => i.active)" 
              :key="issuer.id" 
              :label="issuer.name" 
              :value="issuer.name" 
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="자격증 분야" prop="category">
          <el-select v-model="createForm.category" placeholder="분야를 선택하세요" style="width: 100%">
            <el-option label="IT/컴퓨터" value="IT" />
            <el-option label="금융/회계" value="Finance" />
            <el-option label="의료/보건" value="Medical" />
            <el-option label="건설/기계" value="Engineering" />
            <el-option label="교육" value="Education" />
            <el-option label="기타" value="Other" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="난이도" prop="difficulty_level">
          <el-select v-model="createForm.difficulty_level" placeholder="난이도를 선택하세요" style="width: 100%">
            <el-option label="초급" value="Beginner" />
            <el-option label="중급" value="Intermediate" />
            <el-option label="고급" value="Advanced" />
            <el-option label="전문가" value="Expert" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="설명" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="3"
            placeholder="자격증에 대한 설명을 입력하세요"
          />
        </el-form-item>
        
        <el-form-item label="상태" prop="is_active">
          <el-switch
            v-model="createForm.is_active"
            active-text="활성"
            inactive-text="비활성"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showCreateDialog = false">취소</el-button>
          <el-button type="primary" @click="handleCreateCertificate">
            자격증 등록
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 발행기관 관리 Dialog -->
    <el-dialog
      v-model="showIssuersDialog"
      title="발행기관 관리"
      width="1000px"
      top="5vh"
    >
      <div class="issuers-management">
        <!-- 새 발행기관 추가 -->
        <div class="add-issuer-form">
          <h3>새 발행기관 추가</h3>
          <el-form :model="newIssuer" label-width="100px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="기관명" required>
                  <el-input v-model="newIssuer.name" placeholder="발행기관명을 입력하세요" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="기관코드" required>
                  <el-input v-model="newIssuer.code" placeholder="예: HRDK" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="웹사이트">
                  <el-input v-model="newIssuer.website" placeholder="https://..." />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="연락처">
                  <el-input v-model="newIssuer.phone" placeholder="02-1234-5678" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="설명">
              <el-input 
                v-model="newIssuer.description" 
                type="textarea" 
                :rows="2"
                placeholder="발행기관에 대한 간단한 설명을 입력하세요"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="addIssuer">
                <el-icon><Plus /></el-icon>
                발행기관 추가
              </el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 발행기관 목록 -->
        <div class="issuers-list">
          <div class="list-header">
            <h3>등록된 발행기관 ({{ filteredIssuers.length }}개)</h3>
            <el-input
              v-model="issuerSearchQuery"
              placeholder="기관명, 코드, 설명으로 검색..."
              :prefix-icon="Search"
              style="width: 300px"
              clearable
            />
          </div>
          
          <el-table :data="filteredIssuers" style="width: 100%" height="400">
            <el-table-column prop="name" label="기관명" min-width="150" />
            <el-table-column prop="code" label="기관코드" width="100" />
            <el-table-column label="연락정보" min-width="200">
              <template #default="scope">
                <div v-if="scope.row.website || scope.row.phone">
                  <div v-if="scope.row.website" class="contact-info">
                    <el-icon><Link /></el-icon>
                    <a :href="scope.row.website" target="_blank" class="website-link">
                      {{ scope.row.website }}
                    </a>
                  </div>
                  <div v-if="scope.row.phone" class="contact-info">
                    <el-icon><Phone /></el-icon>
                    {{ scope.row.phone }}
                  </div>
                </div>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="설명" min-width="200" show-overflow-tooltip />
            <el-table-column label="상태" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.active ? 'success' : 'danger'">
                  {{ scope.row.active ? '활성' : '비활성' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="작업" width="160">
              <template #default="scope">
                <el-button
                  size="small"
                  :icon="Edit"
                  @click="editIssuer(scope.row)"
                >
                  편집
                </el-button>
                <el-button
                  size="small"
                  :type="scope.row.active ? 'warning' : 'success'"
                  @click="toggleIssuerStatus(scope.row)"
                >
                  {{ scope.row.active ? '비활성화' : '활성화' }}
                </el-button>
                <el-button
                  size="small"
                  type="danger"
                  :icon="Delete"
                  @click="removeIssuer(scope.row.id)"
                >
                  삭제
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showIssuersDialog = false">닫기</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 발행기관 편집 Dialog -->
    <el-dialog
      v-model="showEditIssuerDialog"
      title="발행기관 편집"
      width="600px"
    >
      <el-form :model="editingIssuer" label-width="100px">
        <el-form-item label="기관명" required>
          <el-input v-model="editingIssuer.name" />
        </el-form-item>
        <el-form-item label="기관코드" required>
          <el-input v-model="editingIssuer.code" />
        </el-form-item>
        <el-form-item label="웹사이트">
          <el-input v-model="editingIssuer.website" />
        </el-form-item>
        <el-form-item label="연락처">
          <el-input v-model="editingIssuer.phone" />
        </el-form-item>
        <el-form-item label="설명">
          <el-input 
            v-model="editingIssuer.description" 
            type="textarea" 
            :rows="3"
          />
        </el-form-item>
        <el-form-item label="상태">
          <el-switch 
            v-model="editingIssuer.active" 
            active-text="활성" 
            inactive-text="비활성"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditIssuerDialog = false">취소</el-button>
          <el-button type="primary" @click="saveIssuer">저장</el-button>
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
  Upload,
  Refresh,
  Document,
  View,
  Cpu,
  More,
  Download,
  Edit,
  Delete,
  Reading,
  Plus,
  DocumentCopy,
  Link,
  Phone,
  Setting,
} from '@element-plus/icons-vue'
import { useCertificatesStore } from '@/stores/certificates'
import type { Certificate, CertificateUpdate, User } from '@/types'
import { formatDate, formatFileSize } from '@/utils/format'

const router = useRouter()
const certificatesStore = useCertificatesStore()

// Search and pagination
const searchQuery = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

// Dialog states
const showEditDialog = ref(false)
const showCreateDialog = ref(false)
const showIssuersDialog = ref(false)

// Form refs
const editFormRef = ref<FormInstance>()
const createFormRef = ref<FormInstance>()

// Forms
const editForm = reactive<CertificateUpdate & { id: number }>({
  id: 0,
  name: '',
  issuing_authority: '',
  category: '',
  difficulty_level: '',
  description: '',
  is_active: true,
})

const createForm = reactive({
  name: '',
  issuing_authority: '',
  category: '',
  difficulty_level: '',
  description: '',
  is_active: true,
})

// 발행기관 관리
const issuers = ref([
  { id: 1, name: '한국산업인력공단', code: 'HRDK', active: true, website: 'https://www.q-net.or.kr', phone: '1644-8000', description: '국가기술자격 및 직업능력개발 전문기관' },
  { id: 2, name: '대한상공회의소', code: 'KCCI', active: true, website: 'https://www.korcham.net', phone: '02-6050-3114', description: '상공회의소법에 의한 경제단체' },
  { id: 3, name: '한국정보통신기술협회', code: 'TTA', active: true, website: 'https://www.tta.or.kr', phone: '02-580-0114', description: 'ICT 표준화 및 시험인증 전문기관' },
  { id: 4, name: '정보처리기술자격관리소', code: 'ITPE', active: true, website: 'https://www.ihd.or.kr', phone: '02-2239-7900', description: '정보처리 관련 자격증 관리기관' },
])

const issuerSearchQuery = ref('')
const showEditIssuerDialog = ref(false)
const editingIssuer = reactive({
  id: 0,
  name: '',
  code: '',
  active: true,
  website: '',
  phone: '',
  description: '',
})

const newIssuer = reactive({
  name: '',
  code: '',
  website: '',
  phone: '',
  description: '',
  active: true,
})

// 발행기관 필터링
const filteredIssuers = computed(() => {
  if (!issuerSearchQuery.value) return issuers.value
  const query = issuerSearchQuery.value.toLowerCase()
  return issuers.value.filter(issuer => 
    issuer.name.toLowerCase().includes(query) ||
    issuer.code.toLowerCase().includes(query) ||
    issuer.description?.toLowerCase().includes(query)
  )
})

// Form validation rules
const editRules: FormRules = {
  name: [
    { required: true, message: 'Please enter certificate name', trigger: 'blur' },
    { min: 3, max: 200, message: 'Length should be 3 to 200', trigger: 'blur' },
  ],
}

const createRules: FormRules = {
  name: [
    { required: true, message: '자격증 이름을 입력하세요', trigger: 'blur' },
    { min: 2, max: 200, message: '길이는 2자에서 200자 사이여야 합니다', trigger: 'blur' },
  ],
  issuing_authority: [
    { required: true, message: '발급기관을 입력하세요', trigger: 'blur' },
  ],
  category: [
    { required: true, message: '분야를 선택하세요', trigger: 'change' },
  ],
  difficulty_level: [
    { required: true, message: '난이도를 선택하세요', trigger: 'change' },
  ],
}

// Methods
const fetchCertificates = () => {
  let search = searchQuery.value
  if (statusFilter.value) {
    search += ` status:${statusFilter.value}`
  }
  certificatesStore.fetchCertificates(currentPage.value, pageSize.value, search)
}

const handleSearch = () => {
  currentPage.value = 1
  fetchCertificates()
}

const handleSortChange = () => {
  fetchCertificates()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchCertificates()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchCertificates()
}

const refreshCertificates = () => {
  fetchCertificates()
}

// 발행기관 관리 함수들
const addIssuer = () => {
  if (!newIssuer.name.trim() || !newIssuer.code.trim()) {
    ElMessage.warning('기관명과 기관코드를 모두 입력해주세요')
    return
  }
  
  // 중복 체크
  const codeExists = issuers.value.some(i => i.code.toLowerCase() === newIssuer.code.trim().toLowerCase())
  if (codeExists) {
    ElMessage.warning('이미 존재하는 기관코드입니다')
    return
  }
  
  const newId = Math.max(...issuers.value.map(i => i.id)) + 1
  issuers.value.push({
    id: newId,
    name: newIssuer.name.trim(),
    code: newIssuer.code.trim().toUpperCase(),
    website: newIssuer.website.trim(),
    phone: newIssuer.phone.trim(),
    description: newIssuer.description.trim(),
    active: true
  })
  
  // 폼 초기화
  Object.assign(newIssuer, {
    name: '',
    code: '',
    website: '',
    phone: '',
    description: '',
    active: true,
  })
  
  ElMessage.success('발행기관이 추가되었습니다')
}

const editIssuer = (issuer: any) => {
  Object.assign(editingIssuer, issuer)
  showEditIssuerDialog.value = true
}

const saveIssuer = () => {
  if (!editingIssuer.name.trim() || !editingIssuer.code.trim()) {
    ElMessage.warning('기관명과 기관코드를 모두 입력해주세요')
    return
  }
  
  const index = issuers.value.findIndex(i => i.id === editingIssuer.id)
  if (index > -1) {
    issuers.value[index] = { ...editingIssuer }
    showEditIssuerDialog.value = false
    ElMessage.success('발행기관 정보가 업데이트되었습니다')
  }
}

const toggleIssuerStatus = async (issuer: any) => {
  try {
    const statusText = issuer.active ? '비활성화' : '활성화'
    const relatedCertificatesCount = certificatesStore.certificates.filter(
      cert => cert.issuer === issuer.name
    ).length
    
    let confirmMessage = `"${issuer.name}"을(를) ${statusText}하시겠습니까?`
    
    if (!issuer.active) {
      // 활성화하는 경우
      confirmMessage += `\n\n이 발행기관의 관련 자격증들도 다시 활성화됩니다.`
    } else if (relatedCertificatesCount > 0) {
      // 비활성화하는 경우
      confirmMessage += `\n\n이 발행기관에서 발행한 ${relatedCertificatesCount}개의 자격증도 함께 비활성화되며, 관련 문제와 학습자료를 사용할 수 없게 됩니다.`
    }
    
    await ElMessageBox.confirm(
      confirmMessage,
      `발행기관 ${statusText}`,
      {
        confirmButtonText: statusText,
        cancelButtonText: '취소',
        type: 'warning',
        dangerouslyUseHTMLString: true,
      }
    )
    
    const oldStatus = issuer.active
    issuer.active = !issuer.active
    
    // 관련 자격증들도 상태 변경
    if (relatedCertificatesCount > 0) {
      certificatesStore.certificates.forEach(cert => {
        if (cert.issuer === issuer.name) {
          cert.is_active = issuer.active
        }
      })
    }
    
    ElMessage.success(
      `${issuer.name}이(가) ${issuer.active ? '활성화' : '비활성화'}되었습니다` +
      (relatedCertificatesCount > 0 ? `\n관련 자격증 ${relatedCertificatesCount}개도 함께 ${statusText}되었습니다` : '')
    )
  } catch (error) {
    // 취소됨
  }
}

const removeIssuer = async (id: number) => {
  try {
    const issuer = issuers.value.find(i => i.id === id)
    if (!issuer) return
    
    await ElMessageBox.confirm(
      `"${issuer.name}"을(를) 삭제하시겠습니까?\n\n삭제된 발행기관은 복구할 수 없습니다.`,
      '발행기관 삭제',
      {
        confirmButtonText: '삭제',
        cancelButtonText: '취소',
        type: 'danger',
      }
    )
    
    const index = issuers.value.findIndex(i => i.id === id)
    if (index > -1) {
      issuers.value.splice(index, 1)
      ElMessage.success('발행기관이 삭제되었습니다')
    }
  } catch (error) {
    // 취소됨
  }
}

// 자격증 상태 토글 함수
const toggleCertificateStatus = async (certificate: Certificate) => {
  try {
    const newStatus = certificate.is_active
    const statusText = newStatus ? '활성화' : '비활성화'
    const impactMessage = newStatus 
      ? '관련 문제와 학습자료가 사용 가능해집니다.'
      : '관련 문제와 학습자료가 비활성화되어 사용할 수 없게 됩니다.'
    
    await ElMessageBox.confirm(
      `"${certificate.name}" 자격증을 ${statusText}하시겠습니까?\n\n${impactMessage}`,
      `자격증 ${statusText} 확인`,
      {
        confirmButtonText: statusText,
        cancelButtonText: '취소',
        type: 'warning',
        dangerouslyUseHTMLString: true,
      }
    )
    
    // 실제 API 호출로 상태 업데이트
    const updateData = {
      name: certificate.name,
      description: certificate.description,
      issuer: certificate.issuer,
      category: certificate.category,
      difficulty_level: certificate.difficulty_level,
      is_active: newStatus
    }
    
    const response = await fetch(`http://localhost:8100/api/admin/certificates/${certificate.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updateData)
    })
    
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success(`자격증이 ${statusText}되었습니다`)
      // 목록 새로고침
      await fetchCertificates()
    } else {
      // 실패 시 스위치 원래 상태로 되돌리기
      certificate.is_active = !newStatus
      throw new Error(data.message || '상태 변경에 실패했습니다')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to toggle certificate status:', error)
      // 상태를 원래대로 되돌림
      certificate.is_active = !newStatus
      ElMessage.error('상태 변경에 실패했습니다')
    } else {
      // 사용자가 취소한 경우 상태를 원래대로 되돌림
      certificate.is_active = !newStatus
    }
  }
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

const getIssuerCode = (issuerName: string): string => {
  const issuer = issuers.value.find(i => i.name === issuerName)
  return issuer ? issuer.code : ''
}


// handleAction 함수 제거됨 - 직접 버튼 클릭으로 대체


const editCertificate = (certificate: Certificate) => {
  editForm.id = certificate.id
  editForm.name = certificate.name
  editForm.issuing_authority = certificate.issuer || ''
  editForm.category = certificate.category || ''
  editForm.difficulty_level = certificate.difficulty_level || ''
  editForm.description = certificate.description || ''
  editForm.is_active = certificate.is_active ?? true
  showEditDialog.value = true
}

const deleteCertificate = async (certificate: Certificate) => {
  try {
    await ElMessageBox.confirm(
      `"${certificate.name}" 자격증을 삭제하시겠습니까?\n\n삭제된 자격증은 복구할 수 없으며, 관련된 모든 문제와 학습자료도 함께 삭제됩니다.`,
      '자격증 삭제',
      {
        confirmButtonText: '삭제',
        cancelButtonText: '취소',
        type: 'error',
        dangerouslyUseHTMLString: true,
      }
    )

    // 실제 백엔드 API 호출
    const response = await fetch(`http://localhost:8100/api/admin/certificates/${certificate.id}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('Delete response:', data) // 디버깅용
    
    if (data.success === true) {
      ElMessage.success('자격증이 삭제되었습니다')
      // 목록 새로고침
      await fetchCertificates()
    } else {
      throw new Error(data.message || '삭제 요청 실패')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete certificate:', error)
      ElMessage.error('자격증 삭제에 실패했습니다')
    }
  }
}

const handleUpdateCertificate = async () => {
  if (!editFormRef.value) return

  try {
    await editFormRef.value.validate()
    
    // 실제 백엔드 API 호출
    const updateData = {
      name: editForm.name,
      description: editForm.description,
      issuer: editForm.issuing_authority,
      category: editForm.category,
      difficulty_level: editForm.difficulty_level,
      is_active: editForm.is_active
    }
    
    const response = await fetch(`http://localhost:8100/api/admin/certificates/${editForm.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updateData)
    })
    
    const data = await response.json()
    
    if (data.success) {
      ElMessage.success('자격증이 수정되었습니다')
      showEditDialog.value = false
      resetEditForm()
      // 목록 새로고침
      await fetchCertificates()
    } else {
      throw new Error(data.message || '수정 요청 실패')
    }
  } catch (error) {
    console.error('Failed to update certificate:', error)
    ElMessage.error('자격증 수정에 실패했습니다')
  }
}

const resetEditForm = () => {
  Object.assign(editForm, {
    id: 0,
    name: '',
    description: '',
  })
  editFormRef.value?.resetFields()
}

const handleCreateCertificate = async () => {
  if (!createFormRef.value) return

  try {
    await createFormRef.value.validate()
    
    // 백엔드에서 title 필드를 사용하므로 매핑
    const certificateData = {
      title: createForm.name,
      description: createForm.description,
      issuer: createForm.issuing_authority,
      category: createForm.category,
      difficulty_level: createForm.difficulty_level,
      exam_duration_minutes: 120,
      passing_score: 60.0
    }
    
    const response = await fetch('http://localhost:8100/api/admin/certificates/create', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(certificateData)
    })
    
    const data = await response.json()
    
    if (data.success) {
      // 새로 생성된 자격증을 로컬 데이터에 추가
      const newCert = {
        id: data.certificate.id,
        name: data.certificate.title, // title -> name 매핑
        description: data.certificate.description,
        issuer: data.certificate.issuer,
        category: data.certificate.category,
        difficulty_level: data.certificate.difficulty_level,
        is_active: data.certificate.status === 'active',
        upload_date: data.certificate.created_at,
        user: {
          id: 1,
          username: 'admin',
          full_name: 'Administrator'
        }
      }
      certificatesStore.certificates.unshift(newCert)
      
      ElMessage.success('자격증이 성공적으로 등록되었습니다')
      showCreateDialog.value = false
      resetCreateForm()
    } else {
      throw new Error(data.error || '자격증 등록에 실패했습니다')
    }
  } catch (error) {
    console.error('Failed to create certificate:', error)
    ElMessage.error('자격증 등록에 실패했습니다')
  }
}

const resetCreateForm = () => {
  Object.assign(createForm, {
    name: '',
    issuing_authority: '',
    category: '',
    difficulty_level: '',
    description: '',
    is_active: true,
  })
  createFormRef.value?.resetFields()
}

// Initialize
onMounted(() => {
  fetchCertificates()
})
</script>

<style scoped>
.certificates-view {
  width: 100%;
  max-width: none;
  padding: 0;
}

.actions-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 0;
}

.search-section {
  display: flex;
  align-items: center;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

/* ===== 반응형 테이블 디자인 ===== */

/* 데스크톱 테이블 스타일 */
.responsive-table {
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

:deep(.responsive-table) {
  table-layout: auto;
}

:deep(.responsive-table th) {
  background-color: #fafafa;
  font-weight: 600;
  color: #606266;
  padding: 16px 12px;
  border-bottom: 2px solid #e4e7ed;
}

:deep(.responsive-table td) {
  padding: 14px 12px;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.responsive-table .cell) {
  word-break: break-word;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.4;
}

/* 작업 컨트롤 레이아웃 */
.action-controls {
  display: flex;
  align-items: center;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
  min-width: 180px;
}

.status-switch {
  display: flex;
  align-items: center;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 표준 버튼 스타일 - 규격 통일 */
.action-btn {
  width: 32px !important;
  height: 32px !important;
  min-width: 32px !important;
  padding: 0 !important;
  border-radius: 50% !important;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.action-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.action-btn.el-button--primary {
  background-color: #409eff;
  border-color: #409eff;
}

.action-btn.el-button--danger {
  background-color: #f56c6c;
  border-color: #f56c6c;
}

/* 날짜 셀 스타일 */
.date-cell {
  font-size: 12px;
  color: #909399;
  line-height: 1.2;
  white-space: nowrap;
}

/* 모바일 카드 레이아웃 */
.mobile-cards {
  display: none;
  gap: 16px;
  flex-direction: column;
}

.certificate-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 16px;
  border: 1px solid #e4e7ed;
  transition: all 0.2s ease;
}

.certificate-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transform: translateY(-1px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #2c3e50;
  flex: 1;
}

.card-number {
  background-color: #409eff;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.card-icon {
  color: #409eff;
  font-size: 18px;
}

.card-status {
  flex-shrink: 0;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
}

.info-label {
  font-weight: 500;
  color: #606266;
  min-width: 70px;
}

.info-value {
  color: #303133;
  flex: 1;
  text-align: right;
  word-break: break-word;
}

.card-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.action-switch {
  display: flex;
  align-items: center;
}

.action-buttons-mobile {
  display: flex;
  gap: 8px;
}

.mobile-btn {
  min-width: 60px;
  height: 32px;
  font-size: 12px;
}

/* ===== 반응형 미디어 쿼리 ===== */

/* 대형 화면 (1200px 이상) */
@media (min-width: 1200px) {
  .action-controls {
    gap: 20px;
    min-width: 200px;
  }
  
  .action-btn {
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
  }
}

/* 중간 화면 (768px - 1199px) */
@media (max-width: 1199px) and (min-width: 769px) {
  :deep(.responsive-table th),
  :deep(.responsive-table td) {
    padding: 12px 8px;
  }
  
  .action-controls {
    gap: 12px;
    min-width: 160px;
  }
  
  .action-btn {
    width: 30px !important;
    height: 30px !important;
    min-width: 30px !important;
  }
  
  .date-cell {
    font-size: 11px;
  }
}

/* 태블릿 (481px - 768px) */
@media (max-width: 768px) and (min-width: 481px) {
  :deep(.responsive-table th),
  :deep(.responsive-table td) {
    padding: 10px 6px;
  }
  
  .action-controls {
    flex-direction: column;
    gap: 8px;
    min-width: 120px;
  }
  
  .action-buttons {
    gap: 6px;
  }
  
  .action-btn {
    width: 28px !important;
    height: 28px !important;
    min-width: 28px !important;
  }
  
  .date-cell {
    font-size: 10px;
  }
}

/* 모바일 (480px 이하) */
@media (max-width: 480px) {
  /* 테이블 숨기고 카드 레이아웃 표시 */
  .responsive-table {
    display: none !important;
  }
  
  .mobile-cards {
    display: flex !important;
  }
  
  .certificate-card {
    padding: 12px;
  }
  
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .card-title {
    font-size: 14px;
  }
  
  .card-icon {
    font-size: 16px;
  }
  
  .info-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
  }
  
  .info-label {
    font-size: 12px;
    min-width: auto;
  }
  
  .info-value {
    font-size: 13px;
    text-align: left;
  }
  
  .card-actions {
    flex-direction: column;
    gap: 12px;
  }
  
  .action-buttons-mobile {
    width: 100%;
    justify-content: center;
  }
  
  .mobile-btn {
    flex: 1;
    max-width: 80px;
  }
}

.table-card {
  margin-bottom: 20px;
}

.certificate-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.certificate-icon {
  width: 32px;
  height: 32px;
  background: #f0f9ff;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #409eff;
}

.certificate-name {
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 2px;
}

.certificate-description {
  font-size: 12px;
  color: #7f8c8d;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-avatar {
  background-color: #409eff;
}

.username {
  font-size: 14px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.dialog-footer {
  display: flex;
  gap: 12px;
}

/* 발행기관 관리 스타일 */
.issuers-management {
  .add-issuer-form {
    margin-bottom: 24px;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 12px;
    border: 1px solid #e4e7ed;
    
    h3 {
      margin: 0 0 20px 0;
      color: #303133;
      font-size: 18px;
      font-weight: 600;
    }
  }

  .issuers-list {
    .list-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      
      h3 {
        margin: 0;
        color: #303133;
        font-size: 18px;
        font-weight: 600;
      }
    }
  }
}

.contact-info {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
  font-size: 13px;
  color: #606266;
  
  .el-icon {
    color: #909399;
  }
}

.website-link {
  color: #409eff;
  text-decoration: none;
  
  &:hover {
    text-decoration: underline;
  }
}

.status-tags {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.issuer-info {
  .issuer-name {
    font-weight: 500;
    color: #303133;
    line-height: 1.4;
  }
  
  .issuer-code {
    font-size: 12px;
    color: #909399;
    margin-top: 2px;
  }
}

.description-text {
  color: #606266;
  line-height: 1.4;
}

.no-description {
  color: #c0c4cc;
  font-style: italic;
}

/* Responsive design */
@media (max-width: 768px) {
  .actions-bar {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .search-section {
    width: 100%;
    flex-direction: column;
    gap: 12px;
  }
  
  .search-section .el-input,
  .search-section .el-select {
    width: 100% !important;
    margin-left: 0 !important;
  }
  
  .action-buttons {
    justify-content: center;
  }
  
  .certificate-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>