from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from domain.customer_service.context import OrderView
from domain.customer_service.eligibility import EligibilityRuleService
from domain.customer_service.ticketing import (
    TicketActionConflict,
    TicketActionInput,
    TicketActionService,
    TicketEligibilityConflict,
)


NOW = datetime(2026, 5, 27, 12, 0)


class FakeOrderService:
    def get_order(self, user_id, order_id):
        if user_id != "customer_alice":
            return None
        dates = {
            "ORD-A-C1": "2026-03-01",
            "ORD-A-G2-OLD": "2025-01-01",
        }
        purchased_at = dates.get(order_id)
        if purchased_at is None:
            return None
        return OrderView(order_id, "C1", "产品", "camera", purchased_at, "completed", "399.00")


class FakeTicketRepository:
    def __init__(self):
        self.actions = {}
        self.tickets = {}

    def create_action(self, action):
        self.actions[action.action_id] = action
        return action

    def confirm_with_lock(self, user_id, conversation_id, action_id, build_ticket):
        action = self.actions.get(action_id)
        if not action or action.user_id != user_id or action.conversation_id != conversation_id:
            return None, False
        if action.status == "executed":
            return self.tickets[action.executed_ticket_id], True
        ticket = build_ticket(action)
        self.tickets[ticket.ticket_id] = ticket
        self.actions[action_id] = replace(
            action, status="executed", executed_ticket_id=ticket.ticket_id
        )
        return ticket, False


def service(repository=None, now=NOW):
    return TicketActionService(
        repository or FakeTicketRepository(),
        FakeOrderService(),
        EligibilityRuleService(),
        now_fn=lambda: now,
        id_fn=iter(["act-1", "ticket-1"]).__next__,
    )


def warranty_input():
    return TicketActionInput(
        order_id="ORD-A-C1",
        request_type="warranty_repair",
        issue_cause="non_human_fault",
        packaging_intact=None,
        issue_summary="摄像头无法开机",
    )


def test_eligible_request_creates_pending_action_but_no_ticket():
    repository = FakeTicketRepository()

    action = service(repository).create_action("customer_alice", "alice-conv", warranty_input())

    assert action.status == "pending"
    assert action.ticket_type == "warranty_repair"
    assert repository.tickets == {}


def test_create_action_uses_one_time_snapshot_for_decision_and_expiration():
    repository = FakeTicketRepository()
    now = datetime(2026, 5, 27, 23, 59, 59)
    ticket_service = TicketActionService(
        repository,
        FakeOrderService(),
        EligibilityRuleService(),
        now_fn=iter([now]).__next__,
        id_fn=lambda: "act-1",
    )

    action = ticket_service.create_action(
        "customer_alice", "alice-conv", warranty_input()
    )

    assert action.expires_at == now + timedelta(minutes=30)


def test_ineligible_request_does_not_create_action():
    repository = FakeTicketRepository()
    request = replace(warranty_input(), issue_cause="human_damage")

    with pytest.raises(TicketEligibilityConflict):
        service(repository).create_action("customer_alice", "alice-conv", request)

    assert repository.actions == {}


def test_alternative_recommendation_does_not_silently_create_other_ticket_type():
    repository = FakeTicketRepository()
    request = TicketActionInput(
        "ORD-A-G2-OLD", "return_or_exchange", "non_human_fault", True, "希望退货"
    )

    with pytest.raises(TicketEligibilityConflict):
        service(repository).create_action("customer_alice", "alice-conv", request)

    assert repository.actions == {}


def test_confirm_revalidates_and_creates_ticket_once():
    repository = FakeTicketRepository()
    ticket_service = service(repository)
    action = ticket_service.create_action("customer_alice", "alice-conv", warranty_input())

    first = ticket_service.confirm_action("customer_alice", "alice-conv", action.action_id)
    second = ticket_service.confirm_action("customer_alice", "alice-conv", action.action_id)

    assert first.ticket.ticket_id == second.ticket.ticket_id
    assert first.idempotent_replay is False
    assert second.idempotent_replay is True
    assert len(repository.tickets) == 1


def test_expired_action_cannot_create_ticket():
    repository = FakeTicketRepository()
    ticket_service = service(repository)
    action = ticket_service.create_action("customer_alice", "alice-conv", warranty_input())
    repository.actions[action.action_id] = replace(action, expires_at=NOW - timedelta(seconds=1))

    with pytest.raises(TicketActionConflict):
        ticket_service.confirm_action("customer_alice", "alice-conv", action.action_id)

    assert repository.tickets == {}


def test_confirmation_rejects_when_recomputed_eligibility_is_no_longer_valid():
    repository = FakeTicketRepository()
    created = service(repository).create_action("customer_alice", "alice-conv", warranty_input())
    repository.actions[created.action_id] = replace(
        created, expires_at=datetime(2027, 6, 2, 12, 0)
    )

    with pytest.raises(TicketEligibilityConflict):
        service(repository, datetime(2027, 6, 1, 12, 0)).confirm_action(
            "customer_alice", "alice-conv", created.action_id
        )

    assert repository.tickets == {}
