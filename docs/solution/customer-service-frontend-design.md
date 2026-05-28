# QA-agent 前端设计方案

| 项目 | 内容 |
| --- | --- |
| 文档状态 | 已确认方案基线 |
| 创建日期 | 2026-05-28 |
| 项目展示名称 | `QA-agent` |
| 适用仓库路径 | `E:\myProgram\QA_agent\frontend_new` |
| 当前目标 | 内部试用级客服前端测试界面 |
| 设计原则 | 最小可行（Karpathy Simplicity First） |
| 配套任务台账 | `docs/worklists/customer-service-frontend-worklist.md` |

## 1. 文档目的

本文档定义 `QA-agent` 前端测试界面的设计方案，用于在内部试用阶段验证多智能体客服系统的所有已完成能力。前端采用最小可行方案，优先覆盖所有测试场景，不过度设计，避免增加维护成本。

本文档用于指导前端实施与验收，不等同于已完成的实现。开发进度及验收结果记录在配套 worklist 中。

## 2. 设计原则

基于 Karpathy Guidelines：

1. **Simplicity First** - 最小代码解决问题，不添加未要求的功能
2. **Goal-Driven Execution** - 明确每个功能的测试目标
3. **No Speculative Code** - 不做假设，只实现已确认需求

核心约束：
- 前端不替换后端逻辑，只做可视化展示
- 优先测试完整流程，不追求界面美观度
- 使用成熟框架快速开发，避免过度封装
- 文档与实现同步更新

## 3. 当前后端能力基线

### 3.1 已实现 API（必须覆盖）

| API | 说明 | 前端测试场景 |
| --- | --- | --- |
| `POST /api/chat` | 核心对话接口 | 对话窗口、意图识别、多轮交互 |
| `POST /api/conversations` | 创建会话 | 会话管理、新建对话 |
| `GET /api/conversations/{id}` | 获取会话详情 | 历史消息查看 |
| `GET /api/conversations` | 列出活跃会话 | 会话列表展示 |
| `GET /api/orders` | 查看当前用户订单 | 订单查询测试 |
| `GET /api/orders/{id}` | 订单详情 | 订单详情展示 |
| `POST /api/conversations/{id}/actions` | 创建待确认动作 | 动作创建测试 |
| `POST /api/conversations/{id}/actions/{id}/confirm` | 确认执行动作 | 售后办理确认流程 |
| `GET /api/tickets/{id}` | 工单查询 | 工单状态查看 |
| `GET /health` | 健康检查 | 系统状态监控 |

### 3.2 多智能体架构（必须测试）

```
LangGraphSupervisor（意图路由 + 汇总）
  ├── TroubleshootingAgent（故障排查 LLM 循环）
  ├── AfterSalesAgent（售后办理确定性管道）
  ├── ConsultationHandler（产品咨询检索）
  └── HandoffWorkflow（转人工）

支持意图：
  - RouteConsultation（产品咨询）
  - RouteTroubleshooting（故障排查）
  - RouteAfterSales（售后办理）
  - AskUser（主动澄清）
  - Handoff（转人工）
```

### 3.3 响应协议（必须展示）

统一响应格式：
```json
{
  "type": "final_answer|ask_user|confirm_action|handoff|error",
  "content": "文本内容",
  "conversation_id": "uuid",
  "citations": [...],
  "pending_action": {...},
  "metadata": {...}
}
```

## 4. 前端方案选择

### 4.1 技术栈

| 层面 | 选择 | 理由 |
| --- | --- | --- |
| 框架 | Vue 3 + TypeScript | 简单易用、生态成熟、社区活跃 |
| 构建工具 | Vite | 快速开发、即时热更新 |
| 状态管理 | Pinia | Vue 3 官方推荐、轻量级 |
| HTTP 客户端 | Axios | 易用、支持拦截器 |
| UI 组件库 | Element Plus | 中文支持好、组件丰富 |
| 路由 | Vue Router | Vue 生态标准方案 |

**为什么选择 Vue？**
- 最小可行方案：Vue 学习曲线平缓，文档完整
- 不过度封装：直接使用 Vue 响应式，不引入复杂状态机
- 快速原型：Vite 热更新速度极快，适合快速迭代

### 4.2 整体架构

