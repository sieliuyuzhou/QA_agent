# Vibe Coding 实战：为 RAG 服务接入 ReAct Agent 智能客服

## 项目概述

本文档是 [guide.md](guide.md) 的增量扩展。假设你已按 guide.md 完成开发，当前项目状态：

**已有模块**：

| 模块 | 位置 | 功能 |
|------|------|------|
| model (llm) | `model/` | LLM 文本生成调用，支持同步/流式对话，OpenAI 兼容接口 |
| rag | `rag/` | FAQ 向量存储与检索，已导入 FAQ 数据并通过 `VectorStore.search()` 对外提供检索 |
| retriever | `retriever/` | 查询改写 + 检索编排，组合 model 的改写能力与 rag 的检索能力 |
| api | `api/` | HTTP 检索接口 `POST /search`，依赖 retriever |

**核心接口**：

- LLM 调用：`ChatService` 类提供 `chat(prompt, system_prompt=None) -> str` 和 `stream()` 方法
- 向量检索：`VectorStore` 实例的 `search(query_text, top_k=5)` 方法，返回带 metadata 的检索结果列表
- 检索编排：`Pipeline` 类组合查询改写与向量检索
- HTTP API：`POST /search` 接收 `{"question": "...", "enable_rewrite": true}`，返回改写后的查询和检索结果

本次扩展将在这个基础上：重组项目目录结构、引入 ReAct Agent 替代 retriever 的编排能力、增加会话管理支持多轮对话和主动反问。

## 我们要做什么

在已有的 RAG 检索服务之上，扩展为一个**具备多轮对话和主动反问能力的智能客服 Agent**。

原项目是一个无状态的检索服务：用户提问 → 改写 → 检索 → 返回结果，每次请求彼此独立。智能客服需要在此基础上增加三项关键能力：

1. **会话管理** — 记住"刚才说了什么"，多轮对话不丢失上下文
2. **Agent 编排** — 不再是无脑检索，而是由 Agent 判断意图、选择行动（检索 / 反问 / 回答）
3. **主动反问** — 用户意图模糊时，Agent 向用户提问澄清，而非强行猜测

### 0.1 与原 guide.md 的关系

本文件是对 [guide.md](guide.md) 的**增量扩展**，而非替代。已在 guide.md 中完成的模块（rag 向量存储）保持不变。同时，对项目目录结构做一次重组，为后续扩展（订单查询、物流跟踪等）预留位置。

| 模块 | 原 guide.md | 本次变更 |
|------|-----------|---------|
| rag | FAQ 向量入库与检索 | **不变**（数据已导入，复用现有检索接口） |
| llm | 属于 model 模块 | **独立**：从 model 中拆出，作为独立目录；`__init__.py` 以模块级单例导出，替换原工厂函数 |
| model/conversation | 不存在 | **新增**：会话持久化存储与 LLM 上下文构建 |
| retriever | 查询改写 + 检索编排 | **重构**：简化为单一检索 Tool，去掉改写和编排 |
| agent | 不存在 | **新增**：ReAct Agent，编排工具调用，支持反问 |
| api | 直接依赖 retriever | **调整**：依赖 Agent 而非 retriever |

### 0.2 四层架构

```
main.py                       ← FastAPI 启动入口

apps/                         ← 应用层：路由注册，极薄
    customer_service/
        routes.py              ← POST /chat, /conversations

domain/                       ← 领域层：纯业务逻辑
    customer_service/
        agent.py               ← CustomerServiceAgent (ReAct + AskUser)
        prompts.py             ← 客服 prompt 模板

tools/                        ← 工具层：基类 + 实现，双模式调用
    base.py                    ← Tool + ToolParameter
    faq_search.py              ← search_faq Tool

llm/                          ← 模型层：LLM API 调用
    client.py                  ← OpenAI 兼容 API 封装

utils/                        ← 通用层：跨模块共享的数据操作
    conversation.py            ← ConversationManager

infrastructure/               ← 仓储层：纯数据持久化
    rag/                       ← 向量存储与检索（不变）
        embedding.py
        store.py
    database.py                ← 数据库连接管理
    models.py                  ← 数据模型定义
```

### 0.3 依赖方向

