<template>
  <div class="instructor-analytics">
    <div class="page-header">
      <div>
        <h1 class="page-title">학습 분석</h1>
        <p class="page-description">학습자들의 학습 데이터를 분석하고 인사이트를 얻으세요.</p>
      </div>
    </div>

    <el-card>
      <el-empty description="학습 분석 기능을 구현 중입니다">
        <el-button type="primary">분석 리포트 생성</el-button>
      </el-empty>
    </el-card>
  </div>
</template>

<script setup lang="ts">
// 분석 로직 구현 예정
</script>

<style scoped>
.instructor-analytics {
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