# QA-agent Phase 1 Confirmed Ticket Write Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add persisted, conversation-bound pending actions and idempotent confirmed creation of mock service tickets without wiring the behavior into the chat Agent.

**Architecture:** A focused ticketing domain service uses existing authorized order reads and deterministic eligibility rules to issue pending actions. A PostgreSQL repository owns the confirmation transaction and row lock so repeated confirmations return one ticket. A protected FastAPI router exposes create/confirm endpoints for direct verification only.

**Tech Stack:** Python 3, dataclasses, FastAPI, PostgreSQL/psycopg2, pytest

---

## File Map And Boundary

| File | Responsibility |
| --- | --- |
| `infrastructure/models.py` | Table DDL and SQL for pending actions and service tickets. |
| `domain/customer_service/ticketing.py` | Domain DTOs, controlled errors, action creation and confirmation orchestration. |
| `utils/tickets.py` | PostgreSQL mapping and transaction-locked confirmation persistence. |
| `apps/customer_service/action_routes.py` | Protected create/confirm HTTP endpoints only. |
| `apps/customer_service/schemas.py` | Request/response schemas for action confirmation endpoints. |
| `main.py` | Construct ticket service and mount the new router, without changing Agent tools. |
| `tests/test_ticket_models.py` | Schema and repository transaction contract tests. |
| `tests/test_ticketing.py` | Domain tests for eligibility, expiry, revalidation and idempotency. |
| `tests/test_action_routes.py` | API tests for identity/conversation and HTTP result mapping. |
| `docs/worklists/customer-service-multi-agent-worklist.md` | State and verification evidence. |

Non-goals: no chat `confirm_action` dispatch, ticket query endpoint, audit table, Workflow, Supervisor, or Agent tool registration.

## Task 1: Ticket And Pending Action Persistence Contract

**Worklist ID:** `P1-004`

**Files:**
- Modify: `infrastructure/models.py`
- Create: `tests/test_ticket_models.py`
- Create: `utils/tickets.py`
- Modify: `utils/__init__.py`

- [ ] **Step 1: Write failing schema and atomic-confirmation tests**

Create `tests/test_ticket_models.py` with:

```python
from infrastructure.models import init_tables


class CaptureDB:
    def __init__(self):
        self.calls = []

    def execute(self, query, params=None, fetch=False):
        self.calls.append(query)


def test_init_tables_creates_pending_action_and_ticket_tables():
    db = CaptureDB()
    init_tables(db)
    sql = "\n".join(db.calls)
    assert "pending_actions" in sql
    assert "service_tickets" in sql
    assert "executed_ticket_id" in sql
```

Add a repository contract test using a fake connection/cursor that records SQL and returns a pending action row. It invokes:

```python
repository.confirm_with_lock("customer_alice", "alice-conv", "act-1", build_ticket)
```