```
apps ──────→ domain ──────→ tools / llm / utils ──────→ infrastructure
 入口         业务           原子能力                    数据持久化
```

规则：

- `apps` 只做参数接收、调用 domain、格式化响应
- `domain` 不直接调 API、不操作数据库，通过 tools / llm / utils 的接口获取能力
- `tools`、`llm`、`utils` 互不依赖，各自提供独立能力
- `infrastructure` 不包含任何业务逻辑
- `utils` 是通用数据操作层（如会话管理），与 tools/llm 同级，通过操作 infrastructure 的 ORM 模型间接访问数据库

### 0.4 模块边界原则（沿用）

1. **单向依赖**：依赖关系只能从上往下，禁止反向依赖或循环依赖
2. **模块公开接口隔离**：模块间只通过 `__init__.py` 的导出来交互，禁止 import 其他模块的内部文件
3. **配置隔离**：每个模块用独立前缀的环境变量（如 `LLM_*` / `RAG_*` / `CONVERSATION_*`），避免冲突

### 0.5 开发建议

- 构建顺序：infrastructure → tools / llm / utils → domain → apps（对应步骤1 → 步骤2-4 → 步骤5 → 步骤6）
- 功能最小可用即可，不做过度设计
- 增量式开发，每完成一个步骤就验证
- 新依赖写入 requirements.txt

> **项目迁移**：如果你已按 guide.md 完成了开发，在开始之前需要先重组项目目录结构。详见**步骤1：项目初始化**。

---

## 步骤1：项目初始化 —— 目录重组与迁移

如果你已完成 guide.md 的全部内容，当前项目是扁平结构。本步骤将项目重组为嵌套结构，后续步骤均在新结构上开发。

### 1.1 目录重映射

| 旧位置 | 新位置 | 操作 |
|--------|--------|------|
| `model/chat.py` | `llm/client.py` | **移动**（类名 `ChatService` 可保留或改为 `LLMClient`） |
| `model/exceptions.py` | `llm/exceptions.py` | **移动** |
| `model/__init__.py` | `llm/__init__.py` | 移动，更新导出 |
| `rag/` 整个目录 | `infrastructure/rag/` | **移动**（内部代码不变） |
| `retriever/` | — | **删除**（ReAct Agent 替代了查询改写和编排） |
| `api/` | `apps/customer_service/` | **重写**（接口从 `/search` 变为 `/chat`） |

### 1.2 迁移操作

将目录重映射表（见 1.1）交给 LLM 执行迁移。核心动作：按映射表移动文件、创建新目录结构、更新所有 import 路径。后续步骤中新增的模块文件在各自的步骤中按需创建，不在本步处理。

### 1.3 import 路径验证

迁移完成后，验证所有 import 路径正确无误：`from llm import chat_service`、`from infrastructure.rag import vector_store` 等关键导入应正常解析，`scripts/` 目录中的旧路径已同步更新，`from retriever` 相关的引用已全部移除。

> **注意**：`.env` 中已有的 `LLM_*` 和 `RAG_*` 环境变量无需修改。新增的 `CONVERSATION_*` 变量（如 `CONVERSATION_DB_PATH`）在开发会话管理模块时按需添加。

### 1.4 校验

完成目录重组后，编写脚本验证迁移无断裂：确认旧目录（`model/chat.py`、`retriever/`）已移除，新目录结构完整，关键 import（`from llm import chat_service`、`from infrastructure.rag import vector_store`）可正常解析，`.env` 文件存在且必需的环境变量已配置。任一项失败脚本以非零 exit code 退出。

---

## 步骤2：工具层 —— Tool 基类与注册模式

> **本步骤需要新建的目录和文件**：`tools/__init__.py`、`tools/base.py`。`tools/faq_search.py` 在步骤2.4 中创建。

工具层是连接 Agent 和后端代码的桥梁。核心设计：**函数和 Tool 对象分离**。函数是纯 Python，任何模块都能 import 直接调用；Tool 对象是对函数的薄封装，供 Agent 按名称调度。两者互不污染。

### 2.1 设计目标与思路

