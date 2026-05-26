import tools.base as tool_base
from conftest import MemoryConversationManager, SequenceLLM
from domain.customer_service.agent import CustomerServiceAgent
from tools.base import Tool, ToolParameter


def test_agent_returns_citations_from_tool_observation():
    citation_type = tool_base.Citation
    tool_result_type = tool_base.ToolResult

    def retrieve(query):
        return tool_result_type(
            content="X1 重置步骤",
            citations=[
                citation_type(
                    source_id="doc1-x1",
                    title="Doc1-X1智能门锁FAQ",
                    section="怎么重置 WiFi？",
                    excerpt="长按设置键约 5 秒。",
                )
            ],
        )

    tool = Tool(
        "search_faq",
        "检索",
        retrieve,
        [ToolParameter("query", "string", "检索词")],
    )
    agent = CustomerServiceAgent(
        SequenceLLM(
            "Action: search_faq[怎么重置 WiFi]",
            "Action: Finish[请长按设置键约 5 秒。]",
        ),
        MemoryConversationManager(),
        [tool],
    )

    response = agent.run("怎么重置 WiFi", "conv-1")

    assert response.citations[0].source_id == "doc1-x1"


def test_plain_search_function_remains_a_string_for_non_agent_callers(monkeypatch):
    from tools import faq_search

    tool_result_type = tool_base.ToolResult
    monkeypatch.setattr(
        faq_search,
        "retrieve_faq",
        lambda query, top_k=5: tool_result_type(
            content="plain output",
            citations=[],
        ),
    )

    assert faq_search.search_faq("x") == "plain output"


def test_finish_after_empty_knowledge_result_becomes_handoff():
    tool = Tool(
        "search_faq",
        "检索",
        lambda query: tool_base.ToolResult(content="未找到相关内容。", citations=[]),
        [ToolParameter("query", "string", "检索词")],
    )
    manager = MemoryConversationManager()
    agent = CustomerServiceAgent(
        SequenceLLM("Action: search_faq[未知问题]", "Action: Finish[猜测答案]"),
        manager,
        [tool],
    )

    response = agent.run("未知问题", "conv-1")

    assert response.type == "handoff"
    assert "可靠知识依据" in response.content
    assert manager.messages[-1]["metadata"]["action_type"] == "handoff"


def test_ask_user_message_records_auditable_waiting_state():
    manager = MemoryConversationManager()
    agent = CustomerServiceAgent(
        SequenceLLM("Action: AskUser[请提供产品型号。]"),
        manager,
        [],
    )

    agent.run("设备坏了", "conv-1")

    assert (
        manager.messages[-1]["metadata"]["conversation_state"]
        == "awaiting_clarification"
    )
