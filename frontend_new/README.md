# QA-agent 前端测试界面

## 快速开始

### 1. 安装依赖

```bash
cd frontend_new
npm install
```

### 2. 启动后端服务

确保后端 API 服务运行在 `http://localhost:8000`：

```bash
# 在项目根目录
python main.py
```

### 3. 启动前端开发服务器

```bash
cd frontend_new
npm run dev
```

前端将在 `http://localhost:3001` 启动（如果 3000 端口被占用会自动切换）。

### 4. 开始测试

1. 打开浏览器访问 `http://localhost:3001`
2. 选择测试用户（Alice/Bob/管理员）
3. 创建新会话开始对话测试

## 功能说明

### 核心功能

- ✅ **会话管理** - 创建、切换、查看会话列表
- ✅ **对话交互** - 发送消息、接收智能体回复
- ✅ **意图识别** - 显示当前意图（咨询/排障/售后/转人工）
- ✅ **引用来源** - 展示答案的知识来源
- ✅ **待确认动作** - 售后办理确认按钮
- ✅ **响应类型标识** - 视觉区分不同响应类型

### 测试场景

| 场景 | 测试消息 | 预期响应类型 |
|------|---------|------------|
| 产品咨询 | "X2 支持 Zigbee 吗？" | `final_answer` + 引用 |
| 型号澄清 | "门锁连不上 WiFi" | `ask_user` |
| 故障排查 | "X1 连不上 WiFi" | `final_answer` + 排障步骤 |
| 售后办理 | "我要退货" | `confirm_action` |
| 转人工 | 超出知识库的问题 | `handoff` + 摘要 |

## 技术栈

- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI 库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP 客户端**: Axios

## 项目结构

```
frontend_new/
├── src/
│   ├── components/         # 可复用组件
│   │   ├── ChatWindow.vue         # 对话窗口
│   │   ├── ConversationList.vue   # 会话列表
│   │   └── ChatDetail.vue         # 对话详情
│   ├── views/              # 页面视图
│   │   ├── ChatView.vue           # 主对话页面
│   │   ├── OrderView.vue          # 订单管理
│   │   ├── TicketView.vue         # 工单查询
│   │   ├── AuditView.vue          # 审计日志
│   │   ├── EvaluationView.vue     # 评测结果
│   │   └── HealthView.vue         # 系统状态
│   ├── stores/             # Pinia 状态管理
│   │   ├── auth.ts                # 用户认证
│   │   └── conversation.ts        # 会话管理
│   ├── router/             # 路由配置
│   │   └── index.ts
│   ├── main.ts             # 应用入口
│   ├── App.vue             # 根组件
│   └── style.css           # 全局样式
├── index.html
├── vite.config.ts          # Vite 配置
├── tsconfig.json
└── package.json
```

## API 代理配置

开发模式下，Vite 会自动代理以下请求到后端：

- `/api/*` → `http://localhost:8000/api/*`
- `/health` → `http://localhost:8000/health`

## 后续开发

### Phase 2（完整业务流程）

- 订单详情展示
- 工单查询功能
- 售后办理完整流程
- 健康检查实时状态

### Phase 3（管理与监控）

- 审计日志查看
- 评测结果统计
- 系统监控面板

## 故障排查

### 问题：无法连接后端 API

**解决方案**：
1. 确保后端服务运行在 `http://localhost:8000`
2. 检查后端服务是否正常启动
3. 查看浏览器控制台是否有 CORS 错误

### 问题：页面空白或加载失败

**解决方案**：
1. 检查浏览器控制台错误信息
2. 确保所有依赖已安装（`npm install`）
3. 清除浏览器缓存后重试

### 问题：会话创建失败

**解决方案**：
1. 检查后端数据库是否正常运行
2. 查看后端日志是否有错误信息
3. 确认测试用户数据已初始化

## 开发指南

### 添加新页面

1. 在 `src/views/` 创建新组件
2. 在 `src/router/index.ts` 添加路由
3. 在 `src/components/` 创建所需子组件

### 添加新 Store

1. 在 `src/stores/` 创建新 store 文件
2. 使用 `defineStore` 定义状态和方法
3. 在组件中通过 `useXxxStore()` 使用

### 调用后端 API

```typescript
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// GET 请求
const response = await axios.get('/api/xxx', {
  headers: { 'X-QA-User-Id': authStore.userId }
})

// POST 请求
const response = await axios.post('/api/xxx', 
  { /* 请求体 */ },
  { headers: { 'X-QA-User-Id': authStore.userId } }
)
```

## 相关文档

- 前端设计规格：`docs/solution/customer-service-frontend-design.md`
- 前端 worklist：`docs/worklists/customer-service-frontend-worklist.md`
- 后端方案：`docs/solution/customer-service-multi-agent-solution.md`
- 后端 worklist：`docs/worklists/customer-service-multi-agent-worklist.md`
