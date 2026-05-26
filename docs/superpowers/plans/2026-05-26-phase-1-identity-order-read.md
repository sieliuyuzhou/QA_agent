# QA-agent Phase 1 Identity And Order Read Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first Phase 1 slice of `QA-agent`: internal test-user identity, conversation ownership enforcement, deterministic mock customer/product/order data, and authorized read-only order APIs.

**Architecture:** Protected HTTP routes receive `X-QA-User-Id` and resolve it through a deterministic mock-customer repository into a `CurrentUser` context. Conversation and order access are scoped to that current user in deterministic Python/database services; the Agent does not receive an order tool in this slice. PostgreSQL schema/bootstrap and deterministic seed data supply the mock facts.

**Tech Stack:** Python 3.11, FastAPI/Pydantic, PostgreSQL/psycopg2, pytest/TestClient.

---

## 1. Scope And Constraints

**Specification:** `docs/superpowers/specs/2026-05-26-phase-1-identity-order-read-design.md`

**Worklist IDs implemented by this plan:** `P1-001`, `P1-002`, `P1-003`.

**Partially prepared only:** `P1-006` receives a reusable `OrderQueryService` foundation, but remains open because no `MockOrderTool` is registered with the Agent in this slice.

**Hard boundaries:**

- All product/user-visible documentation says `QA-agent`; Python identifiers remain legal identifiers such as `customer_service`.
- `X-QA-User-Id` is an internal testing identity mechanism, not production authentication.
- No qualification decision, ticket creation, confirmation action, audit event model, Supervisor, or child Agent is introduced.
- No live LLM/Embedding request is required for verification.

## 2. File Map

| File | Responsibility |
| --- | --- |
| `infrastructure/models.py` | Mock customer/product/order schema and SQL constants |
| `scripts/seed_mock_data.py` | Idempotent internal test dataset seeding |
| `domain/customer_service/context.py` | Immutable `CurrentUser` and `OrderView` domain DTOs |
| `utils/mock_data.py` | Deterministic customer and order repository queries |
| `domain/customer_service/orders.py` | Read-only authorized order query service |
| `apps/customer_service/dependencies.py` | Resolve `X-QA-User-Id` to `CurrentUser` |
| `apps/customer_service/routes.py` | Protect existing conversation/chat endpoints |
| `apps/customer_service/order_routes.py` | Expose read-only order endpoints |
| `apps/customer_service/schemas.py` | Order response models; remove caller-selected create user |
| `apps/customer_service/__init__.py` | Export both route groups and response types |
| `main.py` | Wire repositories/services and advertise `QA-agent` APIs |
| `scripts/smoke_test.py` | Use internal identity headers for opt-in persistent smoke tests |
| `README.md`, `docs/pgsql_setup.md` | Explain internal seed/bootstrap and request header |
| `tests/test_mock_data.py` | Schema/seed/repository/service unit tests |
| `tests/test_identity_and_conversations.py` | Identity and conversation authorization API tests |
| `tests/test_orders_api.py` | Order API isolation tests |
| `docs/worklists/customer-service-multi-agent-worklist.md` | Task state and evidence |

## Task 1: Add Deterministic Mock Data Schema And Seed

**Worklist IDs:** `P1-003`

**Files:**
- Modify: `infrastructure/models.py`
- Create: `scripts/seed_mock_data.py`
- Create: `tests/test_mock_data.py`
- Modify: `docs/worklists/customer-service-multi-agent-worklist.md`

- [ ] **Step 1: Mark mock data work in progress**

Set `P1-003` to `IN_PROGRESS` and set the current execution stage to Phase 1 Task 1.

- [ ] **Step 2: Write failing schema and seed tests**

Create `tests/test_mock_data.py` with the first tests:

```python
from scripts.seed_mock_data import CUSTOMERS, ORDERS, PRODUCTS, seed_mock_data
from infrastructure.models import init_tables


class CaptureDB:
    def __init__(self):
        self.calls = []

    def execute(self, query, params=None, fetch=False):
        self.calls.append((query, params))
        return []


def test_init_tables_creates_mock_business_tables():
    db = CaptureDB()

    init_tables(db)

    sql = "\n".join(query for query, _ in db.calls)
    assert "mock_customers" in sql
    assert "products" in sql
    assert "mock_orders" in sql


def test_seed_data_has_two_customers_and_all_supported_products():
    assert {row[0] for row in CUSTOMERS} >= {"customer_alice", "customer_bob"}
    assert {row[0] for row in PRODUCTS} == {"X1", "X2", "C1", "G2"}
    assert {row[1] for row in ORDERS} >= {"customer_alice", "customer_bob"}


def test_seed_mock_data_uses_idempotent_inserts():
    db = CaptureDB()

    seed_mock_data(db)

    sql = "\n".join(query for query, _ in db.calls)
    assert "ON CONFLICT" in sql
    assert len(db.calls) == len(CUSTOMERS) + len(PRODUCTS) + len(ORDERS)
```

- [ ] **Step 3: Run tests to verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_mock_data.py -q --basetemp=.pytest_cache\tmp
```

Expected: tests fail for the missing mock table SQL and seed module/behavior. During execution, keep imports for not-yet-created modules inside test functions or turn their absence into an assertion failure, so RED is a behavioral failure rather than a collection error.

- [ ] **Step 4: Add mock schema and idempotent insert constants**

In `infrastructure/models.py`, add schema constants before existing insert/query constants:

```python
CREATE_MOCK_CUSTOMERS_TABLE = """
CREATE TABLE IF NOT EXISTS mock_customers (
    user_id       VARCHAR(128) PRIMARY KEY,
    display_name  VARCHAR(128) NOT NULL,
    status        VARCHAR(16) NOT NULL CHECK(status IN ('active', 'disabled')),
    created_at    TIMESTAMP DEFAULT NOW()
);
"""

CREATE_PRODUCTS_TABLE = """
CREATE TABLE IF NOT EXISTS products (
    product_id   VARCHAR(16) PRIMARY KEY,
    name         VARCHAR(128) NOT NULL,
    category     VARCHAR(32) NOT NULL
);
"""

CREATE_MOCK_ORDERS_TABLE = """
CREATE TABLE IF NOT EXISTS mock_orders (
    order_id      VARCHAR(32) PRIMARY KEY,
    user_id       VARCHAR(128) NOT NULL REFERENCES mock_customers(user_id),
    product_id    VARCHAR(16) NOT NULL REFERENCES products(product_id),
    purchased_at  DATE NOT NULL,
    status        VARCHAR(16) NOT NULL,
    amount        NUMERIC(10, 2) NOT NULL,
    created_at    TIMESTAMP DEFAULT NOW()
);
"""

UPSERT_MOCK_CUSTOMER = """
INSERT INTO mock_customers (user_id, display_name, status)
VALUES (%s, %s, %s)
ON CONFLICT (user_id) DO UPDATE
SET display_name = EXCLUDED.display_name, status = EXCLUDED.status;
"""

UPSERT_PRODUCT = """
INSERT INTO products (product_id, name, category)
VALUES (%s, %s, %s)
ON CONFLICT (product_id) DO UPDATE
SET name = EXCLUDED.name, category = EXCLUDED.category;
"""

UPSERT_MOCK_ORDER = """
INSERT INTO mock_orders (order_id, user_id, product_id, purchased_at, status, amount)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (order_id) DO UPDATE
SET user_id = EXCLUDED.user_id,
    product_id = EXCLUDED.product_id,
    purchased_at = EXCLUDED.purchased_at,
    status = EXCLUDED.status,
    amount = EXCLUDED.amount;
"""
```

Extend `init_tables()` in dependency order:

```python
def init_tables(db_manager):
    db_manager.execute(CREATE_CONVERSATIONS_TABLE)
    db_manager.execute(CREATE_MESSAGES_TABLE)
    db_manager.execute(CREATE_MOCK_CUSTOMERS_TABLE)
    db_manager.execute(CREATE_PRODUCTS_TABLE)
    db_manager.execute(CREATE_MOCK_ORDERS_TABLE)
    db_manager.execute(CREATE_INDEXES)
