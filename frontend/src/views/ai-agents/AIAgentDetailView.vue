<template>
  <div class="agent-detail">
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack">Back</el-button>
        <div>
          <h1 class="page-title">AI Agent Details</h1>
          <p class="page-description">View and manage AI agent configuration</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button
          type="success"
          :icon="ChatLineRound"
          @click="showTestDialog = true"
        >
          Test Agent
        </el-button>
        <el-button type="primary" :icon="Edit" @click="showEditDialog = true">
          Edit Agent
        </el-button>
      </div>
    </div>

    <div v-if="agent" class="agent-content">
      <el-row :gutter="20">
        <!-- Agent Information -->
        <el-col :xs="24" :lg="12">
          <el-card class="info-card">
            <template #header>
              <div class="card-header">
                <span class="card-title">Agent Information</span>
                <el-switch
                  v-model="agent.is_active"
                  active-text="Active"
                  inactive-text="Inactive"
                  @change="toggleAgentStatus"
                />
              </div>
            </template>
            
            <el-descriptions :column="1" border>
              <el-descriptions-item label="Name">
                {{ agent.name }}
              </el-descriptions-item>
              <el-descriptions-item label="Description">
                {{ agent.description || 'No description' }}
              </el-descriptions-item>
              <el-descriptions-item label="Model">
                <el-tag type="info" size="small">
                  {{ agent.model_name }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="Status">
                <el-tag
                  :type="agent.is_active ? 'success' : 'danger'"
                  size="small"
                >
                  {{ agent.is_active ? 'Active' : 'Inactive' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="Created">
                {{ formatDateTime(agent.created_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="Last Updated">
                {{ formatDateTime(agent.updated_at) }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- Agent Statistics -->
          <el-card class="stats-card">
            <template #header>
              <span class="card-title">Usage Statistics</span>
            </template>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-value">{{ agentStats.totalRequests }}</div>
                <div class="stat-label">Total Requests</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ agentStats.successfulRequests }}</div>
                <div class="stat-label">Successful</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ formatPercentage(agentStats.successRate) }}</div>
                <div class="stat-label">Success Rate</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ agentStats.avgResponseTime }}ms</div>
                <div class="stat-label">Avg Response</div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="12">
          <!-- System Prompt -->
          <el-card class="prompt-card">
            <template #header>
              <span class="card-title">System Prompt</span>
            </template>
            
            <div class="prompt-content">
              <pre>{{ agent.system_prompt }}</pre>
            </div>
          </el-card>

          <!-- Recent Activity -->
          <el-card class="activity-card">
            <template #header>
              <span class="card-title">Recent Activity</span>
            </template>
            
            <el-timeline>
              <el-timeline-item
                v-for="activity in recentActivities"
                :key="activity.id"
                :timestamp="formatDateTime(activity.timestamp)"
                :type="activity.type"
              >
                <div class="activity-content">
                  <h4>{{ activity.title }}</h4>
                  <p>{{ activity.description }}</p>
                </div>
              </el-timeline-item>
            </el-timeline>
          </el-card>
        </el-col>
      </el-row>

      <!-- Performance Metrics -->
      <el-row :gutter="20" class="metrics-section">
        <el-col :span="24">
          <el-card class="metrics-card">
            <template #header>
              <span class="card-title">Performance Metrics</span>
            </template>
            
            <div class="metrics-content">
              <div class="metric-item">
                <div class="metric-header">
                  <span class="metric-name">Response Time (Last 24h)</span>
                  <el-tag size="small" type="success">Optimal</el-tag>
                </div>
                <el-progress :percentage="85" color="#67c23a" />
                <div class="metric-details">
                  Average: 450ms | Peak: 1.2s | Min: 200ms
                </div>
              </div>

              <div class="metric-item">
                <div class="metric-header">
                  <span class="metric-name">Success Rate (Last 7 days)</span>
                  <el-tag size="small" type="success">Excellent</el-tag>
                </div>
                <el-progress :percentage="96" color="#409eff" />
                <div class="metric-details">
                  256 successful / 267 total requests
                </div>
              </div>

              <div class="metric-item">
                <div class="metric-header">
                  <span class="metric-name">Error Rate</span>
                  <el-tag size="small" type="warning">Low</el-tag>
                </div>
                <el-progress :percentage="4" color="#e6a23c" />
                <div class="metric-details">
                  11 errors / 267 total requests
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- Loading State -->
    <div v-else-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <!-- Error State -->
    <div v-else class="error-container">
      <el-empty description="AI Agent not found" />
    </div>

    <!-- Edit Agent Dialog -->
    <el-dialog
      v-model="showEditDialog"
      title="Edit AI Agent"
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
          <el-button @click="showEditDialog = false">Cancel</el-button>
          <el-button type="primary" @click="handleUpdateAgent">
            Update Agent
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- Test Agent Dialog -->
    <el-dialog
      v-model="showTestDialog"
      title="Test AI Agent"
      width="700px"
      @close="resetTestDialog"
    >
      <div class="test-section">
        <h4>Test {{ agent?.name }}</h4>
        <p>Send a test prompt to this AI agent and see the response.</p>
        
        <el-form :model="testForm" label-width="80px">
          <el-form-item label="Prompt">
            <el-input
              v-model="testForm.prompt"
              type="textarea"
              :rows="4"
              placeholder="Enter your test prompt here..."
            />
          </el-form-item>
          
          <el-form-item>
            <el-button
              type="primary"
              :loading="testLoading"
              @click="executeTest"
            >
              Send Test
            </el-button>
            <el-button @click="clearTest">Clear</el-button>
          </el-form-item>
        </el-form>
        
        <div v-if="testResponse" class="test-response">
          <h4>Response:</h4>
          <div class="response-content">
            {{ testResponse }}
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import {
  ArrowLeft,
  Edit,
  ChatLineRound,
} from '@element-plus/icons-vue'
import { useAIAgentsStore } from '@/stores/aiAgents'
import type { AIAgent, AIAgentUpdate } from '@/types'
import { formatDateTime, formatPercentage } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const aiAgentsStore = useAIAgentsStore()

// State
const loading = ref(false)
const showEditDialog = ref(false)
const showTestDialog = ref(false)
const editFormRef = ref<FormInstance>()

// Available models
const availableModels = ref<string[]>([])

// Mock statistics (replace with real API calls)
const agentStats = reactive({
  totalRequests: 267,
  successfulRequests: 256,
  successRate: 0.96,
  avgResponseTime: 450,
})

// Mock recent activities (replace with real API calls)
const recentActivities = ref([
  {
    id: 1,
    title: 'Agent Used for Processing',
    description: 'Generated study materials for AWS certification',
    timestamp: new Date().toISOString(),
    type: 'primary',
  },
  {
    id: 2,
    title: 'Configuration Updated',
    description: 'System prompt was modified',
    timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    type: 'info',
  },
  {
    id: 3,
    title: 'Agent Activated',
    description: 'Agent status changed to active',
    timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
    type: 'success',
  },
])

// Testing
const testLoading = ref(false)
const testResponse = ref('')
const testForm = reactive({
  prompt: 'Hello, can you help me with certification study materials?',
})

// Edit form
const editForm = reactive<AIAgentUpdate & { id: number }>({
  id: 0,
  name: '',
  description: '',
  model_name: '',
  system_prompt: '',
  is_active: true,
})

// Form validation rules
const editRules: FormRules = {
  name: [
    { required: true, message: 'Please enter agent name', trigger: 'blur' },
    { min: 3, max: 100, message: 'Length should be 3 to 100', trigger: 'blur' },
  ],
  model_name: [
    { required: true, message: 'Please select a model', trigger: 'change' },
  ],
  system_prompt: [
    { required: true, message: 'Please enter system prompt', trigger: 'blur' },
    { min: 10, message: 'System prompt should be at least 10 characters', trigger: 'blur' },
  ],
}

// Computed
const agentId = computed(() => parseInt(route.params.id as string))
const agent = computed(() => aiAgentsStore.currentAgent)

// Methods
const goBack = () => {
  router.push('/ai-agents')
}

const toggleAgentStatus = async () => {
  if (!agent.value) return
  
  try {
    await aiAgentsStore.toggleAgentStatus(agent.value.id)
    ElMessage.success(`Agent ${agent.value.is_active ? 'activated' : 'deactivated'} successfully`)
  } catch (error) {
    console.error('Failed to toggle agent status:', error)
    ElMessage.error('Failed to update agent status')
    // Revert the switch
    if (agent.value) {
      agent.value.is_active = !agent.value.is_active
    }
  }
}

const handleUpdateAgent = async () => {
  if (!editFormRef.value || !agent.value) return

  try {
    await editFormRef.value.validate()
    const { id, ...updateData } = editForm
    await aiAgentsStore.updateAIAgent(id, updateData)
    ElMessage.success('AI agent updated successfully')
    showEditDialog.value = false
    resetEditForm()
  } catch (error) {
    console.error('Failed to update agent:', error)
    ElMessage.error('Failed to update AI agent')
  }
}

const executeTest = async () => {
  if (!agent.value || !testForm.prompt.trim()) {
    ElMessage.warning('Please enter a test prompt')
    return
  }

  try {
    testLoading.value = true
    testResponse.value = await aiAgentsStore.testAIAgent(agent.value.id, testForm.prompt)
  } catch (error) {
    console.error('Failed to test agent:', error)
    ElMessage.error('Failed to test AI agent')
  } finally {
    testLoading.value = false
  }
}

const clearTest = () => {
  testForm.prompt = ''
  testResponse.value = ''
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

const resetEditForm = () => {
  if (agent.value) {
    editForm.id = agent.value.id
    editForm.name = agent.value.name
    editForm.description = agent.value.description || ''
    editForm.model_name = agent.value.model_name
    editForm.system_prompt = agent.value.system_prompt
    editForm.is_active = agent.value.is_active
  }
  editFormRef.value?.resetFields()
}

const resetTestDialog = () => {
  testForm.prompt = 'Hello, can you help me with certification study materials?'
  testResponse.value = ''
}

// Initialize
onMounted(async () => {
  try {
    loading.value = true
    await aiAgentsStore.fetchAIAgent(agentId.value)
    resetEditForm()
    await loadAvailableModels()
  } catch (error) {
    console.error('Failed to fetch agent:', error)
    ElMessage.error('Failed to load AI agent details')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.agent-detail {
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.info-card {
  margin-bottom: 20px;
}

.stats-card {
  margin-bottom: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #7f8c8d;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.prompt-card {
  margin-bottom: 20px;
}

.prompt-content {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  border-left: 4px solid #409eff;
}

.prompt-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  color: #2c3e50;
}

.activity-card {
  margin-bottom: 20px;
}

.activity-content h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
}

.activity-content p {
  margin: 0;
  font-size: 12px;
  color: #7f8c8d;
}

.metrics-section {
  margin-top: 20px;
}

.metrics-card {
  margin-bottom: 20px;
}

.metrics-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.metric-item {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.metric-name {
  font-weight: 600;
  color: #2c3e50;
}

.metric-details {
  margin-top: 8px;
  font-size: 12px;
  color: #7f8c8d;
}

.loading-container,
.error-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
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
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .header-left {
    flex-direction: column;
    gap: 12px;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .metric-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>