```
Frontend（Vue 3 SPA）
  ├── 公共层
  │   ├── 路由配置
  │   ├── 状态管理（Pinia stores）
  │   ├── HTTP 工具（Axios 实例 + 拦截器）
  │   └── 工具函数
  │
  ├── 组件库
  │   ├── 对话组件（ChatWindow、MessageBubble）
  │   ├── 会话组件（ConversationList、ConversationItem）
  │   ├── 展示组件（OrderCard、TicketCard、CitationCard）
  │   ├── 交互组件（ConfirmDialog、ActionCard）
  │   └── 管理组件（AuditTable、EvaluationPanel）
  │
  └── 页面视图
      ├── ChatView（核心对话页面）
      ├── OrderView（订单管理页面）
      ├── TicketView（工单查询页面）
      ├── AuditView（审计日志页面）
      ├── EvaluationView（评测结果页面）
      └── HealthView（系统状态页面）
```

### 4.3 功能模块划分

| 模块 | 职责 | 测试目标 |
| --- | --- | --- |
| **会话管理** | 创建、选择、删除会话 | 验证会话归属校验 |
| **对话窗口** | 消息发送、接收、展示 | 验证意图识别和响应协议 |
| **意图识别展示** | 标识当前意图和路由 | 验证 Supervisor 路由正确性 |
| **来源引用展示** | 展示答案来源和依据 | 验证结构化引用 |
| **订单查询** | 列表和详情展示 | 验证授权访问控制 |
| **售后办理流程** | 待确认动作交互 | 验证写操作保护机制 |
| **工单查询** | 工单详情展示 | 验证工单状态流转 |
| **转人工展示** | 摘要和状态提示 | 验证 HandoffSummary 质量 |
| **审计日志** | 工具调用和风险事件 | 验证审计记录完整性 |
| **评测面板** | 评测结果和统计 | 验证评测覆盖和正确率 |
| **系统状态** | 健康检查展示 | 验证系统可用性 |

## 5. 核心页面设计

### 5.1 ChatView（核心对话页面）

**布局设计：**
```
┌─────────────────────────────────────────────────────┐
│ 会话侧边栏 │          对话窗口          │ 侧边详情
│ (20%)       │           (60%)           │ (20%)
│             │                            │
│ 新建会话     │  [消息列表]                │ 当前意图
│ 会话列表     │    ····                    │ 路由决策
│             │    用户消息                 │ 引用来源
│             │    智能体回复               │ 订单信息
│             │                            │ 待确认动作
│             │  [输入框] [发送]            │
└─────────────────────────────────────────────────────┘
```

**关键功能：**
1. 对话消息实时发送与接收
2. 消息类型标识（final_answer / ask_user / confirm_action / handoff）
3. 待确认动作交互（确认按钮）
4. 来源引用点击展开
5. 当前会话状态展示

**测试场景：**
- ✅ 产品咨询（X2 支持 Zigbee 吗？）
- ✅ 型号澄清（门锁连不上 WiFi → ask_user）
- ✅ 故障排查（X1 连不上 WiFi → 步骤建议）
- ✅ 售后办理（查询订单 → 判资格 → confirm_action）
- ✅ 转人工（无知识 → handoff + 摘要）

### 5.2 OrderView（订单管理页面）

**功能：**
- 订单列表（按用户过滤）
- 订单详情展示
- 订单状态筛选

**测试场景：**
- ✅ 当前用户只能看到自己的订单
- ✅ 订单详情完整展示（产品、购买时间、状态）
- ✅ 越权访问拦截（其他用户订单）

### 5.3 TicketView（工单查询页面）

**功能：**
- 工单列表（管理视角）
- 工单详情
- 工单状态追踪

**测试场景：**
- ✅ 售后办理后工单正确创建
- ✅ 工单类型正确标识
- ✅ 幂等重复确认不重复建单

### 5.4 AuditView（审计日志页面）

**功能：**
- Agent 运行记录
- 工具调用日志
- 风险事件查看
- 按会话过滤

**测试场景：**
- ✅ 每次对话生成 Agent run 记录
- ✅ 工具调用完整记录（名称、输入、输出、状态）
- ✅ 风险事件正确标记（越权、提示注入等）

### 5.5 EvaluationView（评测结果页面）

**功能：**
- 评测用例列表
- 评测结果统计
- 单条用例详情

**测试场景：**
- ✅ 14 个场景覆盖验证
- ✅ pass/fail 正确统计
- ✅ 错误案例详情查看

## 6. 数据流设计

### 6.1 对话流程

