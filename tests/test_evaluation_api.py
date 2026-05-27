from fastapi import FastAPI
from fastapi.testclient import TestClient

from domain.customer_service.context import CurrentUser
from apps.customer_service.admin_routes import router
from apps.customer_service.dependencies import get_current_user
from utils.evaluation_repo import EvaluationRepository


ADMIN = CurrentUser("admin_zhang", "Zhang Admin", role="admin")
CUSTOMER = CurrentUser("customer_alice", "Alice Test", role="customer")


class FakeEvalDB:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.inserted = []

    def execute(self, query, params=None, fetch=False):
        if fetch:
            return self.rows
        self.inserted.append(params)
        return None


class FakeManager:
    def list_all_conversations(self):
        return []

    def get_conversation(self, cid):
        return None

    def get_history(self, cid):
        return []


class FakeTicketActionService:
    def __init__(self):
        self.repository = type("R", (), {"db": FakeEvalDB()})()


def _app(current_user, eval_rows=None):
    app = FastAPI()
    app.include_router(router)
    app.state.conversation_manager = FakeManager()
    app.state.ticket_action_service = FakeTicketActionService()
    app.state.evaluation_repository = EvaluationRepository(FakeEvalDB(eval_rows))
    app.dependency_overrides[get_current_user] = lambda: current_user
    return app


def test_admin_can_list_evaluation_runs():
    rows = [
        ("run-1", "EVAL-001", "final_answer", True, None, "mock", 100, "2026-05-27"),
        ("run-2", "EVAL-003", "ask_user", False, "wrong type", "mock", 50, "2026-05-27"),
    ]
    app = _app(ADMIN, eval_rows=rows)
    client = TestClient(app)

    resp = client.get("/admin/evaluations")

    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert data["passed"] == 1
    assert data["failed"] == 1


def test_customer_cannot_access_evaluations():
    app = _app(CUSTOMER)
    client = TestClient(app)

    resp = client.get("/admin/evaluations")

    assert resp.status_code == 403


def test_eval_repo_insert_and_query():
    db = FakeEvalDB()
    repo = EvaluationRepository(db)

    repo.insert_run("run-1", "EVAL-001", "final_answer", True)
    assert len(db.inserted) == 1
    assert db.inserted[0][0] == "run-1"

    repo.get_runs("EVAL-001")
    assert len(db.rows) == 0  # rows not set, just verifying no error
