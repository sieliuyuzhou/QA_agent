# Phase 2 多智能体架构设计规格

| 项目 | 内容 |
| --- | --- |
| 文档状态 | 待用户确认 |
| 创建日期 | 2026-05-27 |
| 对应方案 | `docs/solution/customer-service-multi-agent-solution.md` §5.3, §10.3, §14.3 |
| 前置里程碑 | M2（Phase 1 MVP 验收通过） |
| 设计决策 | 方案 B — 领域 Agent 独立 ReAct 循环 |

## 1. 设计目标

Phase 2 在稳定的一期单 Agent 流程基础上引入领域子 Agent，实现：

1. `TroubleshootingAgent` 可独立运行、测试并被 Supervisor 调用。
2. `AfterSalesAgent` 可独立完成资格/待确认建议并被调度。
3. Supervisor 仅负责路由、汇总和全局对话控制。
4. 子 Agent 工具白名单与调用审计隔离。
5. 拆分前后行为、延迟和成本可对照验证。

## 2. 当前架构基线

```text
CustomerServiceAgent (单 ReAct 循环)
  ├── search_faq Tool
  ├── PrepareDiagnosis → DiagnosisWorkflow (纯业务逻辑)
  ├── PrepareAfterSales → AfterSalesWorkflow (纯业务逻辑)
  ├── Finish / AskUser / Handoff (终端动作)
  └── HandoffSummary (转人工摘要)
```

当前 Workflow 类无独立 LLM 循环，由 Agent 统一调度。Phase 2 将为每个领域 Agent 建立独立 ReAct 循环。

## 3. 目标架构

```text
CustomerServiceSupervisor (路由 + 汇总)
  ├── TroubleshootingAgent (独立 ReAct 循环)
  │     └── search_faq Tool
  ├── AfterSalesAgent (独立 ReAct 循环)
  │     ├── search_policy Tool
  │     ├── get_order Tool
  │     ├── check_eligibility Service
  │     └── create_pending_action Tool (受确认保护)
  ├── ConsultationHandler (知识检索 + 回答，保留为 Workflow)
  └── HandoffWorkflow (转人工，保留为 Workflow)
```

> 注：`diagnosis_state` 服务在方案文档长期架构中标注，Phase 2 初期由 Supervisor 通过 `extracted_facts` 传递槽位信息，状态跨轮由会话层管理。
```

### 3.1 组件职责分工

| 组件 | 职责 | 拥有 LLM 循环 | 调用工具 |
| --- | --- | --- | --- |
| `CustomerServiceSupervisor` | 意图路由、结果汇总、全局对话控制 | 是（主循环） | 不直接调用业务工具 |
| `TroubleshootingAgent` | 故障槽位收集、排障方案生成、升级建议 | 是（子循环） | search_faq |
| `AfterSalesAgent` | 订单查询、政策检索、资格判断、待确认动作生成 | 是（子循环） | search_policy, get_order, check_eligibility, create_pending_action |
| `ConsultationHandler` | 产品和政策知识回答 | 否 | search_faq, search_policy |
| `HandoffWorkflow` | 转人工原因判断与摘要组织 | 否 | 无 |

## 4. SubAgent 协议

### 4.1 SubAgent 输入协议

Supervisor 向子 Agent 传递结构化输入：

```json
{
  "conversation_id": "conv-uuid",
  "current_user": {
    "user_id": "customer_alice",
    "display_name": "Alice"
  },
  "user_message": "原始用户消息",
  "context_messages": ["历史对话消息"],
  "extracted_facts": {
    "product_model": "X1",
    "symptom": "无法联网"
  }
}
```

### 4.2 SubAgent 输出协议

子 Agent 返回结构化结果，不直接向用户输出未经 Supervisor 审查的自由文本：

```json
{
  "status": "completed | awaiting_info | handoff",
  "facts": {
    "product_model": "X1",
    "symptom": "无法联网",
    "order_id": "ORD-A-X1"
  },
  "decision": {
    "code": "eligible_for_warranty_repair",
    "reason": "购买 30 天内，非人为故障",
    "policy_source": "Doc5-售后与保修政策"
  },
  "recommended_response": "您的 X1 智能门锁符合免费保修维修条件...",
  "pending_action": {
    "type": "create_service_ticket",
    "action_id": "act-uuid",
    "display_summary": "为订单 ORD-A-X1 创建保修维修工单",
    "expires_at": "2026-05-27T18:00:00+08:00"
  },
  "citations": [
    {
      "source_id": "Doc5-售后与保修政策",
      "title": "售后与保修政策",
      "section": "保修维修",
      "excerpt": "..."
    }
  ],
  "metadata": {
    "agent": "AfterSalesAgent",
    "workflow": "after_sales",
    "steps_taken": 3
  }
}
```

### 4.3 状态码定义

| 状态 | 含义 | Supervisor 行为 |
| --- | --- | --- |
| `completed` | 子 Agent 已完成处理 | 将 `recommended_response` 返回用户 |
| `awaiting_info` | 需要用户补充信息 | 将 `recommended_response` 作为 `ask_user` 返回 |
| `handoff` | 需要转人工 | 触发转人工流程 |

## 5. CustomerServiceSupervisor 设计

### 5.1 意图路由

Supervisor 接收用户消息后，先通过 LLM 判断意图，再路由到对应处理器：

| 意图 | 路由目标 | 判断依据 |
| --- | --- | --- |
| `consultation` | ConsultationHandler | 产品功能、使用方法、政策咨询 |
| `diagnosis` | TroubleshootingAgent | 故障描述、设备异常 |
| `after_sales` | AfterSalesAgent | 退换、维修、售后申请 |
| `handoff` | HandoffWorkflow | 用户主动要求人工、投诉 |
| `unknown` | AskUser | 信息不足无法判断 |

### 5.2 Supervisor ReAct 循环

```text
Step 1: LLM 判断意图
  → consultation: 直接调用 ConsultationHandler，返回结果
  → diagnosis: 构建 SubAgent 输入，调用 TroubleshootingAgent
  → after_sales: 构建 SubAgent 输入，调用 AfterSalesAgent
  → handoff: 调用 HandoffWorkflow

