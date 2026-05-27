from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from apps.customer_service.routes import router
from domain.customer_service.agent import AgentResponse
from domain.customer_service.context import CurrentUser
from domain.customer_service.ticketing import PendingActionView
from tools.base import Citation


class FakeCustomerRepository:
    def find_active(self, user_id):
        if user_id == "customer_alice":
            return CurrentUser("customer_alice", "Alice Test")
        return None


class FakeConversationManager:
    def get_conversation(self, conversation_id):
        return {
            "conversation_id": conversation_id,
            "user_id": "customer_alice",
            "status": "active",
        }


class FakeAgent:
    def __init__(self):
        self.calls = []

    def run(self, message, conversation_id, current_user=None):
        self.calls.append((message, conversation_id, current_user))
        return AgentResponse(
            type="confirm_action",
            content="请确认是否提交模拟售后工单。",
            conversation_id=conversation_id,
            metadata={"intent": "after_sales", "workflow": "after_sales"},
            citations=[
                Citation("Doc5-售后与保修政策", "Doc5-售后与保修政策", "保修条款", "依据")
            ],
            pending_action=PendingActionView(
                "act-1",
                conversation_id,
                current_user.user_id,
                "create_service_ticket",
                "ORD-A-C1",
                "warranty_repair",
                "eligible_for_warranty_repair",
                {},
                "无法开机",
                "为订单 ORD-A-C1 创建保修维修工单",
                "pending",
                datetime(2026, 5, 27, 12, 30),
            ),
        )


def build_client():
    app = FastAPI()
    app.state.customer_repository = FakeCustomerRepository()
    app.state.conversation_manager = FakeConversationManager()
    app.state.agent = FakeAgent()
    app.include_router(router, prefix="/api")
    return TestClient(app, raise_server_exceptions=False), app


def test_chat_forwards_current_user_and_serializes_confirm_action():
    client, app = build_client()
    with client:
        response = client.post(
            "/api/chat",
            headers={"X-QA-User-Id": "customer_alice"},
            json={
                "conversation_id": "alice-conv",
                "message": "摄像头无法开机，申请保修",
            },
        )

    assert response.status_code == 200
    assert response.json()["type"] == "confirm_action"
    assert response.json()["pending_action"]["action_id"] == "act-1"
    assert app.state.agent.calls[0][2].user_id == "customer_alice"
