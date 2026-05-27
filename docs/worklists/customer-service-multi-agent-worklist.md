# QA-agent 多智能体客服演进 Worklist

| 项目 | 内容 |
| --- | --- |
| 台账状态 | 已初始化 |
| 创建日期 | 2026-05-26 |
| 项目展示名称 | `QA-agent` |
| 对应方案 | `docs/solution/customer-service-multi-agent-solution.md` |
| 第一阶段目标 | 内部试用级客服 MVP |
| 长期目标 | 企业级多智能体客服平台 |
| 当前执行阶段 | Phase 2 完成，M3 已关闭，待 Phase 3 启动确认 |

## 1. 使用规则

本文件用于记录总体方案落地过程中的全部任务状态、验收结果、依赖、阻塞与关键决策。实际开发任务开始、完成或阻塞时，必须同步更新本台账。

### 1.1 状态定义

| 状态 | 含义 |
| --- | --- |
| `PENDING` | 已识别，尚未开始 |
| `IN_PROGRESS` | 已进入实施 |
| `BLOCKED` | 因依赖、环境或待决策事项暂无法继续 |
| `REVIEW` | 实现已完成，等待验证或用户验收 |
| `✅ DONE` | 已验证完成 |
| `DEFERRED` | 明确推迟至后续阶段 |

### 1.2 优先级定义

| 优先级 | 含义 |
| --- | --- |
| `P0` | 阻塞后续建设或涉及安全/正确性，必须优先处理 |
| `P1` | 一期闭环所需，应在对应阶段完成 |
| `P2` | 优化和企业化能力，可在基础闭环后推进 |

### 1.3 更新要求

- 每项任务开始实施前，将状态从 `PENDING` 更新为 `IN_PROGRESS`。
- 实现完成但尚未验证时，状态更新为 `REVIEW`。
- 只有在验收标准得到证据支撑后，状态才能更新为 `✅ DONE`。
- 任务发生范围调整、依赖变化或技术决策变化时，在“决策与阻塞记录”补充说明。
- 每个实施批次结束后，在“进度更新日志”中记录日期、任务、验证结果和下一步。

## 2. 里程碑概览

| 里程碑 | 目标 | 状态 | 完成判定 |
| --- | --- | --- | --- |
| `M0` 方案与任务基线 | 明确总体方案和 worklist | `✅ DONE` | 两份文档完成并自检通过 |
| `M1` Phase 0 工程基线 | 现有原型稳定、能力声明真实 | `✅ DONE` | 配置/测试/AskUser/引用/健康检查基线通过 |
| `M2` Phase 1 内部试用 MVP | 模拟售后闭环可用 | `✅ DONE` | 咨询、排障、办理、确认、转人工、审计验收通过 |
| `M3` Phase 2 多智能体 | 领域子 Agent 协同运行 | `✅ DONE` | Supervisor 与两个子 Agent 通过回归评测 |
| `M4` Phase 3 企业化 | 真实系统接入与治理 | `DEFERRED` | 企业发布门禁另行批准 |

## 3. 文档与规划任务

| ID | 优先级 | 任务 | 依赖 | 状态 | 验收标准 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `DOC-001` | `P0` | 评审当前仓库能力、缺口与运行现状 | 无 | `✅ DONE` | 已基于源码、文档和非破坏性验证形成结论 | 完成于 2026-05-26 |
| `DOC-002` | `P0` | 确定第一期业务边界与总体架构原则 | `DOC-001` | `✅ DONE` | 用户确认一期选择模拟订单/售后闭环及多 Agent 原则 | 完成于 2026-05-26 |
| `DOC-003` | `P0` | 编写总体方案文档 | `DOC-002` | `✅ DONE` | 方案覆盖架构、业务、数据、API、安全、评测和路线 | 路径见文档头部 |
| `DOC-004` | `P0` | 初始化持续维护的 worklist | `DOC-002` | `✅ DONE` | 台账包含任务、状态、依赖、验收和更新机制 | 当前文件 |
| `DOC-005` | `P0` | 用户审阅已落盘方案与 worklist | `DOC-003`, `DOC-004` | `✅ DONE` | 用户确认文档无需修改或提出修订意见并处理完成 | 2026-05-26 用户指示开始实施 |
| `DOC-006` | `P0` | 编写 Phase 0 详细实施计划 | `DOC-005` | `✅ DONE` | 计划拆解到文件、测试和验证命令，并经用户确认 | `docs/superpowers/plans/2026-05-26-phase-0-engineering-baseline.md` |
| `DOC-007` | `P0` | 统一项目展示名称为 `QA-agent` | `DOC-006` | `✅ DONE` | README、方案和台账使用确认后的展示名称 | 技术路径/标识保留运行所需形式 |
| `DOC-008` | `P0` | 编写 Phase 1 首批身份与订单读取设计规格 | `M1` | `✅ DONE` | 范围、授权边界、数据/API 和测试契约明确 | 2026-05-26 用户确认规格 |
| `DOC-009` | `P0` | 编写 Phase 1 首批详细实施计划 | `DOC-008` | `✅ DONE` | 计划拆解到文件、测试、验证和提交批次 | `docs/superpowers/plans/2026-05-26-phase-1-identity-order-read.md` |
| `DOC-010` | `P0` | 编写 Phase 1 售后政策、资格规则与授权工具设计规格 | `P1-001` 至 `P1-003` | `✅ DONE` | 政策、授权工具、确定性规则和测试边界明确并经落盘复核 | 2026-05-27 用户确认规格 |
| `DOC-011` | `P0` | 编写 Phase 1 售后政策、资格规则与授权工具实施计划 | `DOC-010` | `✅ DONE` | 计划拆解到文件、测试、验证与台账收口步骤 | `docs/superpowers/plans/2026-05-27-phase-1-policy-eligibility-tools.md` |
| `DOC-012` | `P0` | 编写 Phase 1 待确认动作与模拟工单写入设计规格 | `P1-006` 至 `P1-008` | `✅ DONE` | 会话绑定、确认重算、事务幂等和接口边界明确并经落盘复核 | 2026-05-27 用户授权按方案自主实施 |
| `DOC-013` | `P0` | 编写 Phase 1 待确认动作与模拟工单写入实施计划 | `DOC-012` | `✅ DONE` | 计划拆解到 schema、服务、API、测试和本地幂等验证 | `docs/superpowers/plans/2026-05-27-phase-1-confirmed-ticket-write.md` |
| `DOC-014` | `P0` | 编写 Phase 1 售后 Workflow 与对话接入设计规格 | `P1-004`, `P1-009` | `✅ DONE` | 单 Agent 流程边界、政策依据门禁、对话协议和确认复用路径明确 | `docs/superpowers/specs/2026-05-27-phase-1-after-sales-workflow-design.md` |
| `DOC-015` | `P0` | 编写 Phase 1 售后 Workflow 与对话接入实施计划 | `DOC-014` | `✅ DONE` | 计划拆解到 workflow、Agent 协议、API、测试和数据库验证 | `docs/superpowers/plans/2026-05-27-phase-1-after-sales-workflow.md` |