Agent 需要调用后端业务函数，但不能直接耦合。解决方案是一套薄封装机制——**函数和 Tool 对象分离**。纯 Python 函数不依赖 Agent，后端任何模块都能直接 import 调用；Tool 对象是对函数的薄封装，描述函数的名称、参数和用途，供 Agent 按名称调度。

Tool 的参数通过构造函数传入，不含任何业务逻辑，只负责参数校验和调用转发。Agent 通过 `self.tools = [...]` 列表管理工具，新增工具只需新建文件（函数 + Tool 对象）后追加到列表中，无需独立的注册中心。Agent 始终通过 `tool.run(params: dict) -> str` 调用工具。

预留 `to_openai_schema()` 方法签名（暂不实现），未来如需切换到 OpenAI 原生 function calling 只需实现此方法即可。

### 2.2 Tool 基类

需要创建两个类：`ToolParameter`（参数定义）和 `Tool`（工具封装）。

**ToolParameter** — 描述工具的一个输入参数：

| 属性 | 类型 | 说明 |
|------|------|------|
| `name` | `str` | 参数名 |
| `type` | `str` | 参数类型标签（如 `"string"`、`"integer"`），用于 prompt 展示 |
| `description` | `str` | 参数用途说明 |
| `required` | `bool` | 是否必填，默认 `True` |
| `default` | `Any` | 默认值，仅对非必填参数生效 |

**Tool** — 对纯函数的薄封装，不修改原始函数：

| 属性/方法 | 说明 |
|-----------|------|
| `name: str` | 工具名称，Agent 按此名称调度（如 `"search_faq"`） |
| `description: str` | 工具功能描述，注入 prompt 供 LLM 理解用途 |
| `parameters: list[ToolParameter]` | 参数列表，通过构造函数传入 |
| `run(params: dict) -> str` | **Agent 的唯一调用入口**。接收已解析的参数字典，内部解包为 keyword arguments 调用原始函数。缺少必填参数时应抛出异常 |
| `to_prompt_desc() -> str` | 生成注入 prompt 的工具描述文本。输出格式示例：`- search_faq(query: string, top_k: integer (可选)): 检索FAQ知识库` |
| `to_openai_schema() -> dict` | **[预留]** 转换为 OpenAI function calling 格式。当前阶段不需要实现（Agent 使用正则解析 LLM 文本输出），但保留方法签名以便未来平滑迁移 |

**关键约束**：

- `Tool` 只是薄封装层，**不包含任何业务逻辑**
- 原始函数和 `Tool` 对象是两个独立的东西——函数供后端代码直接 import，`Tool` 对象供 Agent 调度
- 参数定义通过构造函数传入，不使用抽象方法或装饰器

### 2.3 参数智能映射

Agent 从 LLM 输出中解析到的工具输入是一段**纯文本**（如 `"退货流程"` 或 `"{\"query\":\"退货\"}"`）。工具调度时需要将这段文本映射到正确的参数上。策略（按优先级）：

1. **JSON 解析**：如果文本是合法 JSON 对象，直接解析为 dict → `tool.run(dict)`
2. **单必填参数映射**：如果工具只有一个必填参数，将整个文本作为该参数的值
3. **兜底**：报错，提示需要结构化参数

这一步在 Agent 的工具调度方法中完成（见步骤5），不在 Tool 基类中。

### 2.4 工具实现：函数 + Tool 对象分离注册

以 FAQ 检索工具为例，在 `tools/faq_search.py` 中完成两部分：

**纯函数** `search_faq(query, top_k)` — 调用 `VectorStore.search()` 检索 FAQ 知识库，将结果格式化为易读文本返回，无结果时返回提示文本。

> 注意：`VectorStore.search()` 返回结果中 `question` 和 `answer` 嵌套在 `metadata` 字段下，距离字段名是 `distance` 而非 `score`。

**Tool 对象** `search_faq_tool` — 创建 `Tool` 实例，设置 `name`、`description`、`func`、`parameters` 字段：
- `name="search_faq"`，Agent 按此名称调度
- `description` 说明工具的用途和输入格式
- `func=search_faq`，指向上面的纯函数
- `parameters` 包含 `query`（string，必填）和 `top_k`（integer，可选，默认 5）

### 2.5 完成标志

