# QA_agent

## 项目概述

基于 RAG 的多智能体客服系统，支持多轮对话、主动反问、LangGraph 多智能体编排、模拟售后办理流程和 Vue 3 测试前端。

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

| 文档 | 用途 | 适用场景 |
|------|------|----------|
| `guide.md` | 基础版：RAG 检索增强服务 | 从零搭建 RAG 服务（向量入库 + 检索 + HTTP 接口） |
| `guide_agent_extension_clean.md` | 精简版：ReAct Agent 扩展 | 在已有 RAG 服务基础上扩展 Agent 能力 |
| `guide_agent_extension.md` | 详细版：ReAct Agent 扩展（参考用） | 包含完整实现细节，可借鉴具体代码和设计思路 |

**使用方式：** 开发时以 `clean` 版本为主，遇到问题时查阅详细版参考。

## 开发进度

### Step 1: 项目初始化 —— 目录重组与迁移 ✅

已完成目录结构重组（`llm/`、`tools/`、`utils/`、`domain/`、`apps/`、`infrastructure/` 四层架构），模块迁移和旧目录清理。

---

### Step 2: 工具层 —— Tool 基类与 FAQ 检索工具 ✅

完成 `Tool` + `ToolParameter` 基类（参数校验、prompt 描述生成、OpenAI function calling 格式预留），实现 `search_faq` 检索工具。

---

### Step 3: 会话管理模块 ✅

完成 PostgreSQL 连接池管理（`DatabaseManager`）、会话/消息表结构定义、`ConversationManager` 实现（创建/追加/上下文截取/历史查询）。

---

### Step 4: 模型层确认 ✅

确认 `llm/` 模块已迁移完成，提供 `chat(prompt, system_prompt, history)` 核心方法，支持指数退避重试和分类异常处理。

---

### Step 5: 领域层 —— ReAct Agent ✅

完成 Prompt 模板体系（角色设定 + 工具说明 + 输出格式）、`CustomerServiceAgent` 核心实现、ReAct 循环（Thought/Action 正则解析、工具调度、max_steps 兜底）。

---

### Step 6: 应用层 —— API 接口服务 ✅

完成 FastAPI 入口配置、Pydantic 模型定义、API 路由（聊天/会话/订单）、Swagger 文档。

---

### Step 7: 多智能体客服系统 ✅

**1. 多智能体架构设计**
- Supervisor + 领域子 Agent 架构
- 四层架构：应用层 → 领域层（Supervisor/子 Agent）→ 工具/服务层 → 基础设施层
- 统一响应协议：final_answer / ask_user / confirm_action / handoff / error

**2. LangGraph 框架集成**
- LangChain 适配层：`ChatServiceLLM` 包装为 `BaseChatModel`
- 工具转换层：`Tool` → `StructuredTool` 转换
- `BaseLangGraphAgent`：StateGraph 替代自研 ReAct 循环
- `LangGraphSupervisor`：LangChain 原生 tool_calls 路由
- Checkpointer：`MemorySaver`，线程 ID = conversation_id

**3. 领域子 Agent**
- `ConsultationHandler`：产品/政策咨询，无 LLM 循环，直接检索+格式化
- `TroubleshootingAgent`：故障排查，LangGraph StateGraph，多轮槽位收集
- `AfterSalesAgent`：售后办理，确定性管道，从对话历史提取订单号/办理类型/问题原因

**4. 售后业务闭环**
- `EligibilityRuleService`：确定性资格规则（退换/保修/付费维修边界）
- `TicketActionService`：待确认动作创建与幂等确认
- 写操作保护：未确认不建单，幂等重复确认不重复建单，30 分钟有效期

**5. 身份与权限**
- 内部试用认证：`X-QA-User-Id` 请求头
- 会话/订单/工单按 user_id 归属校验
- 管理端 RBAC：`require_admin` 依赖

**6. 审计与评测**
- `agent_runs` / `tool_calls` / `risk_events` / `handoff_records` 四表审计
- 14 个评测场景覆盖产品咨询、故障排查、售后办理、权限隔离

**7. Vue 3 前端测试界面** (`frontend_new/`)
- Vue 3 + TypeScript + Vite + Element Plus + Pinia + Vue Router
- 6 个页面：对话窗口、订单管理、工单查询、审计日志、评测结果、系统状态
- 响应类型标识和待确认动作交互

### 架构

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

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

推荐使用虚拟环境：

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# Windows CMD
.\.venv\Scripts\activate.bat
# Linux/Mac
source .venv/bin/activate

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
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe scripts\seed_mock_data.py
```

### 5. 验证安装

```bash
# 全量回归测试（194 项）
.\.venv\Scripts\python.exe -m pytest -q

# 启动后端
.\.venv\Scripts\python.exe main.py
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
