<script setup lang="ts">
import { ref, computed, nextTick, watch } from 'vue'
import { useConversationStore } from '@/stores/conversation'
import { ElMessage } from 'element-plus'

const conversationStore = useConversationStore()
const inputMessage = ref('')
const messageContainer = ref<HTMLElement>()

// 计算属性
const hasConversation = computed(() => !!conversationStore.currentConversationId)
const isSending = computed(() => conversationStore.isSending)

// 发送消息
async function handleSend() {
  if (!inputMessage.value.trim() || isSending.value) return

  const message = inputMessage.value.trim()
  inputMessage.value = ''

  try {
    await conversationStore.sendMessage(message)
    // 滚动到底部
    await nextTick()
    scrollToBottom()
  } catch (error) {
    ElMessage.error('发送消息失败')
  }
}

// 确认动作
async function handleConfirmAction(actionId: string) {
  try {
    await conversationStore.confirmAction(actionId)
    ElMessage.success('动作已确认')
    // 重新加载消息以获取更新
    if (conversationStore.currentConversationId) {
      await conversationStore.fetchMessages(conversationStore.currentConversationId)
    }
  } catch (error) {
    ElMessage.error('确认失败')
  }
}

// 滚动到底部
function scrollToBottom() {
  if (messageContainer.value) {
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight
  }
}

// 监听消息变化，自动滚动
watch(() => conversationStore.messages.length, () => {
  nextTick(() => scrollToBottom())
})
</script>

<template>
  <div class="chat-window">
    <!-- 头部 -->
    <div class="chat-header">
      <div class="header-info">
        <h3 v-if="conversationStore.currentConversation">
          {{ conversationStore.currentConversation.title || '新对话' }}
        </h3>
        <h3 v-else>选择或创建会话</h3>
      </div>
      <div class="header-actions">
        <el-tag v-if="conversationStore.currentConversation" type="success" size="small">
          {{ conversationStore.currentConversation.status }}
        </el-tag>
      </div>
    </div>

    <!-- 消息列表 -->
    <div ref="messageContainer" class="message-container">
      <div v-if="!hasConversation" class="empty-state">
        <el-empty description="请从左侧选择或创建会话" />
      </div>

      <div v-else class="message-list">
        <div
          v-for="msg in conversationStore.messages"
          :key="msg.id"
          :class="['message-item', msg.role]"
        >
          <div class="message-avatar">
            <el-avatar :size="36" :style="{ background: msg.role === 'user' ? '#409eff' : '#67c23a' }">
              {{ msg.role === 'user' ? '用' : '智' }}
            </el-avatar>
          </div>

          <div class="message-content">
            <div class="message-header">
              <span class="message-role">{{ msg.role === 'user' ? '用户' : '智能体' }}</span>
              <span class="message-time">{{ new Date(msg.created_at).toLocaleTimeString() }}</span>
              <el-tag v-if="msg.type" :type="getTypeTagType(msg.type)" size="small">
                {{ getTypeLabel(msg.type) }}
              </el-tag>
            </div>

            <div class="message-text">{{ msg.content }}</div>

            <!-- 引用来源 -->
            <div v-if="msg.citations && msg.citations.length > 0" class="citations">
              <el-collapse>
                <el-collapse-item title="查看引用来源">
                  <div v-for="(citation, idx) in msg.citations" :key="idx" class="citation-item">
                    <strong>{{ citation.title }}</strong>
                    <p>{{ citation.excerpt }}</p>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </div>

            <!-- 待确认动作 -->
            <div v-if="msg.pending_action" class="pending-action">
              <el-card shadow="hover">
                <template #header>
                  <span>待确认动作</span>
                </template>
                <p>{{ msg.pending_action.display_summary }}</p>
                <el-button
                  type="primary"
                  size="small"
                  @click="handleConfirmAction(msg.pending_action.action_id)"
                >
                  确认执行
                </el-button>
              </el-card>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入框 -->
    <div class="input-container">
      <el-input
        v-model="inputMessage"
        :disabled="!hasConversation || isSending"
        placeholder="输入消息..."
        @keyup.enter="handleSend"
        size="large"
      >
        <template #append>
          <el-button
            :icon="isSending ? 'Loading' : 'Promotion'"
            :loading="isSending"
            @click="handleSend"
            :disabled="!inputMessage.trim()"
          />
        </template>
      </el-input>
    </div>
  </div>
</template>

<script lang="ts">
// 工具函数
function getTypeTagType(type: string): string {
  const map: Record<string, string> = {
    'final_answer': 'success',
    'ask_user': 'warning',
    'confirm_action': 'primary',
    'handoff': 'danger',
    'error': 'danger'
  }
  return map[type] || 'info'
}

function getTypeLabel(type: string): string {
  const map: Record<string, string> = {
    'final_answer': '回答',
    'ask_user': '询问',
    'confirm_action': '待确认',
    'handoff': '转人工',
    'error': '错误'
  }
  return map[type] || type
}
</script>

<style scoped>
.chat-window {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafafa;
}

.header-info h3 {
  margin: 0;
  font-size: 16px;
  color: #303133;
}

.message-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.message-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-item {
  display: flex;
  gap: 12px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-content {
  max-width: 70%;
}

.message-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.message-item.user .message-header {
  flex-direction: row-reverse;
}

.message-role {
  font-weight: 600;
  font-size: 13px;
  color: #303133;
}

.message-time {
  font-size: 12px;
  color: #909399;
}

.message-text {
  background: #f4f4f5;
  padding: 12px 16px;
  border-radius: 8px;
  line-height: 1.6;
  word-break: break-word;
}

.message-item.user .message-text {
  background: #ecf5ff;
  color: #409eff;
}

.citations {
  margin-top: 8px;
}

.citation-item {
  padding: 8px;
  background: #fafafa;
  border-radius: 4px;
  margin-bottom: 8px;
}

.citation-item strong {
  display: block;
  margin-bottom: 4px;
  color: #409eff;
}

.citation-item p {
  margin: 0;
  font-size: 13px;
  color: #606266;
}

.pending-action {
  margin-top: 12px;
}

.input-container {
  padding: 16px 20px;
  border-top: 1px solid #e4e7ed;
  background: #fafafa;
}
</style>
