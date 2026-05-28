<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useEvaluationStore } from '@/stores/evaluation'
import { useAuthStore } from '@/stores/auth'

const evaluationStore = useEvaluationStore()
const authStore = useAuthStore()
const categoryFilter = ref('')

onMounted(async () => {
  if (authStore.isAdmin) {
    await evaluationStore.fetchEvaluations()
  }
})

async function handleFilter() {
  await evaluationStore.fetchEvaluations(categoryFilter.value || undefined)
}

function getPassTagType(passed: boolean): string {
  return passed ? 'success' : 'danger'
}

function getPassLabel(passed: boolean): string {
  return passed ? '通过' : '失败'
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('zh-CN')
}

// 从 evaluations 中提取所有唯一的 category
const categories = computed(() => {
  const cats = new Set(evaluationStore.evaluations.map(e => e.category))
  return Array.from(cats).filter(Boolean)
})
</script>

<script lang="ts">
import { computed } from 'vue'
</script>

<template>
  <div class="evaluation-view">
    <el-card v-if="authStore.isAdmin">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon><DataAnalysis /></el-icon>
            <span>评测结果</span>
          </div>
          <div class="header-right">
            <el-select
              v-model="categoryFilter"
              placeholder="筛选分类"
              clearable
              @change="handleFilter"
              style="width: 200px; margin-right: 12px;"
            >
              <el-option label="全部" value="" />
              <el-option
                v-for="cat in categories"
                :key="cat"
                :label="cat"
                :value="cat"
              />
            </el-select>
            <el-button @click="handleFilter" :loading="evaluationStore.isLoading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <!-- 统计信息 -->
      <div class="statistics">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-statistic title="总用例数" :value="evaluationStore.totalCases" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="通过数" :value="evaluationStore.passedCases">
              <template #suffix>
                <span style="color: #67c23a;">✓</span>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="失败数" :value="evaluationStore.failedCases">
              <template #suffix>
                <span style="color: #f56c6c;">✗</span>
              </template>
            </el-statistic>
          </el-col>
          <el-col :span="6">
            <el-statistic title="通过率">
              <template #default>
                <el-progress
                  :percentage="evaluationStore.passRate"
                  :status="evaluationStore.passRate >= 90 ? 'success' : 'exception'"
                  :stroke-width="20"
                  :text-inside="true"
                />
              </template>
            </el-statistic>
          </el-col>
        </el-row>
      </div>

      <el-divider />

      <!-- 评测列表 -->
      <el-table
        :data="evaluationStore.evaluations"
        v-loading="evaluationStore.isLoading"
        style="width: 100%"
      >
        <el-table-column prop="case_id" label="用例 ID" width="180" />

        <el-table-column prop="category" label="分类" width="150">
          <template #default="{ row }">
            <el-tag type="info">{{ row.category || '未分类' }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="input" label="输入" show-overflow-tooltip />

        <el-table-column prop="expected_response_type" label="期望类型" width="120" />

        <el-table-column prop="actual_type" label="实际类型" width="120" />

        <el-table-column prop="passed" label="结果" width="100">
          <template #default="{ row }">
            <el-tag :type="getPassTagType(row.passed)">
              {{ getPassLabel(row.passed) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="评测时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="evaluationStore.evaluations.length === 0 && !evaluationStore.isLoading"
        description="暂无评测记录"
      />
    </el-card>

    <el-card v-else>
      <el-result
        icon="warning"
        title="权限不足"
        sub-title="评测结果仅管理员可访问"
      />
    </el-card>
  </div>
</template>

<style scoped>
.evaluation-view {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
}

.statistics {
  margin-bottom: 20px;
}
</style>
