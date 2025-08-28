<template>
  <div class="not-found-view">
    <div class="not-found-container">
      <div class="error-content">
        <div class="error-code">404</div>
        <h1 class="error-title">Page Not Found</h1>
        <p class="error-description">
          The page you're looking for doesn't exist or has been moved.
        </p>
        
        <div class="error-actions">
          <el-button type="primary" size="large" @click="goHome">
            <el-icon><House /></el-icon>
            Go to Dashboard
          </el-button>
          
          <el-button size="large" @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            Go Back
          </el-button>
        </div>
        
        <div class="suggestions">
          <h3>You might be looking for:</h3>
          <ul class="suggestions-list">
            <li><router-link to="/dashboard">Dashboard</router-link></li>
            <li><router-link to="/certificates">Certificate Management</router-link></li>
            <li><router-link to="/upload">Upload PDF</router-link></li>
            <li><router-link to="/users">User Management</router-link></li>
            <li><router-link to="/ai-agents">AI Agents</router-link></li>
          </ul>
        </div>
      </div>
      
      <div class="error-illustration">
        <el-icon size="200" color="#d9d9d9"><Warning /></el-icon>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { House, ArrowLeft, Warning } from '@element-plus/icons-vue'

const router = useRouter()

const goHome = () => {
  router.push('/dashboard')
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.not-found-view {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 20px;
}

.not-found-container {
  display: flex;
  align-items: center;
  gap: 60px;
  max-width: 800px;
  width: 100%;
}

.error-content {
  flex: 1;
}

.error-code {
  font-size: 120px;
  font-weight: 900;
  color: #409eff;
  line-height: 1;
  margin-bottom: 20px;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
}

.error-title {
  font-size: 36px;
  font-weight: 700;
  color: #2c3e50;
  margin: 0 0 16px 0;
}

.error-description {
  font-size: 18px;
  color: #7f8c8d;
  margin: 0 0 32px 0;
  line-height: 1.6;
}

.error-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 40px;
}

.suggestions {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.suggestions h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #2c3e50;
}

.suggestions-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.suggestions-list li {
  margin-bottom: 8px;
}

.suggestions-list a {
  color: #409eff;
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s;
}

.suggestions-list a:hover {
  color: #66b1ff;
  text-decoration: underline;
}

.error-illustration {
  flex-shrink: 0;
  opacity: 0.3;
}

/* Responsive design */
@media (max-width: 768px) {
  .not-found-container {
    flex-direction: column;
    text-align: center;
    gap: 40px;
  }
  
  .error-code {
    font-size: 80px;
  }
  
  .error-title {
    font-size: 28px;
  }
  
  .error-description {
    font-size: 16px;
  }
  
  .error-actions {
    flex-direction: column;
    align-items: center;
  }
  
  .error-illustration {
    order: -1;
  }
  
  .error-illustration .el-icon {
    font-size: 120px !important;
  }
}

@media (max-width: 480px) {
  .error-actions {
    width: 100%;
  }
  
  .error-actions .el-button {
    width: 100%;
  }
}
</style>