`search_faq` 函数和 `search_faq_tool.run()` 都能返回正确的检索结果，新增工具只需新建文件（函数 + Tool 对象）即可加入 Agent。

### 2.6 协作提示

本模块创建 `tools/base.py`（ToolParameter 和 Tool 基类）、`tools/faq_search.py`（纯函数 + Tool 对象）、`tools/__init__.py`（导出）。Tool 只是薄封装层，不含业务逻辑；函数和 Tool 对象各自独立。注意 `Tool.run()` 用 `**params` 解包调用原始函数，`to_prompt_desc()` 生成的可读描述会注入 Agent 的 prompt。检索结果格式化时注意字段路径为 `metadata.question` / `metadata.answer`，距离字段为 `distance`。

### 2.7 常见错误

- 在 Tool 基类中写业务逻辑（Tool 是纯框架代码）
- 工具中 import Agent 或 domain 的内容（工具是最底层，不知道上层存在）

---

## 步骤3：会话管理模块

> **本步骤需要新建的目录和文件**：`utils/__init__.py`、`utils/conversation.py`、`infrastructure/database.py`、`infrastructure/models.py`。

会话的持久化存储和 LLM 上下文构建分为两层：

- `infrastructure/database.py` + `infrastructure/models.py` — 纯数据持久化：建表、DB 连接
- `utils/conversation.py` — `ConversationManager`：对 infrastructure ORM 的封装，提供会话 CRUD 和上下文窗口截取

ConversationManager 与 `tools/`、`llm/` 同级，通过 infrastructure 的 ORM 模型间接操作数据库，不直接写 SQL。

> **PostgreSQL 依赖**：数据库采用 PostgreSQL，需要安装 `psycopg2`（同步）或 `asyncpg`（异步）作为数据库驱动。`infrastructure/database.py` 中使用连接池管理连接，`__init__()` 中自动建表。后续计划将向量存储也迁移到 PostgreSQL（利用 `pgvector` 扩展），届时 RAG 模块的向量检索与对话数据将统一在同一数据库中，简化运维。

### 3.1 概念区分

```
会话记录（SQL 里存的东西）           LLM 上下文（prompt 里的东西）
─────────────────────────           ──────────────────────────
完整的对话历史                      最近 N 轮的 messages 数组
用于审计、回顾、恢复会话             用于让 LLM 理解"刚才在聊什么"
持久化，不会丢失                    临时的，每次请求重新构建
```

**数据流**：请求进来 → 从 SQL 读最近 N 轮 → 格式化为上下文字符串 → 替换 prompt 中的 `{context}` 占位符 → 发给 LLM → LLM 回复 → 写入 SQL。

### 3.2 数据模型

行级存储，两张表：

```sql
-- 会话元数据
CREATE TABLE conversations (
    id               SERIAL PRIMARY KEY,           -- 内部自增主键
    conversation_id  VARCHAR(36),                   -- 业务 UUID，对外暴露
    user_id          VARCHAR(128),                  -- 用户标识
    title            TEXT,                          -- 首轮对话自动截取作为标题
    status           VARCHAR(16) DEFAULT 'active',  -- active / closed
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
);

-- 消息明细
CREATE TABLE messages (
    id               SERIAL PRIMARY KEY,
    conversation_id  VARCHAR(36),
    role             VARCHAR(16) CHECK(role IN ('user', 'assistant', 'system')),
    content          TEXT,
    turn_number      INTEGER,                   -- 轮次序号，同轮 user 和 assistant 共享
    metadata         JSONB,                     -- 预留：{"action_type": "ask_user"}
    created_at       TIMESTAMP DEFAULT NOW()
);
```

> **UUID 生成**：`conversation_id` 由应用层生成（Python `uuid.uuid4()` 或 PostgreSQL `gen_random_uuid()`），作为对外暴露的业务标识。`id` 仅作为内部自增主键，不对外暴露。区分两者的目的：自增 `id` 高效索引，UUID `conversation_id` 避免遍历攻击且便于分布式扩展。

**role 说明**：

