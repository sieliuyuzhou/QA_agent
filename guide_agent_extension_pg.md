# Vibe Coding 实战：为 RAG 服务接入 ReAct Agent 智能客服

## 我们要做什么

在已有的 RAG 检索服务之上，扩展为一个**具备多轮对话和主动反问能力的智能客服 Agent**。

原项目是一个无状态的检索服务：用户提问 → 改写 → 检索 → 返回结果，每次请求彼此独立。智能客服需要在此基础上增加三项关键能力：

1. **会话管理** — 记住"刚才说了什么"，多轮对话不丢失上下文
2. **Agent 编排** — 不再是无脑检索，而是由 Agent 判断意图、选择行动（检索 / 反问 / 回答）
3. **主动反问** — 用户意图模糊时，Agent 向用户提问澄清，而非强行猜测

### 1.1 与原 guide.md 的关系

本文件是对 [guide.md](guide.md) 的**增量扩展**，而非替代。已在 guide.md 中完成的模块（rag 向量存储）保持不变。同时，对项目目录结构做一次重组，为后续扩展（订单查询、物流跟踪等）预留位置。

| 模块 | 原 guide.md | 本次变更 |
|------|-----------|---------|
| rag | FAQ 向量入库与检索 | **不变**（数据已导入，复用现有检索接口） |
| llm | 属于 model 模块 | **独立**：从 model 中拆出，作为独立目录；`__init__.py` 以模块级单例导出，替换原工厂函数 |
| model/conversation | 不存在 | **新增**：会话持久化存储与 LLM 上下文构建 |
| retriever | 查询改写 + 检索编排 | **重构**：简化为单一检索 Tool，去掉改写和编排 |
| agent | 不存在 | **新增**：ReAct Agent，编排工具调用，支持反问 |
| api | 直接依赖 retriever | **调整**：依赖 Agent 而非 retriever |

### 1.2 四层架构

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

### 1.3 依赖方向

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

### 1.4 模块边界原则（沿用）

1. **单向依赖**：依赖关系只能从上往下，禁止反向依赖或循环依赖
2. **模块公开接口隔离**：模块间只通过 `__init__.py` 的导出来交互，禁止 import 其他模块的内部文件
3. **配置隔离**：每个模块用独立前缀的环境变量（如 `LLM_*` / `RAG_*` / `CONVERSATION_*`），避免冲突

### 1.5 开发建议

- 构建顺序：infrastructure → tools / llm / utils → domain → apps（对应步骤1 → 步骤2-5 → 步骤6 → 步骤7）
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

将目录重映射表（见 1.1）交给 LLM 执行迁移。你需要让 LLM 明确以下要点：

1. 在项目根目录下创建新目录结构（`apps/`, `domain/`, `tools/`, `llm/`, `utils/`, `infrastructure/` 及其子目录——仅创建空目录和 `__init__.py`，不创建模块文件）
2. 移动 `model/` → `llm/`，并更新所有旧 import 路径为新的模块级单例导出方式
3. 移动 `rag/` → `infrastructure/rag/`，更新 import（其他模块中 `from rag` → `from infrastructure.rag`），`__init__.py` 改为模块级单例导出
4. 更新 `scripts/` 目录中的 import 路径（`start_server.py`、`import_faq.py`）
5. 删除 `retriever/` 目录

> **重要**：原 `model/__init__.py` 中的 `get_service()` 工厂函数，迁移到 `llm/__init__.py` 后改为模块级单例：直接创建 `ChatService`（或 `LLMClient`）实例作为模块变量导出。同理，`infrastructure/rag/__init__.py` 中的工厂函数也改为模块级单例。后续步骤中新增的模块文件（如 `tools/base.py`、`domain/customer_service/agent.py` 等）在各自的步骤中按需创建，不在本步处理。

### 1.3 import 路径变更速查

| 旧 import | 新 import |
|-----------|-----------|
| `from model.chat import ChatService` | `from llm import chat_service`（模块级单例，类名可改为 `LLMClient`） |
| `from model import get_service` | 不再使用，改为 `from llm import chat_service` |
| `from rag import get_store` | `from infrastructure.rag import vector_store`（模块级单例） |
| `from rag.store import VectorStore` | `from infrastructure.rag import VectorStore` |
| `from retriever import get_pipeline` | 不再使用，由 Agent 替代 |
| `scripts/` 中任何 `from model.xxx` | 对应改为 `from llm` |
| `scripts/` 中任何 `from rag.xxx` | 对应改为 `from infrastructure.rag` |

> **注意**：`.env` 中已有的 `LLM_*` 和 `RAG_*` 环境变量无需修改。新增的 `CONVERSATION_*` 变量（如 `CONVERSATION_DB_PATH`）在开发会话管理模块时按需添加。项目提供了 `.env.example` 作为环境变量模板（可提交 git），请将其复制为 `.env` 并填入你自己的 API Key。`.env` 包含密钥，**不应提交到 git**。

### 1.4 校验脚本

完成目录重组后，编写校验脚本确认迁移无断裂。脚本需检查：

> 本步骤只验证目录迁移和 `llm` / `rag` 相关导入；`tools` 相关验证放到步骤2完成后。

1. **旧目录已移除**：`model/` 不包含 `chat.py`（文件已移走），`retriever/` 已删除
2. **新目录结构完整**：`apps/`, `domain/`, `tools/`, `llm/`, `utils/`, `infrastructure/` 及子目录均已创建（仅目录和 `__init__.py`，模块文件在后续步骤中按需创建）
3. **关键 import 可解析**：尝试分别 import 以下模块，确认不报 `ModuleNotFoundError`：
   - `from llm import chat_service`（模块级单例，不报错即可）
   - `from infrastructure.rag import vector_store`（模块级单例）
