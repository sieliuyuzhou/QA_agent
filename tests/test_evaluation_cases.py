from domain.customer_service.evaluation import (
    EvaluationCase,
    evaluate_response,
    load_cases,
)
from domain.customer_service.agent import AgentResponse


def test_load_cases_returns_all_scenarios():
    cases = load_cases()

    assert len(cases) == 14
    categories = {c.category for c in cases}
    assert "product_consultation" in categories
    assert "troubleshooting" in categories
    assert "return_eligibility" in categories
    assert "warranty_eligibility" in categories
    assert "warranty_exclusion" in categories
    assert "no_knowledge" in categories
    assert "prompt_injection" in categories


def test_each_case_has_required_fields():
    cases = load_cases()
    for case in cases:
        assert case.case_id, f"missing case_id"
        assert case.category, f"{case.case_id}: missing category"
        assert case.input, f"{case.case_id}: missing input"
        assert case.expected_response_type, f"{case.case_id}: missing expected_response_type"


def test_case_ids_are_unique():
    cases = load_cases()
    ids = [c.case_id for c in cases]
    assert len(ids) == len(set(ids))


def test_all_expected_types_are_valid():
    valid_types = {"final_answer", "ask_user", "confirm_action", "handoff", "error"}
    cases = load_cases()
    for case in cases:
        assert case.expected_response_type in valid_types, \
            f"{case.case_id}: invalid type '{case.expected_response_type}'"


def _make_response(response_type, content="", citations=None, pending_action=None):
    return AgentResponse(
        type=response_type,
        content=content,
        conversation_id="eval-conv",
        citations=citations or [],
        pending_action=pending_action,
    )


def test_evaluate_passes_when_all_criteria_met():
    case = EvaluationCase(
        case_id="TEST-001",
        category="test",
        input="test",
        expected_response_type="final_answer",
        required_content_keywords=["hello"],
    )
    response = _make_response("final_answer", "hello world")

    result = evaluate_response(case, response)

    assert result.passed is True
    assert result.failure_reason is None


def test_evaluate_fails_on_wrong_response_type():
    case = EvaluationCase(
        case_id="TEST-002",
        category="test",
        input="test",
        expected_response_type="final_answer",
    )
    response = _make_response("ask_user", "what?")

    result = evaluate_response(case, response)

    assert result.passed is False
    assert "response_type" in result.failure_reason


def test_evaluate_fails_on_missing_source_id():
    from tools.base import Citation
    case = EvaluationCase(
        case_id="TEST-003",
        category="test",
        input="test",
        expected_response_type="final_answer",
        required_source_ids=["doc1-x1"],
    )
    response = _make_response(
        "final_answer", "answer",
        citations=[Citation("other-doc", "Other", "section", "excerpt")],
    )

    result = evaluate_response(case, response)

    assert result.passed is False
    assert "source_id" in result.failure_reason


def test_evaluate_fails_on_missing_keyword():
    case = EvaluationCase(
        case_id="TEST-004",
        category="test",
        input="test",
        expected_response_type="final_answer",
        required_content_keywords=["Zigbee"],
    )
    response = _make_response("final_answer", "some answer without the keyword")

    result = evaluate_response(case, response)

    assert result.passed is False
    assert "keyword" in result.failure_reason


def test_evaluate_fails_on_missing_pending_action():
    case = EvaluationCase(
        case_id="TEST-005",
        category="test",
        input="test",
        expected_response_type="confirm_action",
        required_pending_action=True,
    )
    response = _make_response("confirm_action", "please confirm")

    result = evaluate_response(case, response)

    assert result.passed is False
    assert "pending_action" in result.failure_reason
