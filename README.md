# QA_agent

## 项目概述

An intelligent customer service multi-agent system built on RAG, supporting multi-turn conversations, proactive questioning, LangGraph-based agent orchestration, simulated after-sales workflows, and a Vue 3 testing frontend.

## 目录结构

```
QA_agent/
├── llm/                        # 模型层：LLM API 调用封装
│   ├── __init__.py
│   ├── client.py               # ChatService 类
│   ├── exceptions.py           # 异常定义
│   └── langchain_adapter.py    # LangChain BaseChatModel 适配层
├── tools/                      # 工具层：Tool 基类与实现
│   ├── __init__.py
│   ├── base.py                 # Tool + ToolParameter + ToolResult + Citation
│   ├── faq_search.py           # FAQ 检索工具
│   ├── policy_search.py        # 售后政策检索工具
│   └── langchain_convert.py    # Tool → LangChain StructuredTool 转换
├── utils/                      # 通用层：跨模块共享数据操作
│   ├── __init__.py
│   ├── conversation.py         # ConversationManager
│   ├── tickets.py              # 工单仓储与待确认动作服务
│   └── evaluation_repo.py      # 评测结果仓储
├── domain/                     # 领域层：业务逻辑
│   ├── __init__.py
│   └── customer_service/
│       ├── __init__.py
│       ├── agent.py            # CustomerServiceAgent（旧版 ReAct）
│       ├── base_agent.py       # BaseReActAgent 共享循环基类
│       ├── prompts.py          # Prompt 模板
│       ├── context.py          # CurrentUser/OrderView 数据类
│       ├── eligibility.py      # EligibilityRuleService 资格规则服务
│       ├── ticketing.py        # TicketActionService（PendingAction + 工单）
│       ├── workflows.py        # Workflow 定义与常量
│       ├── sub_agent.py        # SubAgentInput/SubAgentResponse 协议
│       ├── consultation_handler.py  # ConsultationHandler（无 LLM 循环）
│       ├── troubleshooting_agent.py # TroubleshootingAgent
│       ├── after_sales_agent.py     # AfterSalesAgent（确定性管道）
│       ├── supervisor.py            # 旧版 Supervisor
│       ├── langgraph_agent.py       # BaseLangGraphAgent（StateGraph）
│       ├── langgraph_supervisor.py  # LangGraphSupervisor（tool_calls）
│       ├── ticket_query.py          # TicketQueryService
│       ├── handoff.py               # HandoffSummary 转接摘要
│       └── tool_registry.py         # 工具注册与白名单
├── apps/                       # 应用层：API 路由
│   ├── __init__.py
│   └── customer_service/
│       ├── __init__.py
│       ├── routes.py           # 聊天/会话 API
│       ├── admin_routes.py     # 管理端 API
│       ├── order_routes.py     # 订单 API
│       ├── ticket_routes.py    # 工单 API
│       ├── action_routes.py    # 待确认动作 API
│       ├── schemas.py          # Pydantic 响应模型
│       ├── dependencies.py     # get_current_user 依赖
│       └── admin_dependencies.py # require_admin 依赖
├── infrastructure/             # 仓储层：数据持久化
│   ├── __init__.py
│   ├── database.py             # 数据库连接池
│   ├── models.py               # 表结构与 SQL 常量
│   └── rag/                    # 向量存储
│       ├── __init__.py
│       ├── embedding.py
│       ├── exceptions.py
│       └── store.py
├── frontend_new/               # Vue 3 前端测试界面
├── scripts/                    # 脚本工具
│   ├── init_db.py              # 数据库 schema 初始化
│   ├── seed_mock_data.py       # 模拟业务数据导入
│   ├── verify_migration.py     # 迁移验证脚本
│   └── smoke_test.py           # 功能冒烟测试
├── tests/                      # 自动化测试
│   ├── test_agent_actions.py
│   ├── test_agent_citations.py
│   ├── test_agent_diagnosis.py
│   ├── test_agent_workflow.py
│   ├── test_eligibility_rules.py
│   ├── test_conversation.py
│   ├── test_identity_and_conversations.py
│   ├── test_mock_data.py
│   ├── test_orders_api.py
│   ├── test_security_gate.py
│   ├── test_ticket_full.py
│   ├── test_ticket_query_api.py
│   ├── test_handoff_summary.py
│   ├── test_admin_api.py
│   ├── test_evaluation_repo.py
│   ├── test_sub_agent_protocol.py
│   ├── test_tool_registry.py
│   ├── test_supervisor.py
│   ├── test_comparison.py
│   ├── test_langchain_adapter.py
│   ├── test_langchain_convert.py
│   ├── test_langgraph_agent.py
│   └── test_langgraph_supervisor.py
├── data/                       # 数据目录
│   └── chroma/                 # 向量数据库
├── docs/                       # 文档目录
│   ├── solution/               # 设计方案
│   └── worklists/              # 任务台账
├── .env                        # 环境变量配置
├── main.py                     # FastAPI 启动入口
├── docker-compose.yml          # PostgreSQL 容器
└── requirements.txt            # 依赖列表
```