```

- [ ] **Step 5: Add the deterministic seed script**

Create `scripts/seed_mock_data.py`:

```python
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.database import DatabaseManager
from infrastructure.models import (
    UPSERT_MOCK_CUSTOMER,
    UPSERT_MOCK_ORDER,
    UPSERT_PRODUCT,
)


CUSTOMERS = [
    ("customer_alice", "Alice Test", "active"),
    ("customer_bob", "Bob Test", "active"),
    ("customer_disabled", "Disabled Test", "disabled"),
]

PRODUCTS = [
    ("X1", "X1 智能门锁", "smart_lock"),
    ("X2", "X2 智能门锁", "smart_lock"),
    ("C1", "C1 智能摄像头", "camera"),
    ("G2", "G2 智能网关", "gateway"),
]

ORDERS = [
    ("ORD-A-X1", "customer_alice", "X1", "2026-05-22", "delivered", "1299.00"),
    ("ORD-A-C1", "customer_alice", "C1", "2026-03-01", "completed", "399.00"),
    ("ORD-B-X2", "customer_bob", "X2", "2026-05-20", "delivered", "1599.00"),
    ("ORD-B-G2", "customer_bob", "G2", "2025-10-10", "completed", "299.00"),
]


def seed_mock_data(db) -> None:
    for row in CUSTOMERS:
        db.execute(UPSERT_MOCK_CUSTOMER, row)
    for row in PRODUCTS:
        db.execute(UPSERT_PRODUCT, row)
    for row in ORDERS:
        db.execute(UPSERT_MOCK_ORDER, row)


def main() -> int:
    load_dotenv()
    db = DatabaseManager(os.getenv("CONVERSATION_DB_URL", ""))
    try:
        seed_mock_data(db)
        print("[SUCCESS] QA-agent mock customer and order data seeded.")
        return 0
    finally:
        db.close_all()


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 6: Verify and commit mock data baseline**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_mock_data.py tests\test_health_and_initialization.py -q --basetemp=.pytest_cache\tmp
git diff --check
```

Expected: all selected tests pass and diff check exits `0`.

Set `P1-003` to `✅ DONE`, add evidence to the progress log, then commit:

```powershell
git add infrastructure\models.py scripts\seed_mock_data.py tests\test_mock_data.py docs\worklists\customer-service-multi-agent-worklist.md
git commit -m "feat: add mock customer and order seed data"
```

## Task 2: Resolve Internal Test Identity

**Worklist IDs:** `P1-001`

**Files:**
- Create: `domain/customer_service/context.py`
- Create: `utils/mock_data.py`
- Modify: `utils/__init__.py`
- Create: `apps/customer_service/dependencies.py`
- Modify: `main.py`
- Modify: `tests/test_mock_data.py`
- Create: `tests/test_identity_and_conversations.py`
- Modify: `docs/worklists/customer-service-multi-agent-worklist.md`

- [ ] **Step 1: Mark identity task in progress**

Set `P1-001` to `IN_PROGRESS`.

- [ ] **Step 2: Write failing tests for repository identity resolution and HTTP dependency**

Append to `tests/test_mock_data.py`:

```python
from utils.mock_data import CustomerRepository


class RowDB:
    def __init__(self, row):
        self.row = row
        self.calls = []

    def execute_one(self, query, params=None, fetch=False):
        self.calls.append((query, params, fetch))
        return self.row


def test_customer_repository_returns_only_active_user_context():
    db = RowDB(("customer_alice", "Alice Test", "active"))

    user = CustomerRepository(db).find_active("customer_alice")

    assert user.user_id == "customer_alice"
    assert db.calls[0][1] == ("customer_alice",)


def test_customer_repository_rejects_missing_user():
    assert CustomerRepository(RowDB(None)).find_active("unknown") is None
