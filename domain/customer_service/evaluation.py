import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    category: str
    input: str
    expected_response_type: str
    required_source_ids: List[str] = field(default_factory=list)
    required_content_keywords: List[str] = field(default_factory=list)
    required_pending_action: bool = False
    simulate_tool_failure: Optional[str] = None
    follow_up: Optional[str] = None
    description: str = ""


@dataclass
class EvaluationResult:
    case_id: str
    passed: bool
    actual_type: str
    failure_reason: Optional[str] = None


def load_cases(path: str = None) -> List[EvaluationCase]:
    if path is None:
        path = str(Path(__file__).parent.parent.parent / "data" / "evaluation_cases.json")
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    cases = []
    for item in raw:
        cases.append(EvaluationCase(
            case_id=item["case_id"],
            category=item["category"],
            input=item["input"],
            expected_response_type=item["expected_response_type"],
            required_source_ids=item.get("required_source_ids", []),
            required_content_keywords=item.get("required_content_keywords", []),
            required_pending_action=item.get("required_pending_action", False),
            simulate_tool_failure=item.get("simulate_tool_failure"),
            follow_up=item.get("follow_up"),
            description=item.get("description", ""),
        ))
    return cases


def evaluate_response(case: EvaluationCase, response) -> EvaluationResult:
    failures = []

    if response.type != case.expected_response_type:
        failures.append(
            f"response_type: expected '{case.expected_response_type}', got '{response.type}'"
        )

    if case.required_source_ids:
        actual_source_ids = {c.source_id for c in response.citations}
        for req_id in case.required_source_ids:
            if req_id not in actual_source_ids:
                failures.append(f"missing required source_id: '{req_id}'")

    if case.required_content_keywords:
        content_lower = response.content.lower()
        for keyword in case.required_content_keywords:
            if keyword.lower() not in content_lower:
                failures.append(f"missing required keyword in content: '{keyword}'")

    if case.required_pending_action and response.pending_action is None:
        failures.append("expected pending_action but got None")

    return EvaluationResult(
        case_id=case.case_id,
        passed=len(failures) == 0,
        actual_type=response.type,
        failure_reason="; ".join(failures) if failures else None,
    )
