from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from domain.customer_service.langgraph_agent import BaseLangGraphAgent
from tools.base import Tool, ToolParameter, ToolResult
from tools.langchain_convert import to_structured_tool


class FakeLLM:
    """Returns predefined AIMessages in order on each _generate call."""
    def __init__(self, *responses):
        self._responses = list(responses)
        self._call_idx = 0

    def bind_tools(self, tools, **kwargs):
        class Bound:
            def __init__(self, parent):
                self._parent = parent
            def invoke(self, messages, **kw):
                return self._parent._generate(messages, **kw)
        return Bound(self)

    def _generate(self, messages, **kwargs):
        resp = self._responses[self._call_idx]
        self._call_idx += 1
        return resp


def _search_faq(query: str) -> ToolResult:
    return ToolResult(
        content=f"FAQ: {query} 的排障步骤",
        citations=[type("C", (), {"source_id": "doc1", "title": "FAQ", "section": "s", "excerpt": "e"})()],
    )


def _make_tools():
    search = to_structured_tool(Tool(
        "search_faq", "检索FAQ", _search_faq,
        [ToolParameter("query", "string", "查询词")],
    ))
    finish = to_structured_tool(Tool(
        "Finish", "给出最终答案", lambda answer: "OK",
        [ToolParameter("answer", "string", "答案")],
    ))
    ask = to_structured_tool(Tool(
        "AskUser", "向用户提问", lambda question: "OK",
        [ToolParameter("question", "string", "问题")],
    ))
    handoff = to_structured_tool(Tool(
        "Handoff", "转人工", lambda reason: "OK",
        [ToolParameter("reason", "string", "原因")],
    ))
    return [search, finish, ask, handoff]


def test_search_then_finish():
    tools = _make_tools()
    llm = FakeLLM(
        AIMessage(content="", tool_calls=[{"id": "c1", "name": "search_faq", "args": {"query": "X1 重置"}}]),
        AIMessage(content="", tool_calls=[{"id": "c2", "name": "Finish", "args": {"answer": "请长按设置键 5 秒"}}]),
    )
    agent = BaseLangGraphAgent(llm=llm, tools=tools)
    resp = agent.run("X1 怎么重置", context_messages=[])
    assert resp.status == "completed"
    assert "长按设置键" in resp.recommended_response
    assert resp.citations
    assert resp.citations[0].source_id == "doc1"


def test_direct_finish():
    tools = _make_tools()
    llm = FakeLLM(
        AIMessage(content="", tool_calls=[{"id": "c1", "name": "Finish", "args": {"answer": "你好，请问有什么可以帮您？"}}]),
    )
    agent = BaseLangGraphAgent(llm=llm, tools=tools)
    resp = agent.run("你好", context_messages=[])
    assert resp.status == "completed"
    assert "你好" in resp.recommended_response


def test_ask_user():
    tools = _make_tools()
    llm = FakeLLM(
        AIMessage(content="", tool_calls=[{"id": "c1", "name": "AskUser", "args": {"question": "请提供产品型号"}}]),
    )
    agent = BaseLangGraphAgent(llm=llm, tools=tools)
    resp = agent.run("连不上网", context_messages=[])
    assert resp.status == "awaiting_info"
    assert "型号" in resp.recommended_response


def test_handoff():
    tools = _make_tools()
    llm = FakeLLM(
        AIMessage(content="", tool_calls=[{"id": "c1", "name": "Handoff", "args": {"reason": "知识库无匹配"}}]),
    )
    agent = BaseLangGraphAgent(llm=llm, tools=tools)
    resp = agent.run("完全未知的问题", context_messages=[])
    assert resp.status == "handoff"


def test_no_tool_calls_returns_content():
    tools = _make_tools()
    llm = FakeLLM(
        AIMessage(content="我是客服，请问有什么可以帮您？"),
    )
    agent = BaseLangGraphAgent(llm=llm, tools=tools)
    resp = agent.run("你好", context_messages=[])
    assert resp.status == "completed"
    assert "客服" in resp.recommended_response


def test_metadata_contains_agent_name():
    tools = _make_tools()
    llm = FakeLLM(
        AIMessage(content="", tool_calls=[{"id": "c1", "name": "Finish", "args": {"answer": "done"}}]),
    )
    agent = BaseLangGraphAgent(llm=llm, tools=tools, agent_name="TestAgent")
    resp = agent.run("test", context_messages=[])
    assert resp.metadata["agent"] == "TestAgent"
    assert resp.metadata["steps_taken"] >= 1


def test_multiturn_same_conversation():
    """Same conversation_id should accumulate messages via checkpointer."""
    tools = _make_tools()
    llm = FakeLLM(
        AIMessage(content="", tool_calls=[{"id": "c1", "name": "Finish", "args": {"answer": "你好"}}]),
        AIMessage(content="", tool_calls=[{"id": "c2", "name": "Finish", "args": {"answer": "X1 重置步骤"}}]),
    )
    agent = BaseLangGraphAgent(llm=llm, tools=tools)
    resp1 = agent.run("你好", context_messages=[], conversation_id="conv-multi")
    assert resp1.status == "completed"
    resp2 = agent.run("X1 怎么重置", conversation_id="conv-multi")
    assert resp2.status == "completed"
    assert "重置" in resp2.recommended_response