```

Create `tests/test_identity_and_conversations.py` initially with:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.customer_service.routes import router
from domain.customer_service.context import CurrentUser


class FakeCustomerRepository:
    def find_active(self, user_id):
        if user_id == "customer_alice":
            return CurrentUser("customer_alice", "Alice Test")
        return None


def build_client():
    app = FastAPI()
    app.state.customer_repository = FakeCustomerRepository()
    app.include_router(router, prefix="/api")
    return TestClient(app)


def test_protected_conversation_endpoint_requires_internal_user_header():
    with build_client() as client:
        response = client.get("/api/conversations")

    assert response.status_code == 401
```

- [ ] **Step 3: Run identity tests to verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_mock_data.py tests\test_identity_and_conversations.py -q --basetemp=.pytest_cache\tmp
```

Expected: tests fail because the identity repository/dependency or authorization behavior does not exist. During execution, introduce tests incrementally so missing new modules fail from assertions inside tests rather than collection errors.

- [ ] **Step 4: Create immutable identity DTO and repository**

Create `domain/customer_service/context.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    display_name: str
```

Add to `infrastructure/models.py`:

```python
SELECT_ACTIVE_MOCK_CUSTOMER = """
SELECT user_id, display_name, status
FROM mock_customers
WHERE user_id = %s AND status = 'active';
"""
```

Create `utils/mock_data.py` with the customer portion:

```python
from typing import Optional

from domain.customer_service.context import CurrentUser
from infrastructure.models import SELECT_ACTIVE_MOCK_CUSTOMER


class CustomerRepository:
    def __init__(self, db):
        self.db = db

    def find_active(self, user_id: str) -> Optional[CurrentUser]:
        row = self.db.execute_one(
            SELECT_ACTIVE_MOCK_CUSTOMER,
            (user_id,),
            fetch=True,
        )
        if not row:
            return None
        return CurrentUser(user_id=row[0], display_name=row[1])
```

Export `CustomerRepository` from `utils/__init__.py`.

- [ ] **Step 5: Implement the FastAPI identity dependency and application wiring**

Create `apps/customer_service/dependencies.py`:

```python
from typing import Optional

from fastapi import Header, HTTPException, Request

from domain.customer_service.context import CurrentUser


async def get_current_user(
    request: Request,
    x_qa_user_id: Optional[str] = Header(default=None, alias="X-QA-User-Id"),
) -> CurrentUser:
    if not x_qa_user_id:
        raise HTTPException(status_code=401, detail="缺少内部试用用户标识")
    user = request.app.state.customer_repository.find_active(x_qa_user_id)
    if not user:
        raise HTTPException(status_code=401, detail="内部试用用户不可用")
    return user
```

In `main.py`, construct the repository from the already-owned application database pool:

```python
from utils import ConversationManager, CustomerRepository

# inside lifespan after conversation_manager creation
app.state.customer_repository = CustomerRepository(conversation_manager.db)
```

In `apps/customer_service/routes.py`, add `Depends(get_current_user)` to protected route signatures. For this task, the failing header test only requires the dependency to run; ownership behavior is completed in Task 3.

- [ ] **Step 6: Verify and commit internal identity**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_mock_data.py tests\test_identity_and_conversations.py tests\test_health_and_initialization.py -q --basetemp=.pytest_cache\tmp
git diff --check
```

Set `P1-001` to `✅ DONE`, log evidence, then commit:

```powershell
git add domain\customer_service\context.py infrastructure\models.py utils apps\customer_service\dependencies.py apps\customer_service\routes.py main.py tests docs\worklists\customer-service-multi-agent-worklist.md
git commit -m "feat: add internal test user context"
```

## Task 3: Enforce Conversation Ownership

**Worklist IDs:** `P1-002`

