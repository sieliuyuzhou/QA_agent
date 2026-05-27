from conftest import SequenceLLM
from domain.customer_service.troubleshooting_agent import TroubleshootingAgent
from tools.base import Citation, Tool, ToolParameter, ToolResult


def _make_faq_tool(content="X1 重置步骤", citations=None):
    def retrieve(query):
        return ToolResult(
            content=content,
            citations=citations or [
                Citation("doc1-x1", "X1 FAQ", "重置 WiFi", "长按设置键 5 秒")
            ],
        )
    return Tool("search_faq", "检索", retrieve, [ToolParameter("query", "string", "查询")])


def test_complete_input_returns_completed():
    agent = TroubleshootingAgent(
        SequenceLLM("Action: search_faq[X1 无法联网]",
                     "Action: Finish[请长按设置键 5 秒重置 WiFi。]"),
        [_make_faq_tool()],
    )
    resp = agent.run("X1 连不上 WiFi", context_messages=[])
    assert resp.status == "completed"
    assert resp.citations
    assert "重置" in resp.recommended_response


def test_missing_model_returns_awaiting_info():
    agent = TroubleshootingAgent(
        SequenceLLM("Action: AskUser[请提供产品型号。]"),
        [_make_faq_tool()],
    )
    resp = agent.run("连不上 WiFi", context_messages=[],
                     extracted_facts={"symptom": "无法联网"})
    assert resp.status == "awaiting_info"


def test_no_knowledge_returns_handoff():
    empty_tool = Tool("search_faq", "检索",
                       lambda q: ToolResult(content="", citations=[]),
                       [ToolParameter("query", "string", "查询")])
    agent = TroubleshootingAgent(
        SequenceLLM("Action: search_faq[未知问题]",
                     "Action: Handoff[知识库无匹配内容]"),
        [empty_tool],
    )
    resp = agent.run("完全未知的问题", context_messages=[])
    assert resp.status == "handoff"


def test_metadata_includes_agent_name():
    agent = TroubleshootingAgent(
        SequenceLLM("Action: search_faq[X1 WiFi]",
                     "Action: Finish[建议重置]"),
        [_make_faq_tool()],
    )
    resp = agent.run("X1 连不上网", context_messages=[])
    assert resp.metadata["agent"] == "TroubleshootingAgent"
    assert resp.metadata["workflow"] == "diagnosis"
