import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'
import { useAuthStore } from './auth'

// 类型定义
interface Order {
  order_id: string
  product_id: string
  product_name: string
  product_model: string
  purchased_at: string
  status: string
  damage_type?: string
}

export const useOrderStore = defineStore('order', () => {
  // 状态
  const orders = ref<Order[]>([])
  const currentOrderId = ref<string>('')
  const isLoading = ref(false)

  // 计算属性
  const currentOrder = computed(() =>
    orders.value.find(o => o.order_id === currentOrderId.value)
  )

  const sortedOrders = computed(() =>
    [...orders.value].sort((a, b) =>
      new Date(b.purchased_at).getTime() - new Date(a.purchased_at).getTime()
    )
  )

  const activeOrders = computed(() =>
    orders.value.filter(o => o.status === 'active')
  )

  // 方法
  async function fetchOrders(statusFilter?: string) {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated) return

    isLoading.value = true
    try {
      const params: Record<string, string> = {}
      if (statusFilter) params.status = statusFilter

      const response = await axios.get('/api/orders', {
        headers: { 'X-QA-User-Id': authStore.userId },
        params
      })
      orders.value = response.data.orders || []
    } catch (error) {
      console.error('获取订单列表失败:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function fetchOrderDetail(orderId: string) {
    const authStore = useAuthStore()
    if (!authStore.isAuthenticated) return

    try {
      const response = await axios.get(`/api/orders/${orderId}`, {
        headers: { 'X-QA-User-Id': authStore.userId }
      })
      return response.data
    } catch (error) {
      console.error('获取订单详情失败:', error)
      throw error
    }
  }

  function selectOrder(orderId: string) {
    currentOrderId.value = orderId
  }

  function clearSelection() {
    currentOrderId.value = ''
  }

  return {
    orders,
    currentOrderId,
    isLoading,
    currentOrder,
    sortedOrders,
    activeOrders,
    fetchOrders,
    fetchOrderDetail,
    selectOrder,
    clearSelection
  }
})
