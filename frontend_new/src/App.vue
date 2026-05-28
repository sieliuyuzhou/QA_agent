<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

const showUserDialog = ref(false)
const tempUserId = ref('')

const mockUsers: Record<string, { name: string; role: string }> = {
  customer_alice: { name: 'Alice', role: 'customer' },
  customer_bob: { name: 'Bob', role: 'customer' },
  admin_zhang: { name: '张管理', role: 'admin' }
}

const activeMenu = computed(() => route.path)

const menuItems = [
  { path: '/', label: '对话', icon: 'ChatDotSquare' },
  { path: '/orders', label: '订单', icon: 'ShoppingCart' },
  { path: '/tickets', label: '工单', icon: 'Tickets' },
  { path: '/audit', label: '审计', icon: 'Document' },
  { path: '/evaluation', label: '评测', icon: 'DataAnalysis' },
  { path: '/health', label: '状态', icon: 'Monitor' }
]

onMounted(() => {
  authStore.init()
  if (!authStore.isAuthenticated) {
    showUserDialog.value = true
  }
})

function setUser() {
  if (!tempUserId.value) return
  const user = mockUsers[tempUserId.value] || { name: tempUserId.value, role: 'customer' }
  authStore.setUser(tempUserId.value, user.name, user.role)
  authStore.saveToStorage()
  showUserDialog.value = false
  ElMessage.success(`已切换为用户: ${user.name}`)
}

function switchUser() {
  authStore.clearUser()
  authStore.saveToStorage()
  tempUserId.value = ''
  showUserDialog.value = true
}

function handleMenuSelect(path: string) {
  router.push(path)
}
</script>

<template>
  <div id="app-root">
    <!-- 用户选择对话框 -->
    <el-dialog
      v-model="showUserDialog"
      title="设置测试用户"
      width="400px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="false"
    >
      <el-form @submit.prevent="setUser">
        <el-form-item label="用户 ID">
          <el-select v-model="tempUserId" placeholder="选择测试用户" style="width: 100%">
            <el-option label="Alice (普通用户)" value="customer_alice" />
            <el-option label="Bob (普通用户)" value="customer_bob" />
            <el-option label="张管理 (管理员)" value="admin_zhang" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button type="primary" @click="setUser" :disabled="!tempUserId">确认</el-button>
      </template>
    </el-dialog>

    <!-- 导航栏 -->
    <el-menu
      :default-active="activeMenu"
      mode="horizontal"
      class="top-nav"
      @select="handleMenuSelect"
    >
      <el-menu-item index="/">
        <el-icon><ChatDotSquare /></el-icon>
        <span>对话</span>
      </el-menu-item>
      <el-menu-item index="/orders">
        <el-icon><ShoppingCart /></el-icon>
        <span>订单</span>
      </el-menu-item>
      <el-menu-item index="/tickets">
        <el-icon><Tickets /></el-icon>
        <span>工单</span>
      </el-menu-item>
      <el-menu-item index="/audit">
        <el-icon><Document /></el-icon>
        <span>审计</span>
      </el-menu-item>
      <el-menu-item index="/evaluation">
        <el-icon><DataAnalysis /></el-icon>
        <span>评测</span>
      </el-menu-item>
      <el-menu-item index="/health">
        <el-icon><Monitor /></el-icon>
        <span>状态</span>
      </el-menu-item>

      <!-- 右侧用户信息 -->
      <div class="nav-right" v-if="authStore.isAuthenticated">
        <el-avatar :size="28" style="background: #409eff">
          {{ authStore.displayName ? authStore.displayName[0] : '?' }}
        </el-avatar>
        <span class="user-name">{{ authStore.displayName }}</span>
        <el-tag v-if="authStore.isAdmin" size="small" type="danger">管理员</el-tag>
        <el-button text @click="switchUser">切换</el-button>
      </div>
    </el-menu>

    <!-- 主内容区 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style>
/* 全局样式重置 */
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

#app {
  height: 100%;
}

#app-root {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f7fa;
}

.main-content {
  flex: 1;
  overflow: auto;
}

/* 导航栏样式 */
.top-nav {
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid #e4e7ed;
}

.nav-right {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
}

.nav-right .user-name {
  font-size: 14px;
  color: #303133;
}
</style>
