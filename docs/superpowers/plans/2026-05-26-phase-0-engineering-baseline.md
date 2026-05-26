# Phase 0 Engineering Baseline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the existing RAG customer-service prototype into a reproducible, testable baseline with truthful interaction states, cited knowledge answers, explicit initialization, and dependency-aware health reporting.

**Architecture:** Keep the current FastAPI, PostgreSQL conversation storage, and Chroma knowledge store during Phase 0. Tighten the existing single-agent boundary instead of introducing business agents: `CustomerServiceAgent` receives structured tool observations, returns typed user-visible actions, and delegates deterministic infrastructure checks to existing lower layers. Phase 1 can build simulated after-sales workflows on this stable contract.

**Tech Stack:** Python 3, FastAPI, Pydantic 2, PostgreSQL/psycopg2, ChromaDB, OpenAI-compatible SDK, pytest.

---

## 1. Scope And Assumptions

This plan implements only Phase 0 worklist items `P0-001` through `P0-016`. It does not add simulated orders, tickets, authentication, Supervisor routing, or child agents; those belong to Phase 1 and Phase 2.

Assumptions fixed for this plan:

1. The existing local `docker-compose.yml` modification mapping PostgreSQL to host port `5433` represents the active development environment and will be adopted deliberately in the documentation change, without removing local database data.
2. Chroma remains the vector store through Phase 1 MVP development. Moving vectors into PostgreSQL/pgvector is postponed until the customer workflows and evaluation set are stable, because it does not prove any Phase 1 user behavior.
3. Generated data (`data/`), local virtual environments, cache directories, and `.env` remain local and must not enter commits.
4. The default automated test command must not call an external LLM or embedding API.
5. User-visible messages and auditable action summaries may be persisted; model reasoning text remains ephemeral.

## 2. Target File Map

| File | Responsibility In This Plan |
| --- | --- |
| `.gitignore` | Prevent local secrets, generated data, environments, and caches from being tracked |
| `.env.example` | Canonical configuration names consumed by runtime code |
| `requirements-dev.txt` | Development-only test dependency entry point |
| `README.md`, `docs/pgsql_setup.md` | Reproducible startup, test split, capability truth, and selected local database port |
| `docs/solution/customer-service-multi-agent-solution.md` | Record Chroma retention decision for Phase 0/1 |
| `docs/worklists/customer-service-multi-agent-worklist.md` | Track task state and verification evidence after each implementation batch |
| `tools/base.py` | Add a structured, still-thin tool observation contract |
| `tools/faq_search.py` | Preserve plain text callable while supplying structured FAQ citations to Agent |
| `domain/customer_service/prompts.py` | Separate system instructions from per-turn user context and declare allowed actions |
| `domain/customer_service/agent.py` | Handle `AskUser`/`Handoff`, citations, grounding fallback, and proper system prompt calls |
| `apps/customer_service/schemas.py` | Expose response type, citations, and metadata through API contract |
| `apps/customer_service/routes.py` | Map Agent response fields without embedding domain logic |
| `infrastructure/database.py` | Add cheap database health probe |
| `utils/conversation.py` | Make schema initialization explicit instead of swallowing initialization failure |
| `scripts/init_db.py` | Intentional schema bootstrap command |
| `main.py` | Fail visibly on incorrect initialization and expose dependency-aware health output |
| `tests/conftest.py` | Test path setup and shared test doubles |
| `tests/test_agent_actions.py` | Offline typed-action/system-prompt tests |
| `tests/test_agent_citations.py` | Offline structured retrieval and grounding tests |
| `tests/test_health_and_initialization.py` | Initialization and health status tests |
| `tests/test_faq_import.py` | FAQ parsing and source metadata tests |

## 3. Worklist Discipline

For each task below:

1. Before code edits, update the referenced worklist IDs to `IN_PROGRESS`.
2. After implementation but before verification, update them to `REVIEW`.
3. After the listed verification command succeeds, update them to `DONE` and add one row to the progress log with the exact command and result.
4. Commit the worklist update in the same commit as the verified change.

## Task 1: Establish Repository Hygiene And Canonical Local Setup

**Worklist IDs:** `P0-001`, `P0-003`, `P0-004`, `P0-005`

