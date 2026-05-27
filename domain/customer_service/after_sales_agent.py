from typing import Callable

from .context import CurrentUser
from .sub_agent import SubAgentResponse
from .ticketing import TicketActionInput, TicketEligibilityConflict, TicketNotFound
from .workflows import POLICY_SOURCE_ID, ALLOWED_REQUEST_TYPES, ALLOWED_ISSUE_CAUSES


class AfterSalesAgent:
    def __init__(
        self,
        order_service,
        policy_lookup: Callable,
        ticket_action_service,
    ):
        self.order_service = order_service
        self.policy_lookup = policy_lookup
        self.ticket_action_service = ticket_action_service

    def run(
        self,
        current_user: CurrentUser,
        conversation_id: str,
        payload: dict,
        user_message: str = "",
        context_messages: list = None,
    ) -> SubAgentResponse:
        action_input = self._parse_input(payload)
        if action_input is None:
            return self._ask_user("请提供订单号、办理类型和问题情况，以便核对售后资格。")
        if action_input.issue_cause == "unknown":
            return self._ask_user("请确认问题是否由人为损坏导致。")

        policy = self.policy_lookup(
            f"{action_input.request_type} {action_input.issue_summary}"
        )
        citations = [
            c for c in policy.citations if c.source_id == POLICY_SOURCE_ID
        ]
        if not citations:
            return SubAgentResponse(
                status="handoff",
                recommended_response="当前没有找到可靠的售后政策依据，已为您转接人工进一步确认。",
                metadata=self._metadata(),
            )

        try:
            action = self.ticket_action_service.create_action(
                current_user.user_id, conversation_id, action_input
            )
        except TicketNotFound:
            return self._ask_user(
                "未找到当前账户可办理的订单，请核对订单号。", citations
            )
        except TicketEligibilityConflict as exc:
            return self._eligibility_response(exc, citations)

        return SubAgentResponse(
            status="completed",
            facts={"order_id": action_input.order_id, "request_type": action_input.request_type},
            decision={
                "code": action.eligibility_code,
                "policy_source": POLICY_SOURCE_ID,
            },
            recommended_response="根据售后政策，您的申请符合办理条件。请确认是否提交模拟售后工单。",
            pending_action=action,
            citations=citations,
            metadata=self._metadata(),
        )

    def _parse_input(self, payload: dict):
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

    def _eligibility_response(self, exc, citations) -> SubAgentResponse:
        if exc.code == "requires_clarification":
            return self._ask_user(
                "办理信息仍不完整，请补充商品状态或故障原因。", citations
            )
        suggested = {
            "return_or_exchange": "退换货",
            "warranty_repair": "保修维修",
            "paid_repair": "付费维修",
        }.get(exc.decision.recommended_service)
        if suggested:
            content = f"根据售后政策，当前申请不能直接办理。您可以明确申请{suggested}后重新评估。"
        else:
            content = "根据售后政策，当前申请不符合办理条件。"
        return SubAgentResponse(
            status="completed",
            facts={},
            decision={
                "code": exc.code,
                "reason_codes": exc.decision.reason_codes,
                "policy_source": POLICY_SOURCE_ID,
            },
            recommended_response=content,
            citations=citations,
            metadata=self._metadata(),
        )

    def _ask_user(self, content: str, citations=None) -> SubAgentResponse:
        return SubAgentResponse(
            status="awaiting_info",
            recommended_response=content,
            citations=citations or [],
            metadata=self._metadata(),
        )

    @staticmethod
    def _metadata() -> dict:
        return {"agent": "AfterSalesAgent", "workflow": "after_sales"}
