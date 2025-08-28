<template>
  <div class="instructor-student-detail">
    <div class="page-header">
      <div>
        <h1 class="page-title">학습자 상세</h1>
        <p class="page-description">학습자의 상세한 학습 현황을 확인하세요.</p>
      </div>
    </div>

    <el-card>
      <el-empty description="학습자 상세 정보 기능을 구현 중입니다">
        <el-button type="primary">학습 현황 보기</el-button>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// 학습자 상세 로직 구현 예정
</script>

<style scoped>
.instructor-student-detail {
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