from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable, Optional

import uuid

from .eligibility import EligibilityRequest, EligibilityRuleService


@dataclass(frozen=True)
class TicketActionInput:
    order_id: str
    request_type: str
    issue_cause: str
    packaging_intact: Optional[bool]
    issue_summary: str


@dataclass(frozen=True)
class PendingActionView:
    action_id: str
    conversation_id: str
    user_id: str
    action_type: str
    order_id: str
    ticket_type: str
    eligibility_code: str
    eligibility_payload: dict
    issue_summary: str
    display_summary: str
    status: str
    expires_at: datetime
    executed_ticket_id: Optional[str] = None


@dataclass(frozen=True)
class ServiceTicketView:
    ticket_id: str
    user_id: str
    order_id: str
    ticket_type: str
    issue_summary: str
    eligibility_code: str
    status: str = "submitted"


@dataclass(frozen=True)
class ConfirmationResult:
    ticket: ServiceTicketView
    idempotent_replay: bool


class TicketNotFound(Exception):
    pass


class TicketActionConflict(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class TicketEligibilityConflict(Exception):
    def __init__(self, decision):
        self.decision = decision
        self.code = decision.code
        super().__init__(decision.code)


class TicketActionService:
    def __init__(
        self,
        repository,
        order_service,
        eligibility_service: EligibilityRuleService,
        now_fn: Callable[[], datetime] = datetime.now,
        id_fn: Callable[[], str] = lambda: str(uuid.uuid4()),
    ):
        self.repository = repository
        self.order_service = order_service
        self.eligibility_service = eligibility_service
        self.now_fn = now_fn
        self.id_fn = id_fn

    def create_action(
        self,
        user_id: str,
        conversation_id: str,
        action_input: TicketActionInput,
    ) -> PendingActionView:
        order = self.order_service.get_order(user_id, action_input.order_id)
        if order is None:
            raise TicketNotFound("order_not_found")

        now = self.now_fn()
        decision = self.eligibility_service.evaluate(
            EligibilityRequest(
                order=order,
                request_type=action_input.request_type,
                issue_cause=action_input.issue_cause,
                packaging_intact=action_input.packaging_intact,
                evaluated_on=now.date(),
            )
        )
        if (
            not decision.eligible
            or decision.recommended_service != action_input.request_type
        ):
            raise TicketEligibilityConflict(decision)

        action = PendingActionView(
            action_id=self.id_fn(),
            conversation_id=conversation_id,
            user_id=user_id,
            action_type="create_service_ticket",
            order_id=order.order_id,
            ticket_type=decision.recommended_service,
            eligibility_code=decision.code,
            eligibility_payload={
                "request_type": action_input.request_type,
                "issue_cause": action_input.issue_cause,
                "packaging_intact": action_input.packaging_intact,
            },
            issue_summary=action_input.issue_summary,
            display_summary=(
                f"为订单 {order.order_id} 创建"
                f"{self._ticket_type_label(decision.recommended_service)}工单"
            ),
            status="pending",
            expires_at=now + timedelta(minutes=30),
        )
        return self.repository.create_action(action)

    def confirm_action(
        self, user_id: str, conversation_id: str, action_id: str
    ) -> ConfirmationResult:
        ticket, replay = self.repository.confirm_with_lock(
            user_id,
            conversation_id,
            action_id,
            self._build_confirmed_ticket,
        )
        if ticket is None:
            raise TicketNotFound("action_not_found")
        return ConfirmationResult(ticket=ticket, idempotent_replay=replay)

    def _build_confirmed_ticket(self, action: PendingActionView) -> ServiceTicketView:
        now = self.now_fn()
        if action.action_type != "create_service_ticket":
            raise TicketActionConflict("unsupported_action_type")
        if action.status != "pending":
            raise TicketActionConflict(f"action_{action.status}")
        if action.expires_at <= now:
            raise TicketActionConflict("action_expired")

        order = self.order_service.get_order(action.user_id, action.order_id)
        if order is None:
            raise TicketNotFound("order_not_found")
        payload = action.eligibility_payload
        decision = self.eligibility_service.evaluate(
            EligibilityRequest(
                order=order,
                request_type=payload["request_type"],
                issue_cause=payload["issue_cause"],
                packaging_intact=payload.get("packaging_intact"),
                evaluated_on=now.date(),
            )
        )
        if not decision.eligible or decision.recommended_service != action.ticket_type:
            raise TicketEligibilityConflict(decision)
        return ServiceTicketView(
            ticket_id=self.id_fn(),
            user_id=action.user_id,
            order_id=action.order_id,
            ticket_type=action.ticket_type,
            issue_summary=action.issue_summary,
            eligibility_code=decision.code,
        )

    @staticmethod
    def _ticket_type_label(ticket_type: str) -> str:
        return {
            "return_or_exchange": "退换货",
            "warranty_repair": "保修维修",
            "paid_repair": "付费维修",
        }[ticket_type]
