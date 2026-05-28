import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from './auth'

// 类型定义（保留供后续使用）
// interface AgentRun {
//   run_id: string
//   conversation_id: string
//   intent: string
//   workflow: string
//   response_type: string
//   latency_ms: number
//   status: string
//   created_at: string
// }

// interface ToolCall {
//   call_id: string
//   run_id: string
//   tool_name: string
//   input_summary: string
//   output_summary: string
//   status: string
//   latency_ms: number
//   created_at: string
// }

// interface RiskEvent {
//   event_id: string
//   conversation_id: string
//   event_type: string
//   severity: string
//   summary: string
//   created_at: string
// }

export const useAuditStore = defineStore('audit', () => {
  // 状态
  const conversations = ref<any[]>([])
  const currentConversation = ref<any>(null)
  const isLoading = ref(false)

  // 计算属性
  const sortedConversations = computed(() =>
    [...conversations.value].sort((a, b) =>
      new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    )
  )

  // 方法
  async function fetchConversations() {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated || !authStore.isAdmin) return

    isLoading.value = true
    try {
      const response = await axios.get('/api/admin/conversations', {
        headers: { 'X-QA-User-Id': authStore.userId }
      })
      conversations.value = response.data.conversations || []
    } catch (error) {
      console.error('获取会话列表失败:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function fetchConversationDetail(conversationId: string) {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated || !authStore.isAdmin) return

    isLoading.value = true
    try {
      const response = await axios.get(`/api/admin/conversations/${conversationId}`, {
        headers: { 'X-QA-User-Id': authStore.userId }
      })
      currentConversation.value = response.data
      return response.data
    } catch (error) {
      console.error('获取会话详情失败:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  return {
    conversations,
    currentConversation,
    isLoading,
    sortedConversations,
    fetchConversations,
    fetchConversationDetail
  }
})