Assert SQL includes `FOR UPDATE`, one ticket insert, and one action status update; calling with a row already marked `executed` returns its existing ticket and does not insert a second ticket.

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ticket_models.py -q --basetemp=.pytest_cache\red_ticket_models
```

Expected: fail because the new tables and `utils.tickets` repository do not exist.

- [ ] **Step 3: Add schema and repository transaction implementation**

Add DDL to `infrastructure/models.py`:

```python
CREATE_PENDING_ACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS pending_actions (
    action_id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL REFERENCES conversations(conversation_id),
    user_id VARCHAR(128) NOT NULL REFERENCES mock_customers(user_id),
    action_type VARCHAR(32) NOT NULL CHECK(action_type IN ('create_service_ticket')),
    order_id VARCHAR(32) NOT NULL REFERENCES mock_orders(order_id),
    ticket_type VARCHAR(32) NOT NULL,
    eligibility_code VARCHAR(64) NOT NULL,
    eligibility_payload JSONB NOT NULL,
    issue_summary TEXT NOT NULL,
    display_summary TEXT NOT NULL,
    status VARCHAR(16) NOT NULL CHECK(status IN ('pending', 'executed', 'expired', 'cancelled')),
    expires_at TIMESTAMP NOT NULL,
    executed_ticket_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
"""

CREATE_SERVICE_TICKETS_TABLE = """
CREATE TABLE IF NOT EXISTS service_tickets (
    ticket_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(128) NOT NULL REFERENCES mock_customers(user_id),
    order_id VARCHAR(32) NOT NULL REFERENCES mock_orders(order_id),
    ticket_type VARCHAR(32) NOT NULL,
    issue_summary TEXT NOT NULL,
    eligibility_code VARCHAR(64) NOT NULL,
    status VARCHAR(16) NOT NULL CHECK(status IN ('submitted')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
"""
```

Call both DDL statements from `init_tables`, and add SQL constants for action insert, action lock by `(action_id, conversation_id, user_id)`, ticket insert/read, and action executed update.

Create `utils/tickets.py` with `TicketRepository.create_action(action)` and:

```python
def confirm_with_lock(self, user_id, conversation_id, action_id, build_ticket):
    conn = self.db.get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(SELECT_PENDING_ACTION_FOR_UPDATE, (action_id, conversation_id, user_id))
            row = cur.fetchone()
            action = _to_pending_action(row) if row else None
            if action is None:
                conn.commit()
                return None, False
            if action.status == "executed":
                cur.execute(SELECT_SERVICE_TICKET_BY_ID, (action.executed_ticket_id, user_id))
                ticket = _to_service_ticket(cur.fetchone())
                conn.commit()
                return ticket, True
            ticket = build_ticket(action)
            cur.execute(INSERT_SERVICE_TICKET, _ticket_params(ticket))
            cur.execute(UPDATE_PENDING_ACTION_EXECUTED, (ticket.ticket_id, action.action_id))
            conn.commit()
            return ticket, False
    except Exception:
        conn.rollback()
        raise
    finally:
        self.db.return_connection(conn)
```

Export `TicketRepository` from `utils/__init__.py`.

- [ ] **Step 4: Run persistence tests to verify GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ticket_models.py tests\test_mock_data.py -q --basetemp=.pytest_cache\green_ticket_models
```

Expected: selected tests pass, including schema creation and transaction lock behavior.

## Task 2: Ticketing Domain Service

**Worklist IDs:** `P1-004`, `P1-009`

**Files:**
- Create: `domain/customer_service/ticketing.py`
- Modify: `domain/customer_service/__init__.py`
- Create: `tests/test_ticketing.py`

- [ ] **Step 1: Write failing domain tests**

Create tests that build `TicketActionService` with fake repositories and the existing `EligibilityRuleService`. Cover:

```python
def test_eligible_request_creates_pending_action_but_no_ticket():
    action = service.create_action("customer_alice", "alice-conv", request)
    assert action.status == "pending"
    assert repository.created_tickets == []

def test_ineligible_request_does_not_create_action():
    with pytest.raises(TicketEligibilityConflict):
        service.create_action("customer_alice", "alice-conv", damaged_request)
    assert repository.actions == []

def test_alternative_recommendation_does_not_silently_create_other_ticket_type():
    with pytest.raises(TicketEligibilityConflict):
        service.create_action("customer_alice", "alice-conv", expired_return_request)
    assert repository.actions == []

def test_confirm_revalidates_and_creates_ticket_once():
    first = service.confirm_action("customer_alice", "alice-conv", "act-1")
    second = service.confirm_action("customer_alice", "alice-conv", "act-1")
    assert first.ticket.ticket_id == second.ticket.ticket_id
    assert second.idempotent_replay is True

def test_expired_action_cannot_create_ticket():
    with pytest.raises(TicketActionConflict):
        service.confirm_action("customer_alice", "alice-conv", "expired-act")

def test_confirmation_rejects_when_recomputed_eligibility_is_no_longer_valid():
    with pytest.raises(TicketEligibilityConflict):
        service.confirm_action("customer_alice", "alice-conv", "expired-qualification-act")
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ticketing.py -q --basetemp=.pytest_cache\red_ticketing
```

Expected: fail because `domain.customer_service.ticketing` does not exist.

- [ ] **Step 3: Implement minimal ticketing domain service**

Create immutable dataclasses:

```python
@dataclass(frozen=True)
class TicketActionInput:
    order_id: str
    request_type: str
    issue_cause: str
    packaging_intact: Optional[bool]
    issue_summary: str

@dataclass(frozen=True)
class PendingActionView:
    action_id: str
    conversation_id: str
    user_id: str
    action_type: str
    order_id: str
    ticket_type: str
    eligibility_code: str
    eligibility_payload: dict
    issue_summary: str
    display_summary: str
    status: str
    expires_at: datetime
    executed_ticket_id: Optional[str] = None

@dataclass(frozen=True)
class ServiceTicketView:
    ticket_id: str
    user_id: str
    order_id: str
    ticket_type: str
    issue_summary: str
    eligibility_code: str
    status: str = "submitted"
```

Implement exceptions `TicketNotFound`, `TicketActionConflict` and `TicketEligibilityConflict`, plus `TicketActionService`. `create_action` reads the current user's order, evaluates eligibility with `now_fn().date()`, and creates an action only when `decision.eligible` is true and `decision.recommended_service == input.request_type`; a recommendation for a different service is returned as a conflict rather than silently converted into a write action. It persists a `PendingActionView` expiring after 30 minutes and never creates a ticket. `confirm_action` calls `repository.confirm_with_lock(...)`; the callback rejects non-pending/expired actions, rereads the authorized order, reruns `EligibilityRuleService` using saved payload and confirmation date, requires the same recommended ticket type, and creates one `ServiceTicketView`.

- [ ] **Step 4: Run domain tests to verify GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ticketing.py tests\test_eligibility.py tests\test_mock_order_tool.py -q --basetemp=.pytest_cache\green_ticketing
```

Expected: domain write-control tests and existing deterministic rule/tool tests pass.

## Task 3: Protected Action API

**Worklist ID:** `P1-009`

**Files:**
- Create: `apps/customer_service/action_routes.py`
- Modify: `apps/customer_service/schemas.py`
- Modify: `apps/customer_service/__init__.py`
- Modify: `main.py`
- Create: `tests/test_action_routes.py`

- [ ] **Step 1: Write failing API tests**

Create a FastAPI test app using existing `get_current_user` behavior, an owned/foreign conversation manager, and a fake ticket action service. Cover:

```python
def test_create_action_requires_owned_conversation():
    response = client.post("/api/conversations/bob-conv/actions", headers=alice, json=payload)
    assert response.status_code == 404

def test_eligible_request_returns_confirm_action():
    response = client.post("/api/conversations/alice-conv/actions", headers=alice, json=payload)
    assert response.status_code == 200
    assert response.json()["type"] == "confirm_action"

def test_confirmation_returns_ticket_and_idempotency_flag():
    response = client.post("/api/conversations/alice-conv/actions/act-1/confirm", headers=alice)
    assert response.status_code == 200
    assert response.json()["ticket"]["ticket_id"] == "ticket-1"

def test_action_conflict_maps_to_409():
    response = client.post("/api/conversations/alice-conv/actions/expired/confirm", headers=alice)
    assert response.status_code == 409
```

- [ ] **Step 2: Run tests to verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_action_routes.py -q --basetemp=.pytest_cache\red_action_routes
```

Expected: fail because action router/schemas do not exist.

- [ ] **Step 3: Implement action schemas and router**

Add request and response models to `apps/customer_service/schemas.py` for the input payload, `PendingActionItem`, `CreatePendingActionResponse`, `ServiceTicketItem`, and `ConfirmTicketResponse`.

Create `apps/customer_service/action_routes.py`:

```python
@router.post("/conversations/{conversation_id}/actions", response_model=CreatePendingActionResponse)
async def create_action(request, conversation_id, body, current_user=Depends(get_current_user)):
    _require_owned_conversation(request.app.state.conversation_manager, conversation_id, current_user)
    try:
        action = request.app.state.ticket_action_service.create_action(
            current_user.user_id, conversation_id, TicketActionInput(...)
        )
    except TicketNotFound:
        raise HTTPException(status_code=404, detail="订单不存在")
    except TicketEligibilityConflict as exc:
        raise HTTPException(status_code=409, detail={"code": exc.code})
    return ...
```

Add a confirm endpoint mapping `TicketNotFound` to `404` and ticket/action conflicts to `409`. Mount `action_router` in `main.py` and construct `TicketActionService(TicketRepository(conversation_manager.db), app.state.order_service, EligibilityRuleService())`. Do not add new tools to `CustomerServiceAgent`.

- [ ] **Step 4: Run API tests to verify GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_action_routes.py tests\test_identity_and_conversations.py tests\test_orders_api.py -q --basetemp=.pytest_cache\green_action_routes
```

Expected: new action API tests pass and existing identity/authorized order API tests remain green.

## Task 4: Full Verification And Worklist Closure

**Worklist IDs:** `DOC-012`, `P1-004`, `P1-009`

**Files:**
- Modify: `docs/worklists/customer-service-multi-agent-worklist.md`

- [ ] **Step 1: Run full offline and bootstrap validation**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest_cache\tmp
.\.venv\Scripts\python.exe scripts\verify_migration.py
.\.venv\Scripts\python.exe scripts\init_db.py
git diff --check
```

Expected: all tests pass, migration imports pass, PostgreSQL schema bootstrap creates the new tables, and no whitespace errors are reported.

- [ ] **Step 2: Run local database idempotency verification**

Run a small authenticated TestClient or direct service script against local PostgreSQL that:

```text
creates an owned conversation
creates a warranty-repair pending action for an eligible order
confirms it once and records ticket_id
confirms the same action again
checks both confirmation results have the same ticket_id
checks exactly one service_tickets row exists for that action/order
```

Expected: the repeated confirmation reuses the initial ticket.

- [ ] **Step 3: Update worklist with exact evidence**

After Steps 1-2 pass, mark `DOC-012`, `P1-004`, and `P1-009` as `✅ DONE`, record test counts and database idempotency evidence, and leave `P1-010`, `P1-012` through `P1-017`, and audit work as `PENDING`.

- [ ] **Step 4: Commit verified implementation**

Run:

```powershell
git add infrastructure domain utils apps main.py tests docs\worklists\customer-service-multi-agent-worklist.md docs\superpowers
git commit -m "feat: add confirmed mock ticket creation"
```

Expected: one implementation commit for only the confirmed ticket-write slice and evidence.

## Self-Review

### Spec Coverage

| Requirement | Task |
| --- | --- |
| Persistent pending action and service ticket models | Task 1 |
| User/conversation binding | Tasks 2-3 |
| Server-generated action from authorized eligible facts | Task 2 |
| Confirmation revalidation | Task 2 |
| Row-locked idempotent ticket creation | Task 1-2 |
| Protected create/confirm endpoints | Task 3 |
| No Agent/Workflow integration | File map and Task 3 boundary |
| Local PostgreSQL evidence | Task 4 |

### Consistency Checks

- `TicketActionService` does not accept client-provided eligibility results or ticket IDs.
- A suggested alternate service never becomes a pending write action without a new explicit request for that service.
- `TicketRepository.confirm_with_lock` is the only write path that creates a ticket and marks an action executed.
- New routes expose controlled write foundations only; they do not alter `CustomerServiceAgent.tools`.
- Ticket read/query and audit tasks remain outside this slice.

### No-Placeholder Check

This plan contains no unresolved placeholders or speculative functionality outside `P1-004` and `P1-009`.
