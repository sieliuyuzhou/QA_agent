from tools.base import Tool, ToolParameter, ToolResult
from tools.langchain_convert import to_structured_tool, to_structured_tools


def _make_search_tool():
    def retrieve(query: str, top_k: int = 5) -> ToolResult:
        return ToolResult(content=f"results for {query}", citations=[])
    return Tool(
        name="search_faq",
        description="检索FAQ知识库",
        func=retrieve,
        parameters=[
            ToolParameter(name="query", type="string", description="查询词", required=True),
            ToolParameter(name="top_k", type="integer", description="返回数量", required=False, default=5),
        ],
    )


def test_convert_name_and_description():
    tool = to_structured_tool(_make_search_tool())
    assert tool.name == "search_faq"
    assert tool.description == "检索FAQ知识库"


def test_convert_schema_has_required_and_optional():
    tool = to_structured_tool(_make_search_tool())
    schema = tool.args_schema.model_json_schema()
    assert "query" in schema["required"]
    assert "top_k" not in schema["required"]


def test_invoke_with_required_only():
    tool = to_structured_tool(_make_search_tool())
    result = tool.invoke({"query": "X1 重置"})
    assert "X1 重置" in result.content


def test_invoke_with_all_params():
    tool = to_structured_tool(_make_search_tool())
    result = tool.invoke({"query": "X1", "top_k": 3})
    assert "X1" in result.content


def test_convert_batch():
    t1 = Tool("a", "desc a", lambda query: "a", [ToolParameter("query", "string", "q")])
    t2 = Tool("b", "desc b", lambda query: "b", [ToolParameter("query", "string", "q")])
    tools = to_structured_tools([t1, t2])
    assert len(tools) == 2
    assert tools[0].name == "a"
    assert tools[1].name == "b"


def test_bind_tools_with_llm():
    from unittest.mock import MagicMock
    from llm.langchain_adapter import ChatServiceLLM

    mock_service = MagicMock()
    mock_service.model_name = "gpt-3.5-turbo"
    llm = ChatServiceLLM(chat_service=mock_service)

    tool = to_structured_tool(_make_search_tool())
    bound = llm.bind_tools([tool])
    assert bound is not None