| role | 用途 | 示例 |
|------|------|------|
| `user` | 用户发送的消息 | "怎么退款" |
| `assistant` | Agent 返回的消息（AskUser 反问 或 Finish 答案） | "请问您是..." |
| `system` | 会话元信息（如 prompt 版本、知识库版本） | "客服v2.3 \| FAQ版本: 2024Q3" |

ReAct 内部的 Thought / Action / Observation 是 Agent 的**内存工作状态**，存储在 `step_history` 列表中，不写入 SQL。

**为什么用行级而非 JSON 文档**：

- 窗口截取简单：`ORDER BY turn_number DESC LIMIT N * 2` 即取最近 N 轮（每轮 user + assistant = 2 条）
- 未来可扩展：按角色统计、对话质量分析、检索历史消息
- 追加写入：不产生整文档覆盖的并发问题

**多轮对话的关系维护**：通过 `(conversation_id, turn_number)` 组合。同一轮对话的 user 消息和 assistant 消息共享同一个 `turn_number`。

turn_number=1: user="怎么退款",          assistant="请问您是退货还是退款？"  
turn_number=2: user="退货退款",          assistant="好的，退货流程是..."  
turn_number=3: user="需要什么条件",      assistant="您需要在7天内..."

**`add_message()` 中 turn_number 的自动计算**：查询当前会话的最大 turn_number，role 为 `"user"` 时 +1（开启新轮次），role 为 `"assistant"` 时复用当前值。用角色驱动而非"看上一条"的原因：如果 Agent 回复前崩溃（user 已写入但 assistant 未写入），下一条 user 消息仍能正确开启新轮次。




### 3.3 ConversationManager 接口

`ConversationManager` 类接收数据库连接配置和 `max_context_turns` 构造参数。`__init__()` 中自动建表（`CREATE TABLE IF NOT EXISTS`）。

| 方法 | 职责 |
|------|------|
| `create(user_id) -> str` | 新建会话，生成 UUID 作为 conversation_id 并返回 |
| `add_message(conversation_id, role, content, metadata=None) -> int` | 追加消息，自动计算 turn_number |
| `get_context(conversation_id) -> list[dict]` | 取最近 max_context_turns 轮，按时间正序返回 |
| `get_history(conversation_id) -> list[dict]` | 获取完整会话历史，不受轮数限制 |
| `list_conversations(user_id) -> list[dict]` | 列出用户的所有会话 |
| `close(conversation_id)` | 关闭会话 |

### 3.4 上下文注入方式

职责边界：`ConversationManager.get_context()` 只负责从 SQL 取数据并截取窗口，返回结构化列表 `[{role, content}, ...]`，不做格式化。将列表格式化为纯文本并替换 prompt 中的占位符是调用方的职责，应在调用 LLM 前完成。完整数据流为：请求进入 → 从 SQL 读取最近 N 轮 → 将结构化列表格式化为纯文本 → 替换 prompt 中的 `{context}` 占位符 → 发给 LLM → LLM 回复 → 写入 SQL。

### 3.5 完成标志

`ConversationManager` 的 `create()` + `add_message()` + `get_context()` 端到端跑通，超过窗口限制的旧消息不出现在上下文结果中，完整历史可通过 `get_history()` 获取。

### 3.6 协作提示

本模块是会话管理层，需要有一个会话表（conversations）记录会话基本信息，一个消息表（messages）作为子表记录用户和模型对话的具体内容。turn_number 由 `add_message()` 按角色自动计算（user +1，assistant 复用当前值）。ConversationManager 只负责存储和上下文截取，不涉及 LLM 调用和 prompt 模板。

### 3.7 常见错误

- 把 LLM 调用或 prompt 模板写进 ConversationManager（它只管存储和上下文）
- 把 Thought / Action / Observation 写入 SQL（它们是 Agent 内存状态，不是对话 transcript）

---

## 步骤4：模型层 —— LLM 调用封装

> **无需新建文件**：`llm/` 目录及文件已在步骤1 中从 `model/` 迁移完成。本步骤确认 `__init__.py` 的模块单例导出，并根据需要调整接口。

步骤1 已将原 guide.md 中 `model/chat.py` 移动到 `llm/client.py`。本步骤确认 `llm/` 模块的公开接口和模块单例导出方式。