## 4. Phase 0：工程基线与能力补齐

### 4.1 复现、配置与存储决策

| ID | 优先级 | 任务 | 依赖 | 状态 | 验收标准 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `P0-001` | `P0` | 补齐 `.gitignore`，隔离 `.env`、`.venv`、缓存和本地生成数据 | `DOC-006` | `✅ DONE` | Git 状态不再暴露敏感/生成文件，必要源文件仍可追踪 | 不移除用户本地数据 |
| `P0-002` | `P0` | 将必要的 FAQ 导入脚本纳入可复现基线并核对解析行为 | `DOC-006` | `✅ DONE` | 新环境能从 FAQ 原文重建索引且导入条数可验证 | 导入脚本已纳入版本并保存文档来源；实际重建需显式调用嵌入服务 |
| `P0-003` | `P0` | 统一 `.env.example` 与代码读取的配置名称 | `DOC-006` | `✅ DONE` | Embedding、LLM、数据库配置名称一致并有测试/启动验证 | 已统一为 `EMBEDDING_MODEL` |
| `P0-004` | `P1` | 统一 Docker 端口配置与运行文档 | `DOC-006` | `✅ DONE` | README、部署文档与 compose 示例一致，端口冲突方案明确 | 使用宿主机端口 `5433` |
| `P0-005` | `P1` | 决策一期向量存储路径：暂留 Chroma 或迁移 pgvector | `DOC-006` | `✅ DONE` | 形成有验收条件的明确决策并同步方案/任务 | Phase 0/1 保留 Chroma |
| `P0-006` | `P1` | 引入显式数据库迁移方案，替代静默自动建表路径 | `P0-005` | `✅ DONE` | 数据结构变更可版本化执行、失败可见、可验证 | `scripts/init_db.py` 显式执行幂等 schema bootstrap |

### 4.2 Agent 协议与可信回答

| ID | 优先级 | 任务 | 依赖 | 状态 | 验收标准 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `P0-007` | `P0` | 重构 LLM/system prompt 调用边界和 Agent 结构化响应协议 | `DOC-006` | `✅ DONE` | 系统规则通过正确角色传递；响应可表达所需状态 | 覆盖 `final_answer`、`ask_user`、`handoff` |
| `P0-008` | `P0` | 实现 `AskUser` 主动澄清能力 | `P0-007` | `✅ DONE` | 型号/关键信息不足时返回 `ask_user` 并持久化可见消息 | README 已同步当前能力 |
| `P0-009` | `P0` | 将 FAQ 检索结果升级为结构化来源并返回引用 | `P0-007` | `✅ DONE` | 标准知识回答带文档/章节引用；客户端响应含 `citations` | `ToolResult`、Agent 与 `/chat` 响应已透传结构化来源 |
| `P0-010` | `P1` | 增加无依据回答的拒答/澄清/转人工降级规则 | `P0-008`, `P0-009` | `✅ DONE` | 无有效来源案例不会生成未经证实的答案 | 空引用检索后的回答改为人工转接 |
| `P0-011` | `P1` | 规范会话状态字段以支持等待澄清和转人工扩展 | `P0-008` | `✅ DONE` | 对话状态可持久化或稳定重建，避免重复询问 | 以消息元数据承载 Phase 0 最小状态 |

### 4.3 测试、运行与健康状态

