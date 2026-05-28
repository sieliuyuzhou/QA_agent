<script setup lang="ts">
import { useConversationStore } from '@/stores/conversation'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const conversationStore = useConversationStore()
const authStore = useAuthStore()

// 创建新会话
async function handleCreateConversation() {
  try {
    await conversationStore.createConversation()
    ElMessage.success('会话已创建')
  } catch (error) {
    ElMessage.error('创建会话失败')
  }
}

// 选择会话
function handleSelectConversation(conversationId: string) {
  conversationStore.currentConversationId = conversationId
}

// 格式化时间
function formatTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`

  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}小时前`

  return date.toLocaleDateString()
}
</script>

<template>
  <div class="conversation-list">
    <!-- 头部 -->
    <div class="list-header">
      <div class="user-info">
        <el-avatar :size="32" style="background: #409eff">
          {{ authStore.displayName ? authStore.displayName[0] : '?' }}
        </el-avatar>
        <div class="user-detail">
          <div class="user-name">{{ authStore.displayName || '未登录' }}</div>
          <div class="user-role">{{ authStore.role === 'admin' ? '管理员' : '用户' }}</div>
        </div>
      </div>
      <el-button
        type="primary"
        :icon="'Plus'"
        @click="handleCreateConversation"
        size="small"
      >
        新建会话
      </el-button>
    </div>

    <!-- 会话列表 -->
    <div class="list-content">
      <div v-if="conversationStore.sortedConversations.length === 0" class="empty-list">
        <el-empty description="暂无会话" :image-size="80" />
      </div>

      <div
        v-for="conv in conversationStore.sortedConversations"
        :key="conv.conversation_id"
        :class="['conversation-item', { active: conv.conversation_id === conversationStore.currentConversationId }]"
        @click="handleSelectConversation(conv.conversation_id)"
      >
        <div class="conv-info">
          <div class="conv-title">{{ conv.title || '新对话' }}</div>
          <div class="conv-time">{{ formatTime(conv.updated_at) }}</div>
        </div>
        <el-tag :type="conv.status === 'active' ? 'success' : 'info'" size="small">
          {{ conv.status }}
        </el-tag>
      </div>
    </div>
  </div>
</template>

<style scoped>
.conversation-list {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.list-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-detail {
  flex: 1;
}

.user-name {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.user-role {
  font-size: 12px;
  color: #909399;
}

.list-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.empty-list {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.conversation-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 4px;
}

.conversation-item:hover {
  background: #f5f7fa;
}

.conversation-item.active {
  background: #ecf5ff;
  border-left: 3px solid #409eff;
}

.conv-info {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 6px;
}

.conv-title {
  font-size: 14px;
  font-weight: 500;
  color: #303133;
  flex: 1;
}

.conv-time {
  font-size: 12px;
  color: #909399;
  white-space: nowrap;
}
</style>