**Files:**
- Modify: `apps/customer_service/routes.py`
- Modify: `apps/customer_service/schemas.py`
- Modify: `apps/customer_service/__init__.py`
- Modify: `scripts/smoke_test.py`
- Modify: `tests/test_identity_and_conversations.py`
- Modify: `docs/worklists/customer-service-multi-agent-worklist.md`

- [ ] **Step 1: Mark conversation authorization task in progress**

Set `P1-002` to `IN_PROGRESS`.

- [ ] **Step 2: Add failing route authorization tests**

Expand `tests/test_identity_and_conversations.py` with in-memory route doubles:

```python
class FakeConversationManager:
    def __init__(self):
        self.created_for = []
        self.conversations = {
            "alice-conv": {
                "conversation_id": "alice-conv",
                "user_id": "customer_alice",
                "title": None,
                "status": "active",
                "created_at": "2026-05-26",
                "updated_at": "2026-05-26",
            },
            "bob-conv": {
                "conversation_id": "bob-conv",
                "user_id": "customer_bob",
                "title": None,
                "status": "active",
                "created_at": "2026-05-26",
                "updated_at": "2026-05-26",
            },
        }

    def create(self, user_id):
        self.created_for.append(user_id)
        return "alice-conv"

    def get_conversation(self, conversation_id):
        return self.conversations.get(conversation_id)

    def list_conversations(self, user_id):
        return [row for row in self.conversations.values() if row["user_id"] == user_id]

    def get_history(self, conversation_id):
        return []


class FakeAgent:
    called = False

    def run(self, message, conversation_id):
        self.called = True
        raise AssertionError("unauthorized chat must not reach agent")


def test_create_conversation_uses_header_identity():
    with build_client() as client:
        response = client.post(
            "/api/conversations",
            headers={"X-QA-User-Id": "customer_alice"},
        )
    assert response.status_code == 200
    assert response.json()["user_id"] == "customer_alice"


def test_other_users_conversation_is_hidden():
    with build_client() as client:
        response = client.get(
            "/api/conversations/bob-conv",
            headers={"X-QA-User-Id": "customer_alice"},
        )
    assert response.status_code == 404


def test_chat_cannot_continue_other_users_conversation():
    with build_client() as client:
        response = client.post(
            "/api/chat",
            headers={"X-QA-User-Id": "customer_alice"},
            json={"conversation_id": "bob-conv", "message": "查看进展"},
        )
    assert response.status_code == 404
```

Update `build_client()` to attach `FakeConversationManager` and `FakeAgent` to application state.

- [ ] **Step 3: Run authorization tests to verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_identity_and_conversations.py -q --basetemp=.pytest_cache\tmp
```

Expected: tests fail because routes still accept caller-provided `user_id` and do not filter fetched conversations by the resolved identity.

- [ ] **Step 4: Make existing conversation routes identity scoped**

In `apps/customer_service/routes.py`:

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from domain.customer_service.context import CurrentUser
from .dependencies import get_current_user


def _require_owned_conversation(conversation_manager, conversation_id, current_user):
    conversation = conversation_manager.get_conversation(conversation_id)
    if not conversation or conversation["user_id"] != current_user.user_id:
        raise HTTPException(status_code=404, detail="会话不存在")
    return conversation
```

Use this helper before chat continuation and conversation detail reads. For new chats and creates, call:

```python
conversation_id = conversation_manager.create(user_id=current_user.user_id)
```

Replace the list handler with no caller-selected `user_id`:

```python
@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
):
    conversations = request.app.state.conversation_manager.list_conversations(
        current_user.user_id
    )
    ...
```

Remove `CreateConversationRequest` usage from `POST /conversations`; it should take only `request` and `current_user`. Remove that schema/export if no caller uses it.

- [ ] **Step 5: Keep opt-in smoke callers consistent**

In `scripts/smoke_test.py`, the external API test must seed/use an internal test identity after Task 1:

```python
headers = {"X-QA-User-Id": "customer_alice"}
response = client.post("/api/conversations", headers=headers)
response = client.post("/api/chat", headers=headers, json={...})
response = client.get(f"/api/conversations/{conversation_id}", headers=headers)
response = client.get("/api/conversations", headers=headers)
```