本模块提供两个核心方法：`chat(prompt, system_prompt=None) -> str`（非流式调用）和 `stream(prompt, system_prompt=None)`（流式调用，当前可选）。配置通过环境变量注入（`LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL` 等），使用 OpenAI 兼容 SDK 对接。重试策略：网络超时和限流时指数退避重试，认证错误直接抛出。Agent 层只依赖 `chat()` 方法，`stream()` 为后续预留。

`llm/__init__.py` 以模块级单例导出实例，其他模块通过 `from llm import chat_service` 调用。

### 4.1 完成标志

`from llm import chat_service` 正常 import，`chat_service.chat("你好")` 返回 LLM 响应文本。

### 4.2 协作提示

本模块已在步骤1 从 `model/` 迁移完成，`chat()` 方法签名保持不变，Agent 层仅需非流式调用。

---

## 步骤5：领域层 —— ReAct Agent（基础）

> **本步骤需要新建的目录和文件**：`domain/__init__.py`、`domain/customer_service/__init__.py`、`domain/customer_service/agent.py`、`domain/customer_service/prompts.py`。

这是本次扩展的核心。Agent 层负责理解用户意图、决定行动（检索 FAQ / 给出答案）、编排工具调用。

本步骤先实现最基础的 ReAct 循环——`search_faq`（检索）+ `Finish`（回答）。跑通后再按附录 E 叠加反问能力。

### 5.1 ReAct 范式

Agent 使用 ReAct（Reasoning + Acting）范式编排行为。每次循环中，LLM 输出一个 `Thought`（分析当前状态）+ 一个 `Action`（决定下一步行动）：

```
循环:
  Thought: 分析当前状态，决定下一步
  Action:
    search_faq[检索词]    → Observation: 检索结果 → 继续循环
    Finish[最终答案]       → 结束循环，返回答案
```

核心执行链路：用户输入 → Agent 判断意图 → 调用 `search_faq` 检索 → 获取 Observation → 基于结果用 `Finish` 给出最终答案。