## 开发指南

本项目包含三份开发指南文档，用于 Vibe Coding 协作开发：

### 文档说明

| 文档 | 用途 | 适用场景 |
|------|------|----------|
| `guide.md` | **基础版**：RAG 检索增强服务 | 从零搭建 RAG 服务（向量入库 + 检索 + HTTP 接口） |
| `guide_agent_extension_clean.md` | **精简版**：ReAct Agent 扩展 | 在已有 RAG 服务基础上扩展 Agent 能力，适合作为 Vibe Coding 指引 |
| `guide_agent_extension.md` | **详细版**：ReAct Agent 扩展（参考用） | 包含完整实现细节，可借鉴具体代码和设计思路 |

### 使用方式

**场景一：从零开始搭建 RAG 服务**

```
阅读 guide.md → 按章节逐步开发 → 完成基础 RAG 服务
```

**场景二：在 RAG 服务基础上扩展 Agent**

```
阅读 guide_agent_extension_clean.md → 理解架构变更 → 与 AI 协作开发
```

**场景三：遇到具体实现问题**

```
查阅 guide_agent_extension.md → 找到对应章节 → 参考详细实现
```

### 文档关系

```
guide.md（基础 RAG 服务）
    │
    └──→ guide_agent_extension_clean.md（Agent 扩展指引）
              │
              └──→ guide_agent_extension.md（详细实现参考）
```

### 为什么有两个 Agent 扩展文档？

| 对比项 | `guide_agent_extension_clean.md` | `guide_agent_extension.md` |
|--------|----------------------------------|---------------------------|
| 定位 | Vibe Coding 指引 | 实现参考手册 |
| 内容 | 架构设计 + 任务清单 + 完成标志 | 完整代码 + 详细步骤 |
| 灵活性 | 高（AI 可自由发挥） | 低（固定了具体实现） |
| 适用 | 与 AI 协作开发 | 查阅具体实现细节 |

**建议**：开发时以 `clean` 版本为主，遇到问题时查阅详细版参考。

---

## 开发进度

### Step 1: 项目初始化 —— 目录重组与迁移 ✅

**已完成工作：**

1. **目录重组** — Created new directory structure (`llm/`, `tools/`, `utils/`, `domain/`, `apps/`, `infrastructure/`), conforming to a four-layer architecture: application → domain → tools/llm/utils → infrastructure.

2. **模块迁移** — `model/chat.py` → `llm/client.py`, `model/exceptions.py` → `llm/exceptions.py`, `rag/` → `infrastructure/rag/`.

3. **旧目录清理** — Removed `retriever/`, `api/`, and old `model/` and `rag/` directories.

4. **占位文件创建** — Placeholder implementations for `tools/base.py`, `utils/conversation.py`, and `domain/customer_service/agent.py`.

---

### Step 2: 工具层 —— Tool 基类与 FAQ 检索工具 ✅

**已完成工作：**

1. **Tool 基类完善** (`tools/base.py`) — `ToolParameter` for parameter definitions, `Tool` as a tool encapsulation with `run(params: dict) -> str` as the sole Agent entry point supporting required parameter validation and optional defaults, `to_prompt_desc() -> str` for generating tool descriptions injected into prompts, and `to_openai_schema() -> dict` reserved for future OpenAI function calling format.

2. **FAQ 检索工具实现** (`tools/faq_search.py`) — A pure function `search_faq(query, top_k=5) -> str` that calls `VectorStore.search()`, and a corresponding `search_faq_tool` Tool object.

3. **设计原则** — Functions and Tool objects are separated; pure functions can be directly imported by any module; "Tool 是薄封装层，不包含业务逻辑"; new tools simply require a new file (function + Tool object) appended to the Agent's tools list.

---

### Step 3: 会话管理模块 ✅

**已完成工作：**

1. **数据库连接管理** (`infrastructure/database.py`) — `DatabaseManager` class with PostgreSQL connection pool management, supporting `execute()` and `execute_one()` methods with automatic connection acquisition and return.

2. **数据模型定义** (`infrastructure/models.py`) — `conversations` table (conversation_id, user_id, title, status) and `messages` table (role, content, turn_number, metadata), with `turn_number` auto-calculated: user messages increment the turn, assistant messages reuse the current value.

