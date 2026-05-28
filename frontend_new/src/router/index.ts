import { createRouter, createWebHistory } from 'vue-router'
import ChatView from '@/views/ChatView.vue'
import OrderView from '@/views/OrderView.vue'
import TicketView from '@/views/TicketView.vue'
import AuditView from '@/views/AuditView.vue'
import EvaluationView from '@/views/EvaluationView.vue'
import HealthView from '@/views/HealthView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'chat',
      component: ChatView,
      meta: { title: '对话' }
    },
    {
      path: '/orders',
      name: 'orders',
      component: OrderView,
      meta: { title: '订单管理' }
    },
    {
      path: '/tickets',
      name: 'tickets',
      component: TicketView,
      meta: { title: '工单查询' }
    },
    {
      path: '/audit',
      name: 'audit',
      component: AuditView,
      meta: { title: '审计日志' }
    },
    {
      path: '/evaluation',
      name: 'evaluation',
      component: EvaluationView,
      meta: { title: '评测结果' }
    },
    {
      path: '/health',
      name: 'health',
      component: HealthView,
      meta: { title: '系统状态' }
    }
  ]
})

// 路由守卫 - 设置页面标题
router.beforeEach((to, _from, next) => {
  document.title = `${to.meta.title || 'QA-agent'} - 智能客服`
  next()
})

export default router
