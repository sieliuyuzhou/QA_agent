from fastapi import FastAPI
from fastapi.testclient import TestClient

from domain.customer_service.context import CurrentUser
from apps.customer_service.admin_dependencies import require_admin
from apps.customer_service.admin_routes import router


ADMIN = CurrentUser("admin_zhang", "Zhang Admin", role="admin")
CUSTOMER = CurrentUser("customer_alice", "Alice Test", role="customer")


class FakeManager:
    def __init__(self, conversations=None, messages=None):
        self._conversations = conversations or []
        self._messages = messages or []

    def list_all_conversations(self):
        return self._conversations

    def get_conversation(self, conv_id):
        for c in self._conversations:
            if c["conversation_id"] == conv_id:
                return c
        return None

    def get_history(self, conv_id):
        return self._messages


class FakeRepo:
    def __init__(self, db):
        self.db = db


class FakeDB:
    def __init__(self, rows=None):
        self.rows = rows or []

    def execute(self, query, params=None, fetch=False):
        return self.rows if fetch else None


class FakeTicketActionService:
    def __init__(self, db):
        self.repository = FakeRepo(db)


def _app(current_user, manager=None, db_rows=None):
    app = FastAPI()
    app.include_router(router)

    app.state.conversation_manager = manager or FakeManager()
    app.state.ticket_action_service = FakeTicketActionService(
        FakeDB(db_rows or [])
    )

    from apps.customer_service.dependencies import get_current_user
    app.dependency_overrides[get_current_user] = lambda: current_user
    return app


def test_admin_can_list_conversations():
    manager = FakeManager(
        conversations=[{"conversation_id": "c1", "user_id": "alice", "status": "active"}]
    )
    app = _app(ADMIN, manager=manager)
    client = TestClient(app)

    resp = client.get("/admin/conversations")

    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_customer_cannot_access_admin_conversations():
    app = _app(CUSTOMER)
    client = TestClient(app)

    resp = client.get("/admin/conversations")

    assert resp.status_code == 403


def test_admin_can_get_conversation_detail():
    manager = FakeManager(
        conversations=[{"conversation_id": "c1", "user_id": "alice", "status": "active"}],
        messages=[
            {"id": 1, "role": "user", "content": "你好", "metadata": None, "turn_number": 1, "created_at": "2026-05-27"},
        ],
    )
    app = _app(ADMIN, manager=manager)
    client = TestClient(app)

    resp = client.get("/admin/conversations/c1")

    assert resp.status_code == 200
    assert len(resp.json()["messages"]) == 1


def test_admin_get_nonexistent_conversation_returns_404():
    app = _app(ADMIN, manager=FakeManager())
    client = TestClient(app)

    resp = client.get("/admin/conversations/nonexistent")

    assert resp.status_code == 404


def test_admin_can_list_tickets():
    db_rows = [
        ("TKT-001", "alice", "ORD-A-X1", "warranty_repair", "无法开机",
         "eligible_for_warranty_repair", "submitted", "2026-05-27"),
    ]
    app = _app(ADMIN, db_rows=db_rows)
    client = TestClient(app)

    resp = client.get("/admin/tickets")

    assert resp.status_code == 200
    assert resp.json()["total"] == 1
    assert resp.json()["tickets"][0]["ticket_id"] == "TKT-001"


def test_customer_cannot_access_admin_tickets():
    app = _app(CUSTOMER)
    client = TestClient(app)

    resp = client.get("/admin/tickets")

    assert resp.status_code == 403
