# Phase 1 After-Sales Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose a policy-backed after-sales workflow through `/api/chat` that returns a server-generated confirmation action and uses the existing confirmed ticket transaction for execution.

**Architecture:** Add a focused `AfterSalesWorkflow` that consumes explicit facts, requires policy citations, and delegates action creation to `TicketActionService`. Extend the existing single `CustomerServiceAgent` with one controlled `PrepareAfterSales` dispatch action and extend the chat response protocol with `confirm_action` and `pending_action`. The existing confirmation endpoint remains the only ticket creation path.

**Tech Stack:** Python 3, FastAPI, Pydantic, pytest, PostgreSQL repository/services already in this project.

---

## File Map

| File | Responsibility |
| --- | --- |
| `domain/customer_service/workflows.py` | Workflow request/result DTOs and policy-backed after-sales orchestration. |
| `domain/customer_service/agent.py` | Dispatch `PrepareAfterSales` with current identity and persist workflow response state. |
| `domain/customer_service/prompts.py` | Advertise the allowed workflow action and its explicit JSON input. |
| `apps/customer_service/schemas.py` | Extend chat response contract with `confirm_action` and optional pending action. |
| `apps/customer_service/routes.py` | Pass current identity into Agent and serialize pending action. |
| `main.py` | Assemble `AfterSalesWorkflow` from existing services and inject into Agent. |
| `tests/test_after_sales_workflow.py` | Workflow policy, eligibility and no-write-before-confirm behavior. |
| `tests/test_agent_workflow.py` | Agent controlled dispatch/state behavior. |
| `tests/test_chat_workflow.py` | `/api/chat` workflow response serialization and identity forwarding. |

Explicit non-goals: no domain sub-agent, no confirmation through free-form chat, no ticket query, no audit model, no changes to real external systems.

### Task 1: Policy-Backed After-Sales Workflow

**Files:**
- Create: `tests/test_after_sales_workflow.py`
- Create: `domain/customer_service/workflows.py`
- Modify: `domain/customer_service/__init__.py`

- [ ] **Step 1: Write failing workflow tests**

Create tests with a fake ticket action service and policy function:

```python
def test_eligible_policy_backed_request_returns_confirm_action():
    result = workflow_with_policy().prepare(
        CurrentUser("customer_alice", "Alice Test"),
        "alice-conv",
        warranty_payload(),
    )
    assert result.response_type == "confirm_action"
    assert result.pending_action.action_id == "act-1"
    assert result.citations[0].source_id == "Doc5-售后与保修政策"

def test_request_without_policy_citation_handoffs_without_creating_action():
    service = FakeTicketActionService()
    result = workflow_without_policy(service).prepare(
        CurrentUser("customer_alice", "Alice Test"), "alice-conv", warranty_payload()
    )
    assert result.response_type == "handoff"
    assert service.calls == []

def test_clarification_and_alternative_recommendations_never_create_pending_action():
    user = CurrentUser("customer_alice", "Alice Test")
    result = workflow_raising("requires_clarification").prepare(
        user, "alice-conv", warranty_payload()
    )
    assert result.response_type == "ask_user"
    result = workflow_raising("paid_repair_available").prepare(
        user, "alice-conv", warranty_payload()
    )
    assert result.response_type == "final_answer"
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_after_sales_workflow.py -q --basetemp=.pytest_cache\red_workflow
```

Expected: collection fails because `domain.customer_service.workflows` does not exist.

- [ ] **Step 3: Implement minimal workflow**

Create DTOs and orchestration:

```python
@dataclass(frozen=True)
class WorkflowResult:
    response_type: str
    content: str
    citations: list
    pending_action: Optional[PendingActionView] = None
    metadata: dict = field(default_factory=dict)

class AfterSalesWorkflow:
    def __init__(self, ticket_action_service, policy_lookup):
        self.ticket_action_service = ticket_action_service
        self.policy_lookup = policy_lookup

    def prepare(self, current_user, conversation_id, payload):
        action_input = TicketActionInput(**payload)
        if action_input.issue_cause == "unknown":
            return WorkflowResult("ask_user", "请确认问题是否由人为损坏导致。", [], metadata=self._metadata())
        policy = self.policy_lookup(action_input.issue_summary)
        if not policy.citations:
            return WorkflowResult("handoff", "当前没有找到可靠的售后政策依据，已为您转接人工进一步确认。", [], metadata=self._metadata())
        try:
            action = self.ticket_action_service.create_action(
                current_user.user_id, conversation_id, action_input
            )
        except TicketNotFound:
            return WorkflowResult("ask_user", "未找到当前账户可办理的订单，请核对订单号。", policy.citations, metadata=self._metadata())
        except TicketEligibilityConflict as exc:
            return self._eligibility_result(exc, policy.citations)
        return WorkflowResult("confirm_action", "根据售后政策，您的申请符合办理条件。请确认是否提交模拟售后工单。", policy.citations, action, self._metadata())
```