| ID | 优先级 | 任务 | 依赖 | 状态 | 验收标准 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `P0-012` | `P0` | 建立不调用真实模型的 Agent 控制流单元测试 | `P0-007`, `P0-008` | `✅ DONE` | 覆盖检索回答、反问、解析失败、兜底行为 | 当前覆盖 system prompt、反问、人工转接；降级分支随 `P0-010` 补齐 |
| `P0-013` | `P0` | 建立引用和无依据降级测试 | `P0-009`, `P0-010` | `✅ DONE` | 引用正确返回，低依据请求进入规定状态 | 覆盖引用透传、空检索转人工和澄清状态 |
| `P0-014` | `P1` | 区分离线测试、数据库集成测试和外部 API 冒烟测试 | `P0-012` | `✅ DONE` | 默认测试不会消耗外部 API，冒烟测试显式执行 | `RUN_EXTERNAL_SMOKE=true` 才运行外部/持久化 smoke 路径 |
| `P0-015` | `P1` | 完善健康检查和启动失败可见性 | `P0-003`, `P0-006` | `✅ DONE` | 数据库/向量依赖异常能反映为非健康或启动错误 | `/health` 返回数据库和本地知识库检查状态 |
| `P0-016` | `P1` | Phase 0 回归验证和文档更新 | `P0-001` 至 `P0-015` | `✅ DONE` | 新环境启动验证、测试通过、README 与能力一致 | `M1` 已依据离线回归、bootstrap 和健康检查证据关闭 |

## 5. Phase 1：内部试用客服 MVP

### 5.1 身份、数据与业务基础

| ID | 优先级 | 任务 | 依赖 | 状态 | 验收标准 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `P1-001` | `P0` | 设计并实现内部试用用户认证上下文 | `M1` | `✅ DONE` | API 能识别当前用户，测试账号可用 | 使用 `X-QA-User-Id` 的内部试用身份，不等同生产认证 |
| `P1-002` | `P0` | 实现会话归属和授权校验 | `P1-001` | `✅ DONE` | 用户无法查看其他用户会话 | 创建、列表、读取与聊天续接均绑定当前内部身份 |
| `P1-003` | `P0` | 增加产品、模拟客户与模拟订单数据模型/种子数据 | `M1` | `✅ DONE` | 可查询 X1/X2/C1/G2 对应订单案例 | 幂等种子数据覆盖两个用户和四类产品，不使用真实个人数据 |
| `P1-004` | `P0` | 增加模拟售后工单与待确认动作数据模型 | `P1-003` | `✅ DONE` | 支持工单状态及确认动作幂等存储 | `pending_actions` 与 `service_tickets` 已持久化，确认事务使用行锁防止重复建单 |
| `P1-005` | `P1` | 增加 Agent run、tool call 和风险事件审计模型 | `M1` | `✅ DONE` | 核心调用链可按会话检索复盘 | `agent_runs`/`tool_calls`/`risk_events`/`handoff_records` 四表已持久化；`AuditRepository` 提供插入和按会话查询方法；8 项模型测试通过 |

### 5.2 工具与规则服务

| ID | 优先级 | 任务 | 依赖 | 状态 | 验收标准 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `P1-006` | `P0` | 实现授权的模拟订单查询工具 | `P1-001`, `P1-003` | `✅ DONE` | 仅返回当前用户订单；越权被拦截 | `MockOrderTool` 绑定当前用户，参数不能选择其他用户 |
| `P1-007` | `P0` | 区分产品知识与售后政策检索能力 | `M1` | `✅ DONE` | 可针对产品/政策返回结构化来源 | 政策工具按 `Doc5-售后与保修政策` 来源检索并二次过滤 |
| `P1-008` | `P0` | 实现售后资格规则服务 | `P1-003`, `P1-007` | `✅ DONE` | 退换、保修、人为损坏、过保结论测试 100% 正确 | `0-7`/`8-365`/`>365` 边界、损坏与澄清路径已覆盖 |
| `P1-009` | `P0` | 实现待确认动作与模拟工单创建工具 | `P1-004`, `P1-008` | `✅ DONE` | 未确认不建单；确认后仅建一单；失败可追踪 | 待确认服务与受保护 API 已完成；未接入聊天 Agent 自动写操作 |
| `P1-010` | `P1` | 实现工单查询工具 | `P1-004`, `P1-009` | `✅ DONE` | 当前用户可查询自身工单状态 | `GET /api/tickets/{id}` + `TicketQueryService`；用户归属校验拦截越权访问；3 项 API 测试通过 |
| `P1-011` | `P1` | 实现人工转接记录与摘要服务 | `P1-005` | `✅ DONE` | 可保存转接原因及结构化摘要 | `HandoffSummary` 从对话上下文提取事实/步骤/型号；摘要已集成到 Agent `Handoff` 响应 metadata；`handoff_records` 表支持持久化；7 项摘要测试通过 |

### 5.3 Supervisor 与用户流程

| ID | 优先级 | 任务 | 依赖 | 状态 | 验收标准 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `P1-012` | `P0` | 建立 Supervisor 意图路由与 Workflow 接口 | `M1`, `P1-007` | `✅ DONE` | 能区分咨询、排障、售后、转人工 | 单 Agent 以 `Finish`/`AskUser`/`PrepareAfterSales`/`Handoff` 提供流程动作接口；领域子 Agent 留待 Phase 2 |
| `P1-013` | `P0` | 实现产品咨询闭环 | `P1-007`, `P1-012` | `✅ DONE` | 产品/政策问题回答带引用且满足评测 | 咨询场景集成测试覆盖：带型号回答、型号澄清、政策引用、无知识转人工；Agent regex 修复支持嵌套 JSON 参数 |
| `P1-014` | `P0` | 实现故障排查槽位收集与流程 | `P1-012` | `✅ DONE` | 型号缺失会澄清；充分后返回排障步骤 | `DiagnosisWorkflow` 结构化槽位验证；`PrepareDiagnosis` 动作接入 Agent；12 项 workflow 测试 + 5 项 Agent 集成测试 |
| `P1-015` | `P0` | 实现模拟售后办理流程 | `P1-006`, `P1-008`, `P1-009`, `P1-012` | `✅ DONE` | 查询订单、判资格、确认、建单全链路通过 | `/api/chat` 可生成政策支持的待确认动作；确认事务幂等建单已验证 |
| `P1-016` | `P1` | 实现转人工触发策略和用户响应 | `P1-011`, `P1-012` | `✅ DONE` | 明确请求/低依据/故障时返回 `handoff` | `HandoffSummary` 从对话上下文提取事实/步骤/型号；摘要已集成到 Agent `Handoff` 响应 metadata |
| `P1-017` | `P1` | 扩展 API 协议与用户侧接口 | `P1-013` 至 `P1-016` | `✅ DONE` | Chat/确认/转人工/订单/工单接口可用 | `GET /api/tickets/{id}` 新增，用户归属校验；`handoff_summary` 含在 chat 响应 metadata 中 |

