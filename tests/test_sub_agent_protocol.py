from domain.customer_service.sub_agent import SubAgentInput, SubAgentResponse
from domain.customer_service.context import CurrentUser


def test_sub_agent_input_holds_user_and_facts():
    user = CurrentUser("alice", "Alice")
    inp = SubAgentInput(
        conversation_id="conv-1",
        current_user=user,
        user_message="X1 连不上 WiFi",
        context_messages=["[user]: X1 连不上 WiFi"],
        extracted_facts={"product_model": "X1", "symptom": "无法联网"},
    )
    assert inp.current_user.user_id == "alice"
    assert inp.extracted_facts["product_model"] == "X1"


def test_sub_agent_response_completed_with_decision():
    resp = SubAgentResponse(
        status="completed",
        facts={"product_model": "X1"},
        decision={"code": "eligible", "reason": "符合条件"},
        recommended_response="建议如下...",
        citations=[],
        metadata={"agent": "TestAgent"},
    )
    assert resp.status == "completed"
    assert resp.pending_action is None


def test_sub_agent_response_awaiting_info():
    resp = SubAgentResponse(
        status="awaiting_info",
        facts={},
        recommended_response="请提供型号",
    )
    assert resp.status == "awaiting_info"
    assert resp.citations == []
    assert resp.metadata == {}
