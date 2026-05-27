from conftest import MemoryConversationManager, SequenceLLM
from domain.customer_service.agent import CustomerServiceAgent


def build_agent(*outputs):
    manager = MemoryConversationManager()
    llm = SequenceLLM(*outputs)
    return CustomerServiceAgent(llm, manager, [], max_steps=2), manager, llm


def test_rules_are_sent_as_system_prompt_and_user_input_is_turn_prompt():
    agent, _, llm = build_agent("Action: Finish[已收到]")

    agent.run("用户消息", "conv-1")

    assert "可用工具" in llm.calls[0]["system_prompt"]
    assert "用户消息" in llm.calls[0]["prompt"]
    assert "用户消息" not in llm.calls[0]["system_prompt"]


def test_ask_user_stops_loop_and_persists_visible_question():
    agent, manager, _ = build_agent("Action: AskUser[请提供门锁型号。]")

    response = agent.run("连不上网", "conv-1")

    assert response.type == "ask_user"
    assert response.content == "请提供门锁型号。"
    assert manager.messages[-1]["metadata"] == {
        "action_type": "ask_user",
        "conversation_state": "awaiting_clarification",
    }


def test_handoff_stops_loop_and_returns_user_visible_reason():
    agent, manager, _ = build_agent("Action: Handoff[需要人工进一步确认。]")

    response = agent.run("我要人工", "conv-1")

    assert response.type == "handoff"
    assert manager.messages[-1]["metadata"] == {
        "action_type": "handoff",
        "conversation_state": "handoff_requested",
    }


def test_handoff_response_includes_summary_in_metadata():
    agent, manager, _ = build_agent("Action: Handoff[用户要求人工服务。]")

    response = agent.run("转人工", "conv-1")

    assert response.type == "handoff"
    assert "handoff_summary" in response.metadata
    summary = response.metadata["handoff_summary"]
    assert summary["reason"] == "用户要求人工服务。"
    assert isinstance(summary["facts"], list)
    assert isinstance(summary["steps_taken"], list)