3. **会话管理器** (`utils/conversation.py`) — Methods for creating conversations, adding messages, getting recent N turns of context, retrieving full history, listing user conversations, and closing conversations.

4. **依赖更新** — Added `psycopg2-binary` to `requirements.txt` and `CONVERSATION_DB_URL` to `.env.example`.

---

### Step 4: 模型层确认 ✅

This step confirms the `llm/` module was already migrated in Phase 1, requiring no additional development.

1. **模块单例导出** — `chat_service = ChatService()` as a module-level singleton, accessible via `from llm import chat_service`.

2. **核心方法签名** — `chat(prompt, system_prompt=None, history=None, temperature=0.7, max_tokens=None) -> str`

3. **特性支持** — Exponential backoff retry for network timeouts and rate limits, classified exception handling (`ModelTimeoutError`, `ModelRateLimitError`, `ModelAuthenticationError`), and a reserved `chat_stream()` method.

---

### Step 5: 领域层 —— ReAct Agent ✅

**已完成工作：**

1. **Prompt 模板** (`domain/customer_service/prompts.py`) — `SYSTEM_PROMPT` covering role setting, tool descriptions, workflow, and output format; `build_prompt()` fills `{tools}`, `{context}`, `{user_input}`, `{history}` placeholders.

2. **Agent 核心实现** (`domain/customer_service/agent.py`) — `AgentResponse` structure (type, content, conversation_id, metadata); `CustomerServiceAgent` with constructor injection of llm, conversation_manager, tools, and max_steps, exposing `run(user_input, conversation_id) → AgentResponse`.

3. **ReAct 循环实现** — Persists user messages, retrieves context, loops execution, returns results. Supports `search_faq[关键词]` and `Finish[最终答案]` actions; step_history is kept in memory only; parse failures `continue` to let the LLM retry; max_steps reached triggers a fallback message.

4. **内部能力** — Tool lookup by name, tools description generation, conversation history formatting, regex-based Thought/Action parsing, intelligent parameter mapping (JSON → single param → fallback), and tool dispatch execution.

---

### Step 6: 应用层 —— API 接口服务 ✅

**已完成工作：**

1. **FastAPI 入口** (`main.py`) — Lifespan-managed dependency lifecycle (create/destroy); global singletons for `conversation_manager` and `agent`; routes mounted under `/api` prefix.

2. **Pydantic 模型** (`apps/customer_service/schemas.py`) — `ChatRequest` / `ChatResponse`, `CreateConversationRequest` / `CreateConversationResponse`, `ConversationDetail` / `ConversationListResponse`.

3. **API 路由** (`apps/customer_service/routes.py`)
   - Internal trial identification via `X-QA-User-Id` header
   - `POST /api/chat`, `POST /api/conversations`, `GET /api/conversations`, `GET /api/conversations/{id}`
   - `GET /api/orders`, `GET /api/orders/{id}`

4. **启动方式**
   ```bash
   python main.py
   # or
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

---

### Step 7: 多智能体客服系统 ✅

**已完成工作：**

1. **多智能体架构设计** (`docs/solution/customer-service-multi-agent-solution.md`)
   - Supervisor + 领域子 Agent 架构
   - 四层架构：应用层 → 领域层（Supervisor/子 Agent）→ 工具/服务层 → 基础设施层
   - 响应协议：final_answer / ask_user / confirm_action / handoff / error

2. **LangGraph 框架集成**
   - LangChain 适配层 (`llm/langchain_adapter.py`)：`ChatServiceLLM` 包装为 `BaseChatModel`
   - 工具转换层 (`tools/langchain_convert.py`)：`Tool` → `StructuredTool` 转换
   - `BaseLangGraphAgent` (`domain/customer_service/langgraph_agent.py`)：StateGraph 替代自研 ReAct 循环
   - `LangGraphSupervisor` (`domain/customer_service/langgraph_supervisor.py`)：LangChain tool_calls 路由
   - Checkpointer：`MemorySaver`（开发阶段），线程 ID = conversation_id

3. **领域子 Agent**
   - `ConsultationHandler`：产品/政策咨询，无 LLM 循环，直接检索+格式化
   - `TroubleshootingAgent`：故障排查，LangGraph StateGraph，多轮槽位收集
   - `AfterSalesAgent`：售后办理，确定性管道，提取对话历史信息

4. **售后业务闭环**
   - `EligibilityRuleService`：确定性资格规则（退换/保修/付费维修边界）
   - `TicketActionService`：待确认动作创建与幂等确认
   - `MockOrderTool` / `MockTicketTool`：模拟订单与工单
   - 写操作保护：未确认不建单，幂等重复确认不重复建单，30 分钟有效期

5. **身份与权限**
   - 内部试用认证：`X-QA-User-Id` 请求头
   - 会话/订单/工单按 user_id 归属校验
   - 管理端 RBAC：`require_admin` 依赖，admin_zhang 种子管理员

6. **审计与评测**
   - `agent_runs` / `tool_calls` / `risk_events` / `handoff_records` 四表审计
   - `evaluation_cases` / `evaluation_runs` 评测数据
   - 14 个评测场景覆盖产品咨询、故障排查、售后办理、权限隔离

7. **Vue 3 前端测试界面** (`frontend_new/`)
   - Vue 3 + TypeScript + Vite + Element Plus + Pinia + Vue Router
   - 6 个页面：对话窗口、订单管理、工单查询、审计日志、评测结果、系统状态
   - 响应类型标识：final_answer / ask_user / confirm_action / handoff / error
   - 待确认动作交互（确认按钮）
   - 引用来源展开查看

**验证方式：**

```bash
# 全量回归测试（194 项）
.\.venv\Scripts\python.exe -m pytest -q

