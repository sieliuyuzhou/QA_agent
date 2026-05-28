import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from './auth'

// 类型定义（保留供后续使用）
// interface EvaluationCase {
//   case_id: string
//   category: string
//   input: string
//   expected_response_type: string
//   expected_behavior: string
//   enabled: boolean
// }

// interface EvaluationRun {
//   eval_run_id: string
//   case_id: string
//   actual_type: string
//   passed: boolean
//   created_at: string
// }

export const useEvaluationStore = defineStore('evaluation', () => {
  // 状态
  const evaluations = ref<any[]>([])
  const isLoading = ref(false)
  const statistics = ref<any>(null)

  // 计算属性
  const totalCases = computed(() => evaluations.value.length)
  const passedCases = computed(() => evaluations.value.filter(e => e.passed).length)
  const failedCases = computed(() => evaluations.value.filter(e => !e.passed).length)
  const passRate = computed(() => {
    if (totalCases.value === 0) return 0
    return Math.round((passedCases.value / totalCases.value) * 100)
  })

  // 方法
  async function fetchEvaluations(caseId?: string) {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated || !authStore.isAdmin) return

    isLoading.value = true
    try {
      const params: Record<string, string> = {}
      if (caseId) params.case_id = caseId

      const response = await axios.get('/api/admin/evaluations', {
        headers: { 'X-QA-User-Id': authStore.userId },
        params
      })
      evaluations.value = response.data.evaluations || []
      statistics.value = response.data.statistics || null
    } catch (error) {
      console.error('获取评测结果失败:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  return {
    evaluations,
    isLoading,
    statistics,
    totalCases,
    passedCases,
    failedCases,
    passRate,
    fetchEvaluations
  }
})
