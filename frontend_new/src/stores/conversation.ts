import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from './auth'

// 类型定义
interface Conversation {
  conversation_id: string
  title: string
  status: string
  created_at: string
  updated_at: string
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  type?: string
  citations?: any[]
  pending_action?: any
  metadata?: any
  created_at: string
}

export const useConversationStore = defineStore('conversation', () => {
  // 状态
  const conversations = ref<Conversation[]>([])
  const currentConversationId = ref<string>('')
  const messages = ref<Message[]>([])
  const isLoading = ref(false)
  const isSending = ref(false)

  // 计算属性
  const currentConversation = computed(() =>
    conversations.value.find(c => c.conversation_id === currentConversationId.value)
  )

  const sortedConversations = computed(() =>
    [...conversations.value].sort((a, b) =>
      new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    )
  )

  // 方法
  async function fetchConversations() {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated) return

    isLoading.value = true
    try {
      const response = await axios.get('/api/conversations', {
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

  async function createConversation() {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated) return

    try {
      const response = await axios.post('/api/conversations', {}, {
        headers: { 'X-QA-User-Id': authStore.userId }
      })
      const newConversation = response.data
      conversations.value.unshift(newConversation)
      currentConversationId.value = newConversation.conversation_id
      return newConversation
    } catch (error) {
      console.error('创建会话失败:', error)
      throw error
    }
  }

  async function fetchMessages(conversationId: string) {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated) return

    try {
      const response = await axios.get(`/api/conversations/${conversationId}`, {
        headers: { 'X-QA-User-Id': authStore.userId }
      })
      messages.value = response.data.messages || []
      currentConversationId.value = conversationId
    } catch (error) {
      console.error('获取消息历史失败:', error)
    }
  }

  async function sendMessage(content: string) {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated || !currentConversationId.value || isSending.value) return

    isSending.value = true

    try {
      // 添加用户消息到本地
      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: 'user',
        content,
        created_at: new Date().toISOString()
      }
      messages.value.push(userMessage)

      // 发送到后端
      const response = await axios.post('/api/chat', {
        conversation_id: currentConversationId.value,
        message: content
      }, {
        headers: { 'X-QA-User-Id': authStore.userId }
      })

      // 添加智能体回复
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.data.content,
        type: response.data.type,
        citations: response.data.citations,
        pending_action: response.data.pending_action,
        metadata: response.data.metadata,
        created_at: new Date().toISOString()
      }
      messages.value.push(assistantMessage)

      return response.data
    } catch (error) {
      console.error('发送消息失败:', error)
      throw error
    } finally {
      isSending.value = false
    }
  }

  async function confirmAction(actionId: string) {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated || !currentConversationId.value) return

    try {
      const response = await axios.post(
        `/api/conversations/${currentConversationId.value}/actions/${actionId}/confirm`,
        {},
        { headers: { 'X-QA-User-Id': authStore.userId } }
      )
      return response.data
    } catch (error) {
      console.error('确认动作失败:', error)
      throw error
    }
  }

  return {
    conversations,
    currentConversationId,
    messages,
    isLoading,
    isSending,
    currentConversation,
    sortedConversations,
    fetchConversations,
    createConversation,
    fetchMessages,
    sendMessage,
    confirmAction
  }
})
