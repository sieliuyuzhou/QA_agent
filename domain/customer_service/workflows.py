from dataclasses import dataclass, field
from typing import Optional

from .ticketing import (
    PendingActionView,
    TicketActionInput,
    TicketEligibilityConflict,
    TicketNotFound,
)


POLICY_SOURCE_ID = "Doc5-售后与保修政策"
ALLOWED_REQUEST_TYPES = {
    "return_or_exchange",
    "warranty_repair",
    "paid_repair",
}
ALLOWED_ISSUE_CAUSES = {"non_human_fault", "human_damage", "unknown"}


@dataclass(frozen=True)
class WorkflowResult:
    response_type: str
    content: str
    citations: list = field(default_factory=list)
    pending_action: Optional[PendingActionView] = None
    metadata: dict = field(default_factory=dict)


class AfterSalesWorkflow:
    def __init__(self, ticket_action_service, policy_lookup):
        self.ticket_action_service = ticket_action_service
        self.policy_lookup = policy_lookup

    def prepare(self, current_user, conversation_id: str, payload: dict) -> WorkflowResult:
        action_input = self._parse_input(payload)
        if action_input is None:
            return self._ask_user("请提供订单号、办理类型和问题情况，以便核对售后资格。")
        if action_input.issue_cause == "unknown":
            return self._ask_user("请确认问题是否由人为损坏导致。")

        policy = self.policy_lookup(
            f"{action_input.request_type} {action_input.issue_summary}"
        )
        citations = [
            citation
            for citation in policy.citations
            if citation.source_id == POLICY_SOURCE_ID
        ]
        if not citations:
            return WorkflowResult(
                response_type="handoff",
                content="当前没有找到可靠的售后政策依据，已为您转接人工进一步确认。",
                metadata=self._metadata(),
            )

        try:
            action = self.ticket_action_service.create_action(
                current_user.user_id, conversation_id, action_input
            )
        except TicketNotFound:
            return self._ask_user(
                "未找到当前账户可办理的订单，请核对订单号。",
                citations,
            )
        except TicketEligibilityConflict as exc:
            return self._eligibility_response(exc, citations)

        return WorkflowResult(
            response_type="confirm_action",
            content="根据售后政策，您的申请符合办理条件。请确认是否提交模拟售后工单。",
            citations=citations,
            pending_action=action,
            metadata=self._metadata(),
        )

    def _parse_input(self, payload) -> Optional[TicketActionInput]:
        if not isinstance(payload, dict):
            return None
        required = {"order_id", "request_type", "issue_cause", "issue_summary"}
        if not required.issubset(payload):
            return None
        if payload["request_type"] not in ALLOWED_REQUEST_TYPES:
            return None
        if payload["issue_cause"] not in ALLOWED_ISSUE_CAUSES:
            return None
        if not isinstance(payload["order_id"], str) or not payload["order_id"].strip():
            return None
        if not isinstance(payload["issue_summary"], str) or not payload["issue_summary"].strip():
            return None
        packaging_intact = payload.get("packaging_intact")
        if packaging_intact is not None and not isinstance(packaging_intact, bool):
            return None
        return TicketActionInput(
            order_id=payload["order_id"].strip(),
            request_type=payload["request_type"],
            issue_cause=payload["issue_cause"],
            packaging_intact=packaging_intact,
            issue_summary=payload["issue_summary"].strip(),
        )

    def _eligibility_response(self, exc, citations) -> WorkflowResult:
        if exc.code == "requires_clarification":
            return self._ask_user(
                "办理信息仍不完整，请补充商品状态或故障原因。",
                citations,
            )
        suggested_service = {
            "return_or_exchange": "退换货",
            "warranty_repair": "保修维修",
            "paid_repair": "付费维修",
        }.get(exc.decision.recommended_service)
        if suggested_service:
            content = (
                f"根据售后政策，当前申请不能直接办理。"
                f"您可以明确申请{suggested_service}后重新评估。"
            )
        else:
            content = "根据售后政策，当前申请不符合办理条件。"
        return WorkflowResult(
            response_type="final_answer",
            content=content,
            citations=citations,
            metadata=self._metadata(),
        )

    def _ask_user(self, content: str, citations=None) -> WorkflowResult:
        return WorkflowResult(
            response_type="ask_user",
            content=content,
            citations=citations or [],
            metadata=self._metadata(),
        )

    @staticmethod
    def _metadata() -> dict:
        return {"intent": "after_sales", "workflow": "after_sales"}
