<template>
  <div class="ai-agents-view">
    <div class="page-header">
      <h1 class="page-title">AI 에이전트 관리</h1>
      <p class="page-description">자격증 처리를 위한 AI 에이전트 구성 및 관리</p>
    </div>

    <!-- Actions Bar -->
    <div class="actions-bar">
      <div class="search-section">
        <el-input
          v-model="searchQuery"
          placeholder="AI 에이전트 검색..."
          :prefix-icon="Search"
          clearable
          @input="handleSearch"
          style="width: 300px"
        />
        <el-select
          v-model="statusFilter"
          placeholder="상태별 필터"
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
          AI 에이전트 추가
        </el-button>
        <el-button
          :icon="Refresh"
          @click="refreshAgents"
        >
          새로고침
        </el-button>
      </div>
    </div>

    <!-- AI Agents Table -->
    <el-card class="table-card">
      <el-table
        v-loading="aiAgentsStore.isLoading"
        :data="aiAgentsStore.aiAgents"
        stripe
        @sort-change="handleSortChange"
      >
        <el-table-column
          prop="id"
          label="ID"
          width="80"
          sortable
        />
        
        <el-table-column
          prop="name"
          label="에이전트 이름"
          min-width="200"
          sortable
        >
          <template #default="scope">
            <div class="agent-info">
              <div class="agent-icon">
                <el-icon size="20"><Setting /></el-icon>
              </div>
              <div>
                <div class="agent-name">{{ scope.row.name }}</div>
                <div class="agent-description">
                  {{ scope.row.description || '설명 없음' }}
                </div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column
          prop="model_name"
          label="모델"
          min-width="150"
          sortable
        >
          <template #default="scope">
            <el-tag type="info" size="small">
              {{ scope.row.model_name }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column
          prop="is_active"
          label="상태"
          width="100"
          align="center"
        >
          <template #default="scope">
            <el-switch
              v-model="scope.row.is_active"
              @change="toggleAgentStatus(scope.row)"
            />
          </template>
        </el-table-column>

        <el-table-column
          prop="created_at"
          label="생성일"
          width="120"
          sortable
        >
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column
          label="작업"
          width="220"
          align="center"
        >
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              :icon="View"
              @click="viewAgent(scope.row)"
            >
              보기
            </el-button>
            <el-button
              type="success"
              size="small"
              :icon="ChatLineRound"
              @click="testAgent(scope.row)"
            >
              테스트
            </el-button>
            <el-dropdown @command="handleAction">
              <el-button size="small" :icon="More" />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    :command="{ action: 'edit', row: scope.row }"
                    :icon="Edit"
                  >
                    편집
                  </el-dropdown-item>
                  <el-dropdown-item
                    :command="{ action: 'delete', row: scope.row }"
                    :icon="Delete"
                    divided
                  >
                    삭제
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <!-- Pagination -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="aiAgentsStore.totalAgents"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- Create AI Agent Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      title="AI 에이전트 생성"
      width="600px"
      @close="resetCreateForm"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="120px"
      >
        <el-form-item label="이름" prop="name">
          <el-input v-model="createForm.name" placeholder="에이전트 이름 입력" />
        </el-form-item>
        
        <el-form-item label="설명" prop="description">
          <el-input
            v-model="createForm.description"
            type="textarea"
            :rows="2"
            placeholder="선택사항 설명"
          />
        </el-form-item>
        
        <el-form-item label="모델" prop="model_name">
          <el-select
            v-model="createForm.model_name"
            placeholder="AI 모델 선택"
            style="width: 100%"
            @focus="loadAvailableModels"
          >
            <el-option
              v-for="model in availableModels"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="시스템 프롬프트" prop="system_prompt">
          <el-input
            v-model="createForm.system_prompt"
            type="textarea"
            :rows="6"
            placeholder="AI 에이전트용 시스템 프롬프트 입력"
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
          <el-button type="primary" @click="handleCreateAgent">
            에이전트 생성
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Edit AI Agent Dialog -->
    <el-dialog
      v-model="showEditDialog"
      title="AI 에이전트 편집"
      width="600px"
      @close="resetEditForm"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="120px"
      >
        <el-form-item label="Name" prop="name">
          <el-input v-model="editForm.name" />
        </el-form-item>
        
        <el-form-item label="Description" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="2"
            placeholder="Optional description"
          />
        </el-form-item>
        
        <el-form-item label="Model" prop="model_name">
          <el-select
            v-model="editForm.model_name"
            placeholder="Select AI model"
            style="width: 100%"
            @focus="loadAvailableModels"
          >
            <el-option
              v-for="model in availableModels"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="System Prompt" prop="system_prompt">
          <el-input
            v-model="editForm.system_prompt"
            type="textarea"
            :rows="6"
          />
        </el-form-item>
        
        <el-form-item label="Status" prop="is_active">
          <el-switch
            v-model="editForm.is_active"
            active-text="Active"
            inactive-text="Inactive"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">취소</el-button>
          <el-button type="primary" @click="handleUpdateAgent">
            에이전트 업데이트
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Test AI Agent Dialog -->
    <el-dialog
      v-model="showTestDialog"
      title="AI 에이전트 테스트"
      width="700px"
      @close="resetTestDialog"
    >
      <div class="test-section">
        <h4>{{ testingAgent?.name }} 테스트</h4>
        <p>이 AI 에이전트에 테스트 프롬프트를 보내고 응답을 확인해보세요.</p>
        
        <el-form :model="testForm" label-width="80px">
          <el-form-item label="프롬프트">
            <el-input
              v-model="testForm.prompt"
              type="textarea"
              :rows="4"
              placeholder="테스트 프롬프트를 여기에 입력하세요..."
            />
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              :loading="testLoading"
              @click="executeTest"
            >
              테스트 전송
            </el-button>
          </el-form-item>
        </el-form>
        
        <div v-if="testResponse" class="test-response">
          <h4>응답:</h4>
          <div class="response-content">
            {{ testResponse }}
          </div>
        </div>
      </div>
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
  Setting,
  View,
  ChatLineRound,
  More,
  Edit,
  Delete,
} from '@element-plus/icons-vue'
import { useAIAgentsStore } from '@/stores/aiAgents'
import type { AIAgent, AIAgentCreate, AIAgentUpdate } from '@/types'
import { formatDate } from '@/utils/format'

