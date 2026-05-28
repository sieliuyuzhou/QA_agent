<script setup lang="ts">
import { computed } from 'vue'
import { useConversationStore } from '@/stores/conversation'

const conversationStore = useConversationStore()

// 获取最后一条智能体消息
const lastAssistantMessage = computed(() => {
  const messages = conversationStore.messages
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].role === 'assistant') {
      return messages[i]
    }
  }
  return null
})

// 获取当前意图
const currentIntent = computed(() => {
  if (!lastAssistantMessage.value?.metadata) return null
  return lastAssistantMessage.value.metadata.intent || null
})

// 获取路由决策
const currentWorkflow = computed(() => {
  if (!lastAssistantMessage.value?.metadata) return null
  return lastAssistantMessage.value.metadata.workflow || null
})
</script>

<template>
  <div class="chat-detail">
    <div class="detail-header">
      <h4>对话详情</h4>
    </div>

    <div class="detail-content" v-if="conversationStore.currentConversationId">
      <!-- 当前意图 -->
      <el-card class="detail-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon><Aim /></el-icon>
            <span>当前意图</span>
          </div>
        </template>
        <div v-if="currentIntent" class="intent-info">
          <el-tag :type="getIntentType(currentIntent)" size="default">
            {{ getIntentLabel(currentIntent) }}
          </el-tag>
        </div>
        <div v-else class="empty-info">暂无意图</div>
      </el-card>

      <!-- 路由决策 -->
      <el-card class="detail-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon><Connection /></el-icon>
            <span>路由决策</span>
          </div>
        </template>
        <div v-if="currentWorkflow" class="workflow-info">
          <el-tag type="primary" size="default">{{ currentWorkflow }}</el-tag>
        </div>
        <div v-else class="empty-info">暂无路由</div>
      </el-card>

      <!-- 最新引用来源 -->
      <el-card class="detail-card" shadow="never" v-if="lastAssistantMessage?.citations?.length">
        <template #header>
          <div class="card-header">
            <el-icon><Document /></el-icon>
            <span>引用来源</span>
          </div>
        </template>
        <div class="citations-list">
          <div
            v-for="(citation, idx) in lastAssistantMessage.citations"
            :key="idx"
            class="citation-item"
          >
            <div class="citation-title">{{ citation.title }}</div>
            <div class="citation-section">{{ citation.section }}</div>
          </div>
        </div>
      </el-card>

      <!-- 待确认动作 -->
      <el-card
        class="detail-card"
        shadow="never"
        v-if="lastAssistantMessage?.pending_action"
      >
        <template #header>
          <div class="card-header">
            <el-icon><Warning /></el-icon>
            <span>待确认动作</span>
          </div>
        </template>
        <div class="action-info">
          <div class="action-summary">
            {{ lastAssistantMessage.pending_action.display_summary }}
          </div>
          <div class="action-meta">
            <el-tag type="warning" size="small">
              {{ lastAssistantMessage.pending_action.action_type }}
            </el-tag>
            <span class="action-expires">
              过期时间: {{ new Date(lastAssistantMessage.pending_action.expires_at).toLocaleString() }}
            </span>
          </div>
        </div>
      </el-card>

      <!-- 会话统计 -->
      <el-card class="detail-card" shadow="never">
        <template #header>
          <div class="card-header">
            <el-icon><DataLine /></el-icon>
            <span>会话统计</span>
          </div>
        </template>
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-value">{{ conversationStore.messages.length }}</div>
            <div class="stat-label">消息数</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">
              {{ conversationStore.messages.filter(m => m.role === 'user').length }}
            </div>
            <div class="stat-label">用户消息</div>
          </div>
          <div class="stat-item">
            <div class="stat-value">
              {{ conversationStore.messages.filter(m => m.role === 'assistant').length }}
            </div>
            <div class="stat-label">智能体回复</div>
          </div>
        </div>
      </el-card>
    </div>

    <div v-else class="empty-detail">
      <el-empty description="选择会话查看详情" :image-size="100" />
    </div>
  </div>
</template>

<script lang="ts">
function getIntentType(intent: string): string {
  const map: Record<string, string> = {
    'consultation': 'success',
    'troubleshooting': 'warning',
    'after_sales': 'primary',
    'handoff': 'danger'
  }
  return map[intent] || 'info'
}

function getIntentLabel(intent: string): string {
  const map: Record<string, string> = {
    'consultation': '产品咨询',
    'troubleshooting': '故障排查',
    'after_sales': '售后办理',
    'handoff': '转人工'
  }
  return map[intent] || intent
}
</script>

<style scoped>
.chat-detail {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.detail-header {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  background: #fafafa;
}

.detail-header h4 {
  margin: 0;
  font-size: 15px;
  color: #303133;
}

.detail-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-card {
  border: 1px solid #ebeef5;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.intent-info,
.workflow-info {
  display: flex;
  justify-content: center;
  padding: 8px 0;
}

.empty-info {
  text-align: center;
  color: #909399;
  font-size: 13px;
  padding: 12px 0;
}

.citations-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.citation-item {
  padding: 8px;
  background: #fafafa;
  border-radius: 4px;
}

.citation-title {
  font-weight: 600;
  font-size: 13px;
  color: #409eff;
  margin-bottom: 4px;
}

.citation-section {
  font-size: 12px;
  color: #606266;
}

.action-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-summary {
  font-size: 13px;
  color: #303133;
  line-height: 1.5;
}

.action-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.action-expires {
  font-size: 12px;
  color: #909399;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  text-align: center;
}

.stat-item {
  padding: 8px;
  background: #fafafa;
  border-radius: 4px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #409eff;
}

.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.empty-detail {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>
