from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.customer_service.routes import router


class RejectingCustomerRepository:
    def find_active(self, user_id):
        return None


class EmptyConversationManager:
    def list_conversations(self, user_id):
        return []


def build_client():
    app = FastAPI()
    app.state.customer_repository = RejectingCustomerRepository()
    app.state.conversation_manager = EmptyConversationManager()
    app.include_router(router, prefix="/api")
    return TestClient(app)


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