4. **`.env` 文件存在**且 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL` 均已配置

> 编写脚本时逐项检查，每通过一项打印确认信息。任一项失败则脚本以非零 exit code 退出。

---

## 步骤2：工具层 —— Tool 基类与注册模式

> **本步骤需要新建的目录和文件**：`tools/__init__.py`、`tools/base.py`。`tools/faq_search.py` 在步骤2.4 中创建。

工具层是连接 Agent 和后端代码的桥梁。核心设计：**函数和 Tool 对象分离**。函数是纯 Python，任何模块都能 import 直接调用；Tool 对象是对函数的薄封装，供 Agent 按名称调度。两者互不污染。

### 2.1 设计目标与思路

**目标**：Agent 需要调用后端的业务函数（如检索 FAQ），但不能直接耦合。需要的是一套薄封装机制，让函数和 Agent 各自独立，互不侵入。

**设计思路**：

- **函数与 Tool 对象分离**：写一个纯 Python 函数（如 `search_faq(query, top_k)`），它和 Agent 无关，后端任何模块都能直接 import 调用。再为它创建一个 `Tool` 对象（如 `search_faq_tool`），描述函数的名称、参数和用途，供 Agent 按名称调度。

- **参数通过构造函数传入**：创建 `Tool` 时把参数列表（name、type、description、是否必填）作为属性传入。Tool 只负责参数签名校验和实际调用转发，不含任何业务逻辑。

- **工具列表由 Agent 直接管理**：Agent 维护一个 `self.tools = [...]` 列表。新增工具只需新建一个文件（函数 + Tool 对象），然后追加到列表中。不引入独立的注册中心。

- **Agent 调用入口唯一**：Agent 始终通过 `tool.run(params: dict) -> str` 调用工具，不用关心内部函数签名。后端代码则直接 import 原始函数调用，不走 Tool 对象。

- **预留迁移路径**：在 Tool 基类预留 `to_openai_schema()` 方法签名（暂不实现）。当前 Agent 使用正则解析 LLM 输出，未来如需切换为 OpenAI 原生 function calling，只需实现此方法，工具和 Agent 的其他代码不变。

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

这一步在 Agent 的工具调度方法中完成（见步骤6），不在 Tool 基类中。

### 2.4 工具实现：函数 + Tool 对象分离注册

以 FAQ 检索工具为例，在 `tools/faq_search.py` 中完成两部分：

**第一部分：纯函数**

```python
def search_faq(query: str, top_k: int = 5) -> str:
    """检索 FAQ 知识库，返回格式化的检索结果。纯函数，不依赖 Agent。"""
```

函数职责：
1. 创建 `VectorStore` 实例，调用 `store.search(query, top_k=top_k)`
2. 将检索结果格式化为易读文本返回（供 LLM 理解）
3. 无结果时返回提示文本（如 `"未找到相关FAQ条目。"`）

> **容易踩的坑**：`VectorStore.search()` 返回的结果中，`question` 和 `answer` 嵌套在 `metadata` 字段下，距离字段名是 `distance` 而非 `score`。格式化时注意字段路径——先用一条真实查询确认返回结构再写代码。

**第二部分：Tool 对象**

创建 `search_faq_tool = Tool(...)` 实例：
- `name="search_faq"`
- `description` 需清楚说明工具的用途和输入格式
- `func=search_faq`（指向上面的纯函数）
- `parameters` 包含两个：`query`（string，必填）和 `top_k`（integer，可选，默认 5）

### 2.5 两种调用路径

同一个 `search_faq` 函数，两套调用路径互不耦合：

```
后端代码                               Agent
────────                              ─────
from tools.faq_search import          from tools.faq_search import
  search_faq    ← 纯函数                  search_faq_tool  ← Tool 对象

result = search_faq(                   observation = search_faq_tool.run(
    query="退货流程",                       {"query": "退货流程"}
    top_k=5                            )
)
```

新增工具时：写一个纯函数 → 创建一个 Tool 对象 → 加入 Agent 的 `self.tools` 列表。函数本身零框架侵入。

### 2.6 完成标志

- `Tool` 基类和 `ToolParameter` 可正常使用
- `search_faq` 函数可以被直接 import 调用，返回正确的检索结果
- `search_faq_tool.run({"query": "x"})` 返回相同结果
- `to_prompt_desc()` 输出格式正确，可直接拼入 prompt
- 新增工具只需新建文件（函数 + Tool 对象），不修改基类
- 完成步骤2后，再验证 `from tools.base import Tool, ToolParameter` 与 `from tools.faq_search import search_faq, search_faq_tool` 可以正常 import

### 2.7 AI 协作提示

将以下信息提供给 LLM：

**已有条件**：
- `infrastructure/rag/` 中的 `VectorStore` 已就绪，`vector_store.search(query, top_k)` 返回检索结果列表（每条结果含 `metadata.question`、`metadata.answer`、`distance` 字段）

**需要创建的内容**：
- `tools/base.py`：`ToolParameter`（属性：name/type/description/required/default）和 `Tool`（属性：name/description/parameters/func；方法：run/to_prompt_desc/to_openai_schema）
- `tools/faq_search.py`：纯函数 `search_faq(query, top_k)` + Tool 对象 `search_faq_tool`
- `tools/__init__.py`：导出 Tool、ToolParameter、search_faq、search_faq_tool

**关键约束**：
- `Tool.run(params: dict)` 用 `self.func(**params)` 解包调用原始函数
- `to_prompt_desc()` 输出格式：`- name(param: type, ...): description`，可选参数标注"（可选）"
- `to_openai_schema()` 仅保留方法签名，返回空字典即可，暂不实现
- `search_faq` 函数将检索结果格式化为文本时，注意字段路径：结果条目 `.get("metadata", {}).get("question")` / `"answer"`，距离字段是 `"distance"`
- 函数和 Tool 对象是两个独立的东西：函数供后端 import 调用，Tool 对象供 Agent 调度

**完成标志**：
- `from tools.base import Tool, ToolParameter` 不报错
- `from tools.faq_search import search_faq, search_faq_tool` 不报错
- `search_faq("退货流程")` 返回格式化文本结果
- `search_faq_tool.run({"query": "退货流程"})` 返回相同结果
- `search_faq_tool.to_prompt_desc()` 输出可拼接进 prompt 的文本

### 2.8 常见偏差

- 在 Tool 基类中直接写业务逻辑（Tool 是纯框架代码，不含任何业务）
- 工具（tools/）中 import Agent 或 domain 的内容（工具是最底层，不知道上层存在）
- 忘记同时创建 Tool 对象（只写了函数 Agent 无法调度）

---

## 步骤3：基础设施层 —— RAG 向量存储

> **如果你已完成 guide.md 第三章的全部内容（FAQ 数据已入库、`VectorStore.search()` 可正常检索），直接跳过本章。**

保持 guide.md 第三章的实现不变。FAQ 数据已导入，嵌入模型和向量检索接口已就绪。

本模块对外暴露的核心接口：

```python
# infrastructure/rag/__init__.py 导出模块级单例
from .store import VectorStore

