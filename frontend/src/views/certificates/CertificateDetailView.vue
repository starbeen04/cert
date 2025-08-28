<template>
  <div class="certificate-detail">
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack">Back</el-button>
        <div>
          <h1 class="page-title">Certificate Details</h1>
          <p class="page-description">View certificate information and study materials</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button :icon="Download" @click="downloadCertificate">
          Download
        </el-button>
        <el-button
          v-if="!certificate?.processed"
          type="success"
          :icon="Cpu"
          @click="processCertificate"
        >
          Process
        </el-button>
        <el-button type="primary" :icon="Edit" @click="showEditDialog = true">
          Edit
        </el-button>
      </div>
    </div>

    <div v-if="certificate" class="certificate-content">
      <el-row :gutter="20">
        <!-- Certificate Information -->
        <el-col :xs="24" :lg="12">
          <el-card class="info-card">
            <template #header>
              <div class="card-header">
                <span class="card-title">Certificate Information</span>
                <el-tag
                  :type="certificate.processed ? 'success' : 'warning'"
                  size="small"
                >
                  {{ certificate.processed ? 'Processed' : 'Pending' }}
                </el-tag>
              </div>
            </template>
            
            <el-descriptions :column="1" border>
              <el-descriptions-item label="Name">
                {{ certificate.name }}
              </el-descriptions-item>
              <el-descriptions-item label="Description">
                {{ certificate.description || 'No description' }}
              </el-descriptions-item>
              <el-descriptions-item label="File Size">
                {{ formatFileSize(certificate.file_size) }}
              </el-descriptions-item>
              <el-descriptions-item label="Upload Date">
                {{ formatDateTime(certificate.upload_date) }}
              </el-descriptions-item>
              <el-descriptions-item label="Processed Date">
                {{ certificate.processed_date ? formatDateTime(certificate.processed_date) : 'Not processed' }}
              </el-descriptions-item>
              <el-descriptions-item label="Questions Generated">
                {{ certificate.questions_generated }}
              </el-descriptions-item>
              <el-descriptions-item label="Uploaded By">
                <div v-if="certificate.user" class="user-info">
                  <el-avatar size="small" class="user-avatar">
                    {{ getUserInitials(certificate.user) }}
                  </el-avatar>
                  <span class="username">{{ certificate.user.username }}</span>
                </div>
                <span v-else>-</span>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- Processing Status -->
          <el-card v-if="!certificate.processed" class="status-card">
            <template #header>
              <span class="card-title">Processing Status</span>
            </template>
            
            <div class="processing-status">
              <el-alert
                title="Certificate Pending Processing"
                type="warning"
                description="This certificate has not been processed yet. Click the Process button to generate study materials."
                :closable="false"
              />
              
              <el-button
                type="primary"
                size="large"
                :icon="Cpu"
                @click="processCertificate"
                class="process-btn"
              >
                Process Certificate
              </el-button>
            </div>
          </el-card>
        </el-col>

        <!-- Study Materials -->
        <el-col :xs="24" :lg="12">
          <el-card class="materials-card">
            <template #header>
              <div class="card-header">
                <span class="card-title">Study Materials</span>
                <el-badge
                  :value="studyMaterials.length"
                  :type="studyMaterials.length > 0 ? 'primary' : 'info'"
                />
              </div>
            </template>
            
            <div v-if="loadingMaterials" class="loading-materials">
              <el-skeleton :rows="3" animated />
            </div>
            
            <div v-else-if="studyMaterials.length > 0" class="materials-list">
              <div
                v-for="material in studyMaterials"
                :key="material.id"
                class="material-item"
              >
                <div class="material-header">
                  <h4 class="material-title">{{ material.title }}</h4>
                  <el-tag
                    :type="getMaterialTypeColor(material.content_type)"
                    size="small"
                  >
                    {{ capitalize(material.content_type) }}
                  </el-tag>
                </div>
                <div class="material-content">
                  {{ truncateText(material.content, 200) }}
                </div>
              </div>
            </div>
            
            <el-empty
              v-else
              description="No study materials available"
              :image-size="80"
            />
          </el-card>
        </el-col>
      </el-row>

      <!-- Processing History -->
      <el-row :gutter="20" class="history-section">
        <el-col :span="24">
          <el-card class="history-card">
            <template #header>
              <span class="card-title">Processing History</span>
            </template>
            
            <el-timeline>
              <el-timeline-item
                :timestamp="formatDateTime(certificate.created_at)"
                type="primary"
              >
                <div class="timeline-content">
                  <h4>Certificate Uploaded</h4>
                  <p>Certificate file uploaded by {{ certificate.user?.username || 'Unknown' }}</p>
                </div>
              </el-timeline-item>
              
              <el-timeline-item
                v-if="certificate.processed"
                :timestamp="formatDateTime(certificate.processed_date!)"
                type="success"
              >
                <div class="timeline-content">
                  <h4>Processing Completed</h4>
                  <p>Generated {{ certificate.questions_generated }} study materials</p>
                </div>
              </el-timeline-item>
              
              <el-timeline-item
                :timestamp="formatDateTime(certificate.updated_at)"
                type="info"
              >
                <div class="timeline-content">
                  <h4>Last Updated</h4>
                  <p>Certificate information was last modified</p>
                </div>
              </el-timeline-item>
            </el-timeline>
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
      <el-empty description="Certificate not found" />
    </div>

    <!-- Edit Certificate Dialog -->
    <el-dialog
      v-model="showEditDialog"
      title="Edit Certificate"
      width="500px"
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
            :rows="3"
            placeholder="Optional description"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="showEditDialog = false">Cancel</el-button>
          <el-button type="primary" @click="handleUpdateCertificate">
            Update Certificate
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  ArrowLeft,
  Download,
  Edit,
  Cpu,
} from '@element-plus/icons-vue'
import { useCertificatesStore } from '@/stores/certificates'
import type { Certificate, CertificateUpdate, StudyMaterial, User } from '@/types'
import { formatDateTime, formatFileSize, truncateText, capitalize } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const certificatesStore = useCertificatesStore()