# 数据库初始化
.\.venv\Scripts\python.exe scripts\init_db.py

# 模拟数据导入
.\.venv\Scripts\python.exe scripts\seed_mock_data.py
```

## 多智能体架构

```
用户 → FastAPI API → Auth → LangGraphSupervisor
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
         ConsultationHandler  TroubleshootingAgent  AfterSalesAgent
         （无 LLM 循环）         （LangGraph）        （确定性管道）
                    │               │               │
              KnowledgeSearch   AskUser/槽位收集    Order/Policy/Eligibility
                                                    │
                                               ConfirmAction → Ticket
```

### 响应协议

| 类型 | 含义 | 客户端行为 |
|------|------|-----------|
| `final_answer` | 最终回答 | 展示答案 + 引用来源 |
| `ask_user` | 反问澄清 | 展示澄清问题，等待用户输入 |
| `confirm_action` | 待确认写操作 | 显示确认按钮和动作摘要 |
| `handoff` | 转人工 | 展示转人工提示 + 摘要 |
| `error` | 可恢复错误 | 展示错误信息，引导重试 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 填入 LLM_API_KEY 等配置
```

### 3. 启动 PostgreSQL

```bash
docker compose up -d
```

### 4. 初始化数据库与模拟数据

```bash
python scripts/init_db.py
python scripts/seed_mock_data.py
python scripts/import_faq.py
```

### 5. 验证安装

```bash
# 离线回归测试
.\.venv\Scripts\python.exe -m pytest -q

# 启动后端
python main.py
```

### 6. 启动前端（可选）

```bash
cd frontend_new
npm install
npm run dev
```

## API 接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/chat` | 发送消息 | 试用用户 |
| POST | `/api/conversations` | 创建会话 | 试用用户 |
| GET | `/api/conversations` | 会话列表 | 试用用户 |
| GET | `/api/conversations/{id}` | 会话详情 | 试用用户 |
| POST | `/api/conversations/{id}/actions/{id}/confirm` | 确认动作 | 试用用户 |
| GET | `/api/orders` | 订单列表 | 试用用户 |
| GET | `/api/orders/{id}` | 订单详情 | 试用用户 |
| GET | `/api/tickets/{id}` | 工单详情 | 试用用户 |
| GET | `/api/admin/conversations` | 管理会话列表 | 管理员 |
| GET | `/api/admin/tickets` | 管理工单列表 | 管理员 |
| GET | `/api/admin/evaluations` | 评测结果 | 管理员 |

## 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| LLM_API_KEY | LLM API 密钥 | - |
| LLM_BASE_URL | LLM API 地址 | https://api.openai.com/v1 |
| LLM_MODEL | 模型名称 | gpt-3.5-turbo |
| EMBEDDING_API_KEY | Embedding API 密钥 | - |
| EMBEDDING_BASE_URL | Embedding API 地址 | https://api.openai.com/v1 |
| EMBEDDING_MODEL | Embedding 模型名称 | text-embedding-ada-002 |
| RAG_PERSIST_DIR | 向量数据库路径 | ./data/chroma |
| RAG_COLLECTION_NAME | 集合名称 | faq_collection |
| CONVERSATION_DB_URL | PostgreSQL 连接 | postgresql://user:1234@localhost:5433/agent |

## 依赖方向

```
apps ──────→ domain ──────→ tools / llm / utils ──────→ infrastructure
 入口         业务           原子能力                    数据持久化
```