vector_store = VectorStore()  # 模块单例，全局唯一

# 使用方式
results = vector_store.search(query_text, top_k=5)
# 返回: [{"id": "faq_001", "content": "问题: ...\n答案: ...", "metadata": {"question": "...", "answer": "..."}, "distance": 0.95}, ...]
# 注意：question 和 answer 嵌套在 metadata 下，距离字段名为 distance（不是 score）
```

> 在步骤1 的迁移中，`infrastructure/rag/__init__.py` 已改为模块级单例 `vector_store`，替换原 `get_store()` 工厂函数。

后续所有检索需求均通过此接口完成，不做多策略扩展。

---

## 步骤4：会话管理模块

> **本步骤需要新建的目录和文件**：`utils/__init__.py`、`utils/conversation.py`、`infrastructure/database.py`、`infrastructure/models.py`。

会话的持久化存储和 LLM 上下文构建分为两层：

- `infrastructure/database.py` + `infrastructure/models.py` — 纯数据持久化：建表、DB 连接
- `utils/conversation.py` — `ConversationManager`：对 infrastructure ORM 的封装，提供会话 CRUD 和上下文窗口截取

ConversationManager 与 `tools/`、`llm/` 同级，通过 infrastructure 的 ORM 模型间接操作数据库，不直接写 SQL。

### 4.1 概念区分

```
会话记录（SQL 里存的东西）           LLM 上下文（prompt 里的东西）
─────────────────────────           ──────────────────────────
完整的对话历史                      最近 N 轮的 messages 数组
用于审计、回顾、恢复会话             用于让 LLM 理解"刚才在聊什么"
持久化，不会丢失                    临时的，每次请求重新构建
```

**数据流**：请求进来 → 从 SQL 读最近 N 轮 → 格式化为上下文字符串 → 替换 prompt 中的 `{context}` 占位符 → 发给 LLM → LLM 回复 → 写入 SQL。

### 4.2 数据模型

行级存储，两张表：

```sql
-- 会话元数据
CREATE TABLE conversations (
    id          TEXT PRIMARY KEY,          -- UUID
    user_id     TEXT NOT NULL,             -- 用户标识
    title       TEXT,                      -- 首轮对话自动截取作为标题
    status      TEXT DEFAULT 'active',     -- active / closed
    created_at  TEXT DEFAULT (datetime('now')),
    updated_at  TEXT DEFAULT (datetime('now'))
);

-- 消息明细
CREATE TABLE messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL,
    role            TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,
    turn_number     INTEGER NOT NULL,     -- 轮次序号，同轮 user 和 assistant 共享
    metadata        TEXT,                 -- JSON 字符串，预留：{"action_type": "ask_user"}
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

CREATE INDEX idx_messages_conv ON messages(conversation_id, turn_number);
```

> **metadata 字段说明**：SQLite 不支持 dict 类型，写入前需用 `json.dumps(metadata)` 序列化为 JSON 字符串，读取后用 `json.loads()` 还原为 dict。metadata 为 `None` 时存入 SQL `NULL`。
```

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

```
turn_number=1: user="怎么退款",          assistant="请问您是退货还是退款？"
turn_number=2: user="退货退款",          assistant="好的，退货流程是..."
turn_number=3: user="需要什么条件",      assistant="您需要在7天内..."
```

**`add_message()` 中 turn_number 的自动计算逻辑**：

```
add_message(conversation_id, role, content):

  查询该会话当前的 max(turn_number)：
    SELECT COALESCE(MAX(turn_number), 0) FROM messages WHERE conversation_id = ?

  如果 role == "user"（用户发起新一轮发言）：
      → turn_number = max + 1
      → 如果这是该会话第一条消息（max 为 0），则 turn_number = 1

  如果 role == "assistant"（Agent 完成当前轮回复）：
      → turn_number = max（复用当前轮次，该轮次由前一条 user 消息开启）
```

> **为什么用角色驱动而非"看上一条"**：如果 Agent 在回复前崩溃（user 已写入但 assistant 未写入），下一条 user 消息仍然正确开启新轮次。用角色判断把"谁开启新一轮"的决定权交给写入逻辑本身，不依赖历史表的整洁程度。

### 4.3 ConversationManager 接口

```python
# utils/conversation.py

class ConversationManager:
    def __init__(self, db_path: str, max_context_turns: int = 10):
        """
        db_path: SQLite 数据库文件路径
        max_context_turns: 发给 LLM 的最大对话轮数
        """

    def create(self, user_id: str) -> str:
        """新建会话，返回 conversation_id"""

    def add_message(self, conversation_id: str, role: str,
                    content: str, metadata: dict = None) -> int:
        """
        追加一条消息。
        自动计算 turn_number：同轮 assistant 消息复用最近一条 user 的 turn_number。
        """

    def get_context(self, conversation_id: str) -> list[dict]:
        """
        取最近 max_context_turns 轮对话。

        返回格式: [{"role": "user", "content": "..."},
                   {"role": "assistant", "content": "..."}, ...]
        按 turn_number ASC 排序（时间正序）。
        """

    def get_history(self, conversation_id: str) -> list[dict]:
        """获取完整会话历史（不受 max_context_turns 限制，用于前端展示）"""

    def list_conversations(self, user_id: str) -> list[dict]:
        """列出用户的所有会话"""

    def close(self, conversation_id: str):
        """关闭会话"""
```