- [ ] **Step 6: Verify and commit conversation isolation**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_identity_and_conversations.py tests\test_agent_actions.py tests\test_agent_citations.py -q --basetemp=.pytest_cache\tmp
git diff --check
```

Set `P1-002` to `✅ DONE`, record evidence, then commit:

```powershell
git add apps scripts\smoke_test.py tests docs\worklists\customer-service-multi-agent-worklist.md
git commit -m "feat: enforce conversation ownership"
```

## Task 4: Expose Authorized Read-Only Order APIs

**Worklist IDs:** foundation for `P1-006`; do not close `P1-006`.

**Files:**
- Modify: `domain/customer_service/context.py`
- Create: `domain/customer_service/orders.py`
- Modify: `domain/customer_service/__init__.py`
- Modify: `utils/mock_data.py`
- Modify: `utils/__init__.py`
- Modify: `infrastructure/models.py`
- Modify: `apps/customer_service/schemas.py`
- Create: `apps/customer_service/order_routes.py`
- Modify: `apps/customer_service/__init__.py`
- Modify: `main.py`
- Modify: `tests/test_mock_data.py`
- Create: `tests/test_orders_api.py`
- Modify: `README.md`
- Modify: `docs/worklists/customer-service-multi-agent-worklist.md`

- [ ] **Step 1: Add a worklist note for the order-read foundation**

Keep `P1-006` as `PENDING`, but update its note to state that the authorized API/service foundation is being implemented and the Agent tool remains outstanding.

- [ ] **Step 2: Write failing service and API isolation tests**

Append to `tests/test_mock_data.py`:

```python
from domain.customer_service.orders import OrderQueryService
from utils.mock_data import OrderRepository


def test_order_repository_scopes_detail_query_to_user():
    db = RowDB(("ORD-A-X1", "X1", "X1 智能门锁", "smart_lock", "2026-05-22", "delivered", "1299.00"))

    order = OrderQueryService(OrderRepository(db)).get_order(
        "customer_alice", "ORD-A-X1"
    )

    assert order.order_id == "ORD-A-X1"
    assert db.calls[0][1] == ("ORD-A-X1", "customer_alice")
```

Create `tests/test_orders_api.py`:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.customer_service.order_routes import router
from domain.customer_service.context import CurrentUser, OrderView


class FakeCustomerRepository:
    def find_active(self, user_id):
        if user_id == "customer_alice":
            return CurrentUser("customer_alice", "Alice Test")
        return None


class FakeOrderService:
    def list_orders(self, user_id, status=None):
        assert user_id == "customer_alice"
        return [
            OrderView("ORD-A-X1", "X1", "X1 智能门锁", "smart_lock", "2026-05-22", "delivered", "1299.00")
        ]

    def get_order(self, user_id, order_id):
        assert user_id == "customer_alice"
        if order_id == "ORD-A-X1":
            return self.list_orders(user_id)[0]
        return None


def build_client():
    app = FastAPI()
    app.state.customer_repository = FakeCustomerRepository()
    app.state.order_service = FakeOrderService()
    app.include_router(router, prefix="/api")
    return TestClient(app)


def test_order_list_requires_internal_identity():
    with build_client() as client:
        response = client.get("/api/orders")
    assert response.status_code == 401


def test_current_user_can_list_owned_orders():
    with build_client() as client:
        response = client.get(
            "/api/orders",
            headers={"X-QA-User-Id": "customer_alice"},
        )
    assert response.status_code == 200
    assert response.json()["orders"][0]["order_id"] == "ORD-A-X1"


def test_unowned_order_is_not_disclosed():
    with build_client() as client:
        response = client.get(
            "/api/orders/ORD-B-X2",
            headers={"X-QA-User-Id": "customer_alice"},
        )
    assert response.status_code == 404
```

