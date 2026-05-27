from domain.customer_service.context import CurrentUser
from domain.customer_service.handoff import HandoffSummary, build_handoff_summary


def test_basic_handoff_summary_contains_reason():
    summary = build_handoff_summary(
        "conv-1", "user-1", "用户要求人工", []
    )

    assert summary.conversation_id == "conv-1"
    assert summary.user_id == "user-1"
    assert summary.reason == "用户要求人工"
    assert summary.facts == []
    assert summary.steps_taken == []


def test_diagnosis_metadata_populates_model_and_symptom():
    messages = [
        {
            "role": "assistant",
            "content": "排障步骤...",
            "metadata": {
                "action_type": "final_answer",
                "conversation_state": "active",
                "intent": "diagnosis",
                "workflow": "diagnosis",
                "product_model": "X1",
                "symptom": "无法联网",
            },
        },
    ]

    summary = build_handoff_summary(
        "conv-1", "user-1", "排障无效", messages
    )

    assert summary.product_model == "X1"
    assert any("无法联网" in f for f in summary.facts)


def test_after_sales_metadata_records_workflow_entry():
    messages = [
        {
            "role": "assistant",
            "content": "请确认...",
            "metadata": {
                "action_type": "confirm_action",
                "conversation_state": "awaiting_confirmation",
                "intent": "after_sales",
                "workflow": "after_sales",
            },
        },
    ]

    summary = build_handoff_summary(
        "conv-1", "user-1", "用户未确认", messages
    )

    assert any("售后" in f for f in summary.facts)


def test_ask_user_messages_captured_as_steps():
    messages = [
        {
            "role": "assistant",
            "content": "请告诉我您的门锁型号是 X1 还是 X2？",
            "metadata": {
                "action_type": "ask_user",
                "conversation_state": "awaiting_clarification",
            },
        },
    ]

    summary = build_handoff_summary(
        "conv-1", "user-1", "无法确定型号", messages
    )

    assert len(summary.steps_taken) == 1
    assert "型号" in summary.steps_taken[0]


def test_final_answer_messages_captured_as_steps():
    messages = [
        {
            "role": "assistant",
            "content": "X2 支持 Zigbee 3.0 协议。",
            "metadata": {
                "action_type": "final_answer",
                "conversation_state": "active",
            },
        },
    ]

    summary = build_handoff_summary(
        "conv-1", "user-1", "用户不满意", messages
    )

    assert len(summary.steps_taken) == 1
    assert "Zigbee" in summary.steps_taken[0]


def test_empty_messages_summary_has_reason_only():
    summary = build_handoff_summary(
        "conv-1", "user-1", "系统错误", []
    )

    assert summary.reason == "系统错误"
    assert summary.remaining == "系统错误"
    assert summary.product_model is None


def test_summary_with_facts_clears_remaining():
    messages = [
        {
            "role": "assistant",
            "content": "排障步骤",
            "metadata": {
                "workflow": "diagnosis",
                "product_model": "X1",
                "symptom": "离线",
            },
        },
    ]

    summary = build_handoff_summary(
        "conv-1", "user-1", "排障无效", messages
    )

    assert summary.remaining is None
    assert len(summary.facts) > 0