**实现要点**：

- 使用 Python 标准库 `sqlite3`，无需额外依赖。
- `__init__()` 中需完成建表逻辑：若数据库文件所在目录不存在则自动创建（`Path(db_path).parent.mkdir(parents=True, exist_ok=True)`），然后执行 `CREATE TABLE IF NOT EXISTS` 创建 4.2 节中定义的 `conversations` 和 `messages` 两张表。
- 若你对 sqlite3 不熟悉，可参考以下模式：在 `__init__` 中用 `sqlite3.connect(db_path)` 获取连接，创建游标执行 DDL，最后 `commit()`。之后每个 CRUD 方法内部建立连接、执行 SQL、提交、关闭。

### 4.4 上下文注入方式

**职责边界**：

- `ConversationManager.get_context()` 只负责从 SQL 取数据并截取窗口，返回结构化列表 `[{role, content}, ...]`。**不做格式化**。
- 将结构化列表格式化为纯文本（`用户: xxx\n客服: xxx`）是 **Agent 的 `_format_context()` 方法**的职责（见步骤6）。
- Prompt 模板的 `{context}` 占位符替换也在 Agent 的 `run()` 中完成。

以下展示从取数据到注入 prompt 的完整链路（具体实现在 Agent 侧）：

```python
# 1. 从 SQL 取最近 N 轮
rows = cm.get_context(conversation_id)

# 2. 格式化为纯文本
context_lines = []
for msg in rows:
    label = "用户" if msg["role"] == "user" else "客服"
    context_lines.append(f"{label}: {msg['content']}")
context_text = "\n".join(context_lines)

# 3. 替换 prompt 模板中的占位符
prompt = PROMPT_TEMPLATE.format(
    tools=tools_desc,
    user_input=user_message,
    context=context_text,       # ← 占位符被替换
    history=step_history,
)
```

最终注入 LLM 的上下文形如：

```
用户: 我要退
客服: 请问您是想办理退货还是退款呢？
用户: 退货
```

LLM 看到这段就理解了对话的延续关系。

### 4.5 完成标志

- SQLite 数据库自动创建，conversations 和 messages 两张表结构正确
- `create()` + `add_message()` + `get_context()` 端到端跑通
- 上下文窗口截取正确（超过 10 轮的旧消息不出现在 `get_context()` 中）
- 完整历史通过 `get_history()` 仍可获取（截取仅影响发给 LLM 的上下文）

### 4.6 AI 协作提示

将以下信息提供给 LLM：

**已有条件**：
- 无需依赖其他模块，使用 Python 标准库 `sqlite3` 即可
- 数据库文件路径由构造函数参数 `db_path` 指定（如 `"./data/conversations.db"`）

**需要创建的内容**：
- `infrastructure/database.py`：`get_connection(db_path)` 函数，封装 `sqlite3.connect()`，返回连接对象
- `infrastructure/models.py`：定义简单的数据类（dataclass）`Conversation` 和 `Message`，字段与 4.2 节表结构一致
- `utils/conversation.py`：`ConversationManager` 类，实现 `create` / `add_message` / `get_context` / `get_history` / `list_conversations` / `close` 六个方法
- `utils/__init__.py`：导出 `ConversationManager`

**关键约束**：
- `__init__()` 中调用 `Path(db_path).parent.mkdir(parents=True, exist_ok=True)` 确保目录存在，然后执行 `CREATE TABLE IF NOT EXISTS` 建表
- `add_message()` 的 turn_number 计算：`SELECT COALESCE(MAX(turn_number), 0) FROM messages WHERE conversation_id = ?`，role 为 `"user"` 时 +1，role 为 `"assistant"` 时复用当前值
- `get_context()` 截取最近 N 轮：`SELECT ... FROM messages WHERE conversation_id = ? ORDER BY turn_number DESC LIMIT ? * 2`，得到结果后再按 `turn_number ASC` 排序返回（保证时间正序）
- `get_history()` 与 `get_context()` 逻辑相同但不限行数，返回完整历史
- metadata 字段为预留，当前传 `None` 即可；若需要写入 dict，用 `json.dumps()` 序列化
- 每个 CRUD 方法内部建立连接、执行 SQL、提交、关闭（不使用长连接）
- ConversationManager 只负责存储和上下文构建，不涉及 LLM 调用，不涉及 prompt 模板

**完成标志**：
- `from utils import ConversationManager` 不报错
- SQLite 数据库文件自动创建，conversations 和 messages 两张表结构正确
- `create()` + `add_message()` + `get_context()` 端到端跑通
- `get_context()` 只返回最近 N 轮，超出的旧消息不出现
- `get_history()` 返回完整历史

### 4.7 常见偏差

- 把 LLM 调用逻辑写进 ConversationManager（它只管存储和上下文）
- 把 prompt 模板写进 ConversationManager（system prompt 由 Agent 层提供）
- 用 JSON 文档存整个会话（不利于窗口截取和未来扩展）
- 把 Thought / Action / Observation 写入 SQL（它们是 Agent 内存状态，不是对话 transcript）

---

## 步骤5：模型层 —— LLM 调用封装

> **无需新建文件**：`llm/` 目录及文件已在步骤1 中从 `model/` 迁移完成。本步骤确认 `__init__.py` 的模块单例导出，并根据需要调整接口。

步骤1 已将原 guide.md 中 `model/chat.py` 移动到 `llm/client.py`。本步骤确认 `llm/` 模块的公开接口和模块单例导出方式。

**需要提供的接口**：

| 方法 | 说明 |
|------|------|
| `chat(prompt: str, system_prompt: str = None) -> str` | 非流式调用，传入用户提示词和可选的系统提示词，返回 LLM 的完整响应文本 |
| `stream(prompt: str, system_prompt: str = None)` | 流式调用，yield 文本片段（当前阶段可选，后续用于打字机效果） |