Step 2: 接收子 Agent SubAgentResponse

Step 3: 汇总为 AgentResponse
  → 将 SubAgentResponse.status 映射为 response_type
  → 将 SubAgentResponse.recommended_response 作为 content
  → 将 SubAgentResponse.citations 和 pending_action 透传
  → 写入审计记录

Step 4: 返回用户
```

### 5.3 Supervisor Prompt 设计要点

- 声明可用处理器和各自职责
- 不暴露子 Agent 内部推理
- 明确意图判断规则
- 保留 `AskUser` 和 `Handoff` 终端动作

## 6. TroubleshootingAgent 设计

### 6.1 职责边界

| 做 | 不做 |
| --- | --- |
| 收集故障槽位（型号、现象、状态、已尝试步骤） | 判定退换资格 |
| 调用知识检索获取排障方案 | 创建工单 |
| 返回结构化排障建议 | 直接向用户输出最终回答 |
| 引导售后或转人工 | 执行写操作 |

### 6.2 工具白名单

| 工具 | 用途 |
| --- | --- |
| `search_faq` | 检索排障知识 |

### 6.3 ReAct 循环

```text
输入: SubAgentInput (含 extracted_facts)

Step 1: 检查槽位完整性
  → 缺少型号或现象: status=awaiting_info, 请求补充

Step 2: 构建检索查询
  → "{product_model} {symptom}"

Step 3: 调用 search_faq

Step 4: 检查检索结果
  → 无结果: status=handoff
  → 有结果: 构建排障步骤

Step 5: 返回 SubAgentResponse
  → status=completed
  → recommended_response=排障步骤文本
  → citations=检索来源
```

### 6.4 System Prompt 要点

- 角色定义：故障排查专家
- 工具描述：仅 `search_faq`
- 输出约束：使用 `Finish[action]` 或 `AskUser[action]` 格式
- 槽位规则：型号和现象为必填
- 降级规则：无知识时转人工

## 7. AfterSalesAgent 设计

### 7.1 职责边界

| 做 | 不做 |
| --- | --- |
| 查询授权订单 | 修改订单 |
| 检索售后政策 | 直接向用户输出最终回答 |
| 调用资格规则服务 | 覆盖规则结论 |
| 创建待确认动作 | 未经确认创建工单 |

### 7.2 工具白名单

| 工具 | 用途 |
| --- | --- |
| `search_policy` | 检索售后政策 |
| `get_order` | 查询授权订单 |
| `list_orders` | 列出当前用户订单 |
| `check_eligibility` | 调用资格规则服务 |
| `create_pending_action` | 创建待确认动作 |

注意：`confirm_ticket`（确认建单）不由 AfterSalesAgent 调用，由 Supervisor 或 API 层直接处理，确保用户确认在 Agent 循环之外。

### 7.3 ReAct 循环

```text
输入: SubAgentInput (含 extracted_facts)

Step 1: 检查必要信息
  → 缺少订单号或办理类型: status=awaiting_info

Step 2: 调用 get_order 验证订单归属

