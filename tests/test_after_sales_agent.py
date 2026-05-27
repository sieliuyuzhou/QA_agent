from domain.customer_service.after_sales_agent import AfterSalesAgent
from domain.customer_service.context import CurrentUser, OrderView
from domain.customer_service.eligibility import EligibilityDecision
from domain.customer_service.ticketing import (
    PendingActionView, TicketEligibilityConflict, TicketNotFound,
)
from tools.base import Citation, ToolResult
from datetime import datetime, timedelta


ALICE = CurrentUser("customer_alice", "Alice")

SAMPLE_ORDER = OrderView(
    order_id="ORD-A-X1", product_id="X1", product_name="X1 智能门锁",
    category="smart_lock", purchased_at="2026-05-20",
    status="delivered", amount="1299.00",
)

SAMPLE_ACTION = PendingActionView(
    action_id="act-1", conversation_id="conv-1", user_id="customer_alice",
    action_type="create_service_ticket", order_id="ORD-A-X1",
    ticket_type="warranty_repair", eligibility_code="eligible_for_warranty_repair",
    eligibility_payload={"request_type": "warranty_repair", "issue_cause": "non_human_fault"},
    issue_summary="无法开机", display_summary="为订单 ORD-A-X1 创建保修维修工单",
    status="pending", expires_at=datetime.now() + timedelta(minutes=30),
)


class FakeOrderService:
    def __init__(self, orders=None):
        self._orders = orders or {}

    def get_order(self, user_id, order_id):
        return self._orders.get(order_id)

    def list_orders(self, user_id, status=None):
        return list(self._orders.values())


class FakePolicyLookup:
    def __init__(self, citations=None):
        self._citations = citations or [
            Citation("Doc5-售后与保修政策", "售后政策", "保修维修", "非人为故障免费维修")
        ]

    def __call__(self, query):
        return ToolResult(content="政策内容", citations=self._citations)


class FakeTicketActionService:
    def __init__(self, action=None, error=None):
        self._action = action
        self._error = error

    def create_action(self, user_id, conversation_id, action_input):
        if self._error:
            raise self._error
        return self._action


def test_eligible_request_returns_completed_with_action():
    agent = AfterSalesAgent(
        order_service=FakeOrderService({"ORD-A-X1": SAMPLE_ORDER}),
        policy_lookup=FakePolicyLookup(),
        ticket_action_service=FakeTicketActionService(action=SAMPLE_ACTION),
    )
    resp = agent.run(
        current_user=ALICE, conversation_id="conv-1",
        payload={"order_id": "ORD-A-X1", "request_type": "warranty_repair",
                 "issue_cause": "non_human_fault", "issue_summary": "无法开机"},
    )
    assert resp.status == "completed"
    assert resp.pending_action is not None
    assert resp.pending_action.action_id == "act-1"
    assert resp.decision["code"] == "eligible_for_warranty_repair"
    assert resp.citations


def test_order_not_found_returns_awaiting_info():
    agent = AfterSalesAgent(
        order_service=FakeOrderService(),
        policy_lookup=FakePolicyLookup(),
        ticket_action_service=FakeTicketActionService(
            error=TicketNotFound("order_not_found")),
    )
    resp = agent.run(
        current_user=ALICE, conversation_id="conv-1",
        payload={"order_id": "ORD-999", "request_type": "warranty_repair",
                 "issue_cause": "non_human_fault", "issue_summary": "test"},
    )
    assert resp.status == "awaiting_info"
    assert resp.pending_action is None


def test_ineligible_returns_completed_without_action():
    agent = AfterSalesAgent(
        order_service=FakeOrderService({"ORD-A-X1": SAMPLE_ORDER}),
        policy_lookup=FakePolicyLookup(),
        ticket_action_service=FakeTicketActionService(
            error=TicketEligibilityConflict(
                EligibilityDecision(
                    code="ineligible_for_free_warranty", eligible=False,
                    recommended_service="paid_repair",
                    reason_codes=["human_damage"],
                    policy_sections=["保修维修"],
                )
            )
        ),
    )
    resp = agent.run(
        current_user=ALICE, conversation_id="conv-1",
        payload={"order_id": "ORD-A-X1", "request_type": "warranty_repair",
                 "issue_cause": "human_damage", "issue_summary": "摔坏"},
    )
    assert resp.status == "completed"
    assert resp.pending_action is None
    assert "付费维修" in resp.recommended_response


def test_missing_payload_returns_awaiting_info():
    agent = AfterSalesAgent(
        order_service=FakeOrderService(),
        policy_lookup=FakePolicyLookup(),
        ticket_action_service=FakeTicketActionService(),
    )
    resp = agent.run(
        current_user=ALICE, conversation_id="conv-1", payload={},
    )
    assert resp.status == "awaiting_info"


def test_no_policy_returns_handoff():
    empty_policy = lambda q: ToolResult(content="", citations=[])
    agent = AfterSalesAgent(
        order_service=FakeOrderService({"ORD-A-X1": SAMPLE_ORDER}),
        policy_lookup=empty_policy,
        ticket_action_service=FakeTicketActionService(),
    )
    resp = agent.run(
        current_user=ALICE, conversation_id="conv-1",
        payload={"order_id": "ORD-A-X1", "request_type": "warranty_repair",
                 "issue_cause": "non_human_fault", "issue_summary": "test"},
    )
    assert resp.status == "handoff"


def test_metadata_includes_agent_name():
    agent = AfterSalesAgent(
        order_service=FakeOrderService({"ORD-A-X1": SAMPLE_ORDER}),
        policy_lookup=FakePolicyLookup(),
        ticket_action_service=FakeTicketActionService(action=SAMPLE_ACTION),
    )
    resp = agent.run(
        current_user=ALICE, conversation_id="conv-1",
        payload={"order_id": "ORD-A-X1", "request_type": "warranty_repair",
                 "issue_cause": "non_human_fault", "issue_summary": "test"},
    )
    assert resp.metadata["agent"] == "AfterSalesAgent"
    assert resp.metadata["workflow"] == "after_sales"