**配置项**（通过构造函数参数或环境变量注入）：

| 配置 | 环境变量 | 说明 |
|------|---------|------|
| API Key | `LLM_API_KEY` | 模型 API 密钥 |
| Base URL | `LLM_BASE_URL` | API 端点地址，兼容 OpenAI 接口格式 |
| Model | `LLM_MODEL` | 模型名称 |
| Timeout | `LLM_TIMEOUT` | 请求超时秒数，默认 60 |
| Max Retries | `LLM_MAX_RETRIES` | 重试次数，默认 3 |
| Temperature | — | 生成温度，默认 0.7 |

**实现要点**：

- 使用 OpenAI 兼容 SDK（`openai` 包）对接，因为大多数国产模型提供商的 API 都兼容此格式
- 重试策略：网络超时和限流时指数退避重试，认证错误直接抛出
- 如果原 guide.md 的 `ChatService` 已经实现了上述能力，直接移动文件即可，不修改内部逻辑
- Agent 层只依赖 `chat()` 方法，`stream()` 为后续预留

> **模块公开接口**：`llm/__init__.py` 以模块级单例导出 `LLMClient`（或保留名 `ChatService`）实例。其他模块通过 `from llm import chat_service` 调用，禁止直接 import `llm.client` 等内部文件。模块级单例形式如下：
>
> ```python
> # llm/__init__.py
> from .client import ChatService  # 或 LLMClient
>
> chat_service = ChatService()  # 模块加载时创建，全局唯一
> ```

### 5.1 AI 协作提示

将以下信息提供给 LLM：

**已有条件**：
- `llm/client.py` 已在步骤1 从 `model/chat.py` 迁移完成，原 `ChatService` 类已实现 `chat()` 和 `stream()` 方法
- OpenAI 兼容 SDK（`openai` 包）已安装，配置从环境变量读取

**需要确认/调整的内容**：
- `llm/__init__.py` 中删除原来的工厂函数 `get_service()`，改为模块级单例 `chat_service = ChatService()`（如果类名沿用 `ChatService`）或 `llm_client = LLMClient()`（如果重命名为 `LLMClient`）
- 无论类名是否更改，`chat(prompt, system_prompt=None) -> str` 方法签名不变

**关键约束**：
- 其他模块通过 `from llm import chat_service` 获取单例，不再调用工厂函数
- Agent 层只用 `chat_service.chat(prompt, system_prompt=None) -> str`，`stream()` 为后续预留
- 重试策略保持不变：网络超时和限流时指数退避重试，认证错误直接抛出

**完成标志**：
- `from llm import chat_service` 不报错
- `chat_service.chat("你好")` 返回 LLM 响应文本

---

## 步骤6：领域层 —— ReAct Agent（基础）

> **本步骤需要新建的目录和文件**：`domain/__init__.py`、`domain/customer_service/__init__.py`、`domain/customer_service/agent.py`、`domain/customer_service/prompts.py`。

这是本次扩展的核心。Agent 层负责理解用户意图、决定行动（检索 FAQ / 给出答案）、编排工具调用。

本步骤先实现最基础的 ReAct 循环——`search_faq`（检索）+ `Finish`（回答）。跑通后再按附录 E 叠加反问能力。

### 6.1 ReAct 范式

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

### 6.2 Agent 类设计

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

接收用户消息和会话 ID，返回 AgentResponse。具体流程见 6.3 节。

**Agent 内部需要实现以下辅助方法**：

| 方法 | 职责 | 一句话说明 |
|------|------|-----------|
| `_find_tool(name)` | 按名称查找工具 | 遍历 `self.tools`，匹配 `name` 属性 |
| `_build_tools_description()` | 生成工具描述文本 | 遍历所有 Tool，调用各自的 `to_prompt_desc()`，用换行拼接 |
| `_format_context(msgs)` | 格式化对话历史 | 将 `get_context()` 返回的 `[{role, content}]` 转为纯文本（如 `用户: xxx\n客服: xxx`） |
| `_dispatch_tool(name, input_text)` | 调度工具调用 | 先按名查找 Tool，再将 input_text 映射为参数后调用 `tool.run()` |
| `_parse_output(text)` | 解析 LLM 响应 | 从 LLM 输出文本中提取 `Thought` 和 `Action`（正则匹配 `Thought:` / `Action:` 行） |
| `_parse_action_input(text)` | 提取 Action 参数 | `Finish[答案]` → `"答案"` |
| `_parse_tool_action(text)` | 提取工具调用信息 | `search_faq[退货]` → `("search_faq", "退货")` |

**参数智能映射策略**（`_dispatch_tool` 中使用）：

解析 LLM 输出的工具输入文本（如 `"退货流程"` 或 `"{\"query\":\"退货\"}"`）时，按优先级尝试：

1. **JSON 解析**：如果文本以 `{` 开头，尝试 `json.loads()` 解析为 dict → 传入 `tool.run(dict)`
2. **单必填参数映射**：如果工具只有一个必填参数，将整段文本作为该参数的值
3. **兜底**：返回错误提示（需要结构化参数）

**工具管理方式**：工具通过 `self.tools` 列表管理，**不需要独立的 ToolRegistry**。新增工具只需追加到列表中，不修改 Agent 框架代码。

### 6.3 run() 执行流程

`run()` 是 Agent 的核心入口，接收用户消息和会话 ID，返回 AgentResponse。一次调用的完整数据流如下：