### 5.4 审计、管理与质量验收

| ID | 优先级 | 任务 | 依赖 | 状态 | 验收标准 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `P1-018` | `P1` | 实现管理侧会话、工具调用和工单读取接口 | `P1-005`, `P1-017` | `✅ DONE` | 授权人员可复盘核心流程 | `GET /api/admin/conversations`、`GET /api/admin/conversations/{id}`、`GET /api/admin/tickets`、`GET /api/admin/evaluations`；`require_admin` 基于 `role` 字段的 RBAC；`mock_customers` 表新增 `role` 列；`admin_zhang` 种子管理员账号；6 项 admin API 测试通过 |
| `P1-019` | `P0` | 建立一期离线评测数据集 | `P1-013` 至 `P1-016` | `✅ DONE` | 覆盖方案文档列出的首批场景 | `data/evaluation_cases.json` 覆盖 §13.2 全部 14 个场景；`evaluation_cases`/`evaluation_runs` 表已持久化；`EvaluationCase` 加载与 `evaluate_response` 判定逻辑 9 项测试通过 |
| `P1-020` | `P0` | 建立权限、规则、确认写操作自动化测试 | `P1-002`, `P1-008`, `P1-009` | `✅ DONE` | 关键安全与规则指标 100% 通过 | `test_security_gate.py` 覆盖工单查询越权、workflow 缺失降级、提示注入防护；合计 39 项安全/规则/权限测试通过 |
| `P1-021` | `P1` | 实现运行指标/评测结果记录与查询 | `P1-005`, `P1-019` | `✅ DONE` | 可查看评测结果与核心调用失败 | `GET /api/admin/evaluations` 支持按 case 过滤并返回 pass/fail 统计；`EvaluationRepository` 持久化评测结果；3 项评测 API 测试通过 |
| `P1-022` | `P0` | 执行内部试用 MVP 验收 | `P1-001` 至 `P1-021` | `✅ DONE` | 达到方案中 Phase 1 指标并形成验收记录 | M2 验收通过，验收证据见进度日志 2026-05-27 条目 |

## 6. Phase 2：领域多智能体协作

| ID | 优先级 | 任务 | 依赖 | 状态 | 验收标准 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `P2-001` | `P1` | 定义 Supervisor 与领域子 Agent 的结构化输入输出协议 | `M2` | `✅ DONE` | 契约覆盖事实、决策、动作、引用和错误 | `SubAgentInput`/`SubAgentResponse` 数据类；3 项协议测试通过 |
| `P2-002` | `P1` | 将故障排查流程拆分为 `TroubleshootingAgent` | `P2-001` | `✅ DONE` | 可独立运行、测试并被 Supervisor 调用 | `BaseReActAgent` 共享循环 + 专用 system prompt；4 项 Agent 测试通过 |
| `P2-003` | `P1` | 将售后办理流程拆分为 `AfterSalesAgent` | `P2-001` | `✅ DONE` | 可独立完成资格/待确认建议并被调度 | 确定性管道（get_order→policy→eligibility→create_action）；6 项 Agent 测试通过 |
| `P2-004` | `P1` | 建立子 Agent 工具白名单与调用审计 | `P2-002`, `P2-003` | `✅ DONE` | 越权调用被阻止且可追溯 | `ToolRegistry` 提供按 Agent 名查询工具；4 项测试通过 |
| `P2-005` | `P1` | 实现 Supervisor 调度与统一答复汇总 | `P2-002`, `P2-003` | `✅ DONE` | 多 Agent 输出可统一反馈用户 | LLM 意图路由（RouteConsultation/RouteTroubleshooting/RouteAfterSales/AskUser/Handoff）；4 项 Supervisor 测试通过 |
| `P2-006` | `P1` | 建立拆分前后行为、延迟与成本对照评测 | `P2-005` | `✅ DONE` | 业务正确性不下降，成本可接受 | 5 项对照评测覆盖：产品咨询、无知识转人工、提示攻击、诊断、信息不足 |
| `P2-007` | `P1` | 完成多智能体阶段验收 | `P2-001` 至 `P2-006` | `✅ DONE` | Supervisor + 两子 Agent 达到评测门禁 | 全量 165/165 passed；init_db/seed/verify_migration 全部 SUCCESS |

## 7. Phase 3：企业级能力规划

Phase 3 任务当前作为长期路线登记，详细范围需要在真实业务系统和合规要求明确后另行拆分审批。

