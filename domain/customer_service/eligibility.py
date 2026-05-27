from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from .context import OrderView


@dataclass(frozen=True)
class EligibilityRequest:
    order: OrderView
    request_type: str
    issue_cause: str
    packaging_intact: Optional[bool] = None
    evaluated_on: date = field(default_factory=date.today)


@dataclass(frozen=True)
class EligibilityDecision:
    code: str
    eligible: bool
    recommended_service: Optional[str]
    reason_codes: list[str]
    policy_sections: list[str]


class EligibilityRuleService:
    def evaluate(self, request: EligibilityRequest) -> EligibilityDecision:
        age_days = (
            request.evaluated_on - date.fromisoformat(request.order.purchased_at)
        ).days
        valid_request_types = {
            "return_or_exchange",
            "warranty_repair",
            "paid_repair",
        }
        if (
            age_days < 0
            or request.request_type not in valid_request_types
            or request.issue_cause == "unknown"
        ):
            return EligibilityDecision(
                "requires_clarification",
                False,
                None,
                ["required_fact_missing"],
                [],
            )
        if age_days > 365:
            return EligibilityDecision(
                "paid_repair_available",
                True,
                "paid_repair",
                ["outside_warranty_period"],
                ["过保后维修怎么收费？"],
            )
        if request.request_type == "return_or_exchange" and age_days <= 7:
            if request.packaging_intact is None:
                return EligibilityDecision(
                    "requires_clarification",
                    False,
                    None,
                    ["packaging_state_missing"],
                    ["退换货政策"],
                )
            if request.issue_cause == "non_human_fault" and request.packaging_intact:
                return EligibilityDecision(
                    "eligible_for_return_or_exchange",
                    True,
                    "return_or_exchange",
                    ["within_7_days", "packaging_intact", "not_human_damaged"],
                    ["退换货政策"],
                )
            return EligibilityDecision(
                "ineligible_for_return_or_exchange",
                False,
                "paid_repair",
                ["return_conditions_not_met"],
                ["退换货政策"],
            )
        if request.issue_cause == "human_damage":
            return EligibilityDecision(
                "ineligible_for_free_warranty",
                False,
                "paid_repair",
                ["human_damage_excluded"],
                ["保修条款"],
            )
        if 8 <= age_days <= 365 and request.issue_cause == "non_human_fault":
            return EligibilityDecision(
                "eligible_for_warranty_repair",
                True,
                "warranty_repair",
                ["within_warranty_period", "not_human_damaged"],
                ["保修条款", "维修和退换有什么区别？"],
            )
        return EligibilityDecision(
            "requires_clarification",
            False,
            None,
            ["unsupported_request_or_missing_fact"],
            [],
        )