```
用户输入 (user_input) + 会话ID (conversation_id)
  │
  ├─ 阶段1: 持久化用户消息 → 写入 SQL (messages 表, role="user")
  │
  ├─ 阶段2: 获取对话上下文 → 读 SQL (最近 N 轮) → _format_context() 格式化为纯文本
  │
  └─ 阶段3: ReAct 循环 (最多 max_steps 次)
       │
       ├─ 3a. 构建 prompt
       │    取 system_prompt 模板
       │    → self.system_prompt.format(tools=..., context=..., user_input=..., history=...)
       │    → 得到填充后的完整 prompt 字符串作为 user_prompt
       │
       ├─ 3b. 调用 LLM
       │    self.llm.chat(prompt=user_prompt, system_prompt=system_prompt)
       │    → 解析 Thought / Action
       │
       ├─ 3c. 判断 Action
       │    Finish → 持久化 assistant → return AgentResponse("final_answer", ...)
       │    其他 → 进入工具调度 (3d)
       │
       └─ 3d. 工具调度
            _dispatch_tool(name, input) → tool.run(params) → Observation
            → 追加到 step_history → 继续下一轮循环
```

实现时需完成以下四个阶段：

**阶段 1：持久化用户消息**

调用 `self.cm.add_message(conversation_id, "user", user_input)` 将用户消息写入 SQL。

**阶段 2：构建上下文**

- 调用 `self.cm.get_context(conversation_id)` 获取最近 N 轮历史对话
- 调用 `_format_context()` 将 `[{role, content}]` 格式化为纯文本（供 prompt `{context}` 占位符使用）

**阶段 3：ReAct 循环**（核心）

```
┌─────────────────────────────────────────────────────┐
│  FOR step = 1 to max_steps:                         │
│                                                     │
│    ┌─ 3a. 构建 prompt ──────────────────────────┐  │
│    │  使用 self.system_prompt.format(...)        │  │
│    │  填充 {tools} {context} {user_input}        │  │
│    │  {history}（step_history 拼接）             │  │
│    │  → 填充后的完整字符串作为 user_prompt       │  │
│    └────────────────────────────────────────────┘  │
│         ↓                                          │
│    ┌─ 3b. 调用 LLM ─────────────────────────────┐  │
│    │  response = self.llm.chat(                  │  │
│    │      prompt=user_prompt,                     │  │
│    │      system_prompt=system_prompt             │  │
│    │  )                                           │  │
│    │  解析出 thought, action                      │  │
│    │  → 追加到 step_history                       │  │
│    └────────────────────────────────────────────┘  │
│         ↓                                          │
│    ┌─ 3c. 判断 Action 类型 ──────────────────────┐  │
│    │                                              │  │
│    │  action 以 "Finish" 开头？                    │  │
│    │    YES → 提取最终答案                         │  │
│    │         → 持久化 assistant 消息               │  │
│    │         → return AgentResponse("final_answer")│  │
│    │                                              │  │
│    │  否则 → 进入 3d（工具调度）                    │  │
│    └────────────────────────────────────────────┘  │
│         ↓                                          │
│    ┌─ 3d. 工具调度 ─────────────────────────────┐  │
│    │  调用 _parse_tool_action(action)             │  │
│    │  → 得到 (tool_name, tool_input)              │  │
│    │  → 调用 _dispatch_tool(name, input)          │  │
│    │  → 返回 observation 文本                     │  │
│    │  → 追加 "Observation: ..." 到 step_history   │  │
│    │  → 继续下一轮循环                             │  │
│    └────────────────────────────────────────────┘  │
│                                                     │
│  END FOR                                            │
└─────────────────────────────────────────────────────┘
```

**阶段 4：兜底**

循环达到 `max_steps` 仍未 Finish，持久化一条 fallback 消息（如"正在为您转接人工客服"），返回 `AgentResponse("final_answer", fallback)`。

**关于 LLM 输出解析**：

LLM 的响应文本需要从中提取结构化信息。使用正则表达式匹配即可，不需要引入第三方解析库：

- `_parse_output(text)`：匹配 `Thought: ...` 和 `Action: ...` 两行，分别返回
- `_parse_action_input(text)`：从 `ActionType[参数内容]` 中提取括号内的参数文本
- `_parse_tool_action(text)`：从 `tool_name[参数内容]` 中提取工具名和参数

**工具调度容错**：

工具调度可能失败（找不到工具、参数错误、`tool.run()` 抛异常）。不要直接崩溃——将错误信息作为 `Observation` 追加到 `step_history`，让 LLM 在下一轮看到错误并自行纠正：

```
_dispatch_tool 调用失败 →
  Observation: "工具调用失败: {错误原因}" →
  追加到 step_history →
  继续下一轮循环（LLM 看到错误后会尝试其他方式）
```

**容易踩的坑**：

- Prompt 构建时注意用 `self.system_prompt` 而非硬编码的模板名（否则自定义 prompt 会被忽略）
- LLM 不一定每次输出格式都完美——如果 `_parse_output` 返回的 `action` 为空，应在循环中 `continue` 让 LLM 重试，而不是直接崩溃
- `step_history`（本轮 Thought/Action/Observation）仅存在内存中，**不写入 SQL**。只有 user 消息和最终的 assistant 回复需要持久化
- `_format_context()` 是一个独立方法，负责把 `[{role, content}]` 格式的列表转为纯文本。不要遗漏这个方法的实现
- ReAct 循环中 `self.llm.chat(prompt=user_prompt, system_prompt=system_prompt)` — `system_prompt` 在每轮循环中保持不变（也可传 `None`），对话历史通过 `user_prompt` 中的 `{context}` 和 `{history}` 占位符传递

### 6.4 System Prompt 设计

`run()` 方法在阶段 3a 中完成 prompt 的填充：取模板 → 调 `self.system_prompt.format(...)` 替换占位符 → 得到完整的 prompt 字符串。本节描述的是**模板长什么样**及各占位符的含义。

Prompt 模板是一个字符串，各段落按以下顺序组织：

