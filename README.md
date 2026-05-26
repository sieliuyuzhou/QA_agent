# QA_agent

## 项目概述

基于 RAG 的智能客服 Agent 系统。当前代码支持 FAQ 检索回答、多轮会话持久化、通过 `AskUser` 主动澄清，以及通过 `Handoff` 返回人工转接提示。

## 目录结构

```
test3/
├── llm/                    # 模型层：LLM API 调用封装
│   ├── __init__.py
│   ├── client.py           # ChatService 类
│   └── exceptions.py       # 异常定义
├── tools/                  # 工具层：Tool 基类与实现
│   ├── __init__.py
│   └── base.py             # Tool + ToolParameter 基类
├── utils/                  # 通用层：跨模块共享数据操作
│   ├── __init__.py
│   └── conversation.py     # ConversationManager
├── domain/                 # 领域层：业务逻辑
│   ├── __init__.py
│   └── customer_service/
│       ├── __init__.py
│       ├── agent.py        # CustomerServiceAgent
│       └── prompts.py      # Prompt 模板
├── apps/                   # 应用层：API 路由
│   ├── __init__.py
│   └── customer_service/
│       ├── __init__.py
│       └── routes.py       # HTTP 接口
├── infrastructure/         # 仓储层：数据持久化
│   ├── __init__.py
│   ├── database.py         # 数据库连接
│   ├── models.py           # ORM 模型
│   └── rag/               # 向量存储
│       ├── __init__.py
│       ├── embedding.py
│       ├── exceptions.py
│       └── store.py
├── scripts/                # 脚本工具
│   ├── import_faq.py       # FAQ 数据导入
│   ├── verify_migration.py # 迁移验证脚本
│   └── smoke_test.py       # 功能冒烟测试
├── data/                   # 数据目录
│   └── chroma/            # 向量数据库
├── 实训文档/               # FAQ 文档
├── .env                    # 环境变量配置
└── requirements.txt        # 依赖列表
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

1. **目录重组**
   - 创建新目录结构：`llm/`、`tools/`、`utils/`、`domain/`、`apps/`、`infrastructure/`
   - 符合四层架构：应用层 → 领域层 → 工具层/模型层/通用层 → 仓储层

2. **模块迁移**
   - `model/chat.py` → `llm/client.py`
   - `model/exceptions.py` → `llm/exceptions.py`
   - `rag/` → `infrastructure/rag/`

3. **旧目录清理**
   - 删除 `retriever/` 目录（由 ReAct Agent 替代）
   - 删除 `api/` 目录（后续在 `apps/` 下重写）
   - 删除 `model/` 和 `rag/` 旧目录

4. **占位文件创建**
   - `tools/base.py`：Tool + ToolParameter 基类
   - `utils/conversation.py`：ConversationManager 占位实现
   - `domain/customer_service/agent.py`：AgentResponse + CustomerServiceAgent 占位实现

**验证脚本：**

完成迁移后，请运行以下脚本验证：

```bash
# 1. 目录结构和 import 路径验证
python scripts/verify_migration.py

