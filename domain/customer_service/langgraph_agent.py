from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import StructuredTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

from tools.base import Citation, ToolResult
from .sub_agent import SubAgentResponse


class _GraphState(TypedDict):
    messages: Annotated[list, add_messages]


FINISH_NAMES = frozenset({"Finish", "AskUser", "Handoff"})

STATUS_MAP = {
    "Finish": "completed",
    "AskUser": "awaiting_info",
    "Handoff": "handoff",
}


def _is_terminal(tool_calls: list) -> bool:
    return any(tc["name"] in FINISH_NAMES for tc in tool_calls)


def _extract_citations(messages: list) -> list:
    citations = []
    for msg in messages:
        if isinstance(msg, ToolMessage) and msg.name not in FINISH_NAMES:
            pass
        if hasattr(msg, "content") and isinstance(msg.content, str):
            pass
    return citations


class BaseLangGraphAgent:
    def __init__(
        self,
        llm,
        tools: List[StructuredTool],
        max_steps: int = 5,
        agent_name: str = "LangGraphAgent",
        checkpointer=None,
    ):
        self.llm = llm
        self.tools = tools
        self.max_steps = max_steps
        self.agent_name = agent_name
        self.checkpointer = checkpointer or MemorySaver()
        self._tools_map = {t.name: t for t in tools}
        self._graph = self._build_graph()

    def _execute_tools(self, state: _GraphState) -> dict:
        last_ai = None
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                last_ai = msg
                break
        if last_ai is None:
            return {"messages": []}

        tool_messages = []
        for tc in last_ai.tool_calls:
            name = tc["name"]
            tool = self._tools_map.get(name)
            if tool:
                raw = tool.invoke(tc["args"])
                if isinstance(raw, ToolResult):
                    self._collected_citations.extend(raw.citations)
                    content = raw.content
                else:
                    content = str(raw)
            else:
                content = "OK"
            tool_messages.append(ToolMessage(
                content=content, name=name, tool_call_id=tc["id"],
            ))
        return {"messages": tool_messages}

    def _build_graph(self) -> Any:
        llm_with_tools = self.llm.bind_tools(self.tools)

        def agent_node(state: _GraphState) -> dict:
            system = SystemMessage(content=self._get_system_prompt())
            response = llm_with_tools.invoke([system] + state["messages"])
            return {"messages": [response]}

        def _last_ai(state: _GraphState) -> AIMessage:
            for msg in reversed(state["messages"]):
                if isinstance(msg, AIMessage):
                    return msg
            return AIMessage(content="")

        def router(state: _GraphState) -> str:
            ai = _last_ai(state)
            if not ai.tool_calls:
                return "end"
            if _is_terminal(ai.tool_calls):
                return "terminal"
            return "tools"

        tools_node = self._execute_tools

        def terminal_node(state: _GraphState) -> dict:
            ai = _last_ai(state)
            tc = ai.tool_calls[0]
            name = tc["name"]
            tool = self._tools_map.get(name)
            if tool:
                result = tool.invoke(tc["args"])
            else:
                result = "OK"
            return {"messages": [ToolMessage(
                content=str(result), name=name, tool_call_id=tc["id"],
            )]}

        graph = StateGraph(_GraphState)
        graph.add_node("agent", agent_node)
        graph.add_node("tools", tools_node)
        graph.add_node("terminal", terminal_node)
        graph.set_entry_point("agent")
        graph.add_conditional_edges("agent", router, {
            "tools": "tools",
            "terminal": "terminal",
            "end": END,
        })
        graph.add_edge("tools", "agent")
        graph.add_edge("terminal", END)
        return graph.compile(checkpointer=self.checkpointer)

    def _get_system_prompt(self) -> str:
        return "你是一个智能客服助手。"

    def run(
        self,
        user_message: str,
        context_messages: list = None,
        current_user=None,
        conversation_id: str = "",
        extracted_facts: dict = None,
    ) -> SubAgentResponse:
        messages: list = []
        if context_messages:
            for m in context_messages:
                role = m.get("role", "user") if isinstance(m, dict) else "user"
                content = m.get("content", "") if isinstance(m, dict) else str(m)
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
                elif role == "system":
                    messages.append(SystemMessage(content=content))
        messages.append(HumanMessage(content=user_message))

        self._collected_citations: list = []
        config = {
            "recursion_limit": self.max_steps * 2 + 2,
            "configurable": {"thread_id": conversation_id or "default"},
        }
        final_state = self._graph.invoke({"messages": messages}, config=config)

        return self._to_response(final_state["messages"], self._collected_citations)

    def _to_response(self, messages: list, collected_citations: list = None) -> SubAgentResponse:
        last_ai = None
        terminal_tc = None
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.tool_calls:
                tc = msg.tool_calls[0]
                if tc["name"] in FINISH_NAMES:
                    last_ai = msg
                    terminal_tc = tc
                    break

        if terminal_tc is None:
            for msg in reversed(messages):
                if isinstance(msg, AIMessage):
                    last_ai = msg
                    break
            if last_ai is None:
                return SubAgentResponse(
                    status="handoff",
                    recommended_response="处理异常，已为您转接人工。",
                    metadata={"agent": self.agent_name},
                )
            return SubAgentResponse(
                status="completed",
                recommended_response=last_ai.content or "",
                metadata={"agent": self.agent_name, "steps_taken": len(messages)},
            )

        name = terminal_tc["name"]
        answer = terminal_tc["args"].get("answer") or terminal_tc["args"].get("question") or terminal_tc["args"].get("reason") or ""
        status = STATUS_MAP[name]
        steps = sum(1 for m in messages if isinstance(m, AIMessage))

        return SubAgentResponse(
            status=status,
            recommended_response=answer,
            citations=collected_citations or [],
            metadata={
                "agent": self.agent_name,
                "steps_taken": steps,
            },
        )