```
你是一个智能客服助手，可以使用工具检索FAQ知识库来回答用户的问题。

## 可用工具
{tools}
【由 _build_tools_description() 生成，每个工具一行：- name(param: type): description】

## 工作流程
每次回复必须包含两行：
  Thought: <分析用户意图、信息是否充足>
  Action: <选择以下动作之一>
    search_faq[关键词]  →  在FAQ库中检索相关信息
    Finish[最终答案]    →  信息充足时给出最终答案

## 规则
- 回答必须基于FAQ检索结果，不要编造信息
- 检索不到相关内容时，告知用户并建议转人工客服
- 回答简洁友好，控制在200字以内

## 对话历史
{context}
【由 _format_context(get_context()) 生成，格式如"用户: xxx\n客服: xxx"】

## 当前消息
用户: {user_input}
【由 run() 的 user_input 参数直接填入】

## 执行历史
{history}
【本轮 step_history 列表拼接，记录每一步的 Thought / Action / Observation】

现在开始你的推理和行动：
```

**占位符汇总**：

- `{tools}` → `_build_tools_description()`
- `{context}` → `_format_context(cm.get_context())`
- `{user_input}` → `run()` 的 `user_input` 参数
- `{history}` → `step_history` 列表用换行拼接

**设计要点**：

- 模板在 `run()` 的阶段 3a 中通过 `self.system_prompt.format(...)` 填充，**注意使用实例属性 `self.system_prompt` 而非硬编码的模板名**（因为构造函数允许传入自定义 prompt）
- `{context}`（SQL 历史对话）和 `{history}`（本轮 ReAct 步骤）是两个不同的东西，前者是多轮对话记录，后者是 Agent 单次推理的中间步骤
- `{history}` 初始为空（首轮循环），每步追加 Thought/Action/Observation 后更新，供下一轮 LLM 看到自己之前的推理
- 当前 prompt 只包含 `search_faq` 和 `Finish` 两种动作。附录 E 扩展反问能力时会在此框架上追加 `AskUser` 规则

> **花括号转义警告**：模板使用 Python `.format()` 填充占位符。如果模板中出现非占位符的花括号（如后续在模板中写 JSON 示例 `{"key": "value"}`），必须双写转义为 `{{"key": "value"}}`，否则 `.format()` 会抛出 `KeyError`。另一个方案是使用 `string.Template` 做 `$variable` 替换，但当前阶段用 `.format()` 即可——只需注意转义。

### 6.5 完成标志

- Agent 能根据用户输入调用 `search_faq` 检索 FAQ，基于结果用 `Finish` 给出答案
- 整个 Thought → Action → Observation 链条可追溯（通过 step_history 日志）
- 多轮对话上下文连贯（第2轮 Agent 知道第1轮在聊什么）

### 6.6 AI 协作提示

将以下信息提供给 LLM：

**已有模块接口**：

| 模块 | 调用方式 | 说明 |
|------|---------|------|
| `from tools.faq_search import search_faq_tool` | `search_faq_tool.run({"query": "...", "top_k": 5})` → `str` | 检索 FAQ，返回格式化文本 |
| `from llm import chat_service` | `chat_service.chat(prompt, system_prompt=None)` → `str` | LLM 文本生成 |
| `from utils import ConversationManager` | `cm = ConversationManager(db_path)`；`cm.add_message()` / `cm.get_context()` / `cm.create()` | 会话持久化与上下文获取 |

**需要创建的内容**：
- `domain/customer_service/agent.py`：`AgentResponse` 数据类 + `CustomerServiceAgent` 类
- `domain/customer_service/prompts.py`：`CUSTOMER_SERVICE_PROMPT` 模板字符串
- `domain/__init__.py`、`domain/customer_service/__init__.py`：导出

**Agent 构造函数**：
- `llm` — 从 `llm` import 的模块单例 `chat_service`
- `conversation_manager` — `ConversationManager` 实例
- `tools` — `[search_faq_tool]` 列表
- `system_prompt` — 默认使用 `prompts.py` 中的模板
- `max_steps` — 默认 5

**Agent 内部 6 个辅助方法**：
- `_find_tool(name)` — 遍历 `self.tools` 按名查找
- `_build_tools_description()` — 遍历 tools 调 `to_prompt_desc()`，换行拼接
- `_format_context(msgs)` — `[{role, content}]` → `"用户: xxx\n客服: xxx"`
- `_dispatch_tool(name, input_text)` — 按三级优先级映射参数（JSON解析 → 单必填参数 → 兜底报错），然后 `tool.run(params)`
- `_parse_output(text)` — 正则提取 `Thought:` 和 `Action:` 两行
- `_parse_action_input(text)` — 提取 `Finish[答案]` 中括号内的内容
- `_parse_tool_action(text)` — 提取 `tool_name[参数]` → `(tool_name, 参数)`

**`run()` 方法四个阶段**：
1. 持久化用户消息 → `cm.add_message(cid, "user", user_input)`
2. 获取上下文 → `cm.get_context(cid)` → `_format_context()`
3. ReAct 循环（最多 max_steps 次）→ 构建 prompt → 调 LLM → 解析 → Finish 则返回 / 否则调度工具得到 Observation 后继续
4. 兜底 → 超步数返回 fallback 消息

**关键约束**：
- `self.system_prompt.format(tools=..., context=..., user_input=..., history=...)` 填充 prompt
- 模板中 `{tools}` `{context}` `{user_input}` `{history}` 四个占位符由 Agent 填充
- 模板中任何非占位符的花括号必须双写转义 `{{` `}}`，否则 `.format()` 报错
- `step_history` 仅存内存，不入 SQL。只有 user 和最终 assistant 消息写 SQL
- `_parse_output` 解析失败时 `continue` 让 LLM 重试，不要崩溃
- 工具调度失败时，将错误信息作为 Observation 追加到 step_history
- LLM 调用：`self.llm.chat(prompt=user_prompt, system_prompt=system_prompt)` — system_prompt 在每轮循环中保持不变

**完成标志**：
- 创建 Agent 实例，调用 `agent.run("退货流程", conversation_id)` 返回 `AgentResponse(type="final_answer", ...)`
- 多轮对话：第二轮问答能引用第一轮的上下文

### 6.7 常见偏差