**Files:**
- Create: `.gitignore`
- Create: `requirements-dev.txt`
- Modify: `.env.example`
- Modify: `README.md`
- Modify: `docs/pgsql_setup.md`
- Modify: `docs/solution/customer-service-multi-agent-solution.md`
- Modify: `docs/worklists/customer-service-multi-agent-worklist.md`
- Include existing intended modification: `docker-compose.yml`

- [ ] **Step 1: Mark setup tasks in progress in the worklist**

Change the four task states to `IN_PROGRESS`, and add this decision row:

```markdown
| 2026-05-26 | `DEC-005` | 决策 | Phase 0 与 Phase 1 继续使用 Chroma；pgvector 迁移在 MVP 流程稳定后单独评估 | `P0-005`, `Phase 1` | 已确认 |
```

- [ ] **Step 2: Add ignore rules and a development dependency entry point**

Create `.gitignore`:

```gitignore
.env
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
.coverage
htmlcov/
data/
```

Create `requirements-dev.txt`:

```text
-r requirements.txt
pytest>=8.0.0
```

- [ ] **Step 3: Normalize runtime configuration and local port documentation**

In `.env.example`, replace:

```env
EMBEDDING_MODEL_NAME=your_model
```

with:

```env
EMBEDDING_MODEL=your_model
```

Retain the currently configured compose mapping:

```yaml
ports:
  - "5433:5432"
```

Update `docs/pgsql_setup.md` connection examples to use:

```env
CONVERSATION_DB_URL=postgresql://user:1234@localhost:5433/agent
```

Update `README.md` to state that current capability is multi-turn FAQ answering, while active clarification is completed only when the `AskUser` task lands; replace that statement during Task 2 when the test-backed feature is added.

- [ ] **Step 4: Record the Chroma decision in the solution document**

Add to the vector storage decision section:

```markdown
Phase 0 decision (2026-05-26): Phase 0 and the Phase 1 simulated-business MVP retain Chroma as the knowledge vector store. The pgvector migration is evaluated after workflow and evaluation stability, because changing storage does not validate the customer-service behavior required for the MVP.
```

- [ ] **Step 5: Verify ignored and canonical files**

Run:

```powershell
git check-ignore .env .venv\ data\ __pycache__\
Select-String -Path .env.example -Pattern '^EMBEDDING_MODEL='
Select-String -Path docker-compose.yml,docs\pgsql_setup.md -Pattern '5433'
git diff --check
```

Expected: local generated paths are reported as ignored; `.env.example` contains `EMBEDDING_MODEL`; compose and documentation mention `5433`; `git diff --check` exits `0`.

- [ ] **Step 6: Mark the tasks done and commit**

Update `P0-001`, `P0-003`, `P0-004`, and `P0-005` to `DONE`, then commit only the intended files:

```powershell
git add .gitignore requirements-dev.txt .env.example docker-compose.yml README.md docs\pgsql_setup.md docs\solution\customer-service-multi-agent-solution.md docs\worklists\customer-service-multi-agent-worklist.md
git commit -m "chore: establish reproducible phase zero setup"
```

## Task 2: Implement Typed Agent Actions And Proper System Instructions

**Worklist IDs:** `P0-007`, `P0-008`, `P0-012`

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_agent_actions.py`
- Modify: `domain/customer_service/prompts.py`
- Modify: `domain/customer_service/agent.py`
- Modify: `apps/customer_service/schemas.py`
- Modify: `docs/worklists/customer-service-multi-agent-worklist.md`

- [ ] **Step 1: Mark action tasks in progress and install development dependencies**

Update `P0-007`, `P0-008`, `P0-012` to `IN_PROGRESS`.

Run:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
```

Expected: installation exits `0` and `pytest` is available through the repository virtual environment.

- [ ] **Step 2: Write failing tests for system prompt placement and `AskUser` / `Handoff`**

Create `tests/conftest.py`:

```python
from dataclasses import dataclass


class MemoryConversationManager:
    def __init__(self):
        self.messages = []

    def add_message(self, conversation_id, role, content, metadata=None):
        self.messages.append(
            {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "metadata": metadata,
            }
        )
        return len(self.messages)

    def get_context(self, conversation_id):
        return self.messages


class SequenceLLM:
    def __init__(self, *outputs):
        self.outputs = iter(outputs)
        self.calls = []

    def chat(self, prompt, system_prompt=None, **kwargs):
        self.calls.append({"prompt": prompt, "system_prompt": system_prompt})
        return next(self.outputs)
```

Create `tests/test_agent_actions.py`:

```python
from conftest import MemoryConversationManager, SequenceLLM
from domain.customer_service.agent import CustomerServiceAgent


def build_agent(*outputs):
    manager = MemoryConversationManager()
    llm = SequenceLLM(*outputs)
    return CustomerServiceAgent(llm, manager, [], max_steps=2), manager, llm


def test_rules_are_sent_as_system_prompt_and_user_input_is_turn_prompt():
    agent, _, llm = build_agent("Action: Finish[已收到]")

    agent.run("用户消息", "conv-1")

    assert "可用工具" in llm.calls[0]["system_prompt"]
    assert "用户消息" in llm.calls[0]["prompt"]
    assert "用户消息" not in llm.calls[0]["system_prompt"]


def test_ask_user_stops_loop_and_persists_visible_question():
    agent, manager, _ = build_agent("Action: AskUser[请提供门锁型号。]")

    response = agent.run("连不上网", "conv-1")

    assert response.type == "ask_user"
    assert response.content == "请提供门锁型号。"
    assert manager.messages[-1]["metadata"] == {"action_type": "ask_user"}


def test_handoff_stops_loop_and_returns_user_visible_reason():
    agent, manager, _ = build_agent("Action: Handoff[需要人工进一步确认。]")

    response = agent.run("我要人工", "conv-1")

    assert response.type == "handoff"
    assert manager.messages[-1]["metadata"] == {"action_type": "handoff"}
```

- [ ] **Step 3: Run tests to verify they fail for missing behavior**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_agent_actions.py -q
```

Expected: tests fail because the existing Agent calls `chat(prompt)` without a system prompt and treats `AskUser` / `Handoff` as unknown tools.

- [ ] **Step 4: Separate system and per-turn prompts**

Replace the prompt-building interface in `domain/customer_service/prompts.py` with these public functions while keeping `build_prompt` for existing smoke-script compatibility:

```python
SYSTEM_PROMPT = """你是一个专业的智能客服助手，负责回答智能家居产品问题。

## 可用工具
{tools}

## 允许动作
- Action: search_faq[检索关键词]：需要知识依据时检索 FAQ。
- Action: AskUser[澄清问题]：缺少型号、症状或办理信息时询问用户。
- Action: Handoff[转人工原因]：无法可靠回答、用户要求人工或风险升级时转人工。
- Action: Finish[最终答案]：已有充分依据时回答。

必须一次只输出一个 Action。不得在缺少知识或业务依据时编造答案。
"""

USER_PROMPT = """## 对话历史
{context}

## 当前用户输入
{user_input}

## 本轮执行历史
{history}
"""


def build_system_prompt(tools_desc: str) -> str:
    return SYSTEM_PROMPT.format(tools=tools_desc or "（无）")


def build_user_prompt(context: str, user_input: str, history: str = "") -> str:
    return USER_PROMPT.format(
        context=context,
        user_input=user_input,
        history=history or "（无）",
    )


def build_prompt(tools_desc: str, context: str, user_input: str, history: str = "") -> str:
    return build_system_prompt(tools_desc) + "\n" + build_user_prompt(
        context, user_input, history
    )
```

- [ ] **Step 5: Implement typed terminal actions in the Agent**

In `domain/customer_service/agent.py`, import the new builders:

```python
from .prompts import build_system_prompt, build_user_prompt
```

Inside `run()`, build and call the model as follows:

```python
system_prompt = self.system_prompt or build_system_prompt(tools_desc)
prompt = build_user_prompt(
    context=context,
    user_input=user_input,
    history=history_str,
)
output = self.llm.chat(prompt, system_prompt=system_prompt)
```

Replace the single `Finish` terminal block with:

```python
terminal_actions = {
    "Finish": "final_answer",
    "AskUser": "ask_user",
    "Handoff": "handoff",
}
if action_name in terminal_actions:
    response_type = terminal_actions[action_name]
    final_content = action_input
    self.conversation_manager.add_message(
        conversation_id,
        "assistant",
        final_content,
        metadata={"action_type": response_type},
    )
    return AgentResponse(
        type=response_type,
        content=final_content,
        conversation_id=conversation_id,
        metadata={"total_steps": step + 1},
    )