```
用户输入
  ↓
POST /api/chat
  ↓
返回响应 {
  type: "ask_user" / "final_answer" / "confirm_action" / "handoff"
  content: "..."
  citations: [...]
  pending_action: {...}
}
  ↓
根据 type 展示不同 UI：
  - ask_user: 显示澄清问题
  - final_answer: 显示答案 + 引用
  - confirm_action: 显示确认按钮
  - handoff: 显示转人工提示 + 摘要
  ↓
用户确认（如需要）
  ↓
POST /api/conversations/{id}/actions/{action_id}/confirm
  ↓
更新工单状态
```

### 6.2 状态管理（Pinia stores）

| Store | 职责 |
| --- | --- |
| `useConversationStore` | 当前会话、消息历史 |
| `useAuthStore` | 用户身份、认证状态 |
| `useOrderStore` | 订单数据缓存 |
| `useTicketStore` | 工单数据缓存 |
| `useAuditStore` | 审计日志缓存 |
| `useEvaluationStore` | 评测结果缓存 |

## 7. 实施阶段

### 7.1 Phase 1：核心对话能力（P0）

**目标：** 验证对话和意图识别

| 任务 | 内容 | 验收标准 |
| --- | --- | --- |
| 项目初始化 | Vue 3 + Vite + TypeScript | 可启动开发服务器 |
| 基础布局 | ChatView 三栏布局 | 界面框架就绪 |
| 对话核心 | 消息发送、接收、展示 | 可发送消息并看到回复 |
| 意图展示 | 标识响应类型 | 能区分 final/ask/confirm/handoff |
| 引用展示 | 展示答案来源 | 点击可查看引用详情 |

### 7.2 Phase 2：完整业务流程（P1）

**目标：** 验证售后办理和确认

| 任务 | 内容 | 验收标准 |
| --- | --- | --- |
| 会话管理 | 会话创建、切换 | 可管理多个会话 |
| 订单查询 | 订单列表和详情 | 正确展示当前用户订单 |
| 待确认交互 | confirm_action 处理 | 可确认售后动作 |
| 工单查询 | 工单详情展示 | 工单状态正确 |
| 健康检查 | 系统状态展示 | 能看到依赖状态 |

### 7.3 Phase 3：管理与监控（P2）

**目标：** 验证审计和评测

| 任务 | 内容 | 验收标准 |
| --- | --- | --- |
| 审计日志 | Agent run 和 tool call | 可查看调用链路 |
| 风险事件 | 风险标记和查看 | 能标识风险操作 |
| 评测面板 | 评测结果统计 | 可查看通过率 |
| 系统监控 | 健康状态和性能 | 能监控系统状态 |

## 8. 测试验收矩阵

| 能力 | 测试场景 | 验证方式 |
| --- | --- | --- |
| 产品咨询 | "X2 支持 Zigbee 吗？" | 返回答案 + 引用 |
| 型号澄清 | "门锁连不上 WiFi" | 返回 ask_user |
| 故障排查 | "X1 连不上 WiFi" | 返回排障步骤 |
| 售后办理 | "我要退货" | 查询订单 + confirm_action |
| 确认建单 | 点击确认按钮 | 工单正确创建 |
| 转人工 | 无知识问题 | 返回 handoff + 摘要 |
| 权限隔离 | 查询他人订单 | 返回 404 |
| 审计追踪 | 对话完成后 | Agent run / tool call 有记录 |
| 评测覆盖 | 运行评测 | 14 个场景 > 90% pass |

## 9. 配套文档

| 文档 | 路径 | 内容 |
| --- | --- | --- |
| 前端设计规格 | 当前文档 | 设计方案 |
| 前端 worklist | `docs/worklists/customer-service-frontend-worklist.md` | 实施任务和进度 |
| 总体方案 | `docs/solution/customer-service-multi-agent-solution.md` | 后端能力基线 |
| 后端 worklist | `docs/worklists/customer-service-multi-agent-worklist.md` | 后端开发进度 |

## 10. 关键决策记录

| 决策 | 结论 | 理由 |
| --- | --- | --- |
| 前端框架 | Vue 3 + TypeScript | 最小可行、社区成熟、学习曲线低 |
| UI 库 | Element Plus | 中文支持好、组件丰富 |
| 实施策略 | 先对话核心，后管理功能 | 对话能力是核心测试目标 |
| 状态管理 | Pinia | Vue 3 官方推荐、轻量级 |
| 构建工具 | Vite | 快速开发、即时热更新 |
