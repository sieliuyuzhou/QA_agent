from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.customer_service.action_routes import router
from domain.customer_service.context import CurrentUser
from domain.customer_service.ticketing import (
    ConfirmationResult,
    PendingActionView,
    ServiceTicketView,
    TicketActionConflict,
)


class FakeCustomerRepository:
    def find_active(self, user_id):
        if user_id == "customer_alice":
            return CurrentUser("customer_alice", "Alice Test")
        return None


class FakeConversationManager:
    def get_conversation(self, conversation_id):
        owners = {"alice-conv": "customer_alice", "bob-conv": "customer_bob"}
        owner = owners.get(conversation_id)
        return {"conversation_id": conversation_id, "user_id": owner} if owner else None


class FakeTicketActionService:
    def create_action(self, user_id, conversation_id, _body):
        return PendingActionView(
            "act-1",
            conversation_id,
            user_id,
            "create_service_ticket",
            "ORD-A-C1",
            "warranty_repair",
            "eligible_for_warranty_repair",
            {},
            "无法开机",
            "为订单 ORD-A-C1 创建保修维修工单",
            "pending",
            datetime(2026, 5, 27, 12, 30),
        )

    def confirm_action(self, user_id, conversation_id, action_id):
        if action_id == "expired":
            raise TicketActionConflict("expired")
        return ConfirmationResult(
            ServiceTicketView(
                "ticket-1", user_id, "ORD-A-C1", "warranty_repair",
                "无法开机", "eligible_for_warranty_repair"
            ),
            False,
        )


def build_client():
    app = FastAPI()
    app.state.customer_repository = FakeCustomerRepository()
    app.state.conversation_manager = FakeConversationManager()
    app.state.ticket_action_service = FakeTicketActionService()
    app.include_router(router, prefix="/api")
    return TestClient(app)


PAYLOAD = {
    "order_id": "ORD-A-C1",
    "request_type": "warranty_repair",
    "issue_cause": "non_human_fault",
    "packaging_intact": None,
    "issue_summary": "摄像头无法开机",
}
HEADERS = {"X-QA-User-Id": "customer_alice"}


def test_create_action_requires_owned_conversation():
    with build_client() as client:
        response = client.post("/api/conversations/bob-conv/actions", headers=HEADERS, json=PAYLOAD)

    assert response.status_code == 404


def test_eligible_request_returns_confirm_action():
    with build_client() as client:
        response = client.post("/api/conversations/alice-conv/actions", headers=HEADERS, json=PAYLOAD)

    assert response.status_code == 200
    assert response.json()["type"] == "confirm_action"
    assert response.json()["pending_action"]["action_id"] == "act-1"


def test_confirmation_returns_ticket_and_idempotency_flag():
    with build_client() as client:
        response = client.post("/api/conversations/alice-conv/actions/act-1/confirm", headers=HEADERS)

    assert response.status_code == 200
    assert response.json()["ticket"]["ticket_id"] == "ticket-1"
    assert response.json()["idempotent_replay"] is False


def test_action_conflict_maps_to_409():
    with build_client() as client:
        response = client.post("/api/conversations/alice-conv/actions/expired/confirm", headers=HEADERS)

    assert response.status_code == 409