- [ ] **Step 3: Run order tests to verify RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_mock_data.py tests\test_orders_api.py -q --basetemp=.pytest_cache\tmp
```

Expected: tests fail because the order service/API behavior is missing. During execution, introduce tests incrementally so missing new modules are observed as expected assertion failures rather than collection errors.

- [ ] **Step 4: Implement read-only order DTO, repository and service**

Append to `domain/customer_service/context.py`:

```python
@dataclass(frozen=True)
class OrderView:
    order_id: str
    product_id: str
    product_name: str
    category: str
    purchased_at: str
    status: str
    amount: str
```

Add SQL constants to `infrastructure/models.py`:

```python
SELECT_ORDERS_BY_USER = """
SELECT o.order_id, p.product_id, p.name, p.category, o.purchased_at,
       o.status, o.amount
FROM mock_orders o
JOIN products p ON p.product_id = o.product_id
WHERE o.user_id = %s AND (%s IS NULL OR o.status = %s)
ORDER BY o.purchased_at DESC, o.order_id ASC;
"""

SELECT_ORDER_BY_ID_AND_USER = """
SELECT o.order_id, p.product_id, p.name, p.category, o.purchased_at,
       o.status, o.amount
FROM mock_orders o
JOIN products p ON p.product_id = o.product_id
WHERE o.order_id = %s AND o.user_id = %s;
"""
```

Extend `utils/mock_data.py`:

```python
from domain.customer_service.context import CurrentUser, OrderView
from infrastructure.models import (
    SELECT_ACTIVE_MOCK_CUSTOMER,
    SELECT_ORDER_BY_ID_AND_USER,
    SELECT_ORDERS_BY_USER,
)


def _to_order_view(row):
    return OrderView(
        order_id=row[0],
        product_id=row[1],
        product_name=row[2],
        category=row[3],
        purchased_at=str(row[4]),
        status=row[5],
        amount=str(row[6]),
    )


class OrderRepository:
    def __init__(self, db):
        self.db = db

    def list_for_user(self, user_id, status=None):
        rows = self.db.execute(
            SELECT_ORDERS_BY_USER,
            (user_id, status, status),
            fetch=True,
        )
        return [_to_order_view(row) for row in rows]

    def get_for_user(self, user_id, order_id):
        row = self.db.execute_one(
            SELECT_ORDER_BY_ID_AND_USER,
            (order_id, user_id),
            fetch=True,
        )
        return _to_order_view(row) if row else None
```

Create `domain/customer_service/orders.py`:

```python
class OrderQueryService:
    def __init__(self, repository):
        self.repository = repository

    def list_orders(self, user_id: str, status: str = None):
        return self.repository.list_for_user(user_id, status=status)

    def get_order(self, user_id: str, order_id: str):
        return self.repository.get_for_user(user_id, order_id)
```

- [ ] **Step 5: Implement order response schemas and endpoints**

Add to `apps/customer_service/schemas.py`:

```python
class OrderItem(BaseModel):
    order_id: str
    product_id: str
    product_name: str
    category: str
    purchased_at: str
    status: str
    amount: str


class OrderListResponse(BaseModel):
    orders: List[OrderItem] = Field(default_factory=list)
    total: int
```

Create `apps/customer_service/order_routes.py`:

```python
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from domain.customer_service.context import CurrentUser
from .dependencies import get_current_user
from .schemas import OrderItem, OrderListResponse

router = APIRouter(tags=["orders"])


def _to_item(order):
    return OrderItem(**order.__dict__)


