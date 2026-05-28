<script setup lang="ts">
import { ref, onMounted } from 'vue'
import axios from 'axios'

const health = ref<any>(null)
const loading = ref(false)
const lastCheck = ref<string>('')

onMounted(async () => {
  await checkHealth()
})

async function checkHealth() {
  loading.value = true
  try {
    const response = await axios.get('/health')
    const data = response.data
    // 兼容两种响应格式
    if (data.checks) {
      // 格式: { status: "ok", checks: { database: "ok", knowledge_store: "ok" } }
      health.value = {
        status: data.status === 'ok' ? 'healthy' : data.status,
        message: data.message || '',
        database: data.checks.database || 'unknown',
        vector_store: data.checks.knowledge_store || data.checks.vector_store || 'unknown',
        faq_count: data.checks.faq_count
      }
    } else {
      // 格式: { status: "healthy", database: "ok", vector_store: "ok" }
      health.value = {
        ...data,
        status: data.status === 'ok' ? 'healthy' : data.status
      }
    }
    lastCheck.value = new Date().toLocaleString('zh-CN')
  } catch (error: any) {
    console.error('健康检查失败:', error)
    health.value = {
      status: 'error',
      message: error.message || '无法连接到服务',
      database: 'error',
      vector_store: 'error'
    }
    lastCheck.value = new Date().toLocaleString('zh-CN')
  } finally {
    loading.value = false
  }
}

function getStatusType(status: string): string {
  if (status === 'ok' || status === 'healthy') return 'success'
  if (status === 'error' || status === 'unhealthy') return 'danger'
  return 'warning'
}

function getStatusIcon(status: string): string {
  if (status === 'ok' || status === 'healthy') return 'CircleCheck'
  if (status === 'error' || status === 'unhealthy') return 'CircleClose'
  return 'Warning'
}
</script>

<template>
  <div class="health-view">
    <el-card v-loading="loading">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon><Monitor /></el-icon>
            <span>系统状态</span>
          </div>
          <div class="header-right">
            <span v-if="lastCheck" class="last-check">
              上次检查: {{ lastCheck }}
            </span>
            <el-button @click="checkHealth" :loading="loading">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <div v-if="health" class="health-content">
        <!-- 总体状态 -->
        <div class="overall-status">
          <el-result
            :icon="getStatusIcon(health.status)"
            :title="health.status === 'healthy' ? '系统正常' : '系统异常'"
            :sub-title="health.message || ''"
          />
        </div>

        <!-- 依赖状态 -->
        <el-divider>依赖服务状态</el-divider>

        <el-descriptions :column="2" border class="status-descriptions">
          <el-descriptions-item label="API 服务">
            <el-tag :type="getStatusType(health.status)" size="large">
              <el-icon><component :is="getStatusIcon(health.status)" /></el-icon>
              {{ health.status === 'healthy' ? '正常' : '异常' }}
            </el-tag>
          </el-descriptions-item>

          <el-descriptions-item label="数据库 (PostgreSQL)">
            <el-tag :type="getStatusType(health.database)" size="large">
              <el-icon><component :is="getStatusIcon(health.database)" /></el-icon>
              {{ health.database === 'ok' ? '正常' : '异常' }}
            </el-tag>
          </el-descriptions-item>

          <el-descriptions-item label="向量存储 (ChromaDB)">
            <el-tag :type="getStatusType(health.vector_store)" size="large">
              <el-icon><component :is="getStatusIcon(health.vector_store)" /></el-icon>
              {{ health.vector_store === 'ok' ? '正常' : '异常' }}
            </el-tag>
          </el-descriptions-item>

          <el-descriptions-item label="知识库条数" v-if="health.faq_count !== undefined">
            <el-tag type="info" size="large">
              {{ health.faq_count }} 条
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <!-- 故障排查建议 -->
        <el-divider v-if="health.status !== 'healthy'">故障排查</el-divider>

        <div v-if="health.status !== 'healthy'" class="troubleshooting">
          <el-alert
            title="数据库连接失败"
            type="error"
            description="请检查 PostgreSQL 服务是否启动，以及 docker-compose.yml 中的端口配置（默认 5433）"
            show-icon
            :closable="false"
            v-if="health.database !== 'ok'"
            style="margin-bottom: 12px;"
          />

          <el-alert
            title="向量存储连接失败"
            type="error"
            description="请检查 ChromaDB 数据目录是否存在（默认 data/chroma）"
            show-icon
            :closable="false"
            v-if="health.vector_store !== 'ok'"
            style="margin-bottom: 12px;"
          />

          <el-alert
            title="启动服务"
            type="info"
            description="运行 scripts/init_db.py 初始化数据库，运行 scripts/seed_mock_data.py 导入测试数据"
            show-icon
            :closable="false"
          />
        </div>
      </div>

      <el-empty v-else description="正在检查系统状态..." />
    </el-card>
  </div>
</template>

<style scoped>
.health-view {
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
  gap: 12px;
}

.last-check {
  font-size: 13px;
  color: #909399;
}

.health-content {
  padding: 10px 0;
}

.overall-status {
  text-align: center;
  margin-bottom: 20px;
}

.status-descriptions {
  max-width: 800px;
  margin: 0 auto;
}

.troubleshooting {
  max-width: 800px;
  margin: 0 auto;
}
</style>
