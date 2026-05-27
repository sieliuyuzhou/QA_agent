# QA-agent Phase 1 Policy, Eligibility And Authorized Tools Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add scoped after-sales policy retrieval, a current-user-bound mock order tool, and deterministic after-sales eligibility decisions without introducing write operations or Agent workflow changes.

**Architecture:** The existing vector store gains an optional source filter used by a new `PolicySearchTool`; existing `OrderQueryService` is exposed through a closure-bound `MockOrderTool` that cannot accept a user identity from callers. A new domain `EligibilityRuleService` consumes authorized order facts and explicit issue facts, and returns structured policy decisions with fixed date boundaries.

**Tech Stack:** Python 3, dataclasses, FastAPI project modules, Chroma metadata filtering, pytest

---

## 1. File Map And Boundaries

| File | Responsibility |
| --- | --- |
| `infrastructure/rag/store.py` | Add optional metadata-source restriction to retrieval without changing default FAQ behavior. |
| `tools/policy_search.py` | Provide the source-scoped after-sales policy tool and structured citations. |
| `tools/mock_orders.py` | Provide a server-context-bound read-only mock order tool. |
| `domain/customer_service/eligibility.py` | Define request/decision data and deterministic policy rules. |
| `scripts/seed_mock_data.py` | Add one stable over-warranty order used for local scenario verification. |
| `tests/test_policy_search.py` | Prove policy results are restricted to `Doc5` and citations remain structured. |
| `tests/test_mock_order_tool.py` | Prove tool calls use the bound user and return no cross-user disclosure. |
| `tests/test_eligibility.py` | Prove every approved decision boundary and clarification path. |
| `docs/worklists/customer-service-multi-agent-worklist.md` | Track in-progress/completed states and verification evidence. |

Explicit non-goals: no ticket/pending-action tables, no `confirm_action`, no registration of new tools in `CustomerServiceAgent`, and no Supervisor or workflow implementation.

## Task 1: Scoped Policy Retrieval Tool

**Worklist ID:** `P1-007`

**Files:**
- Create: `tests/test_policy_search.py`
- Create: `tools/policy_search.py`
- Modify: `infrastructure/rag/store.py`
- Modify: `tools/__init__.py`

- [ ] **Step 1: Write failing policy retrieval tests**

Create `tests/test_policy_search.py`:

```python
from tools import policy_search


class FakeStore:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def search(self, query, top_k=5, source_id=None):
        self.calls.append((query, top_k, source_id))
        return self.results


def test_policy_search_requests_only_after_sales_policy_and_returns_citation(monkeypatch):
    store = FakeStore(
        [
            {
                "id": "qa_policy",
                "metadata": {
                    "question": "保修条款",
                    "answer": "所有智能硬件产品享有一年免费保修服务。",
                    "source_id": "Doc5-售后与保修政策",
                    "title": "Doc5-售后与保修政策",
                },
            }
        ]
    )
    monkeypatch.setattr(policy_search, "get_store", lambda: store)

    result = policy_search.retrieve_policy("一年内坏了怎么处理")

    assert store.calls == [("一年内坏了怎么处理", 5, "Doc5-售后与保修政策")]
    assert result.citations[0].source_id == "Doc5-售后与保修政策"
    assert result.citations[0].section == "保修条款"


def test_policy_search_without_policy_result_preserves_empty_citations(monkeypatch):
    store = FakeStore([])
    monkeypatch.setattr(policy_search, "get_store", lambda: store)

    result = policy_search.retrieve_policy("无法确认的政策")

    assert result.citations == []
```

