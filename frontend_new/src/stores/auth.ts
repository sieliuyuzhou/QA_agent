import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const userId = ref<string>('')
  const displayName = ref<string>('')
  const role = ref<string>('')

  // 计算属性
  const isAuthenticated = computed(() => !!userId.value)
  const isAdmin = computed(() => role.value === 'admin')

  // 方法
  function setUser(id: string, name: string, userRole: string) {
    userId.value = id
    displayName.value = name
    role.value = userRole
  }

  function clearUser() {
    userId.value = ''
    displayName.value = ''
    role.value = ''
  }

  // 初始化（从 localStorage 读取）
  function init() {
    const savedUserId = localStorage.getItem('qa_user_id')
    const savedName = localStorage.getItem('qa_user_name')
    const savedRole = localStorage.getItem('qa_user_role')

    if (savedUserId) {
      setUser(savedUserId, savedName || '', savedRole || '')
    }
  }

  // 保存到 localStorage
  function saveToStorage() {
    localStorage.setItem('qa_user_id', userId.value)
    localStorage.setItem('qa_user_name', displayName.value)
    localStorage.setItem('qa_user_role', role.value)
  }

  return {
    userId,
    displayName,
    role,
    isAuthenticated,
    isAdmin,
    setUser,
    clearUser,
    init,
    saveToStorage
  }
})