- Agent 内部直接 import rag.store（应通过 tools 层的 Tool 对象调用）
- 忘记持久化 assistant 消息（Finish 的内容必须写入 ConversationManager）
- 把 Thought / Action / Observation 写入 SQL（它们是 Agent 内存状态，不属于对话 transcript）
- `.format()` 调用时因模板中存在未转义的 `{}` 而报 KeyError
- `_format_context()` 方法遗漏实现，导致 `{context}` 占位符为空

---

## 步骤7：应用层 —— API 接口服务

> **本步骤需要新建/改写的文件**：项目根目录的 `main.py`、`apps/customer_service/__init__.py`、`apps/customer_service/routes.py`。原有的 `api/` 目录在步骤1 迁移中已删除，本步骤在项目根目录和 `apps/customer_service/` 下重新实现 API。

原 guide.md 的 API 直接依赖 retriever，调整后依赖 Agent。

### 7.1 接口变更

| 原接口 | 新接口 | 说明 |
|--------|--------|------|
| `POST /search` | `POST /chat` | 检索接口改为对话接口 |
| 无 | `POST /conversations` | 新增：创建会话 |
| 无 | `GET /conversations/{id}` | 新增：获取会话历史 |
| 无 | `GET /conversations?user_id=xxx` | 新增：列出用户会话 |

### 7.2 /chat 接口

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

### 7.3 API 层实现

API 层只做三件事：接收参数 → 调用 Agent → 格式化响应。不包含任何检索、prompt 构建、会话管理逻辑。

**`main.py` 需要完成的工作**（这是整个项目中唯一做"依赖装配"的地方）：

```
依赖装配顺序（在 main.py 的启动事件或模块级完成）：

1. 加载 .env（dotenv）
2. 导入模块级单例
   → from llm import chat_service                  # 模块单例，无需 new
3. 创建需构造函数注入的实例
   → cm = ConversationManager(db_path="./data/conversations.db", max_context_turns=10)
   → tools = [search_faq_tool]                    # 从 tools.faq_search import
4. 创建 CustomerServiceAgent 实例
   → agent = CustomerServiceAgent(
       llm=chat_service,                          # 模块单例
       conversation_manager=cm,
       tools=tools,
     )
5. 创建 FastAPI app，注册路由
   → 路由函数通过模块级变量访问 agent 和 cm
```

> **模块单例 vs 构造函数注入**：`chat_service` 是固定依赖（全局一份配置），用模块单例直接 import。`ConversationManager` 和 `CustomerServiceAgent` 有可变参数（db_path、tools 列表），在项目根目录的 `main.py` 中用构造函数注入。

**关键约束**：

- `/chat` 路由收到空的 `conversation_id` 时，自动调用 `cm.create()` 创建新会话，并在响应中返回新 ID
- API 层**只依赖 Agent**（和 ConversationManager 的查历史接口），不直接 import tools、rag、llm 等下层模块
- 请求/响应使用 Pydantic 模型做校验（字段定义见 7.2 节）

### 7.4 完成标志

- `/chat` 接口完成一次"用户提问 → Agent 检索 FAQ → 返回答案"的完整交互
- 会话历史可通过接口查询
- API 层代码仅包含参数接收、调用 Agent、格式化响应
- 完成附录 E 后，追加"反问 → 用户回复 → 最终答案"多轮交互验证

### 7.5 AI 协作提示

将以下信息提供给 LLM：

**已有模块接口**：
- `agent.run(user_input: str, conversation_id: str)` → `AgentResponse(type, content, conversation_id, metadata)`
- `cm.create(user_id)` → `conversation_id`
- `cm.get_history(conversation_id)` → `[{role, content, ...}]`
- `cm.list_conversations(user_id)` → `[{id, title, ...}]`

**需要创建的内容**：
- `main.py`（项目根目录）：FastAPI 应用入口，完成依赖装配
- `apps/customer_service/routes.py`：`POST /chat`、`POST /conversations`、`GET /conversations/{id}`、`GET /conversations?user_id=xxx`
- `apps/customer_service/__init__.py`

**关键约束**：
- API 层只依赖 Agent 和 ConversationManager 的查历史接口，不直接 import tools、rag、llm 等下层模块
- `conversation_id` 为空字符串时自动调 `cm.create()` 创建新会话
- 请求/响应使用 Pydantic 模型做校验
- 模块单例（如 `chat_service`）直接 import，不要重复 new
- FastAPI app 的创建和路由注册在项目根目录的 `main.py` 中完成

### 7.6 常见偏差

- 在 API 层直接 import rag 或 tools（API 只依赖 Agent）
- 在 API 层构建 prompt（prompt 是 Agent 的职责）
- 在 API 层处理会话逻辑（会话管理在 ConversationManager）

---

## 步骤8：方法论 —— 与 AI 协作调试 Agent

### 8.1 让 AI 追踪 Thought 链

Agent 的行为不像检索服务那样可预测。当回答不符合预期时，让 AI 追踪完整的思考链路：

"用户输入是'怎么退'，Agent 的 Thought 是什么？为什么选择了 search_faq（或 AskUser）？如果是 search_faq 没命中，Observation 返回了什么？请追踪每一步的 Thought/Action/Observation。"

### 8.2 先验 prompt，再验逻辑

Agent 出问题时，90% 的情况是 prompt 写得不好。优先让 AI 审查 prompt：

"当前 system prompt 中关于各 Action 的触发条件是否明确？用户说'帮我查一下'时，Agent 应该做什么？prompt 是否有歧义？"

### 8.3 用具体对话案例驱动调试

不要描述"Agent 表现不好"，给具体的对话记录。让 AI 基于真实输入输出分析根因，而不是猜测。

### 8.4 增量验证

每完成一个模块就跑验证脚本。会话存储 → 验证 SQL CRUD。工具层 → 验证函数直接调用和 `tool.run()` 返回一致。Agent → 验证 Finish 分支是否正确返回答案。完成附录 E 后 → 验证 AskUser 分支切换。不要堆到最后才发现问题。

---