| ID | 优先级 | 任务 | 依赖 | 状态 | 验收标准 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| `P3-001` | `P2` | 接入真实用户、订单、物流及售后系统 API | `M3` | `DEFERRED` | 按企业集成方案验收 | 需外部系统契约 |
| `P3-002` | `P2` | 建立 OAuth/JWT、RBAC 与多租户数据隔离 | `M3` | `DEFERRED` | 安全与权限审计通过 | 生产前必需 |
| `P3-003` | `P2` | 建立知识审核、版本、灰度与回滚体系 | `M3` | `DEFERRED` | 知识发布受控可追踪 | 运营能力 |
| `P3-004` | `P2` | 建立 Prompt/模型/工具版本与预算治理 | `M3` | `DEFERRED` | 变更、成本和权限均可治理 | Agent 治理 |
| `P3-005` | `P2` | 建设客服工作台与人工接管闭环 | `M3` | `DEFERRED` | 客服可处理转接和质检 | 产品化能力 |
| `P3-006` | `P2` | 接入全链路追踪、指标、告警和灾备机制 | `M3` | `DEFERRED` | 稳定性门禁通过 | 运维能力 |
| `P3-007` | `P2` | 建立企业发布评测、灰度和合规门禁 | `P3-001` 至 `P3-006` | `DEFERRED` | 获得真实客户发布批准 | `M4` 验收任务 |

## 8. 决策与阻塞记录

| 日期 | 编号 | 类型 | 内容 | 影响任务 | 状态 |
| --- | --- | --- | --- | --- | --- |
| 2026-05-26 | `DEC-001` | 决策 | 一期选择“产品咨询 + 故障排查 + 模拟订单/售后办理 + 转人工” | `Phase 1` 全部任务 | 已确认 |
| 2026-05-26 | `DEC-002` | 决策 | 采用 Supervisor 总控；RAG、数据库查询、规则和写操作作为 Tool/Service | `P1-012`, `Phase 2` | 已确认 |
| 2026-05-26 | `DEC-003` | 决策 | 首批业务子 Agent 为 `TroubleshootingAgent` 与 `AfterSalesAgent`，在 Phase 2 拆分 | `Phase 2` | 已确认 |
| 2026-05-26 | `DEC-004` | 决策 | 建立总体方案与 worklist 双文档，并在后续实施中持续更新台账 | 所有任务 | 已确认 |
| 2026-05-26 | `OBS-001` | 现状 | 代码未实现文档宣称的 `AskUser` 主动反问 | `P0-008` | 已由 `P0-008` 关闭 |
| 2026-05-26 | `OBS-002` | 现状 | 配置、Docker 端口及导入脚本追踪存在复现差异 | `P0-001` 至 `P0-004` | 待实施 |
| 2026-05-26 | `OPEN-001` | 待决策 | 一期是否在业务开发前迁移向量存储至 `pgvector` | `P0-005`, `P0-006` | 已由 `DEC-005` 关闭 |
| 2026-05-26 | `DEC-005` | 决策 | Phase 0 与 Phase 1 继续使用 Chroma；`pgvector` 迁移在 MVP 流程稳定后单独评估 | `P0-005`, `Phase 1` | 已确认 |
| 2026-05-27 | `DEC-006` | 决策 | 下一切片限定为政策检索、授权订单工具和确定性资格规则；暂不实施工单写操作或流程编排 | `P1-006` 至 `P1-009`, `P1-012` | 已确认 |
| 2026-05-27 | `DEC-007` | 决策 | 资格日期边界采用自然日 `0-7` 天退换、`8-365` 天免费保修、`>365` 天仅表示可进入付费维修路径 | `P1-008` | 已确认 |
| 2026-05-27 | `DEC-008` | 决策 | 待确认动作与工单确认执行必须绑定当前用户和当前会话，并在确认时重新校验资格 | `P1-004`, `P1-009` | 已确认 |
| 2026-05-27 | `DEC-009` | 决策 | 本切片采用持久化动作与事务化模拟工单创建；暂不接入聊天 Workflow、工单查询或审计表 | `P1-004`, `P1-009`, `P1-012` | 已确认 |
| 2026-05-27 | `DEC-010` | 决策 | 规则给出的替代办理建议不得自动转换为另一类型的待确认写动作；办理类型变更需用户重新明确请求 | `P1-009` | 已确认 |
| 2026-05-27 | `DEC-011` | 决策 | Phase 1 先在现有单 Agent 中以 `PrepareAfterSales` 接入售后 Workflow；模型只提供显式事实，政策依据、资格与工单确认继续由确定性服务控制 | `P1-012`, `P1-015`, `P1-017` | 已实施并验证 |
| 2026-05-27 | `DEC-012` | 决策 | Phase 2 采用方案 B（领域 Agent 独立 ReAct 循环）：`TroubleshootingAgent` 和 `AfterSalesAgent` 各拥有独立 LLM 循环和工具白名单，Supervisor 仅负责路由和汇总；ConsultationHandler 和 HandoffWorkflow 保留为无循环 Workflow | `P2-001` 至 `P2-007` | 用户已确认 |

## 9. 进度更新日志