> **完成本步骤后**，参考[附录 E](#e-扩展反问能力) 追加 `AskUser` 反问能力。

### 5.2 Agent 类设计

需要创建两个类：`AgentResponse`（响应体）和 `CustomerServiceAgent`（Agent 主体）。

**AgentResponse** — Agent 处理完用户消息后的返回结果：

| 属性 | 类型 | 说明 |
|------|------|------|
| `type` | `str` | Agent 对 API 层的指令，基础阶段固定为 `"final_answer"`。后续扩展反问能力时增加 `"ask_user"` |
| `content` | `str` | Agent 返回给用户的文本内容 |
| `conversation_id` | `str` | 所属会话 ID — API 层新建会话时需将此 ID 返回给客户端，后续请求携带此 ID 以延续对话 |
| `metadata` | `dict` | **[预留]** 结构化附加数据（如订单 ID、商品链接），当前阶段为 `None` |

**设计意图**：AgentResponse 不是裸字符串，而是一个带状态标记的结构体。API 层拿到后直接读 `type` 字段即可做分支判断，不需解析 content 文本来猜测对话状态。

> `type` 字段当前只有 `"final_answer"`。附录 E 扩展反问能力时会增加 `"ask_user"` 类型。

**CustomerServiceAgent** — 构造函数需要注入以下依赖：

| 参数 | 说明 |
|------|------|
| `llm` | LLM 客户端实例（来自 `llm/client.py`），提供 `chat(prompt, system_prompt=None) -> str` 方法 |
| `conversation_manager` | `ConversationManager` 实例，负责会话持久化和上下文获取 |
| `tools` | `Tool` 对象列表（如 `[search_faq_tool]`），Agent 可调用的工具集 |
| `system_prompt` | 系统提示词模板，默认使用内置模板 |
| `max_steps` | ReAct 循环最大步数，默认 5，防止无限循环 |

核心入口方法：

```
run(user_input: str, conversation_id: str) -> AgentResponse
```

接收用户消息和会话 ID，返回 AgentResponse。具体流程见 5.3 节。

**step_history**：Agent 在 ReAct 循环中的内存工作状态列表，记录每一步的 Thought / Action / Observation，仅在单次 `run()` 调用期间存在，不写入 SQL。与 messages 表中的对话 transcript（user/assistant 消息）不同，step_history 是 Agent 推理的中间过程，仅供当前轮次的 LLM 看到自己的推理历史。

**Agent 内部能力**：Agent 需具备以下内部能力——按名称查找工具、生成工具描述文本（调用各 Tool 的 `to_prompt_desc()`）、将对话历史格式化为纯文本、按三级优先级（JSON 解析 → 单必填参数映射 → 兜底报错）将 LLM 输出的文本映射为工具参数并调度执行、用正则从 LLM 响应中提取 Thought/Action 结构化信息。工具通过 `self.tools` 列表管理，无需独立的注册中心。

### 5.3 run() 执行流程

`run(user_input, conversation_id) -> AgentResponse` 是 Agent 的核心入口，分为四个阶段：

1. **持久化用户消息**：将 user_input 写入 messages 表
2. **获取对话上下文**：从 SQL 取最近 N 轮历史，格式化为纯文本供 prompt 使用
3. **ReAct 循环**（最多 max_steps 次）：每轮构建 prompt（填充 tools/context/user_input/history 四个占位符）→ 调用 LLM → 解析 Thought/Action → 若 Action 为 `Finish` 则持久化 assistant 消息并返回 AgentResponse；否则调度工具获取 Observation 后继续循环
4. **兜底**：达到 max_steps 仍未 Finish 时，返回 fallback 消息

工具调度失败时，将错误作为 Observation 追加到 step_history，让 LLM 在下一轮自行纠正。

> **关键提醒**：step_history（Thought/Action/Observation）仅存内存不入 SQL；`_parse_output` 解析失败时 `continue` 让 LLM 重试而非崩溃；LLM 输出的 action 为 `Finish` 时才持久化 assistant 消息，工具调用的中间结果不持久化。

### 5.4 System Prompt 设计

Prompt 模板使用 `self.system_prompt.format(...)` 填充，包含四个占位符：

- `{tools}` — 工具描述文本，由 `_build_tools_description()` 生成
- `{context}` — 多轮对话历史（SQL 中取出的最近 N 轮），由 `_format_context()` 格式化为纯文本
- `{user_input}` — 当前用户消息，由 `run()` 的 user_input 参数填入
- `{history}` — 本轮 ReAct 步骤记录（Thought/Action/Observation），初始为空，每步追加

注意 `{context}`（SQL 持久化的对话记录）和 `{history}`（Agent 内存中的推理步骤）是两个不同的概念。Prompt 中应包含角色设定、可用工具说明、工作流程（Thought + Action 格式）和回答规则。模板使用 Python `.format()` 时，非占位符的花括号必须双写转义（如 `{{"key": "value"}}`），否则会报 `KeyError`。

### 5.5 完成标志

`agent.run("退货流程", conversation_id)` 返回 `AgentResponse(type="final_answer")` 且内容基于 FAQ 检索结果，第二轮问答能引用第一轮的上下文。

### 5.6 协作提示

本模块创建 `domain/customer_service/agent.py`（AgentResponse + CustomerServiceAgent）和 `prompts.py`（prompt 模板）。Agent 构造函数注入 llm、conversation_manager、tools 和 system_prompt。`run()` 按"持久化 → 上下文 → ReAct 循环 → 兜底"四阶段执行，内部负责 prompt 构建、LLM 输出解析和工具调度。依赖 tools 层的 Tool 对象调用检索，不直接 import rag。step_history 仅存内存，不写入 SQL。

### 5.7 常见错误

- Agent 直接 import rag.store（应通过 tools 层的 Tool 对象调用）
- 把 Thought/Action/Observation 写入 SQL（它们是 Agent 内存状态）

---

## 步骤6：应用层 —— API 接口服务

> **本步骤需要新建/改写的文件**：项目根目录的 `main.py`、`apps/customer_service/__init__.py`、`apps/customer_service/routes.py`。原有的 `api/` 目录在步骤1 迁移中已删除，本步骤在项目根目录和 `apps/customer_service/` 下重新实现 API。

原 guide.md 的 API 直接依赖 retriever，调整后依赖 Agent。

### 6.1 接口变更

| 原接口 | 新接口 | 说明 |
|--------|--------|------|
| `POST /search` | `POST /chat` | 检索接口改为对话接口 |
| 无 | `POST /conversations` | 新增：创建会话 |
| 无 | `GET /conversations/{id}` | 新增：获取会话历史 |
| 无 | `GET /conversations?user_id=xxx` | 新增：列出用户会话 |

### 6.2 /chat 接口

```
POST /chat
Request:  {"conversation_id": "uuid或空字符串", "message": "用户消息"}
Response: {"type": "ask_user" | "final_answer",
           "content": "...",
           "conversation_id": "uuid"}
```

`conversation_id` 为空时，API 自动创建新会话并在响应中返回。

**Pydantic 模型建议**：

| 模型 | 字段 | 类型 | 说明 |
|------|------|------|------|
| `ChatRequest` | `conversation_id` | `str` | 会话 ID，默认空字符串 `""` |
| | `message` | `str` | 用户消息，不能为空 |
| `ChatResponse` | `type` | `str` | `"ask_user"` 或 `"final_answer"` |
| | `content` | `str` | 反问内容或最终答案 |
| | `conversation_id` | `str` | 会话 ID |
| `CreateConversationRequest` | `user_id` | `str` | 用户标识，不能为空 |

### 6.3 API 层实现

API 层只做三件事：接收参数 → 调用 Service → 格式化响应。`main.py` 是项目中唯一做依赖装配的地方：加载 `.env`，导入单例（`chat_service`），创建需构造函数注入的实例（`ConversationManager`、`CustomerServiceAgent`），注册路由。`/chat` 收到空的 `conversation_id` 时自动创建新会话。

API 依赖链路：**API → Service → Agent → Tools/LLM/Utils**。API 通过 Service 间接使用 Agent，Agent 可被其他 Agent 调用（例如客服 Agent 调用订单查询 Agent），是一个可复用的底层推理组件。

### 6.4 完成标志

`/chat` 接口完成"用户提问 → Agent 检索 FAQ → 返回答案"的完整交互，会话历史可通过接口查询。

### 6.5 协作提示

本模块创建 `main.py`（FastAPI 入口 + 依赖装配）和 `apps/customer_service/routes.py`（四个路由：POST /chat、POST /conversations、GET /conversations/{id}、GET /conversations）。API 层通过 Service 层间接使用 Agent 和其他底层能力，只做参数接收和响应格式化。Agent 是 domain 内的可复用推理组件，不直接暴露给 API。

### 6.6 常见错误

- 在 API 层直接 import rag 或 tools（API 应通过 Service → Agent 间接访问下层模块）
- 在 API 层构建 prompt 或处理会话逻辑（这些是 Service/Agent 和 ConversationManager 的职责）
- 将 Agent 放到 API 或 Service 层（Agent 是底层推理组件，可被多个 Service 或其他 Agent 复用）

---

## 步骤7：方法论 —— 与 AI 协作调试 Agent

### 7.1 让 AI 追踪 Thought 链

Agent 的行为不像检索服务那样可预测。当回答不符合预期时，让 AI 追踪完整的思考链路：

"用户输入是'怎么退'，Agent 的 Thought 是什么？为什么选择了 search_faq（或 AskUser）？如果是 search_faq 没命中，Observation 返回了什么？请追踪每一步的 Thought/Action/Observation。"

### 7.2 先验 prompt，再验逻辑

Agent 出问题时，90% 的情况是 prompt 写得不好。优先让 AI 审查 prompt：

"当前 system prompt 中关于各 Action 的触发条件是否明确？用户说'帮我查一下'时，Agent 应该做什么？prompt 是否有歧义？"

### 7.3 用具体对话案例驱动调试

不要描述"Agent 表现不好"，给具体的对话记录。让 AI 基于真实输入输出分析根因，而不是猜测。

### 7.4 增量验证

每完成一个模块就跑验证脚本。会话存储 → 验证 SQL CRUD。工具层 → 验证函数直接调用和 `tool.run()` 返回一致。Agent → 验证 Finish 分支是否正确返回答案。完成附录 E 后 → 验证 AskUser 分支切换。不要堆到最后才发现问题。

---