// State
const loading = ref(false)
const loadingMaterials = ref(false)
const showEditDialog = ref(false)
const editFormRef = ref<FormInstance>()

// Study materials (mock data - replace with real API calls)
const studyMaterials = ref<StudyMaterial[]>([])

// Edit form
const editForm = reactive<CertificateUpdate & { id: number }>({
  id: 0,
  name: '',
  description: '',
})

// Form validation rules
const editRules: FormRules = {
  name: [
    { required: true, message: 'Please enter certificate name', trigger: 'blur' },
    { min: 3, max: 200, message: 'Length should be 3 to 200', trigger: 'blur' },
  ],
}

// Computed
const certificateId = computed(() => parseInt(route.params.id as string))
const certificate = computed(() => certificatesStore.currentCertificate)

// Methods
const goBack = () => {
  router.push('/certificates')
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

const getMaterialTypeColor = (type: string): string => {
  switch (type) {
    case 'question':
      return 'primary'
    case 'answer':
      return 'success'
    case 'text':
      return 'info'
    default:
      return 'info'
  }
}

const downloadCertificate = async () => {
  if (!certificate.value) return
  
  try {
    await certificatesStore.downloadCertificate(certificate.value.id)
    ElMessage.success('Download started')
  } catch (error) {
    console.error('Failed to download certificate:', error)
    ElMessage.error('Failed to download certificate')
  }
}

const processCertificate = async () => {
  if (!certificate.value) return
  
  try {
    await ElMessageBox.confirm(
      `Process certificate "${certificate.value.name}"? This will generate study materials using AI.`,
      'Confirm Processing',
      {
        confirmButtonText: 'Process',
        cancelButtonText: 'Cancel',
        type: 'info',
      }
    )

    await certificatesStore.processCertificate(certificate.value.id)
    ElMessage.success('Certificate processing started')
    
    // Refresh certificate data
    await certificatesStore.fetchCertificate(certificateId.value)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to process certificate:', error)
      ElMessage.error('Failed to process certificate')
    }
  }
}

const handleUpdateCertificate = async () => {
  if (!editFormRef.value || !certificate.value) return

  try {
    await editFormRef.value.validate()
    const { id, ...updateData } = editForm
    await certificatesStore.updateCertificate(id, updateData)
    ElMessage.success('Certificate updated successfully')
    showEditDialog.value = false
    resetEditForm()
  } catch (error) {
    console.error('Failed to update certificate:', error)
    ElMessage.error('Failed to update certificate')
  }
}

const resetEditForm = () => {
  if (certificate.value) {
    editForm.id = certificate.value.id
    editForm.name = certificate.value.name
    editForm.description = certificate.value.description || ''
  }
  editFormRef.value?.resetFields()
}

const fetchStudyMaterials = async () => {
  // Mock study materials - replace with real API call
  loadingMaterials.value = true
  
  setTimeout(() => {
    studyMaterials.value = [
      {
        id: 1,
        certificate_id: certificateId.value,
        title: 'AWS EC2 Instance Types',
        content: 'Amazon EC2 provides a wide selection of instance types optimized to fit different use cases. Instance types comprise varying combinations of CPU, memory, storage, and networking capacity...',
        content_type: 'text',
        order_index: 1,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: 2,
        certificate_id: certificateId.value,
        title: 'What is the difference between on-demand and reserved instances?',
        content: 'This is a common question about AWS pricing models for EC2 instances.',
        content_type: 'question',
        order_index: 2,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      {
        id: 3,
        certificate_id: certificateId.value,
        title: 'On-Demand vs Reserved Instances Answer',
        content: 'On-Demand instances provide pay-as-you-go pricing with no long-term commitments, while Reserved Instances offer significant discounts (up to 75%) in exchange for a 1 or 3-year commitment.',
        content_type: 'answer',
        order_index: 3,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
    ]
    loadingMaterials.value = false
  }, 1000)
}

// Initialize
onMounted(async () => {
  try {
    loading.value = true
    await certificatesStore.fetchCertificate(certificateId.value)
    resetEditForm()
    await fetchStudyMaterials()
  } catch (error) {
    console.error('Failed to fetch certificate:', error)
    ElMessage.error('Failed to load certificate details')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.certificate-detail {
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

.status-card {
  margin-bottom: 20px;
}

.processing-status {
  text-align: center;
}

.process-btn {
  margin-top: 16px;
  width: 200px;
}

.materials-card {
  margin-bottom: 20px;
  height: fit-content;
}

.loading-materials {
  padding: 20px;
}

.materials-list {
  max-height: 400px;
  overflow-y: auto;
}

.material-item {
  padding: 16px;
  border-bottom: 1px solid #f0f2f5;
  transition: background-color 0.2s;
}

.material-item:hover {
  background-color: #f8f9fa;
}

.material-item:last-child {
  border-bottom: none;
}

.material-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.material-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
  flex: 1;
  margin-right: 12px;
}

.material-content {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

.history-section {
  margin-top: 20px;
}

.history-card {
  margin-bottom: 20px;
}

.timeline-content h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
}

.timeline-content p {
  margin: 0;
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
  
  .material-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .material-title {
    margin-right: 0;
  }
}
</style>