```

Do not persist `step_history` in `AgentResponse.metadata`; retain it only in local memory and optional verbose diagnostics.

- [ ] **Step 6: Restrict the API response type declaration**

In `apps/customer_service/schemas.py`, add:

```python
from typing import Literal
```

and replace the response type field with:

```python
type: Literal["final_answer", "ask_user", "handoff"] = Field(
    ..., description="响应类型：最终回答、澄清问题或人工转接"
)
```

- [ ] **Step 7: Run tests to verify typed actions pass**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_agent_actions.py -q
```

Expected: `3 passed`.

- [ ] **Step 8: Update the worklist and commit**

Set `P0-007`, `P0-008`, `P0-012` to `DONE`, append the test evidence to the progress log, then commit:

```powershell
git add domain\customer_service\prompts.py domain\customer_service\agent.py apps\customer_service\schemas.py tests docs\worklists\customer-service-multi-agent-worklist.md
git commit -m "feat: add typed customer service actions"
```

## Task 3: Return Structured Knowledge Citations Through The API

**Worklist IDs:** `P0-009`, `P0-013`

**Files:**
- Modify: `tools/base.py`
- Modify: `tools/faq_search.py`
- Modify: `domain/customer_service/agent.py`
- Modify: `apps/customer_service/schemas.py`
- Modify: `apps/customer_service/routes.py`
- Create: `tests/test_agent_citations.py`
- Modify: `docs/worklists/customer-service-multi-agent-worklist.md`

- [ ] **Step 1: Mark citation tasks in progress**

Set `P0-009` and `P0-013` to `IN_PROGRESS`.

- [ ] **Step 2: Write failing tests for structured observations and response citations**

Create `tests/test_agent_citations.py`:

```python
from conftest import MemoryConversationManager, SequenceLLM
from domain.customer_service.agent import CustomerServiceAgent
from tools.base import Citation, Tool, ToolParameter, ToolResult


def test_agent_returns_citations_from_tool_observation():
    def retrieve(query):
        return ToolResult(
            content="X1 重置步骤",
            citations=[
                Citation(
                    source_id="doc1-x1",
                    title="Doc1-X1智能门锁FAQ",
                    section="怎么重置 WiFi？",
                    excerpt="长按设置键约 5 秒。",
                )
            ],
        )

    tool = Tool(
        "search_faq",
        "检索",
        retrieve,
        [ToolParameter("query", "string", "检索词")],
    )
    agent = CustomerServiceAgent(
        SequenceLLM("Action: search_faq[X1 WiFi]", "Action: Finish[请按步骤操作。]"),
        MemoryConversationManager(),
        [tool],
    )

    response = agent.run("怎么重置", "conv-1")

    assert response.citations[0].source_id == "doc1-x1"


def test_plain_search_function_remains_a_string_for_non_agent_callers(monkeypatch):
    from tools import faq_search

    monkeypatch.setattr(
        faq_search,
        "retrieve_faq",
        lambda query, top_k=5: ToolResult(content="plain output", citations=[]),
    )

    assert faq_search.search_faq("x") == "plain output"
```

- [ ] **Step 3: Run citation tests to verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_agent_citations.py -q
```

Expected: collection fails because `Citation` and `ToolResult` do not yet exist and `AgentResponse` has no `citations`.

- [ ] **Step 4: Add the thin structured tool result types**

In `tools/base.py`, add:

```python
@dataclass
class Citation:
    source_id: str
    title: str
    section: str
    excerpt: str


@dataclass
class ToolResult:
    content: str
    citations: list[Citation] = field(default_factory=list)
```

Change only the return annotation of `Tool.run` to permit structured results:

```python
def run(self, params: dict) -> Any:
```

Export `Citation` and `ToolResult` from `tools/__init__.py`.

- [ ] **Step 5: Preserve the public FAQ string function and make the Tool structured**

In `tools/faq_search.py`, implement:

```python
from .base import Citation, Tool, ToolParameter, ToolResult


def retrieve_faq(query: str, top_k: int = 5) -> ToolResult:
    store = get_store()
    results = store.search(query, top_k=top_k)
    if not results:
        return ToolResult(content="未找到相关的 FAQ 内容，请补充产品型号或联系人工客服。")

    lines = [f"找到 {len(results)} 条相关 FAQ：\n"]
    citations = []
    for result in results:
        metadata = result.get("metadata", {})
        question = metadata.get("question", "未知问题")
        answer = metadata.get("answer", "未知答案")
        source_id = metadata.get("source_id", result.get("id", "unknown"))
        title = metadata.get("title", "FAQ 知识库")
        lines.append(f"问题：{question}\n答案：{answer}\n")
        citations.append(
            Citation(
                source_id=source_id,
                title=title,
                section=question,
                excerpt=answer[:160],
            )
        )
    return ToolResult(content="\n".join(lines), citations=citations)