# 2. 外部/持久化冒烟测试（显式选择后运行）
$env:RUN_EXTERNAL_SMOKE="true"
python scripts/smoke_test.py
```

两个脚本均显示 `[SUCCESS]` 后，即可进入下一阶段开发。

---

### Step 2: 工具层 —— Tool 基类与 FAQ 检索工具 ✅

**已完成工作：**

1. **Tool 基类完善** (`tools/base.py`)
   - `ToolParameter` 类：参数定义（name、type、description、required、default）
   - `Tool` 类：工具封装（name、description、func、parameters）
   - `run(params: dict) -> str`：Agent 唯一调用入口，支持必填参数校验和可选参数默认值
   - `to_prompt_desc() -> str`：生成注入 prompt 的工具描述文本
   - `to_openai_schema() -> dict`：转换为 OpenAI function calling 格式（预留）

2. **FAQ 检索工具实现** (`tools/faq_search.py`)
   - `search_faq(query, top_k=5) -> str`：纯函数，调用 VectorStore.search() 检索 FAQ
   - `search_faq_tool`：Tool 对象，供 Agent 调度

3. **设计原则**
   - 函数和 Tool 对象分离：纯函数可被任何模块直接 import 调用
   - Tool 是薄封装层，不包含业务逻辑
   - 新增工具只需新建文件（函数 + Tool 对象）后追加到 Agent 的 tools 列表

**外部冒烟验证（显式选择后运行）：**

```powershell
$env:RUN_EXTERNAL_SMOKE="true"
python scripts/smoke_test.py
```

---

### Step 3: 会话管理模块 ✅

**已完成工作：**

1. **数据库连接管理** (`infrastructure/database.py`)
   - `DatabaseManager` 类：PostgreSQL 连接池管理
   - 支持 `execute()` 和 `execute_one()` 方法
   - 自动连接获取和归还

2. **数据模型定义** (`infrastructure/models.py`)
   - `conversations` 表：会话元数据（conversation_id、user_id、title、status）
   - `messages` 表：消息明细（role、content、turn_number、metadata）
   - `turn_number` 自动计算：user +1 开启新轮次，assistant 复用当前值

3. **会话管理器** (`utils/conversation.py`)
   - `create(user_id)` → conversation_id：创建会话
   - `add_message(conversation_id, role, content, metadata)` → message_id：追加消息
   - `get_context(conversation_id)` → 最近 N 轮消息：上下文截取
   - `get_history(conversation_id)` → 完整历史
   - `list_conversations(user_id)` → 用户会话列表
   - `close(conversation_id)`：关闭会话

4. **依赖更新**
   - `requirements.txt`：添加 `psycopg2-binary`
   - `.env.example`：添加 `CONVERSATION_DB_URL` 配置

**数据库配置：**

```bash
# .env 中配置 PostgreSQL 连接
CONVERSATION_DB_URL=postgresql://user:1234@localhost:5433/agent
```

**数据库初始化：**

```powershell
.\.venv\Scripts\python.exe scripts\init_db.py
```

应用启动不会自动创建数据表，也不会忽略 schema 初始化失败；新环境应先显式执行上述 bootstrap 命令。

**外部冒烟验证（显式选择后运行）：**

```powershell
$env:RUN_EXTERNAL_SMOKE="true"
python scripts/smoke_test.py
```

---

### Step 4: 模型层确认 ✅

**已完成工作：**

本步骤确认 `llm/` 模块已在阶段一迁移完成，无需额外开发。

1. **模块单例导出** (`llm/__init__.py`)
   - `chat_service = ChatService()` 模块级单例
   - 其他模块通过 `from llm import chat_service` 调用

2. **核心方法签名**
   ```python
   def chat(
       prompt: str,
       system_prompt: Optional[str] = None,
       history: Optional[List[Dict[str, str]]] = None,
       temperature: float = 0.7,
       max_tokens: Optional[int] = None,
   ) -> str
   ```

3. **特性支持**
   - 重试策略：网络超时和限流时指数退避重试
   - 异常处理：分类处理 `ModelTimeoutError`、`ModelRateLimitError`、`ModelAuthenticationError` 等
   - 流式输出：`chat_stream()` 方法（预留）

**验证方式：**

```python
from llm import chat_service
response = chat_service.chat("你好")
```

---

### Step 5: 领域层 —— ReAct Agent ✅

**已完成工作：**

1. **Prompt 模板** (`domain/customer_service/prompts.py`)
   - `SYSTEM_PROMPT`：包含角色设定、工具说明、工作流程、输出格式
   - `build_prompt()`：填充 `{tools}`、`{context}`、`{user_input}`、`{history}` 占位符

2. **Agent 核心实现** (`domain/customer_service/agent.py`)
   - `AgentResponse`：响应结构体（type、content、conversation_id、metadata）
   - `CustomerServiceAgent`：ReAct Agent 主体
     - 构造函数注入：llm、conversation_manager、tools、max_steps
     - `run(user_input, conversation_id)` → AgentResponse

3. **ReAct 循环实现**
   - 持久化用户消息 → 获取上下文 → 循环执行 → 返回结果
   - 支持的 Action：`search_faq[关键词]`、`Finish[最终答案]`
   - `step_history` 仅存内存不入 SQL
   - 解析失败时 `continue` 让 LLM 重试
   - 达到 `max_steps` 时返回 fallback 消息

4. **内部能力**
   - `_find_tool()`：按名称查找工具
   - `_build_tools_description()`：生成工具描述文本
   - `_format_context()`：格式化对话历史
   - `_parse_output()`：正则解析 Thought/Action
   - `_map_action_input()`：智能参数映射（JSON → 单参数 → 兜底）
   - `_dispatch_tool()`：工具调度执行

**外部冒烟验证（显式选择后运行）：**

```powershell
$env:RUN_EXTERNAL_SMOKE="true"
python scripts/smoke_test.py
```

---

### Step 6: 应用层 —— API 接口服务 ✅

**已完成工作：**

1. **FastAPI 入口** (`main.py`)
   - `lifespan` 管理依赖生命周期（创建/销毁）
   - 全局单例：`conversation_manager`、`agent`
   - 路由挂载：`/api` 前缀

2. **Pydantic 模型** (`apps/customer_service/schemas.py`)
   - `ChatRequest` / `ChatResponse`
   - `CreateConversationRequest` / `CreateConversationResponse`
   - `ConversationDetail` / `ConversationListResponse`

3. **API 路由** (`apps/customer_service/routes.py`)
   - `POST /api/chat`：发送消息（自动创建会话）
   - `POST /api/conversations`：创建会话
   - `GET /api/conversations/{id}`：获取会话详情
   - `GET /api/conversations?user_id=xxx`：列出用户会话

4. **启动方式**
   ```bash
   # 新环境首次启动前初始化 PostgreSQL schema
   python scripts/init_db.py

   # 开发模式
   python main.py
   
   # 或使用 uvicorn
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **API 文档**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

**外部冒烟验证（显式选择后运行）：**

```powershell
$env:RUN_EXTERNAL_SMOKE="true"
python scripts/smoke_test.py
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填入实际配置：

```bash
cp .env.example .env
```

### 3. 初始化 PostgreSQL Schema

```bash
python scripts/init_db.py
```

### 4. 导入 FAQ 数据

```bash
python scripts/import_faq.py
```

### 5. 验证安装

```powershell
# 离线回归测试：不调用已配置的 LLM 或 Embedding 接口
.\.venv\Scripts\python.exe -m pytest -q

# 模块与 import 迁移验证
.\.venv\Scripts\python.exe scripts\verify_migration.py

# 显式外部冒烟测试：可能写入本地数据并发生 API 调用
$env:RUN_EXTERNAL_SMOKE="true"
.\.venv\Scripts\python.exe scripts\smoke_test.py
```

## 依赖方向

```
apps ──────→ domain ──────→ tools / llm / utils ──────→ infrastructure
 入口         业务           原子能力                    数据持久化
```

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