Validate required payload keys and allowed enum strings before calling services; invalid or incomplete input returns `ask_user`.

- [ ] **Step 4: Verify GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_after_sales_workflow.py tests\test_ticketing.py tests\test_policy_search.py -q --basetemp=.pytest_cache\green_workflow
```

Expected: all selected tests pass.

### Task 2: Agent Workflow Dispatch

**Files:**
- Create: `tests/test_agent_workflow.py`
- Modify: `domain/customer_service/agent.py`
- Modify: `domain/customer_service/prompts.py`

- [ ] **Step 1: Write failing Agent dispatch tests**

```python
def test_prepare_after_sales_dispatches_current_user_and_returns_pending_action():
    agent = CustomerServiceAgent(
        SequenceLLM(
            'Action: PrepareAfterSales[{"order_id":"ORD-A-C1",'
            '"request_type":"warranty_repair",'
            '"issue_cause":"non_human_fault",'
            '"packaging_intact":null,'
            '"issue_summary":"摄像头无法开机"}]'
        ),
        manager,
        [],
        after_sales_workflow=fake_workflow,
    )
    response = agent.run("我要保修", "alice-conv", current_user=CurrentUser("customer_alice", "Alice Test"))
    assert fake_workflow.calls[0][0].user_id == "customer_alice"
    assert response.type == "confirm_action"
    assert response.pending_action.action_id == "act-1"
    assert manager.messages[-1]["metadata"]["conversation_state"] == "awaiting_confirmation"

def test_prompt_advertises_prepare_after_sales_as_controlled_workflow_action():
    agent.run("我要保修", "alice-conv", current_user=user)
    assert "PrepareAfterSales" in llm.calls[0]["system_prompt"]
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_agent_workflow.py -q --basetemp=.pytest_cache\red_agent_workflow
```

Expected: failure because the Agent has no workflow dependency, current-user argument or pending-action response.

- [ ] **Step 3: Implement controlled dispatch**

Extend `AgentResponse`:

```python
@dataclass
class AgentResponse:
    type: str
    content: str
    conversation_id: str
    metadata: Optional[dict] = None
    citations: list = field(default_factory=list)
    pending_action: Optional[PendingActionView] = None
```

Add `after_sales_workflow=None` to the constructor and `current_user=None` to `run`. On `PrepareAfterSales`, decode `action_input` as a JSON object; invalid JSON produces a workflow-style `ask_user` response. For valid input call:

```python
result = self.after_sales_workflow.prepare(current_user, conversation_id, payload)
self.conversation_manager.add_message(
    conversation_id,
    "assistant",
    result.content,
    metadata={
        "action_type": result.response_type,
        "conversation_state": (
            "awaiting_confirmation" if result.response_type == "confirm_action"
            else states[result.response_type]
        ),
        **result.metadata,
    },
)
return AgentResponse(
    result.response_type, result.content, conversation_id,
    metadata=result.metadata, citations=result.citations,
    pending_action=result.pending_action,
)
```

Update the prompt with one allowed `PrepareAfterSales` JSON example and state that it creates only a待确认动作.

- [ ] **Step 4: Verify GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_agent_workflow.py tests\test_agent_actions.py tests\test_agent_citations.py -q --basetemp=.pytest_cache\green_agent_workflow
```

Expected: workflow and existing Agent tests pass.

### Task 3: Chat API Protocol and Application Wiring

**Files:**
- Create: `tests/test_chat_workflow.py`
- Modify: `apps/customer_service/schemas.py`
- Modify: `apps/customer_service/routes.py`
- Modify: `main.py`