def search_faq(query: str, top_k: int = 5) -> str:
    return retrieve_faq(query, top_k=top_k).content
```

Bind `search_faq_tool` to `retrieve_faq`, keeping `search_faq()` available for existing non-Agent callers:

```python
func=retrieve_faq,
```

- [ ] **Step 6: Accumulate citations on Agent responses**

In `domain/customer_service/agent.py`, add:

```python
from dataclasses import dataclass, field
from tools.base import ToolResult
```

Extend `AgentResponse`:

```python
citations: list = field(default_factory=list)
```

Initialize citations in `run()`:

```python
citations = []
```

When dispatching a tool:

```python
tool_result = self._dispatch_tool(action_name, action_input)
if isinstance(tool_result, ToolResult):
    observation = tool_result.content
    citations.extend(tool_result.citations)
else:
    observation = tool_result
```

Return `citations=citations` from all terminal and fallback `AgentResponse` instances.

- [ ] **Step 7: Add API citation schemas and mapping**

In `apps/customer_service/schemas.py`, add:

```python
class CitationItem(BaseModel):
    source_id: str
    title: str
    section: str
    excerpt: str
```

Extend `ChatResponse`:

```python
citations: List[CitationItem] = []
metadata: Optional[dict] = None
```

In `apps/customer_service/routes.py`, map:

```python
citations=[
    CitationItem(
        source_id=item.source_id,
        title=item.title,
        section=item.section,
        excerpt=item.excerpt,
    )
    for item in response.citations
],
metadata=response.metadata,
```

and import `CitationItem` from schemas.

- [ ] **Step 8: Run citation and existing action tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_agent_actions.py tests\test_agent_citations.py -q
```

Expected: all tests pass.

- [ ] **Step 9: Update the worklist and commit**

Set `P0-009`, `P0-013` to `DONE`, log the verification command, then commit:

```powershell
git add tools domain apps tests docs\worklists\customer-service-multi-agent-worklist.md
git commit -m "feat: return cited knowledge answers"
```

## Task 4: Enforce Grounded Fallback After Failed Knowledge Retrieval

**Worklist IDs:** `P0-010`, `P0-011`

**Files:**
- Modify: `domain/customer_service/agent.py`
- Modify: `tests/test_agent_citations.py`
- Modify: `docs/worklists/customer-service-multi-agent-worklist.md`

- [ ] **Step 1: Mark fallback/state tasks in progress**

Set `P0-010` and `P0-011` to `IN_PROGRESS`.

- [ ] **Step 2: Write failing tests for no-source answers and auditable state**

Append to `tests/test_agent_citations.py`:

```python
def test_finish_after_empty_knowledge_result_becomes_handoff():
    tool = Tool(
        "search_faq",
        "检索",
        lambda query: ToolResult(content="未找到相关内容。", citations=[]),
        [ToolParameter("query", "string", "检索词")],
    )
    manager = MemoryConversationManager()
    agent = CustomerServiceAgent(
        SequenceLLM("Action: search_faq[未知问题]", "Action: Finish[猜测答案]"),
        manager,
        [tool],
    )

    response = agent.run("未知问题", "conv-1")

    assert response.type == "handoff"
    assert "可靠知识依据" in response.content
    assert manager.messages[-1]["metadata"]["action_type"] == "handoff"


def test_ask_user_message_records_auditable_waiting_state():
    manager = MemoryConversationManager()
    agent = CustomerServiceAgent(
        SequenceLLM("Action: AskUser[请提供产品型号。]"),
        manager,
        [],
    )

    agent.run("设备坏了", "conv-1")

    assert manager.messages[-1]["metadata"]["conversation_state"] == "awaiting_clarification"
```

- [ ] **Step 3: Run tests to verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_agent_citations.py -q
```

Expected: failures show an unsupported final answer after empty retrieval and absent `conversation_state` metadata.

- [ ] **Step 4: Implement the smallest grounded fallback and state mapping**

In `run()`, initialize:

```python
knowledge_lookup_without_sources = False
```

After a `ToolResult` is dispatched:

```python
if action_name == "search_faq" and not tool_result.citations:
    knowledge_lookup_without_sources = True
