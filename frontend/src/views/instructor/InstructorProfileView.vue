<template>
  <div class="instructor-profile">
    <div class="page-header">
      <div>
        <h1 class="page-title">프로필 설정</h1>
        <p class="page-description">강사 프로필을 관리하세요.</p>
      </div>
    </div>

    <el-card>
      <el-form :model="profileForm" label-width="120px">
        <el-form-item label="이름">
          <el-input v-model="profileForm.name" />
        </el-form-item>
        <el-form-item label="이메일">
          <el-input v-model="profileForm.email" />
        </el-form-item>
        <el-form-item label="전문 분야">
          <el-input v-model="profileForm.specialty" />
        </el-form-item>
        <el-form-item label="자기소개">
          <el-input
            v-model="profileForm.bio"
            type="textarea"
            :rows="4"
            placeholder="자기소개를 입력하세요"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary">저장</el-button>
          <el-button>취소</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

const profileForm = ref({
  name: authStore.user?.full_name || '',
  email: authStore.user?.email || '',
  specialty: '',
  bio: ''
})
</script>

<style scoped>
.instructor-profile {
  padding: 0;
}

.page-header {
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
}
</style>