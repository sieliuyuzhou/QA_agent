<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useAuditStore } from '@/stores/audit'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const auditStore = useAuditStore()
const authStore = useAuthStore()
const showDetailDialog = ref(false)
const selectedConversation = ref<any>(null)

onMounted(async () => {
  if (authStore.isAdmin) {
    await auditStore.fetchConversations()
  }
})

async function handleViewDetail(conversationId: string) {
  try {
    const detail = await auditStore.fetchConversationDetail(conversationId)
    selectedConversation.value = detail
    showDetailDialog.value = true
  } catch (error) {
    ElMessage.error('获取会话详情失败')
  }
}

function getStatusType(status: string): string {
  const map: Record<string, string> = {
    'active': 'success',
    'closed': 'info',
    'handoff_requested': 'warning'
  }
  return map[status] || 'info'
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<template>
  <div class="audit-view">
    <el-card v-if="authStore.isAdmin">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon><Document /></el-icon>
            <span>审计日志</span>
          </div>
          <el-button @click="auditStore.fetchConversations()" :loading="auditStore.isLoading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-table
        :data="auditStore.sortedConversations"
        v-loading="auditStore.isLoading"
        style="width: 100%"
      >
        <el-table-column prop="conversation_id" label="会话 ID" width="280">
          <template #default="{ row }">
            <el-link type="primary" @click="handleViewDetail(row.conversation_id)">
              {{ row.conversation_id }}
            </el-link>
          </template>
        </el-table-column>

        <el-table-column prop="user_id" label="用户" width="120" />

        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="title" label="标题" />

        <el-table-column prop="updated_at" label="最后更新" width="180">
          <template #default="{ row }">
            {{ formatDate(row.updated_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleViewDetail(row.conversation_id)">
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty
        v-if="auditStore.sortedConversations.length === 0 && !auditStore.isLoading"
        description="暂无会话记录"
      />
    </el-card>

    <el-card v-else>
      <el-result
        icon="warning"
        title="权限不足"
        sub-title="审计日志仅管理员可访问"
      />
    </el-card>

    <!-- 会话详情对话框 -->
    <el-dialog
      v-model="showDetailDialog"
      title="会话详情"
      width="900px"
    >
      <div v-if="selectedConversation" class="conversation-detail">
        <!-- 会话信息 -->
        <el-descriptions :column="2" border title="会话信息">
          <el-descriptions-item label="会话 ID">
            {{ selectedConversation.conversation_id }}
          </el-descriptions-item>
          <el-descriptions-item label="用户">
            {{ selectedConversation.user_id }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedConversation.status)">
              {{ selectedConversation.status }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ formatDate(selectedConversation.created_at) }}
          </el-descriptions-item>
        </el-descriptions>

        <!-- 消息列表 -->
        <el-divider>消息记录</el-divider>

        <div class="messages-list" v-if="selectedConversation.messages?.length">
          <div
            v-for="msg in selectedConversation.messages"
            :key="msg.id"
            :class="['message-item', msg.role]"
          >
            <div class="message-header">
              <el-tag :type="msg.role === 'user' ? 'primary' : 'success'" size="small">
                {{ msg.role === 'user' ? '用户' : '智能体' }}
              </el-tag>
              <el-tag v-if="msg.type" type="info" size="small">
                {{ msg.type }}
              </el-tag>
              <span class="message-time">{{ formatDate(msg.created_at) }}</span>
            </div>
            <div class="message-content">{{ msg.content }}</div>

            <!-- 引用 -->
            <div v-if="msg.citations?.length" class="message-citations">
              <el-divider content-position="left">引用来源</el-divider>
              <div v-for="(citation, idx) in msg.citations" :key="idx" class="citation">
                <strong>{{ citation.title }}</strong>: {{ citation.section }}
              </div>
            </div>
          </div>
        </div>

        <el-empty v-else description="暂无消息记录" />
      </div>

      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.audit-view {
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

.conversation-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.messages-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message-item {
  padding: 12px;
  border-radius: 8px;
  background: #f5f7fa;
}

.message-item.user {
  background: #ecf5ff;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.message-time {
  font-size: 12px;
  color: #909399;
  margin-left: auto;
}

.message-content {
  font-size: 14px;
  line-height: 1.6;
  word-break: break-word;
}

.message-citations {
  margin-top: 8px;
}

.citation {
  padding: 4px 8px;
  background: #fff;
  border-radius: 4px;
  font-size: 13px;
  margin-bottom: 4px;
}

.citation strong {
  color: #409eff;
}
</style>
