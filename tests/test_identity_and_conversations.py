from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.customer_service.routes import router
from domain.customer_service.agent import AgentResponse
from domain.customer_service.context import CurrentUser


class RejectingCustomerRepository:
    def find_active(self, user_id):
        return None


class EmptyConversationManager:
    def list_conversations(self, user_id):
        return []


class AcceptingCustomerRepository:
    def find_active(self, user_id):
        if user_id == "customer_alice":
            return CurrentUser("customer_alice", "Alice Test")
        return None


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
        return [
            item
            for item in self.conversations.values()
            if item["user_id"] == user_id
        ]

    def get_history(self, conversation_id):
        return []


class FakeAgent:
    def __init__(self):
        self.calls = []

    def run(self, message, conversation_id):
        self.calls.append((message, conversation_id))
        return AgentResponse("final_answer", "ok", conversation_id)


def build_client():
    app = FastAPI()
    app.state.customer_repository = RejectingCustomerRepository()
    app.state.conversation_manager = EmptyConversationManager()
    app.include_router(router, prefix="/api")
    return TestClient(app)


def build_authorized_client():
    app = FastAPI()
    app.state.customer_repository = AcceptingCustomerRepository()
    app.state.conversation_manager = FakeConversationManager()
    app.state.agent = FakeAgent()
    app.include_router(router, prefix="/api")
    return TestClient(app), app


def test_protected_conversation_endpoint_requires_internal_user_header():
    with build_client() as client:
        response = client.get("/api/conversations")

    assert response.status_code == 401


def test_unknown_internal_user_is_rejected():
    with build_client() as client:
        response = client.get(
            "/api/conversations",
            headers={"X-QA-User-Id": "unknown"},
        )

    assert response.status_code == 401


def test_create_conversation_uses_current_user_without_caller_selected_id():
    client, app = build_authorized_client()
    with client:
        response = client.post(
            "/api/conversations",
            headers={"X-QA-User-Id": "customer_alice"},
            json={},
        )

    assert response.status_code == 200
    assert response.json()["user_id"] == "customer_alice"
    assert app.state.conversation_manager.created_for == ["customer_alice"]


def test_list_conversations_ignores_attempt_to_select_other_user():
    client, _ = build_authorized_client()
    with client:
        response = client.get(
            "/api/conversations?user_id=customer_bob",
            headers={"X-QA-User-Id": "customer_alice"},
        )

    assert response.status_code == 200
    assert [item["conversation_id"] for item in response.json()["conversations"]] == [
        "alice-conv"
    ]


def test_other_users_conversation_is_hidden():
    client, _ = build_authorized_client()
    with client:
        response = client.get(
            "/api/conversations/bob-conv",
            headers={"X-QA-User-Id": "customer_alice"},
        )

    assert response.status_code == 404


def test_chat_cannot_continue_other_users_conversation():
    client, app = build_authorized_client()
    with client:
        response = client.post(
            "/api/chat",
            headers={"X-QA-User-Id": "customer_alice"},
            json={"conversation_id": "bob-conv", "message": "查看进展"},
        )

    assert response.status_code == 404
    assert app.state.agent.calls == []