```

Before returning a `Finish` terminal action:

```python
if action_name == "Finish" and knowledge_lookup_without_sources and not citations:
    final_content = "当前没有找到可靠知识依据，已为您转接人工进一步确认。"
    self.conversation_manager.add_message(
        conversation_id,
        "assistant",
        final_content,
        metadata={
            "action_type": "handoff",
            "conversation_state": "handoff_requested",
        },
    )
    return AgentResponse(
        type="handoff",
        content=final_content,
        conversation_id=conversation_id,
        citations=[],
        metadata={"total_steps": step + 1},
    )
```

Use explicit user-visible state metadata for terminal actions:

```python
states = {
    "final_answer": "active",
    "ask_user": "awaiting_clarification",
    "handoff": "handoff_requested",
}
```

Set message metadata to:

```python
{"action_type": response_type, "conversation_state": states[response_type]}
```

This Phase 0 state is intentionally stored with messages; a separate workflow state table is added only with Phase 1 workflows.

- [ ] **Step 5: Verify grounded fallback behavior**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_agent_actions.py tests\test_agent_citations.py -q
```

Expected: all tests pass. Update the existing action tests to expect `conversation_state` alongside `action_type`, because it is now part of the agreed message metadata contract.

- [ ] **Step 6: Update worklist and commit**

Set `P0-010`, `P0-011` to `DONE`, log the verification command, then commit:

```powershell
git add domain tests docs\worklists\customer-service-multi-agent-worklist.md
git commit -m "feat: guard unsupported knowledge answers"
```

## Task 5: Make FAQ Imports Reproducible And Source-Aware

**Worklist IDs:** `P0-002`

**Files:**
- Add/Modify: `scripts/import_faq.py`
- Create: `tests/test_faq_import.py`
- Modify: `infrastructure/rag/store.py`
- Modify: `docs/worklists/customer-service-multi-agent-worklist.md`

- [ ] **Step 1: Mark import work in progress**

Set `P0-002` to `IN_PROGRESS`.

- [ ] **Step 2: Write failing parser/source metadata tests**

Create `tests/test_faq_import.py`:

```python
from pathlib import Path

from scripts.import_faq import parse_faq_file


def test_parse_faq_file_preserves_document_source(tmp_path: Path):
    source = tmp_path / "Doc1-X1智能门锁FAQ.md"
    source.write_text("**怎么重置 WiFi？**\n长按设置键。\n", encoding="utf-8")

    result = parse_faq_file(source)

    assert result == [
        {
            "question": "怎么重置 WiFi？",
            "answer": "长按设置键。",
            "source_id": "Doc1-X1智能门锁FAQ",
            "title": "Doc1-X1智能门锁FAQ",
        }
    ]
```

- [ ] **Step 3: Run parser test to verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_faq_import.py -q
```

Expected: failure because the current local script accepts a string path and returns only question/answer values.

- [ ] **Step 4: Implement source-aware FAQ parsing**

Use this parser contract in `scripts/import_faq.py`:

```python
def parse_faq_file(filepath: Path) -> list[dict]:
    text = filepath.read_text(encoding="utf-8")
    matches = re.findall(r"\*\*(.+?)\*\*\s*\n(.*?)(?=\n\*\*|\Z)", text, re.DOTALL)
    source_id = filepath.stem
    return [
        {
            "question": question.strip(),
            "answer": answer.strip(),
            "source_id": source_id,
            "title": source_id,
        }
        for question, answer in matches
        if question.strip() and answer.strip()
    ]
```

Use the actual source directory without mojibake:

```python
faq_dir = Path(__file__).parent.parent / "实训文档"
```

- [ ] **Step 5: Persist source metadata with vectors**

In `VectorStore.add_qa_pairs()`, extend metadata:

```python
"metadata": {
    "question": question,
    "answer": answer,
    "source_id": qa.get("source_id", f"qa_{i}"),
    "title": qa.get("title", "FAQ 知识库"),
    "type": "qa",
},
```

- [ ] **Step 6: Verify parsing without importing external embeddings**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_faq_import.py tests\test_agent_citations.py -q
```

Expected: all tests pass; do not execute the full import command during this test because it calls the configured embedding endpoint.

- [ ] **Step 7: Update worklist and commit**

Set `P0-002` to `DONE`, record that live index rebuilding is a deliberate external-API operation, then commit:

```powershell
git add scripts\import_faq.py infrastructure\rag\store.py tests docs\worklists\customer-service-multi-agent-worklist.md
git commit -m "feat: preserve FAQ citation sources on import"
```

## Task 6: Replace Silent Initialization With Explicit Bootstrap And Health Checks

**Worklist IDs:** `P0-006`, `P0-015`

**Files:**
- Modify: `infrastructure/database.py`
- Modify: `utils/conversation.py`
- Create: `scripts/init_db.py`
- Modify: `main.py`
- Create: `tests/test_health_and_initialization.py`
- Modify: `README.md`
- Modify: `docs/pgsql_setup.md`
- Modify: `docs/worklists/customer-service-multi-agent-worklist.md`

- [ ] **Step 1: Mark initialization/health tasks in progress**

Set `P0-006` and `P0-015` to `IN_PROGRESS`.

- [ ] **Step 2: Write failing tests for explicit initialization and health status**

Create `tests/test_health_and_initialization.py`:

```python
from fastapi.testclient import TestClient

from main import app
from utils.conversation import ConversationManager


class FakeDB:
    def __init__(self, fail=False):
        self.fail = fail

    def ping(self):
        if self.fail:
            raise RuntimeError("database unavailable")
        return True

    def close_all(self):
        pass


class FakeManager:
    def __init__(self, fail=False):
        self.db = FakeDB(fail=fail)


class FakeStore:
    def count(self):
        return 1


def test_conversation_manager_does_not_initialize_schema_by_default(monkeypatch):
    calls = []
    monkeypatch.setattr("utils.conversation.init_tables", lambda db: calls.append(db))
    monkeypatch.setattr("utils.conversation.DatabaseManager", lambda db_url=None: FakeDB())

    ConversationManager("postgresql://example")

    assert calls == []


def test_health_reports_unavailable_database(monkeypatch):
    monkeypatch.setattr("main.ConversationManager", lambda **kwargs: FakeManager(fail=True))
    monkeypatch.setattr("main.get_store", lambda: FakeStore())

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"
```

- [ ] **Step 3: Run tests to verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_health_and_initialization.py -q
```

Expected: failure because `ConversationManager` initializes tables during construction and `/health` does not probe dependencies.

- [ ] **Step 4: Make initialization explicit**

Change `ConversationManager.__init__` in `utils/conversation.py`:

```python
def __init__(
    self,
    db_url: Optional[str] = None,
    max_context_turns: int = 5,
    initialize_schema: bool = False,
):
    self.db = DatabaseManager(db_url=db_url)
    self.max_context_turns = max_context_turns
    if initialize_schema:
        init_tables(self.db)
```

Remove `_init_tables()` and its broad exception suppression.

Create `scripts/init_db.py`:

```python
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.database import DatabaseManager
from infrastructure.models import init_tables


def main() -> int:
    load_dotenv()
    db = DatabaseManager(os.getenv("CONVERSATION_DB_URL", ""))
    try:
        init_tables(db)
        print("[SUCCESS] PostgreSQL schema initialized.")
        return 0
    finally:
        db.close_all()


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Add dependency health probes**

Add to `DatabaseManager` in `infrastructure/database.py`:

```python
def ping(self) -> bool:
    result = self.execute_one("SELECT 1;", fetch=True)
    return bool(result and result[0] == 1)
```

In `main.py`, import:

```python
from fastapi.responses import JSONResponse
from infrastructure.rag import get_store
```

Replace `/health` with:

```python
@app.get("/health")
async def health(request: Request):
    checks = {}
    manager = request.app.state.conversation_manager
    try:
        checks["database"] = "ok" if manager.db.ping() else "error"
        get_store().count()
        checks["knowledge_store"] = "ok"
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "checks": checks, "error": type(exc).__name__},
        )
    return {"status": "ok", "checks": checks}
```

For tests, monkeypatch the dependency constructors used by the application lifespan before issuing a health request; do not require live PostgreSQL.

- [ ] **Step 6: Document bootstrap before service start**

Add to `README.md` and `docs/pgsql_setup.md`:

```powershell
.\.venv\Scripts\python.exe scripts\init_db.py
```

State that application startup does not silently create or ignore schema failures; schema setup is an intentional bootstrap operation.