- [ ] **Step 2: Run the policy test to verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_policy_search.py -q --basetemp=.pytest_cache\tmp
```

Expected: collection fails because `tools.policy_search` does not exist.

- [ ] **Step 3: Implement source-scoped store search and policy tool**

Change `VectorStore.search` in `infrastructure/rag/store.py` to accept a source restriction and pass it to Chroma:

```python
    def search(
        self,
        query: str,
        top_k: int = 5,
        source_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        try:
            query_embedding = self.embedding_service.embed(query)
            query_args = {
                "query_embeddings": [query_embedding],
                "n_results": top_k,
            }
            if source_id is not None:
                query_args["where"] = {"source_id": source_id}
            results = self.collection.query(**query_args)
```

Create `tools/policy_search.py`:

```python
from infrastructure.rag import get_store
from .base import Citation, Tool, ToolParameter, ToolResult


POLICY_SOURCE_ID = "Doc5-售后与保修政策"


def retrieve_policy(query: str, top_k: int = 5) -> ToolResult:
    results = get_store().search(query, top_k=top_k, source_id=POLICY_SOURCE_ID)
    if not results:
        return ToolResult(content="未找到有效的售后政策依据，请补充信息或联系人工客服。")

    content = []
    citations = []
    for result in results:
        metadata = result.get("metadata", {})
        section = metadata.get("question", "售后政策")
        answer = metadata.get("answer", "")
        content.append(f"政策章节：{section}\n内容：{answer}")
        citations.append(
            Citation(
                source_id=metadata.get("source_id", POLICY_SOURCE_ID),
                title=metadata.get("title", POLICY_SOURCE_ID),
                section=section,
                excerpt=answer[:160],
            )
        )
    return ToolResult(content="\n\n".join(content), citations=citations)


policy_search_tool = Tool(
    name="search_after_sales_policy",
    description="仅检索售后与保修政策，返回政策来源依据。",
    func=retrieve_policy,
    parameters=[
        ToolParameter("query", "string", "需要核对的售后政策问题"),
        ToolParameter("top_k", "integer", "返回结果数量", required=False, default=5),
    ],
)
```

Export from `tools/__init__.py`:

```python
from .policy_search import policy_search_tool, retrieve_policy

__all__ += ["policy_search_tool", "retrieve_policy"]
```

- [ ] **Step 4: Run policy tests to verify GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_policy_search.py tests\test_agent_citations.py -q --basetemp=.pytest_cache\tmp
```

Expected: all selected tests pass; existing FAQ citation behavior is unchanged.

## Task 2: Bound Mock Order Tool And Over-Warranty Fixture

**Worklist ID:** `P1-006`

**Files:**
- Create: `tests/test_mock_order_tool.py`
- Create: `tools/mock_orders.py`
- Modify: `tools/__init__.py`
- Modify: `scripts/seed_mock_data.py`
- Modify: `tests/test_mock_data.py`

- [ ] **Step 1: Write failing tool and seed tests**

Create `tests/test_mock_order_tool.py`:

```python
from domain.customer_service.context import CurrentUser, OrderView
from tools.mock_orders import build_mock_order_tool


class FakeOrderService:
    def __init__(self):
        self.calls = []

    def get_order(self, user_id, order_id):
        self.calls.append((user_id, order_id))
        if order_id == "ORD-A-X1":
            return OrderView(
                "ORD-A-X1", "X1", "X1 智能门锁", "smart_lock",
                "2026-05-22", "delivered", "1299.00",
            )
        return None


def test_mock_order_tool_uses_bound_current_user_and_returns_order_facts():
    service = FakeOrderService()
    tool = build_mock_order_tool(CurrentUser("customer_alice", "Alice Test"), service)

    result = tool.run({"order_id": "ORD-A-X1"})

    assert service.calls == [("customer_alice", "ORD-A-X1")]
    assert result["status"] == "found"
    assert result["order"]["order_id"] == "ORD-A-X1"


def test_mock_order_tool_returns_one_not_found_result_for_inaccessible_order():
    tool = build_mock_order_tool(CurrentUser("customer_alice", "Alice Test"), FakeOrderService())

    result = tool.run({"order_id": "ORD-B-X2"})

    assert result == {"status": "not_found", "order": None}
```

Extend `tests/test_mock_data.py`:

```python
def test_seed_data_includes_over_warranty_order():
    seed_module = _load_seed_module()

    assert any(row[3] == "2025-01-01" for row in seed_module.ORDERS)
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_mock_order_tool.py tests\test_mock_data.py -q --basetemp=.pytest_cache\tmp
```

Expected: collection fails because `tools.mock_orders` is missing, and the over-warranty seed assertion fails until data is added.

- [ ] **Step 3: Implement the bound tool and seed record**

Create `tools/mock_orders.py`:

```python
from dataclasses import asdict

from domain.customer_service.context import CurrentUser
from .base import Tool, ToolParameter


def build_mock_order_tool(current_user: CurrentUser, order_service) -> Tool:
    def get_mock_order(order_id: str) -> dict:
        order = order_service.get_order(current_user.user_id, order_id)
        if order is None:
            return {"status": "not_found", "order": None}
        return {"status": "found", "order": asdict(order)}

    return Tool(
        name="get_mock_order",
        description="读取当前用户可访问的一笔模拟订单。",
        func=get_mock_order,
        parameters=[ToolParameter("order_id", "string", "模拟订单编号")],
    )
```

Export from `tools/__init__.py`:

```python
from .mock_orders import build_mock_order_tool

__all__ += ["build_mock_order_tool"]
```

Append a stable over-warranty fixture in `scripts/seed_mock_data.py`:

```python
    ("ORD-A-G2-OLD", "customer_alice", "G2", "2025-01-01", "completed", "299.00"),
```

- [ ] **Step 4: Run tool and seed tests to verify GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_mock_order_tool.py tests\test_mock_data.py tests\test_orders_api.py -q --basetemp=.pytest_cache\tmp
```

Expected: all selected tests pass; existing order API ownership checks remain green.

## Task 3: Deterministic Eligibility Rule Service

**Worklist ID:** `P1-008`

**Files:**
- Create: `tests/test_eligibility.py`
- Create: `domain/customer_service/eligibility.py`
- Modify: `domain/customer_service/__init__.py`

- [ ] **Step 1: Write failing rules tests**

Create `tests/test_eligibility.py`:

```python
from datetime import date

from domain.customer_service.context import OrderView
from domain.customer_service.eligibility import EligibilityRequest, EligibilityRuleService


def order(purchased_at):
    return OrderView("ORD-1", "X1", "X1 智能门锁", "smart_lock", purchased_at, "delivered", "1299.00")


def evaluate(purchased_at, request_type, issue_cause, packaging_intact=None):
    return EligibilityRuleService().evaluate(
        EligibilityRequest(
            order=order(purchased_at),
            request_type=request_type,
            issue_cause=issue_cause,
            packaging_intact=packaging_intact,
            evaluated_on=date(2026, 5, 27),
        )
    )


def test_qualified_return_within_seven_days():
    decision = evaluate("2026-05-22", "return_or_exchange", "non_human_fault", True)
    assert decision.code == "eligible_for_return_or_exchange"
    assert decision.eligible is True


def test_damaged_or_unpacked_return_is_not_eligible():
    decision = evaluate("2026-05-22", "return_or_exchange", "human_damage", True)
    assert decision.code == "ineligible_for_return_or_exchange"
    assert decision.eligible is False


def test_non_human_fault_from_day_eight_to_day_365_is_warranty_repair():
    decision = evaluate("2026-03-01", "warranty_repair", "non_human_fault")
    assert decision.code == "eligible_for_warranty_repair"
    assert decision.eligible is True


def test_human_damage_is_not_free_warranty():
    decision = evaluate("2026-03-01", "warranty_repair", "human_damage")
    assert decision.code == "ineligible_for_free_warranty"
    assert decision.recommended_service == "paid_repair"


def test_over_warranty_order_only_has_paid_repair_path():
    decision = evaluate("2025-01-01", "warranty_repair", "non_human_fault")
    assert decision.code == "paid_repair_available"
    assert decision.eligible is True


def test_missing_required_fact_requests_clarification():
    decision = evaluate("2026-05-22", "return_or_exchange", "unknown", None)
    assert decision.code == "requires_clarification"
    assert decision.eligible is False


def test_unsupported_request_type_requests_clarification():
    decision = evaluate("2026-03-01", "refund_now", "non_human_fault")
    assert decision.code == "requires_clarification"
    assert decision.eligible is False
```

- [ ] **Step 2: Run rules tests to verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_eligibility.py -q --basetemp=.pytest_cache\tmp
```

Expected: collection fails because `domain.customer_service.eligibility` does not exist.

- [ ] **Step 3: Implement the minimal deterministic rules**

Create `domain/customer_service/eligibility.py`:

```python
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from .context import OrderView


@dataclass(frozen=True)
class EligibilityRequest:
    order: OrderView
    request_type: str
    issue_cause: str
    packaging_intact: Optional[bool] = None
    evaluated_on: date = field(default_factory=date.today)


@dataclass(frozen=True)
class EligibilityDecision:
    code: str
    eligible: bool
    recommended_service: Optional[str]
    reason_codes: list[str]
    policy_sections: list[str]


class EligibilityRuleService:
    def evaluate(self, request: EligibilityRequest) -> EligibilityDecision:
        age_days = (request.evaluated_on - date.fromisoformat(request.order.purchased_at)).days
        valid_request_types = {"return_or_exchange", "warranty_repair", "paid_repair"}
        if (
            age_days < 0
            or request.request_type not in valid_request_types
            or request.issue_cause == "unknown"
        ):
            return EligibilityDecision(
                "requires_clarification", False, None,
                ["required_fact_missing"], [],
            )
        if age_days > 365:
            return EligibilityDecision(
                "paid_repair_available", True, "paid_repair",
                ["outside_warranty_period"], ["过保后维修怎么收费？"],
            )
        if request.request_type == "return_or_exchange" and age_days <= 7:
            if request.packaging_intact is None:
                return EligibilityDecision(
                    "requires_clarification", False, None,
                    ["packaging_state_missing"], ["退换货政策"],
                )
            if request.issue_cause == "non_human_fault" and request.packaging_intact:
                return EligibilityDecision(
                    "eligible_for_return_or_exchange", True, "return_or_exchange",
                    ["within_7_days", "packaging_intact", "not_human_damaged"],
                    ["退换货政策"],
                )
            return EligibilityDecision(
                "ineligible_for_return_or_exchange", False, "paid_repair",
                ["return_conditions_not_met"], ["退换货政策"],
            )
        if request.issue_cause == "human_damage":
            return EligibilityDecision(
                "ineligible_for_free_warranty", False, "paid_repair",
                ["human_damage_excluded"], ["保修条款"],
            )
        if 8 <= age_days <= 365 and request.issue_cause == "non_human_fault":
            return EligibilityDecision(
                "eligible_for_warranty_repair", True, "warranty_repair",
                ["within_warranty_period", "not_human_damaged"],
                ["保修条款", "维修和退换有什么区别？"],
            )
        return EligibilityDecision(
            "requires_clarification", False, None,
            ["unsupported_request_or_missing_fact"], [],
        )
```

Export from `domain/customer_service/__init__.py`:

```python
from .eligibility import EligibilityDecision, EligibilityRequest, EligibilityRuleService

__all__ += ["EligibilityDecision", "EligibilityRequest", "EligibilityRuleService"]
```

- [ ] **Step 4: Run rules tests to verify GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_eligibility.py -q --basetemp=.pytest_cache\tmp
```

Expected: seven rule scenarios pass with deterministic results and no LLM calls.

## Task 4: Verify Slice And Close Worklist Items

**Worklist IDs:** `P1-006`, `P1-007`, `P1-008`, `DOC-010`

**Files:**
- Modify: `docs/worklists/customer-service-multi-agent-worklist.md`

- [ ] **Step 1: Run complete offline validation**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest_cache\tmp
.\.venv\Scripts\python.exe scripts\verify_migration.py
git diff --check
```

Expected: all tests pass, import verification succeeds, and no whitespace errors are reported.

- [ ] **Step 2: Verify idempotent local seed data**

Run:

```powershell
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe scripts\seed_mock_data.py
```

Expected:

```text
[SUCCESS] PostgreSQL schema initialized.
[SUCCESS] QA-agent mock customer and order data seeded.
```

- [ ] **Step 3: Update the worklist with exact evidence**

Change task statuses only after Step 1 and Step 2 succeed:

```markdown
| `P1-006` | `P0` | 实现授权的模拟订单查询工具 | ... | `✅ DONE` | ... | `MockOrderTool` 仅绑定当前用户读取订单 |
| `P1-007` | `P0` | 区分产品知识与售后政策检索能力 | ... | `✅ DONE` | ... | 政策工具按 `Doc5-售后与保修政策` 来源过滤 |
| `P1-008` | `P0` | 实现售后资格规则服务 | ... | `✅ DONE` | ... | `0-7`/`8-365`/`>365` 日期边界及澄清路径已覆盖 |
```

Append a progress row recording the precise test count, bootstrap evidence, and that `P1-004`/`P1-009` remain pending for write-operation design.

- [ ] **Step 4: Commit the implementation and evidence**

Run:

```powershell
git add infrastructure tools domain scripts tests docs\worklists\customer-service-multi-agent-worklist.md
git commit -m "feat: add after-sales eligibility foundations"
```

Expected: one implementation commit containing only the confirmed slice and its worklist verification evidence.

## 2. Self-Review

### Specification Coverage

| Specification Requirement | Implementing Task |
| --- | --- |
| Policy-only structured retrieval from `Doc5-售后与保修政策` | Task 1 |
| Existing FAQ behavior remains available | Task 1 regression run |
| Current-user-bound `MockOrderTool` with no caller-selected user ID | Task 2 |
| Stable over-warranty test order | Task 2 |
| Deterministic `0-7`, `8-365`, `>365` policy boundaries | Task 3 |
| Human damage and insufficient-fact outcomes | Task 3 |
| No write operations, Agent routing or Supervisor work | File map boundary and Task 4 review |
| Worklist evidence and closure only after validation | Task 4 |

### Consistency Checks

- The policy identifier matches the existing import contract: `Path.stem` stores `Doc5-售后与保修政策`.
- `MockOrderTool` closes over `CurrentUser`; its callable schema exposes only `order_id`.
- The over-warranty result is `paid_repair_available`, not an assertion that repair is accepted or priced.
- New tools remain unregistered in `CustomerServiceAgent` until a later workflow slice.

### No-Placeholder Check

This plan contains no unspecified code steps, unresolved placeholders, or write-operation work outside the approved slice.
