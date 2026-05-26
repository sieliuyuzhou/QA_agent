from fastapi.testclient import TestClient

import main
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


def test_conversation_manager_initializes_schema_only_when_requested(monkeypatch):
    calls = []
    monkeypatch.setattr("utils.conversation.init_tables", lambda db: calls.append(db))
    monkeypatch.setattr("utils.conversation.DatabaseManager", lambda db_url=None: FakeDB())

    ConversationManager("postgresql://example", initialize_schema=True)

    assert len(calls) == 1


def test_health_reports_unavailable_database(monkeypatch):
    monkeypatch.setattr(main, "ConversationManager", lambda **kwargs: FakeManager(fail=True))
    monkeypatch.setattr(main, "get_store", lambda: FakeStore(), raising=False)

    with TestClient(main.app, raise_server_exceptions=False) as client:
        response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["status"] == "degraded"


def test_health_reports_ready_dependencies(monkeypatch):
    monkeypatch.setattr(main, "ConversationManager", lambda **kwargs: FakeManager())
    monkeypatch.setattr(main, "get_store", lambda: FakeStore(), raising=False)

    with TestClient(main.app, raise_server_exceptions=False) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "checks": {"database": "ok", "knowledge_store": "ok"},
    }