- [ ] **Step 7: Verify initialization and health behavior**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_health_and_initialization.py -q
```

Expected: tests pass without connecting to external services.

- [ ] **Step 8: Update worklist and commit**

Set `P0-006` and `P0-015` to `DONE`, append verification evidence, then commit:

```powershell
git add infrastructure utils scripts\init_db.py main.py tests README.md docs\pgsql_setup.md docs\worklists\customer-service-multi-agent-worklist.md
git commit -m "feat: add explicit bootstrap and health probes"
```

## Task 7: Separate Test Modes And Verify Phase 0 Exit

**Worklist IDs:** `P0-014`, `P0-016`, milestone `M1`

**Files:**
- Create: `pytest.ini`
- Modify: `scripts/smoke_test.py`
- Modify: `README.md`
- Modify: `docs/worklists/customer-service-multi-agent-worklist.md`

- [ ] **Step 1: Mark verification tasks in progress**

Set `P0-014` and `P0-016` to `IN_PROGRESS`.

- [ ] **Step 2: Add pytest markers and make external tests opt-in**

Create `pytest.ini`:

```ini
[pytest]
testpaths = tests
markers =
    external: requires configured network API calls or persistent local services
```

In `scripts/smoke_test.py`, add an explicit environment gate before real external LLM/embedding/DB E2E paths:

```python
RUN_EXTERNAL_SMOKE = os.getenv("RUN_EXTERNAL_SMOKE", "").lower() == "true"
```

At the start of each external operation test, require:

```python
if not RUN_EXTERNAL_SMOKE:
    print("[SKIP] RUN_EXTERNAL_SMOKE is not true; skipping external smoke test")
    return True
```

- [ ] **Step 3: Document verification commands**

In `README.md`, list:

```powershell
# Offline regression tests; do not call configured LLM or embedding endpoints
.\.venv\Scripts\python.exe -m pytest -q

# Module/import migration verification
.\.venv\Scripts\python.exe scripts\verify_migration.py

# Explicit external smoke tests; may write local data and incur API calls
$env:RUN_EXTERNAL_SMOKE="true"
.\.venv\Scripts\python.exe scripts\smoke_test.py
```

- [ ] **Step 4: Run the offline Phase 0 verification suite**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\verify_migration.py
git diff --check
git status --short --branch
```

Expected:

- `pytest` reports all offline tests passed.
- `verify_migration.py` reports `[SUCCESS]`.
- `git diff --check` exits `0`.
- `git status` contains only intentionally staged/modified Phase 0 files or pre-existing local ignored files; no `.env`, `.venv`, cache or `data/` entries appear because `.gitignore` is active.

- [ ] **Step 5: Update Phase 0 completion status and commit**

Set `P0-014`, `P0-016`, and `M1` to `DONE` only if all Step 4 commands have passed. Add the exact test evidence to the progress log, then commit:

```powershell
git add pytest.ini scripts\smoke_test.py README.md docs\worklists\customer-service-multi-agent-worklist.md
git commit -m "test: establish phase zero verification gates"
```

## 4. Plan Self-Review Results

### Spec Coverage

| Solution Requirement | Task Coverage |
| --- | --- |
| Reproducible repository/config baseline | Task 1 |
| Phase 0 Chroma/pgvector decision | Task 1 |
| System prompt separation and typed responses | Task 2 |
| Active clarification (`AskUser`) and handoff basis | Task 2, Task 4 |
| Citation-bearing knowledge answers | Task 3, Task 5 |
| No unsupported answer after failed retrieval | Task 4 |
| Auditable minimal conversation state | Task 4 |
| Explicit database initialization and health visibility | Task 6 |
| Offline tests separate from external calls | Task 7 |
| Worklist updated alongside work | Every task |

### Boundary Checks

- Phase 1 entities such as simulated orders, tickets, authentication, and Supervisor workflows are intentionally not implemented in this plan.
- Phase 2 child agents are intentionally not implemented in this plan.
- Existing user-local `.env`, `.venv`, vector data, and database records are not deleted.
- The existing local Docker port edit is incorporated only as an explicitly documented Phase 0 setup decision.

### Type And Contract Consistency

- `AgentResponse.type` supports `final_answer`, `ask_user`, and `handoff` in both domain and API schemas.
- `Citation` is produced by structured tool results, collected by Agent, and mapped to `ChatResponse`.
- `confirm_action` remains a Phase 1 addition because no write operation is introduced in Phase 0.
- Minimal Phase 0 conversation state is message metadata; dedicated workflow-state storage remains a Phase 1 concern.
