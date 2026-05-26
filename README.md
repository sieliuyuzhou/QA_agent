# QA_agent

## 项目概述

基于 RAG 的智能客服 Agent 系统，支持多轮对话和主动反问能力。

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

# 2. 功能冒烟测试
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

**验证脚本：**

```bash
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
CONVERSATION_DB_URL=postgresql://user:password@localhost:5432/qa_agent
```

**验证脚本：**

```bash
python scripts/smoke_test.py
```

---

### Step 4: 模型层确认 ⏳

待开发...

### Step 5: 领域层 —— ReAct Agent ⏳

待开发...

### Step 6: 应用层 —— API 接口服务 ⏳

待开发...

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

### 3. 导入 FAQ 数据

```bash
python scripts/import_faq.py
```

### 4. 验证安装

```bash
python scripts/smoke_test.py
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