- [ ] **Step 1: Write failing chat contract tests**

```python
def test_chat_forwards_current_user_and_serializes_confirm_action():
    response = client.post(
        "/api/chat",
        headers={"X-QA-User-Id": "customer_alice"},
        json={"conversation_id": "alice-conv", "message": "摄像头无法开机，申请保修"},
    )
    assert response.status_code == 200
    assert response.json()["type"] == "confirm_action"
    assert response.json()["pending_action"]["action_id"] == "act-1"
    assert app.state.agent.calls[0][2].user_id == "customer_alice"
```

- [ ] **Step 2: Verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_chat_workflow.py -q --basetemp=.pytest_cache\red_chat_workflow
```

Expected: schema rejects `confirm_action` or route does not forward the identity/pending action.

- [ ] **Step 3: Implement chat response extension and app assembly**

Move/reuse `PendingActionItem` above `ChatResponse` and extend it:

```python
type: Literal["final_answer", "ask_user", "confirm_action", "handoff"]
pending_action: Optional[PendingActionItem] = None
```

In `routes.chat`, call `agent.run(body.message, conversation_id, current_user=current_user)` and map `response.pending_action` into `PendingActionItem` when present.

In `main.py`, construct and inject:

```python
order_service = OrderQueryService(OrderRepository(conversation_manager.db))
ticket_action_service = TicketActionService(
    TicketRepository(conversation_manager.db),
    order_service,
    EligibilityRuleService(),
)
after_sales_workflow = AfterSalesWorkflow(ticket_action_service, retrieve_policy)
agent = CustomerServiceAgent(
    llm=chat_service,
    conversation_manager=conversation_manager,
    tools=[search_faq_tool],
    after_sales_workflow=after_sales_workflow,
    max_steps=5,
)
```

- [ ] **Step 4: Verify GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_chat_workflow.py tests\test_identity_and_conversations.py tests\test_action_routes.py -q --basetemp=.pytest_cache\green_chat_workflow
```

Expected: all selected endpoint tests pass.

### Task 4: Verification and Worklist Closure

**Files:**
- Modify: `docs/worklists/customer-service-multi-agent-worklist.md`

- [ ] **Step 1: Run full offline regression**

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest_cache\after_sales_workflow_full
.\.venv\Scripts\python.exe scripts\verify_migration.py
git diff --check
```

Expected: tests and migration verification pass; whitespace check reports no errors.

- [ ] **Step 2: Run local PostgreSQL workflow/confirmation smoke test**

Run `scripts\init_db.py` and `scripts\seed_mock_data.py`, then instantiate `AfterSalesWorkflow` with a deterministic policy result carrying one `Doc5-售后与保修政策` citation and real `TicketActionService`. Verify action creation does not create a ticket, then confirm twice and assert one resulting ticket with `idempotent_replay=True` on the second result.

- [ ] **Step 3: Update worklist**

Set `P1-012` and `P1-015` to `✅ DONE` only after verification. Record that `P1-017` now includes chat protocol support for `confirm_action` but remains open for remaining flow endpoints. Log RED/GREEN evidence, test count, migration result and database smoke-test result.

- [ ] **Step 4: Commit implementation**

```powershell
git add domain/customer_service/workflows.py domain/customer_service/agent.py domain/customer_service/prompts.py domain/customer_service/__init__.py apps/customer_service/schemas.py apps/customer_service/routes.py main.py tests/test_after_sales_workflow.py tests/test_agent_workflow.py tests/test_chat_workflow.py docs/worklists/customer-service-multi-agent-worklist.md
git commit -m "feat: integrate after-sales workflow into chat"
```

## Self-Review

- Coverage: policy-backed action creation, no-policy handoff, clarification/no-alternate-write rule, Agent dispatch, chat protocol, and real confirmation transaction each have an implementation/test task.
- Scope: the plan intentionally leaves ticket querying, audit persistence, other complete workflows, and child Agent decomposition outside this slice.
- Type contract: `WorkflowResult.pending_action` is the existing `PendingActionView`; the API maps it to the existing `PendingActionItem`; confirmation continues to accept only `action_id`.
- Placeholder scan: no unfinished implementation instructions remain; enumerated follow-up capabilities are explicit non-goals.
