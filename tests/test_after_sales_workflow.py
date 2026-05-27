from datetime import datetime

from domain.customer_service.context import CurrentUser
from domain.customer_service.eligibility import EligibilityDecision
from domain.customer_service.ticketing import (
    PendingActionView,
    TicketEligibilityConflict,
    TicketNotFound,
)
from domain.customer_service.workflows import AfterSalesWorkflow
from tools.base import Citation, ToolResult


USER = CurrentUser("customer_alice", "Alice Test")
POLICY_CITATION = Citation(
    source_id="Doc5-售后与保修政策",
    title="Doc5-售后与保修政策",
    section="保修条款",
    excerpt="产品在保修期内出现非人为质量问题，可申请免费维修。",
)


def warranty_payload():
    return {
        "order_id": "ORD-A-C1",
        "request_type": "warranty_repair",
        "issue_cause": "non_human_fault",
        "packaging_intact": None,
        "issue_summary": "摄像头无法开机",
    }


def pending_action():
    return PendingActionView(
        action_id="act-1",
        conversation_id="alice-conv",
        user_id="customer_alice",
        action_type="create_service_ticket",
        order_id="ORD-A-C1",
        ticket_type="warranty_repair",
        eligibility_code="eligible_for_warranty_repair",
        eligibility_payload={},
        issue_summary="摄像头无法开机",
        display_summary="为订单 ORD-A-C1 创建保修维修工单",
        status="pending",
        expires_at=datetime(2026, 5, 27, 12, 30),
    )


class FakeTicketActionService:
    def __init__(self, result=None, error=None):
        self.result = result or pending_action()
        self.error = error
        self.calls = []

    def create_action(self, user_id, conversation_id, action_input):
        self.calls.append((user_id, conversation_id, action_input))
        if self.error:
            raise self.error
        return self.result


def policy_result(_query):
    return ToolResult("政策内容", [POLICY_CITATION])


def test_eligible_policy_backed_request_returns_confirm_action():
    service = FakeTicketActionService()
    workflow = AfterSalesWorkflow(service, policy_result)

    result = workflow.prepare(USER, "alice-conv", warranty_payload())

    assert result.response_type == "confirm_action"
    assert result.pending_action.action_id == "act-1"
    assert result.citations == [POLICY_CITATION]
    assert result.metadata == {"intent": "after_sales", "workflow": "after_sales"}
    assert service.calls[0][0:2] == ("customer_alice", "alice-conv")


def test_request_without_policy_citation_handoffs_without_creating_action():
    service = FakeTicketActionService()
    workflow = AfterSalesWorkflow(service, lambda _query: ToolResult("无依据"))

    result = workflow.prepare(USER, "alice-conv", warranty_payload())

    assert result.response_type == "handoff"
    assert service.calls == []


def test_non_policy_citation_handoffs_without_creating_action():
    service = FakeTicketActionService()
    workflow = AfterSalesWorkflow(
        service,
        lambda _query: ToolResult(
            "产品说明",
            [Citation("Doc1-X1智能门锁FAQ", "Doc1-X1智能门锁FAQ", "重置", "内容")],
        ),
    )

    result = workflow.prepare(USER, "alice-conv", warranty_payload())

    assert result.response_type == "handoff"
    assert service.calls == []


def test_unknown_issue_fact_asks_for_clarification_without_policy_or_action():
    service = FakeTicketActionService()
    policy_calls = []
    workflow = AfterSalesWorkflow(
        service, lambda query: policy_calls.append(query) or policy_result(query)
    )
    payload = {**warranty_payload(), "issue_cause": "unknown"}

    result = workflow.prepare(USER, "alice-conv", payload)

    assert result.response_type == "ask_user"
    assert policy_calls == []
    assert service.calls == []


def test_missing_input_asks_for_clarification_without_action():
    service = FakeTicketActionService()
    workflow = AfterSalesWorkflow(service, policy_result)
    payload = warranty_payload()
    del payload["order_id"]

    result = workflow.prepare(USER, "alice-conv", payload)

    assert result.response_type == "ask_user"
    assert service.calls == []


def test_inaccessible_order_asks_user_to_check_order_without_disclosure():
    workflow = AfterSalesWorkflow(
        FakeTicketActionService(error=TicketNotFound("order_not_found")),
        policy_result,
    )

    result = workflow.prepare(USER, "alice-conv", warranty_payload())

    assert result.response_type == "ask_user"
    assert "当前账户" in result.content


def test_alternative_recommendation_returns_answer_without_pending_action():
    decision = EligibilityDecision(
        code="paid_repair_available",
        eligible=True,
        recommended_service="paid_repair",
        reason_codes=["outside_warranty_period"],
        policy_sections=["过保后维修怎么收费？"],
    )
    workflow = AfterSalesWorkflow(
        FakeTicketActionService(error=TicketEligibilityConflict(decision)),
        policy_result,
    )

    result = workflow.prepare(USER, "alice-conv", warranty_payload())

    assert result.response_type == "final_answer"
    assert result.pending_action is None
    assert "付费维修" in result.content