@router.get("/orders", response_model=OrderListResponse)
async def list_orders(
    request: Request,
    status: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    orders = request.app.state.order_service.list_orders(current_user.user_id, status)
    return OrderListResponse(orders=[_to_item(item) for item in orders], total=len(orders))


@router.get("/orders/{order_id}", response_model=OrderItem)
async def get_order(
    request: Request,
    order_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    order = request.app.state.order_service.get_order(current_user.user_id, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return _to_item(order)
```

Wire `OrderRepository` and `OrderQueryService` in `main.py` using `conversation_manager.db`, include `order_router` under `/api`, and export relevant symbols from package `__init__.py` files.

- [ ] **Step 6: Document internal test usage**

In `README.md` and `docs/pgsql_setup.md`, add the controlled setup and request examples:

```powershell
.\.venv\Scripts\python.exe scripts\init_db.py
.\.venv\Scripts\python.exe scripts\seed_mock_data.py

$headers = @{ "X-QA-User-Id" = "customer_alice" }
Invoke-RestMethod -Uri http://localhost:8000/api/orders -Headers $headers
```

State that the header is only for internal trial data and must not be used as production authentication.

- [ ] **Step 7: Verify and commit authorized order-read foundation**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_mock_data.py tests\test_orders_api.py tests\test_identity_and_conversations.py -q --basetemp=.pytest_cache\tmp
git diff --check
```

Update the `P1-006` note to record that API/service groundwork is complete while the Tool remains pending, add progress evidence, then commit:

```powershell
git add domain utils infrastructure apps main.py README.md docs\pgsql_setup.md tests docs\worklists\customer-service-multi-agent-worklist.md
git commit -m "feat: add authorized mock order reads"
```

## Task 5: Bootstrap Locally And Verify The Slice

**Worklist IDs:** verification for `P1-001`, `P1-002`, `P1-003`; no milestone closure.

**Files:**
- Modify: `docs/worklists/customer-service-multi-agent-worklist.md`

- [ ] **Step 1: Run all offline regression tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.pytest_cache\tmp
.\.venv\Scripts\python.exe scripts\verify_migration.py
git diff --check
```

Expected: all tests and import verification pass without external LLM/Embedding calls.

- [ ] **Step 2: Seed the local PostgreSQL mock dataset**

The schema and seed operations use `CREATE IF NOT EXISTS` and `ON CONFLICT`, so they are idempotent and preserve existing conversation data.

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

- [ ] **Step 3: Run a local authorized read verification without LLM calls**

Run a direct repository/service query or a FastAPI `TestClient` request against `GET /api/orders` using `X-QA-User-Id: customer_alice`. Do not invoke `/api/chat` because it can call the configured LLM.

Expected: Alice receives only orders with IDs beginning `ORD-A-`; querying `ORD-B-X2` returns `404`.

- [ ] **Step 4: Update the worklist and commit verification evidence**

Add exact results to the progress log. `P1-001`, `P1-002`, and `P1-003` must already be `✅ DONE`; `P1-006` remains `PENDING` with the order-read foundation note.

```powershell
git add docs\worklists\customer-service-multi-agent-worklist.md
git commit -m "docs: record phase one identity slice verification"
```

## 3. Self-Review

### Specification Coverage

| Specification Requirement | Implementing Task |
| --- | --- |
| `QA-agent` internal identity context | Task 2 |
| Conversation create/list/read/chat ownership boundary | Task 3 |
| Mock customers/products/orders and repeatable seed | Task 1 |
| Authorized order listing/detail read | Task 4 |
| Service foundation reusable by future `MockOrderTool` | Task 4 |
| No Agent tool/write operation/multi-agent work in this slice | Explicit boundary; `P1-006` remains open |
| Offline plus local database evidence | Task 5 |

### Consistency Checks

- `X-QA-User-Id` is resolved once through `CustomerRepository`; route clients cannot select an arbitrary `user_id`.
- Order detail SQL always includes `(order_id, current_user.user_id)`, so `404` is returned for missing and unowned orders alike.
- Schema initialization remains explicit through `scripts/init_db.py`; deterministic sample rows are separately inserted through `scripts/seed_mock_data.py`.
- This plan does not close `P1-006`, because the specification defers Agent tool registration until the later售后 workflow slice.
- Existing `qa_agent_pgsql` and `E:\myProgram\QA_agent` strings are technical identifiers or real paths, not product display-name regressions.

### No-Placeholder Check

This plan contains no `TBD`, `TODO`, unspecified error handling, or deferred implementation step within its selected scope.