| 日期 | 完成任务 | 验证结果 | 新增问题/决策 | 下一步 |
| --- | --- | --- | --- | --- |
| 2026-05-26 | `DOC-001`, `DOC-002` | 完成源码/文档/运行现状核查；用户确认第一期边界和架构原则 | 确认 Tool/Service 与领域子 Agent 的边界 | 编写并落盘总体方案及任务台账 |
| 2026-05-26 | `DOC-003`, `DOC-004` | 两份文档已创建，待用户审阅 | `OPEN-001` 留待 Phase 0 计划阶段决策 | 用户审阅文档，随后编写 Phase 0 实施计划 |
| 2026-05-26 | `DOC-005` | 用户已指示开始实施，视为总体方案与 worklist 审阅通过 | 实施范围先限定为 Phase 0，避免提前铺开业务能力 | 编写 Phase 0 详细实施计划 |
| 2026-05-26 | `DOC-006` | Phase 0 实施计划已编写并完成占位项、范围与契约一致性检查 | 确定 Phase 0/1 继续使用 Chroma，pgvector 暂不混入业务闭环建设 | 选择计划执行方式并启动 `P0-001` |
| 2026-05-26 | `P0-001`, `P0-003`, `P0-004`, `P0-005` | `git check-ignore` 验证本地生成路径已忽略；配置与端口文本检查通过；`git diff --check` 通过 | 采用当前宿主机 PostgreSQL 端口 `5433`；Phase 0/1 保留 Chroma | 执行 Agent 动作协议与主动澄清任务 |
| 2026-05-26 | `P0-007`, `P0-008`, `P0-012` | 先验证旧行为存在 3 个预期失败；随后 `pytest tests/test_agent_actions.py -q` 通过（3 passed），兼容 prompt 构造检查通过 | 增加 `Handoff` 响应协议，规则通过 system prompt 传递 | 实现 FAQ 引用结构与 API 返回 |
| 2026-05-26 | `P0-009`（`P0-013` 引用部分） | `pytest tests/test_agent_actions.py tests/test_agent_citations.py -q` 通过（5 passed）；未调用外部嵌入服务 | FAQ Tool 返回结构化来源，普通字符串接口保持兼容；无依据降级仍待实施 | 实施无依据回答降级和对话状态元数据 |
| 2026-05-26 | `P0-010`, `P0-011`, `P0-013` | `pytest tests/test_agent_actions.py tests/test_agent_citations.py -q` 通过（7 passed） | 空来源检索后禁止猜测回答；状态暂以消息元数据持久化 | 纳入 FAQ 导入脚本并保留来源元数据 |
| 2026-05-26 | `P0-002` | `pytest tests/test_faq_import.py tests/test_agent_citations.py -q --basetemp=.pytest_cache\tmp` 通过（6 passed） | FAQ 导入现保存文档来源；实时重建索引会调用嵌入服务，未在离线验证中执行 | 完善数据库初始化与健康检查 |
| 2026-05-26 | `P0-006`, `P0-015` | `pytest tests -q --basetemp=.pytest_cache\tmp` 通过（13 passed）；`python scripts\init_db.py` 成功；真实 `/health` 返回两个依赖均为 `ok` | 启动不再静默建表；schema 初始化改为显式 bootstrap | 区分测试模式并完成 Phase 0 验收 |
| 2026-05-26 | `P0-014`, `P0-016`, `M1` | `pytest -q --basetemp=.pytest_cache\tmp` 通过（13 passed）；`scripts\verify_migration.py` 成功；默认 `scripts\smoke_test.py` 在未开启门禁时跳过外部/持久化路径；`git diff --check` 通过 | 外部冒烟改为 `RUN_EXTERNAL_SMOKE=true` 显式选择；保留一条第三方弃用告警待后续依赖升级处理 | 准备 Phase 1 内部试用 MVP 详细实施计划 |
| 2026-05-26 | `DOC-007`, `DOC-008` | 产品展示名称修正为 `QA-agent`；用户确认 Phase 1 首批设计限定为身份上下文、会话授权和模拟订单只读查询 | Python/运行技术标识可使用 `qa_agent` 或 `qa-agent`；已完成状态使用 `✅ DONE` 展示 | 编写并执行 Phase 1 首批实施计划 |
| 2026-05-26 | `DOC-009` | Phase 1 首批实施计划已拆为模拟数据、身份上下文、会话授权、订单只读 API 与本地验证五个批次 | `P1-006` 本轮只准备服务/API 底座，保持未完成直到 Agent Tool 接入 | 执行 `P1-003` 模拟业务数据基线 |
| 2026-05-26 | `P1-003` | `pytest tests\test_mock_data.py tests\test_health_and_initialization.py -q --basetemp=.pytest_cache\tmp` 通过（7 passed） | 新增 mock customers/products/orders schema 与幂等 seed；真实数据库写入延后到切片验收 | 实现内部试用身份上下文 |
| 2026-05-26 | `P1-001` | `pytest tests\test_mock_data.py tests\test_identity_and_conversations.py tests\test_health_and_initialization.py -q --basetemp=.pytest_cache\tmp` 通过（11 passed） | `X-QA-User-Id` 仅解析已启用内部测试用户；不宣称生产认证能力 | 强制会话归属隔离 |
| 2026-05-26 | `P1-002` | `pytest tests\test_identity_and_conversations.py tests\test_agent_actions.py tests\test_agent_citations.py -q --basetemp=.pytest_cache\tmp` 通过（13 passed） | 会话创建和查询不再接受调用方选择用户；越权读取/续接统一返回 `404` | 建立授权订单只读 API 底座 |
| 2026-05-26 | `P1-006`（底座部分） | `pytest tests\test_mock_data.py tests\test_orders_api.py tests\test_identity_and_conversations.py tests\test_health_and_initialization.py tests\test_agent_actions.py tests\test_agent_citations.py -q --basetemp=.pytest_cache\tmp` 通过（26 passed） | 已提供按当前身份过滤的订单 Service/API；不提前将订单查询注册为 Agent Tool | 执行本地 schema/seed 与完整回归验证 |
| 2026-05-26 | Phase 1 首批切片验收 | `pytest -q --basetemp=.pytest_cache\tmp` 通过（28 passed）；`scripts\verify_migration.py` 通过；`scripts\init_db.py` 与 `scripts\seed_mock_data.py` 成功；本地 API 验证 Alice 仅可读取 `ORD-A-X1`/`ORD-A-C1` 且读取 `ORD-B-X2` 返回 `404` | `P1-001`、`P1-002`、`P1-003` 已关闭；`P1-006` 待受控 `MockOrderTool` 接入 | 设计并实施售后资格规则与订单工具接入 |
| 2026-05-27 | `DOC-010`（规格待复核） | 用户已确认本切片架构、规则契约和错误处理；规格已落盘待复核 | 范围限制为只读政策/订单依据与确定性规则；过保结论修订为 `paid_repair_available` | 复核规格后编写详细实施计划并执行 `P1-006`、`P1-007`、`P1-008` |
| 2026-05-27 | `DOC-010`, `DOC-011` | 用户已复核售后规则与授权工具规格；实施计划已按 TDD 和离线验证步骤拆解 | 来源标识采用现有导入契约 `Doc5-售后与保修政策`；不注册未编排工具到通用 Agent | 执行 `P1-006`、`P1-007`、`P1-008` 并记录验证证据 |
| 2026-05-27 | `P1-006`, `P1-007`, `P1-008`（启动） | 实施前离线基线 `pytest -q --basetemp=.pytest_cache\tmp` 通过（28 passed）；`scripts\verify_migration.py` 通过 | 用户明确要求在当前 `main` 工作区继续实施；新增政策来源过滤的直接验证以落实规格边界 | 按 TDD 添加失败测试并实现只读政策/订单依据与确定性规则 |
| 2026-05-27 | `P1-006`, `P1-007`, `P1-008` | 新功能先取得模块/样本缺失的 RED 证据；随后 `pytest -q --basetemp=.pytest_cache\tmp` 通过（49 passed），`scripts\verify_migration.py` 通过，`git diff --check` 通过；启动既有 Docker Compose PostgreSQL 后 `scripts\init_db.py` 与 `scripts\seed_mock_data.py` 成功 | 初次数据库验证因 Docker Desktop 未运行导致 `localhost:5433` 拒绝连接，恢复既有 compose 依赖后通过；本切片未接入聊天 Agent 或写操作 | 设计 `P1-004`、`P1-009` 待确认动作与模拟工单写入切片 |
| 2026-05-27 | `DOC-012`（规格待复核） | 用户已确认待确认动作、模拟工单、事务幂等与确认 API 设计；规格已落盘待复核 | 动作绑定当前用户与当前会话；确认时重新运行资格规则；不接入聊天 Workflow | 复核规格后编写详细实施计划并执行 `P1-004`、`P1-009` |
| 2026-05-27 | `DOC-012`, `DOC-013` | 用户授权在已掌握总体方案后由实现方自行细化并推进；写入切片实施计划已落盘 | 当前数据库封装每次调用独立提交，确认建单将由专用仓储事务锁定动作并回填工单；替代建议不自动变成写动作 | 按 TDD 执行 `P1-004` 与 `P1-009` |
| 2026-05-27 | `P1-004`, `P1-009` | 新测试先取得模块/路由缺失及单时钟快照边界的 RED 证据；随后 `pytest -q --basetemp=.pytest_cache\ticket_full_final` 通过（63 passed）；`scripts\init_db.py` 与 `scripts\seed_mock_data.py` 成功；真实 PostgreSQL 确认两次仅创建一张工单且第二次返回幂等重放 | 动作及执行均绑定当前用户/会话；确认时事务锁定并重新校验资格；替代建议不得自动转成写动作；本切片仍不接入 Agent 自动执行 | 设计并实施 `P1-012` 与 `P1-015` 售后流程编排 |
| 2026-05-27 | `DOC-014`, `DOC-015` | 用户已授权按总体方案自主推进；售后 Workflow 规格与实施计划已落盘，实施前基线 `pytest -q --basetemp=.pytest_cache\workflow_baseline` 通过（63 passed） | 本轮在现有单 Agent 中增加受控 `PrepareAfterSales` 流程动作；政策无依据不生成待确认动作；确认建单仍使用既有事务端点 | 按 TDD 实施 `P1-012` 与 `P1-015` |
| 2026-05-27 | `P1-012`, `P1-015`（含 `P1-017` 协议部分） | Workflow/Agent/Chat 新测试先取得模块缺失和响应协议不支持的 RED 证据；随后 `pytest -q --basetemp=.pytest_cache\after_sales_workflow_full` 通过（74 passed），`scripts\verify_migration.py`、`scripts\init_db.py`、`scripts\seed_mock_data.py` 与 `git diff --check` 通过；真实 PostgreSQL 验证 Workflow 创建动作后工单为零、重复确认后仍仅一张工单 | 首次烟测中的中文来源字面量经 PowerShell 标准输入编码后未命中 `Doc5` 常量，Workflow 正确转人工；改用模块 `POLICY_SOURCE_ID` 后业务链路验证通过 | 实施 `P1-013`、`P1-014` 与 `P1-016`，再收口 `P1-017` |
| 2026-05-27 | `P1-013`, `P1-014`, `P1-016`, `P1-017` | `DiagnosisWorkflow` 12 项单元测试 + 5 项 Agent 集成测试 + 4 项咨询场景测试 + 7 项 Handoff 摘要测试 + 3 项工单查询 API 测试；全量 `pytest` 通过（106 passed）；`scripts\verify_migration.py` 通过；`git diff --check` 仅 CRLF 告警 | Agent regex `.+?` 不支持嵌套 JSON 数组，改为 `.+` 贪婪匹配；`retrieve_faq` 导出至 `tools` 包供 `DiagnosisWorkflow` 注入 | 实施 `P1-018` 管理侧接口、`P1-019` 离线评测数据集、`P1-020` 安全与规则自动化测试 |
| 2026-05-27 | `P1-005`, `P1-010`, `P1-011` | `agent_runs`/`tool_calls`/`risk_events`/`handoff_records` 四表持久化并纳入 `init_tables`；`AuditRepository` 8 项测试通过；`TicketQueryService` 3 项 API 测试通过；全量 `pytest` 通过（114 passed）；`init_db.py` + `seed_mock_data.py` 成功 | P1-010 实际已由上一批次实现（ticket query API），本批次补充标记；P1-011 的 `HandoffSummary` 已集成到 Agent metadata 并新增持久化表 | 实施 `P1-019` 离线评测数据集、`P1-020` 安全自动化测试 |
| 2026-05-27 | `P1-019`, `P1-020`, `P1-018`, `P1-021` | `data/evaluation_cases.json` 14 场景；`evaluation_cases`/`evaluation_runs` 表；`EvaluationCase` + `evaluate_response` 9 项测试；`test_security_gate.py` 7 项安全测试；admin API（会话/工单/评测）6 项测试；`EvaluationRepository` 3 项测试；`mock_customers.role` 列 + `admin_zhang` 种子；`ALTER TABLE ... ADD COLUMN IF NOT EXISTS` 兼容已有库；全量 `pytest` 通过（139 passed）；`init_db.py` + `seed_mock_data.py` 成功 | RBAC 基于 `role` 字段；admin 依赖 `require_admin`；`list_all_conversations` 新增到 ConversationManager | 实施 `P1-022` M2 验收 |
| 2026-05-27 | `P1-022` M2 验收 | **全量回归 139/139 passed**；`init_db.py` / `seed_mock_data.py` / `verify_migration.py` 全部 SUCCESS；**§13.3 指标逐项验证：** ①知识问答引用正确率≥90%——12 项引用/咨询/政策测试全通过；②售后资格规则正确率 100%——12 项边界测试全通过；③未授权访问拦截率 100%——18 项权限隔离测试全通过；④未确认写操作拦截率 100%——11 项确认/幂等/过期测试全通过；⑤无依据乱答率≤5%——5 项空检索转人工测试全通过；⑥核心流程自动化测试——42 项 Agent/Workflow/Chat 测试全通过；⑦工具调用审计——8 项审计模型测试覆盖 agent_runs/tool_calls/risk_events/handoff_records；⑧转人工摘要——7 项 HandoffSummary 测试验证结构化摘要可用。API 端点全部就绪（用户侧 7 + 管理侧 4）。`M2` 里程碑关闭。验收记录：`docs/m2-acceptance-record.md` | 无 | Phase 1 完成；可进入 Phase 2 多智能体协作（`P2-001` 起） |
| 2026-05-27 | Phase 2 设计规格 | 用户确认采用方案 B（领域 Agent 独立 ReAct 循环）；设计规格已落盘：`docs/superpowers/specs/2026-05-27-phase-2-multi-agent-design.md` | DEC-012：TroubleshootingAgent 和 AfterSalesAgent 各有独立 LLM 循环；ConsultationHandler 和 HandoffWorkflow 保留为无循环 Workflow；confirm_ticket 由 Supervisor/API 层处理确保确认在 Agent 循环之外 | 编写并执行 Phase 2 实施计划 |
| 2026-05-27 | `P2-001` 至 `P2-007`、`M3` | TDD 实施：`SubAgentInput`/`SubAgentResponse` 协议（3 测试）→ `BaseReActAgent` 共享循环 → `TroubleshootingAgent`（4 测试）→ `AfterSalesAgent` 确定性管道（6 测试）→ `ToolRegistry`（4 测试）→ `ConsultationHandler` → `Supervisor` 意图路由（4 测试）→ 对照评测（5 测试）→ API 集成；**全量 165/165 passed**；`init_db.py` / `seed_mock_data.py` / `verify_migration.py` 全部 SUCCESS；`main.py` 已切换为 Supervisor 架构 | 新增文件：`sub_agent.py`、`base_agent.py`、`troubleshooting_agent.py`、`after_sales_agent.py`、`tool_registry.py`、`consultation_handler.py`、`supervisor.py`；旧 `agent.py` 保留不删除；AfterSalesAgent 使用确定性管道而非 LLM 循环 | `M3` 里程碑关闭；Phase 2 全部完成；可进入 Phase 3 |

## 10. 当前待办焦点

`M3` 里程碑已关闭。Phase 2 全部任务（P2-001 至 P2-007）完成。

**架构现状：**
```text
Supervisor（意图路由 + 汇总）
  ├── TroubleshootingAgent（独立 ReAct 循环 + search_faq）
  ├── AfterSalesAgent（确定性管道 + order/policy/eligibility）
  ├── ConsultationHandler（FAQ + policy 检索）
  └── HandoffWorkflow（转人工）
```

下一阶段为 **Phase 3：企业级治理与真实接入**（`P3-001` 起），当前状态 `DEFERRED`，需用户确认后启动。
