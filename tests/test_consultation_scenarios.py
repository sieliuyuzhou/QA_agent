from conftest import MemoryConversationManager, SequenceLLM
from domain.customer_service.agent import CustomerServiceAgent
from tools.base import Citation, Tool, ToolParameter, ToolResult


X2_FAQ_CITATION = Citation(
    source_id="doc2-x2",
    title="Doc2-X2智能门锁FAQ",
    section="支持 Zigbee 吗",
    excerpt="X2 支持 Zigbee 3.0 协议。",
)

POLICY_CITATION = Citation(
    source_id="Doc5-售后与保修政策",
    title="Doc5-售后与保修政策",
    section="过保维修收费标准",
    excerpt="超过保修期的产品维修需收取零件和人工费用。",
)


def _mock_faq_tool(results):
    def search(query, top_k=5):
        return results
    return Tool(
        name="search_faq",
        description="检索FAQ知识库",
        func=search,
        parameters=[ToolParameter("query", "string", "查询问题", required=True)],
    )


def test_product_question_with_model_returns_answer_with_citations():
    faq_result = ToolResult(
        content="X2 支持 Zigbee 3.0 协议。",
        citations=[X2_FAQ_CITATION],
    )
    manager = MemoryConversationManager()
    agent = CustomerServiceAgent(
        SequenceLLM(
            'Action: search_faq[X2 Zigbee 支持]',
            'Action: Finish[X2 支持 Zigbee 3.0 协议。]',
        ),
        manager,
        [_mock_faq_tool(faq_result)],
    )

    response = agent.run("X2 支持 Zigbee 吗？", "conv-1")

    assert response.type == "final_answer"
    assert "Zigbee" in response.content
    assert len(response.citations) >= 1
    assert any(c.source_id == "doc2-x2" for c in response.citations)


def test_missing_model_triggers_ask_user():
    faq_result = ToolResult(content="通用门锁说明", citations=[])
    manager = MemoryConversationManager()
    agent = CustomerServiceAgent(
        SequenceLLM('Action: AskUser[请告诉我您的门锁型号是 X1 还是 X2？]'),
        manager,
        [_mock_faq_tool(faq_result)],
    )

    response = agent.run("门锁连不上 WiFi", "conv-1")

    assert response.type == "ask_user"
    assert "型号" in response.content
    assert manager.messages[-1]["metadata"]["conversation_state"] == "awaiting_clarification"


def test_policy_question_returns_answer_with_policy_citation():
    policy_result = ToolResult(
        content="过保维修收费标准说明",
        citations=[POLICY_CITATION],
    )
    manager = MemoryConversationManager()
    agent = CustomerServiceAgent(
        SequenceLLM(
            'Action: search_faq[过保维修收费]',
            'Action: Finish[超过保修期的产品维修需收取零件和人工费用。]',
        ),
        manager,
        [_mock_faq_tool(policy_result)],
    )

    response = agent.run("过保维修怎么收费？", "conv-1")

    assert response.type == "final_answer"
    assert any(c.source_id == "Doc5-售后与保修政策" for c in response.citations)


def test_no_knowledge_hit_triggers_handoff():
    empty_result = ToolResult(content="未找到相关内容", citations=[])
    manager = MemoryConversationManager()
    agent = CustomerServiceAgent(
        SequenceLLM(
            "Action: search_faq[量子纠缠门锁]",
            "Action: Handoff[无法找到相关知识依据。]",
        ),
        manager,
        [_mock_faq_tool(empty_result)],
    )

    response = agent.run("门锁发生量子纠缠了", "conv-1")

    assert response.type == "handoff"
    assert manager.messages[-1]["metadata"]["conversation_state"] == "handoff_requested"
