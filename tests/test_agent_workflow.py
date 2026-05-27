from datetime import datetime

from conftest import MemoryConversationManager, SequenceLLM
from domain.customer_service.agent import CustomerServiceAgent
from domain.customer_service.context import CurrentUser
from domain.customer_service.ticketing import PendingActionView
from domain.customer_service.workflows import WorkflowResult
from tools.base import Citation


class FakeWorkflow:
    def __init__(self):
        self.calls = []

    def prepare(self, current_user, conversation_id, payload):
        self.calls.append((current_user, conversation_id, payload))
        return WorkflowResult(
            response_type="confirm_action",
            content="请确认是否提交模拟售后工单。",
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
            metadata={"intent": "after_sales", "workflow": "after_sales"},
        )


ACTION = (
    'Action: PrepareAfterSales[{"order_id":"ORD-A-C1",'
    '"request_type":"warranty_repair",'
    '"issue_cause":"non_human_fault",'
    '"packaging_intact":null,'
    '"issue_summary":"摄像头无法开机"}]'
)


def test_prepare_after_sales_dispatches_current_user_and_returns_pending_action():
    manager = MemoryConversationManager()
    workflow = FakeWorkflow()
    agent = CustomerServiceAgent(
        SequenceLLM(ACTION), manager, [], after_sales_workflow=workflow
    )

    response = agent.run(
        "摄像头无法开机，申请保修",
        "alice-conv",
        current_user=CurrentUser("customer_alice", "Alice Test"),
    )

    assert workflow.calls[0][0].user_id == "customer_alice"
    assert workflow.calls[0][1] == "alice-conv"
    assert workflow.calls[0][2]["order_id"] == "ORD-A-C1"
    assert response.type == "confirm_action"
    assert response.pending_action.action_id == "act-1"
    assert manager.messages[-1]["metadata"]["conversation_state"] == "awaiting_confirmation"


def test_prompt_advertises_prepare_after_sales_as_controlled_action():
    llm = SequenceLLM("Action: AskUser[请提供订单号。]")
    agent = CustomerServiceAgent(llm, MemoryConversationManager(), [])

    agent.run("我要售后", "alice-conv")

    assert "PrepareAfterSales" in llm.calls[0]["system_prompt"]


def test_invalid_prepare_after_sales_json_asks_for_clarification_without_dispatch():
    manager = MemoryConversationManager()
    workflow = FakeWorkflow()
    agent = CustomerServiceAgent(
        SequenceLLM("Action: PrepareAfterSales[订单号缺失]"),
        manager,
        [],
        after_sales_workflow=workflow,
    )

    response = agent.run(
        "我要售后",
        "alice-conv",
        current_user=CurrentUser("customer_alice", "Alice Test"),
    )

    assert response.type == "ask_user"
    assert workflow.calls == []
    assert manager.messages[-1]["metadata"]["conversation_state"] == "awaiting_clarification"
