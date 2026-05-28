<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useOrderStore } from '@/stores/order'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const orderStore = useOrderStore()
const authStore = useAuthStore()
const statusFilter = ref('')
const showDetailDialog = ref(false)
const selectedOrder = ref<any>(null)

onMounted(async () => {
  if (authStore.isAuthenticated) {
    await loadOrders()
  }
})

async function loadOrders() {
  try {
    await orderStore.fetchOrders(statusFilter.value || undefined)
  } catch (error) {
    ElMessage.error('获取订单失败')
  }
}

async function handleViewDetail(orderId: string) {
  try {
    const detail = await orderStore.fetchOrderDetail(orderId)
    selectedOrder.value = detail
    showDetailDialog.value = true
  } catch (error) {
    ElMessage.error('获取订单详情失败')
  }
}

function getStatusType(status: string): string {
  const map: Record<string, string> = {
    'active': 'success',
    'completed': 'info',
    'returned': 'warning',
    'exchanged': 'primary'
  }
  return map[status] || 'info'
}

function getStatusLabel(status: string): string {
  const map: Record<string, string> = {
    'active': '使用中',
    'completed': '已完成',
    'returned': '已退货',
    'exchanged': '已换货'
  }
  return map[status] || status
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  })
}
</script>

<template>
  <div class="order-view">
    <el-card>
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon><ShoppingCart /></el-icon>
            <span>订单管理</span>
          </div>
          <div class="header-right">
            <el-select
              v-model="statusFilter"
              placeholder="筛选状态"
              clearable
              @change="loadOrders"
              style="width: 150px; margin-right: 12px;"
            >
              <el-option label="全部" value="" />
              <el-option label="使用中" value="active" />
              <el-option label="已完成" value="completed" />
              <el-option label="已退货" value="returned" />
              <el-option label="已换货" value="exchanged" />
            </el-select>
            <el-button @click="loadOrders" :loading="orderStore.isLoading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        :data="orderStore.sortedOrders"
        v-loading="orderStore.isLoading"
        style="width: 100%"
        @row-click="(row: any) => handleViewDetail(row.order_id)"
      >
        <el-table-column prop="order_id" label="订单号" width="180">
          <template #default="{ row }">
            <el-link type="primary">{{ row.order_id }}</el-link>
          </template>
        </el-table-column>

        <el-table-column prop="product_name" label="产品名称" />

        <el-table-column prop="product_model" label="产品型号" width="120" />

        <el-table-column prop="purchased_at" label="购买时间" width="140">
          <template #default="{ row }">
            {{ formatDate(row.purchased_at) }}
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusLabel(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              @click.stop="handleViewDetail(row.order_id)"
            >
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="orderStore.sortedOrders.length === 0 && !orderStore.isLoading"
        description="暂无订单"
      />
    </el-card>

    <!-- 订单详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="订单详情"
      width="600px"
    >
      <div v-if="selectedOrder" class="order-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="订单号">
            {{ selectedOrder.order_id }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedOrder.status)">
              {{ getStatusLabel(selectedOrder.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="产品名称">
            {{ selectedOrder.product_name }}
          </el-descriptions-item>
          <el-descriptions-item label="产品型号">
            {{ selectedOrder.product_model }}
          </el-descriptions-item>
          <el-descriptions-item label="购买时间">
            {{ formatDate(selectedOrder.purchased_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="购买天数">
            {{ selectedOrder.purchase_days }} 天
          </el-descriptions-item>
          <el-descriptions-item label="故障类型" v-if="selectedOrder.damage_type">
            {{ selectedOrder.damage_type }}
          </el-descriptions-item>
          <el-descriptions-item label="保修状态">
            <el-tag :type="selectedOrder.warranty_status === 'in_warranty' ? 'success' : 'warning'">
              {{ selectedOrder.warranty_status === 'in_warranty' ? '保修期内' : '已过保' }}
            </el-tag>
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
.order-view {
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

.order-detail {
  padding: 10px 0;
}
</style>
