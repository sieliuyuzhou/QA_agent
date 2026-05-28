<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useConversationStore } from '@/stores/conversation'
import { useAuthStore } from '@/stores/auth'
import ChatWindow from '@/components/ChatWindow.vue'
import ConversationList from '@/components/ConversationList.vue'
import ChatDetail from '@/components/ChatDetail.vue'

const conversationStore = useConversationStore()
const authStore = useAuthStore()

onMounted(async () => {
  if (authStore.isAuthenticated) {
    await conversationStore.fetchConversations()
  }
})

// 用户选择身份后加载会话列表
watch(() => authStore.isAuthenticated, async (isAuth) => {
  if (isAuth && conversationStore.conversations.length === 0) {
    await conversationStore.fetchConversations()
  }
})

// 监听当前会话变化，加载消息
watch(() => conversationStore.currentConversationId, async (newId) => {
  if (newId) {
    await conversationStore.fetchMessages(newId)
  }
})
</script>

<template>
  <el-container class="chat-view">
    <!-- 主布局 -->
    <el-aside width="280px" class="chat-aside">
      <ConversationList />
    </el-aside>

    <el-main class="chat-main">
      <ChatWindow />
    </el-main>

    <el-aside width="320px" class="chat-detail">
      <ChatDetail />
    </el-aside>
  </el-container>
</template>

<style scoped>
.chat-view {
  height: 100%;
  background: #f5f7fa;
}

.chat-aside {
  background: #fff;
  border-right: 1px solid #e4e7ed;
  overflow: hidden;
}

.chat-main {
  padding: 0;
  background: #fff;
  display: flex;
  flex-direction: column;
}

.chat-detail {
  background: #fff;
  border-left: 1px solid #e4e7ed;
  overflow-y: auto;
}
</style>
