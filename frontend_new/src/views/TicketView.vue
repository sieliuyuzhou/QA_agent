<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTicketStore } from '@/stores/ticket'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const ticketStore = useTicketStore()
const authStore = useAuthStore()
const showDetailDialog = ref(false)
const selectedTicket = ref<any>(null)
const ticketIdInput = ref('')

onMounted(async () => {
  // 如果是管理员，加载工单列表
  if (authStore.isAdmin) {
    await ticketStore.fetchAdminTickets()
  }
})

async function handleQueryTicket() {
  if (!ticketIdInput.value.trim()) {
    ElMessage.warning('请输入工单号')
    return
  }

  try {
    const detail = await ticketStore.fetchTicketDetail(ticketIdInput.value.trim())
    selectedTicket.value = detail
    showDetailDialog.value = true
  } catch (error: any) {
    if (error.response?.status === 404) {
      ElMessage.error('工单不存在或无权访问')
    } else {
      ElMessage.error('查询工单失败')
    }
  }
}

async function handleViewDetail(ticketId: string) {
  try {
    const detail = await ticketStore.fetchTicketDetail(ticketId)
    selectedTicket.value = detail
    showDetailDialog.value = true
  } catch (error) {
    ElMessage.error('获取工单详情失败')
  }
}

function getTypeLabel(type: string): string {
  const map: Record<string, string> = {
    'return_or_exchange': '退换货',
    'warranty_repair': '保修维修',
    'paid_repair': '付费维修'
  }
  return map[type] || type
}

function getTypeTagType(type: string): string {
  const map: Record<string, string> = {
    'return_or_exchange': 'warning',
    'warranty_repair': 'success',
    'paid_repair': 'primary'
  }
  return map[type] || 'info'
}

function getStatusLabel(status: string): string {
  const map: Record<string, string> = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return map[status] || status
}

function getStatusTagType(status: string): string {
  const map: Record<string, string> = {
    'pending': 'warning',
    'processing': 'primary',
    'completed': 'success',
    'cancelled': 'info'
  }
  return map[status] || 'info'
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<template>
  <div class="ticket-view">
    <!-- 工单查询卡片 -->
    <el-card class="query-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon><Tickets /></el-icon>
            <span>工单查询</span>
          </div>
        </div>
      </template>

      <el-form @submit.prevent="handleQueryTicket" class="query-form">
        <el-form-item label="工单号">
          <el-input
            v-model="ticketIdInput"
            placeholder="请输入工单号（如：TKT-xxx）"
            clearable
            style="width: 400px;"
          >
            <template #append>
              <el-button @click="handleQueryTicket" :loading="ticketStore.isLoading">
                <el-icon><Search /></el-icon>
                查询
              </el-button>
            </template>
          </el-input>
        </el-form-item>
      </el-form>

      <el-alert
        title="提示"
        type="info"
        description="工单在售后办理确认后自动创建。您可以在对话中完成售后办理流程，系统会返回工单号。"
        show-icon
        :closable="false"
      />
    </el-card>

    <!-- 管理员工单列表 -->
    <el-card v-if="authStore.isAdmin" class="admin-card">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon><List /></el-icon>
            <span>工单列表（管理员）</span>
          </div>
          <el-button @click="ticketStore.fetchAdminTickets()" :loading="ticketStore.isLoading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-table
        :data="ticketStore.sortedTickets"
        v-loading="ticketStore.isLoading"
        style="width: 100%"
      >
        <el-table-column prop="ticket_id" label="工单号" width="180">
          <template #default="{ row }">
            <el-link type="primary" @click="handleViewDetail(row.ticket_id)">
              {{ row.ticket_id }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column prop="ticket_type" label="类型" width="140">
          <template #default="{ row }">
            <el-tag :type="getTypeTagType(row.ticket_type)">
              {{ getTypeLabel(row.ticket_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="order_id" label="关联订单" width="180" />

        <el-table-column prop="eligibility_code" label="资格代码" width="200" />

        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusTagType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewDetail(row.ticket_id)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="ticketStore.sortedTickets.length === 0 && !ticketStore.isLoading"
        description="暂无工单"
      />
    </el-card>

    <!-- 工单详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="工单详情"
      width="700px"
    >
      <div v-if="selectedTicket" class="ticket-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="工单号">
            {{ selectedTicket.ticket_id }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(selectedTicket.status)">
              {{ getStatusLabel(selectedTicket.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="工单类型">
            <el-tag :type="getTypeTagType(selectedTicket.ticket_type)">
              {{ getTypeLabel(selectedTicket.ticket_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="关联订单">
            {{ selectedTicket.order_id }}
          </el-descriptions-item>
          <el-descriptions-item label="资格代码">
            {{ selectedTicket.eligibility_code }}
          </el-descriptions-item>
          <el-descriptions-item label="用户 ID">
            {{ selectedTicket.user_id }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="2">
            {{ formatDate(selectedTicket.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="原因" :span="2">
            {{ selectedTicket.reason || '无' }}
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.ticket-view {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.query-card,
.admin-card {
  width: 100%;
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

.query-form {
  margin-bottom: 20px;
}

.ticket-detail {
  padding: 10px 0;
}
</style>