const router = useRouter()
const aiAgentsStore = useAIAgentsStore()

// Search and pagination
const searchQuery = ref('')
const statusFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(20)

// Dialog states
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showTestDialog = ref(false)

// Form refs
const createFormRef = ref<FormInstance>()
const editFormRef = ref<FormInstance>()

// Available models
const availableModels = ref<string[]>([])

// Testing
const testingAgent = ref<AIAgent | null>(null)
const testLoading = ref(false)
const testResponse = ref('')
const testForm = reactive({
  prompt: '',
})

// Forms
const createForm = reactive<AIAgentCreate>({
  name: '',
  description: '',
  model_name: '',
  system_prompt: '',
  is_active: true,
})

const editForm = reactive<AIAgentUpdate & { id: number }>({
  id: 0,
  name: '',
  description: '',
  model_name: '',
  system_prompt: '',
  is_active: true,
})

// Form validation rules
const createRules: FormRules = {
  name: [
    { required: true, message: '에이전트 이름을 입력하세요', trigger: 'blur' },
    { min: 3, max: 100, message: '길이는 3자에서 100자 사이여야 합니다', trigger: 'blur' },
  ],
  model_name: [
    { required: true, message: '모델을 선택하세요', trigger: 'change' },
  ],
  system_prompt: [
    { required: true, message: '시스템 프롬프트를 입력하세요', trigger: 'blur' },
    { min: 10, message: '시스템 프롬프트는 최소 10자 이상이어야 합니다', trigger: 'blur' },
  ],
}

const editRules: FormRules = {
  name: [
    { required: true, message: '에이전트 이름을 입력하세요', trigger: 'blur' },
    { min: 3, max: 100, message: '길이는 3자에서 100자 사이여야 합니다', trigger: 'blur' },
  ],
  model_name: [
    { required: true, message: '모델을 선택하세요', trigger: 'change' },
  ],
  system_prompt: [
    { required: true, message: '시스템 프롬프트를 입력하세요', trigger: 'blur' },
    { min: 10, message: '시스템 프롬프트는 최소 10자 이상이어야 합니다', trigger: 'blur' },
  ],
}

// Methods
const fetchAgents = () => {
  let search = searchQuery.value
  if (statusFilter.value) {
    search += ` status:${statusFilter.value}`
  }
  aiAgentsStore.fetchAIAgents(currentPage.value, pageSize.value, search)
}

const handleSearch = () => {
  currentPage.value = 1
  fetchAgents()
}

const handleSortChange = () => {
  fetchAgents()
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
  fetchAgents()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  fetchAgents()
}

const refreshAgents = () => {
  fetchAgents()
}

const viewAgent = (agent: AIAgent) => {
  router.push(`/ai-agents/${agent.id}`)
}

const toggleAgentStatus = async (agent: AIAgent) => {
  try {
    await aiAgentsStore.toggleAgentStatus(agent.id)
    ElMessage.success(`에이전트가 성공적으로 ${agent.is_active ? '활성' : '비활성'}되었습니다`)
  } catch (error) {
    console.error('Failed to toggle agent status:', error)
    ElMessage.error('에이전트 상태 업데이트에 실패했습니다')
    // Revert the switch
    agent.is_active = !agent.is_active
  }
}

