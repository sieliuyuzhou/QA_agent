import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from './auth'

// 类型定义
interface Ticket {
  ticket_id: string
  order_id: string
  user_id: string
  ticket_type: string
  eligibility_code: string
  reason: string
  status: string
  created_at: string
  updated_at: string
}

export const useTicketStore = defineStore('ticket', () => {
  // 状态
  const tickets = ref<Ticket[]>([])
  const currentTicketId = ref<string>('')
  const isLoading = ref(false)

  // 计算属性
  const currentTicket = computed(() =>
    tickets.value.find(t => t.ticket_id === currentTicketId.value)
  )

  const sortedTickets = computed(() =>
    [...tickets.value].sort((a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
  )

  // 方法
  async function fetchTicketDetail(ticketId: string) {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated) return

    isLoading.value = true
    try {
      const response = await axios.get(`/api/tickets/${ticketId}`, {
        headers: { 'X-QA-User-Id': authStore.userId }
      })
      return response.data
    } catch (error) {
      console.error('获取工单详情失败:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function fetchAdminTickets() {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated || !authStore.isAdmin) return

    isLoading.value = true
    try {
      const response = await axios.get('/api/admin/tickets', {
        headers: { 'X-QA-User-Id': authStore.userId }
      })
      tickets.value = response.data.tickets || []
    } catch (error) {
      console.error('获取工单列表失败:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  function selectTicket(ticketId: string) {
    currentTicketId.value = ticketId
  }

  function clearSelection() {
    currentTicketId.value = ''
  }

  return {
    tickets,
    currentTicketId,
    isLoading,
    currentTicket,
    sortedTickets,
    fetchTicketDetail,
    fetchAdminTickets,
    selectTicket,
    clearSelection
  }
})
