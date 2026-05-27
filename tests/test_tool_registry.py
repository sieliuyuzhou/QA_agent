import pytest
from domain.customer_service.tool_registry import ToolRegistry
from tools.base import Tool, ToolParameter


def test_registry_allows_registered_tool():
    tool = Tool("search_faq", "检索", lambda q: "ok", [ToolParameter("query", "string", "查询")])
    registry = ToolRegistry({"TroubleshootingAgent": [tool]})
    assert registry.get_tool("TroubleshootingAgent", "search_faq") is tool


def test_registry_blocks_unregistered_tool():
    tool = Tool("search_faq", "检索", lambda q: "ok", [ToolParameter("query", "string", "查询")])
    registry = ToolRegistry({"TroubleshootingAgent": [tool]})
    assert registry.get_tool("TroubleshootingAgent", "get_order") is None


def test_registry_lists_agent_tools():
    t1 = Tool("a", "desc", lambda: None)
    t2 = Tool("b", "desc", lambda: None)
    registry = ToolRegistry({"X": [t1, t2]})
    names = registry.list_tools("X")
    assert names == ["a", "b"]


def test_registry_raises_for_unknown_agent():
    registry = ToolRegistry({})
    assert registry.get_tool("Unknown", "x") is None