const testAgent = (agent: AIAgent) => {
  testingAgent.value = agent
  testForm.prompt = '안녕하세요, 자격증 학습 자료에 대해 도움을 주실 수 있나요?'
  showTestDialog.value = true
}

const handleAction = async ({ action, row }: { action: string; row: AIAgent }) => {
  switch (action) {
    case 'edit':
      editAgent(row)
      break
    case 'delete':
      await deleteAgent(row)
      break
  }
}

const editAgent = (agent: AIAgent) => {
  editForm.id = agent.id
  editForm.name = agent.name
  editForm.description = agent.description || ''
  editForm.model_name = agent.model_name
  editForm.system_prompt = agent.system_prompt
  editForm.is_active = agent.is_active
  showEditDialog.value = true
}

const deleteAgent = async (agent: AIAgent) => {
  try {
    await ElMessageBox.confirm(
      `정말로 AI 에이전트 "${agent.name}"을(를) 삭제하시겠습니까?`,
      '삭제 확인',
      {
        confirmButtonText: '삭제',
        cancelButtonText: '취소',
        type: 'warning',
      }
    )

    await aiAgentsStore.deleteAIAgent(agent.id)
    ElMessage.success('AI 에이전트가 성공적으로 삭제되었습니다')
    fetchAgents()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete agent:', error)
      ElMessage.error('AI 에이전트 삭제에 실패했습니다')
    }
  }
}

const handleCreateAgent = async () => {
  if (!createFormRef.value) return

  try {
    await createFormRef.value.validate()
    await aiAgentsStore.createAIAgent(createForm)
    ElMessage.success('AI 에이전트가 성공적으로 생성되었습니다')
    showCreateDialog.value = false
    resetCreateForm()
    fetchAgents()
  } catch (error) {
    console.error('Failed to create agent:', error)
    ElMessage.error('AI 에이전트 생성에 실패했습니다')
  }
}

const handleUpdateAgent = async () => {
  if (!editFormRef.value) return

  try {
    await editFormRef.value.validate()
    const { id, ...updateData } = editForm
    await aiAgentsStore.updateAIAgent(id, updateData)
    ElMessage.success('AI 에이전트가 성공적으로 업데이트되었습니다')
    showEditDialog.value = false
    resetEditForm()
    fetchAgents()
  } catch (error) {
    console.error('Failed to update agent:', error)
    ElMessage.error('AI 에이전트 업데이트에 실패했습니다')
  }
}

const executeTest = async () => {
  if (!testingAgent.value || !testForm.prompt.trim()) {
    ElMessage.warning('테스트 프롬프트를 입력하세요')
    return
  }

  try {
    testLoading.value = true
    testResponse.value = await aiAgentsStore.testAIAgent(testingAgent.value.id, testForm.prompt)
  } catch (error) {
    console.error('Failed to test agent:', error)
    ElMessage.error('AI 에이전트 테스트에 실패했습니다')
  } finally {
    testLoading.value = false
  }
}

const loadAvailableModels = async () => {
  if (availableModels.value.length === 0) {
    try {
      availableModels.value = await aiAgentsStore.getAvailableModels()
    } catch (error) {
      console.error('Failed to load models:', error)
    }
  }
}

const resetCreateForm = () => {
  Object.assign(createForm, {
    name: '',
    description: '',
    model_name: '',
    system_prompt: '',
    is_active: true,
  })
  createFormRef.value?.resetFields()
}

const resetEditForm = () => {
  Object.assign(editForm, {
    id: 0,
    name: '',
    description: '',
    model_name: '',
    system_prompt: '',
    is_active: true,
  })
  editFormRef.value?.resetFields()
}

const resetTestDialog = () => {
  testingAgent.value = null
  testForm.prompt = ''
  testResponse.value = ''
}

// Initialize
onMounted(() => {
  fetchAgents()
  loadAvailableModels()
})
</script>

<style scoped>
.ai-agents-view {
  max-width: 1200px;
  margin: 0 auto;
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

.table-card {
  margin-bottom: 20px;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.agent-icon {
  width: 32px;
  height: 32px;
  background: #f0f9ff;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #409eff;
}

.agent-name {
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 2px;
}

.agent-description {
  font-size: 12px;
  color: #7f8c8d;
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

.test-section h4 {
  margin: 0 0 8px 0;
  color: #2c3e50;
}

.test-section p {
  margin: 0 0 20px 0;
  color: #606266;
  font-size: 14px;
}

.test-response {
  margin-top: 20px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #409eff;
}

.test-response h4 {
  margin: 0 0 12px 0;
  color: #2c3e50;
  font-size: 14px;
}

.response-content {
  color: #606266;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
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
  
  .agent-info {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>