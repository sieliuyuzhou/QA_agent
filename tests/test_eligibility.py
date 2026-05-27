from datetime import date

from domain.customer_service.context import OrderView
from domain.customer_service.eligibility import EligibilityRequest, EligibilityRuleService


def order(purchased_at):
    return OrderView(
        "ORD-1",
        "X1",
        "X1 智能门锁",
        "smart_lock",
        purchased_at,
        "delivered",
        "1299.00",
    )


def evaluate(purchased_at, request_type, issue_cause, packaging_intact=None):
    return EligibilityRuleService().evaluate(
        EligibilityRequest(
            order=order(purchased_at),
            request_type=request_type,
            issue_cause=issue_cause,
            packaging_intact=packaging_intact,
            evaluated_on=date(2026, 5, 27),
        )
    )


def test_qualified_return_within_seven_days():
    decision = evaluate("2026-05-22", "return_or_exchange", "non_human_fault", True)

    assert decision.code == "eligible_for_return_or_exchange"
    assert decision.eligible is True


def test_day_seven_remains_eligible_for_return():
    decision = evaluate("2026-05-20", "return_or_exchange", "non_human_fault", True)

    assert decision.code == "eligible_for_return_or_exchange"


def test_damaged_return_is_not_eligible():
    decision = evaluate("2026-05-22", "return_or_exchange", "human_damage", True)

    assert decision.code == "ineligible_for_return_or_exchange"
    assert decision.eligible is False


def test_unpacked_return_is_not_eligible():
    decision = evaluate("2026-05-22", "return_or_exchange", "non_human_fault", False)

    assert decision.code == "ineligible_for_return_or_exchange"
    assert decision.eligible is False


def test_non_human_fault_from_day_eight_to_day_365_is_warranty_repair():
    decision = evaluate("2026-03-01", "warranty_repair", "non_human_fault")

    assert decision.code == "eligible_for_warranty_repair"
    assert decision.eligible is True


def test_day_eight_starts_warranty_repair_path():
    decision = evaluate("2026-05-19", "warranty_repair", "non_human_fault")

    assert decision.code == "eligible_for_warranty_repair"


def test_day_365_remains_warranty_repair_path():
    decision = evaluate("2025-05-27", "warranty_repair", "non_human_fault")

    assert decision.code == "eligible_for_warranty_repair"


def test_day_366_starts_paid_repair_path():
    decision = evaluate("2025-05-26", "warranty_repair", "non_human_fault")

    assert decision.code == "paid_repair_available"


def test_human_damage_is_not_free_warranty():
    decision = evaluate("2026-03-01", "warranty_repair", "human_damage")

    assert decision.code == "ineligible_for_free_warranty"
    assert decision.recommended_service == "paid_repair"


def test_over_warranty_order_only_has_paid_repair_path():
    decision = evaluate("2025-01-01", "warranty_repair", "non_human_fault")

    assert decision.code == "paid_repair_available"
    assert decision.eligible is True


def test_missing_required_fact_requests_clarification():
    decision = evaluate("2026-05-22", "return_or_exchange", "unknown", None)

    assert decision.code == "requires_clarification"
    assert decision.eligible is False


def test_unsupported_request_type_requests_clarification():
    decision = evaluate("2026-03-01", "refund_now", "non_human_fault")

    assert decision.code == "requires_clarification"
    assert decision.eligible is False