Step 3: 调用 search_policy 获取政策依据

Step 4: 调用 check_eligibility 获取资格结论

Step 5: 根据资格结论构建响应
  → eligible: 创建 pending_action, status=completed
  → ineligible: status=completed, 说明原因和替代路径
  → need_info: status=awaiting_info

Step 6: 返回 SubAgentResponse
  → decision 含 code, reason, policy_source
  → pending_action 含 type, action_id, display_summary, expires_at
  → citations 含政策来源
```

### 7.4 System Prompt 要点

- 角色定义：售后办理专家
- 工具描述：order、policy、eligibility、pending_action 工具
- 输出约束：使用 `Finish[action]` 或 `AskUser[action]` 格式
- 规则约束：资格结论由规则服务输出，Agent 不可覆盖
- 确认约束：Agent 只创建待确认动作，不执行确认

## 8. 工具白名单与审计隔离

### 8.1 工具权限矩阵

| 工具 | Supervisor | TroubleshootingAgent | AfterSalesAgent | ConsultationHandler |
| --- | --- | --- | --- | --- |
| `search_faq` | ❌ | ✅ | ❌ | ✅ |
| `search_policy` | ❌ | ❌ | ✅ | ✅ |
| `get_order` | ❌ | ❌ | ✅ | ❌ |
| `list_orders` | ❌ | ❌ | ✅ | ❌ |
| `check_eligibility` | ❌ | ❌ | ✅ | ❌ |
| `create_pending_action` | ❌ | ❌ | ✅ | ❌ |
| `confirm_ticket` | ✅ (API 层) | ❌ | ❌ | ❌ |

### 8.2 审计记录增强

每次子 Agent 调用需记录：
- `agent_runs` 表：新增 `sub_agent` 字段标识子 Agent 名称
- `tool_calls` 表：记录调用方 Agent 标识
- 每次请求记录完整调用链：Supervisor → 子 Agent → 工具调用

## 9. 评测对照框架

### 9.1 对照目标

拆分前后必须保证：
- 业务正确性不下降（14 个评测场景全部通过）
- 核心流程行为一致（响应类型、引用来源、待确认动作）
- 成本可接受（LLM 调用次数在合理范围）

### 9.2 对照评测方法

```text
Phase 1 基线: 单 Agent 对 14 个评测场景的响应
Phase 2 对照: Supervisor + 子 Agent 对相同场景的响应

对比维度:
  1. response_type 一致性
  2. citations 来源一致性
  3. pending_action 有无一致性
  4. content 关键词覆盖一致性
  5. LLM 调用次数对比
  6. 端到端延迟对比
```

### 9.3 评测数据集复用

复用 `data/evaluation_cases.json` 的 14 个场景，新增对照评测运行类型：

```json
{
  "eval_run_id": "run-uuid",
  "case_id": "EC-001",
  "architecture": "multi_agent",
  "result": "pass",
  "metrics": {
    "response_type_match": true,
    "citation_match": true,
    "llm_calls": 2,
    "latency_ms": 3500
  }
}
```

## 10. 实施计划概要

| 阶段 | 任务 | 验收 |
| --- | --- | --- |
| 1. SubAgent 协议 | 定义 `SubAgentInput`、`SubAgentResponse` 数据结构 | 数据结构可独立序列化和测试 |
| 2. TroubleshootingAgent | 创建独立 ReAct 循环类，注入 search_faq 工具 | 12 项诊断场景测试通过 |
| 3. AfterSalesAgent | 创建独立 ReAct 循环类，注入 order/policy/eligibility 工具 | 7 项售后场景测试通过 |
| 4. Supervisor 调度 | 重构 `CustomerServiceAgent` 为 Supervisor，路由到子 Agent | 139 项回归测试通过 |
| 5. 工具白名单 | 实现工具注册表和权限检查 | 越权调用被阻止 |
| 6. 对照评测 | 运行 14 个评测场景对比拆分前后 | 行为一致性达标 |
| 7. Phase 2 验收 | M3 验收 | Supervisor + 两子 Agent 通过回归评测 |

## 11. 风险与控制

| 风险 | 影响 | 控制策略 |
| --- | --- | --- |
| 多次 LLM 调用增加延迟 | 用户体验下降 | 限制子 Agent max_steps=3；ConsultationHandler 不走子循环 |
| 子 Agent 输出不稳定 | 行为不一致 | 结构化输出协议 + 评测对照 |
| 工具白名单遗漏 | 功能缺失 | 先建立权限矩阵再实现工具注册 |
| 拆分引入回归 | 现有功能损坏 | 先建立 Phase 1 基线再拆分 |
