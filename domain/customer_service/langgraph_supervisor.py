import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import StructuredTool

from .agent import AgentResponse
from .handoff import build_handoff_summary
from .sub_agent import SubAgentResponse

_SUPERVISOR_SYSTEM_PROMPT = """你是一个客服 Supervisor，负责判断用户意图并路由到正确的处理器。
请调用合适的工具完成路由，不要输出自由文本。"""

_ROUTE_TOOL_MAP = {
    "RouteConsultation": "consultation",
    "RouteTroubleshooting": "troubleshooting",
    "RouteAfterSales": "after_sales",
}

_STATUS_TYPE_MAP = {
    "completed": "final_answer",
    "awaiting_info": "ask_user",
    "handoff": "handoff",
}


class LangGraphSupervisor:
    def __init__(
        self,
        llm,
        manager,
        troubleshooting_agent,
        after_sales_agent,
        consultation_handler,
        max_steps: int = 3,
    ):
        self.llm = llm
        self.manager = manager
        self.troubleshooting_agent = troubleshooting_agent
        self.after_sales_agent = after_sales_agent
        self.consultation_handler = consultation_handler
        self.max_steps = max_steps
        self._routing_tools = self._build_routing_tools()
        self._llm_with_tools = self.llm.bind_tools(self._routing_tools)

    def _build_routing_tools(self) -> list:
        def route_consultation(message: str) -> str:
            """Route to consultation handler for product/policy questions."""
            return "OK"

        def route_troubleshooting(message: str) -> str:
            """Route to troubleshooting agent for device issues."""
            return "OK"

        def route_after_sales(message: str) -> str:
            """Route to after-sales agent for return/warranty/repair requests. Message should be JSON with order_id, request_type, issue_cause, issue_summary."""
            return "OK"

        def ask_user(question: str) -> str:
            """Ask user for more information."""
            return "OK"

        def handoff(reason: str) -> str:
            """Transfer to human agent."""
            return "OK"

        return [
            StructuredTool.from_function(route_consultation, name="RouteConsultation",
                                          description="产品功能、使用方法、政策咨询类问题"),
            StructuredTool.from_function(route_troubleshooting, name="RouteTroubleshooting",
                                          description="故障描述、设备异常、排障类问题"),
            StructuredTool.from_function(route_after_sales, name="RouteAfterSales",
                                          description="退换、维修、售后申请"),
            StructuredTool.from_function(ask_user, name="AskUser",
                                          description="信息不足无法判断意图时向用户提问"),
            StructuredTool.from_function(handoff, name="Handoff",
                                          description="用户主动要求人工、投诉或风险升级"),
        ]

    def _dispatch(self, tool_name: str, tool_args: dict,
                  context_messages: list, current_user, user_input: str,
                  conversation_id: str) -> AgentResponse:
        if tool_name == "AskUser":
            content = tool_args.get("question", "")
            self.manager.add_message(conversation_id, "assistant", content,
                                     metadata={"action_type": "ask_user", "conversation_state": "awaiting_clarification"})
            return AgentResponse(type="ask_user", content=content,
                                 conversation_id=conversation_id,
                                 metadata={"sub_agent": "Supervisor"})

        if tool_name == "Handoff":
            content = tool_args.get("reason", "已为您转接人工。")
            summary = build_handoff_summary(
                conversation_id=conversation_id,
                user_id=current_user.user_id if current_user else "unknown",
                reason=content, context_messages=context_messages,
            )
            self.manager.add_message(conversation_id, "assistant", content,
                                     metadata={"action_type": "handoff", "conversation_state": "handoff_requested"})
            return AgentResponse(
                type="handoff", content=content, conversation_id=conversation_id,
                metadata={"sub_agent": "Supervisor", "handoff_summary": {
                    "reason": summary.reason, "product_model": summary.product_model,
                    "facts": summary.facts, "steps_taken": summary.steps_taken,
                    "remaining": summary.remaining,
                }},
            )

        if tool_name == "RouteConsultation":
            sub = self.consultation_handler.run(
                user_message=tool_args.get("message", user_input),
                context_messages=context_messages, current_user=current_user,
                conversation_id=conversation_id,
            )
            return self._transform_response(sub, "ConsultationHandler", conversation_id,
                                            context_messages, current_user)

        if tool_name == "RouteTroubleshooting":
            sub = self.troubleshooting_agent.run(
                user_message=tool_args.get("message", user_input),
                context_messages=context_messages, current_user=current_user,
                conversation_id=conversation_id,
            )
            return self._transform_response(sub, "TroubleshootingAgent", conversation_id,
                                            context_messages, current_user)

        if tool_name == "RouteAfterSales":
            message = tool_args.get("message", "")
            try:
                payload = json.loads(message)
            except (json.JSONDecodeError, TypeError):
                payload = {}
            sub = self.after_sales_agent.run(
                current_user=current_user, conversation_id=conversation_id,
                payload=payload, user_message=user_input,
                context_messages=context_messages,
            )
            return self._transform_response(sub, "AfterSalesAgent", conversation_id,
                                            context_messages, current_user)

        self.manager.add_message(conversation_id, "assistant", "无法识别您的请求，已为您转接人工。",
                                 metadata={"action_type": "handoff", "conversation_state": "handoff_requested"})
        return AgentResponse(type="handoff", content="无法识别您的请求，已为您转接人工。",
                             conversation_id=conversation_id, metadata={"sub_agent": "Supervisor"})

    def _transform_response(self, sub_response: SubAgentResponse, agent_name: str,
                            conversation_id: str, context_messages: list,
                            current_user) -> AgentResponse:
        response_type = _STATUS_TYPE_MAP.get(sub_response.status, "final_answer")
        content = sub_response.recommended_response or ""
        metadata = {"sub_agent": agent_name, **(sub_response.metadata or {})}

        if sub_response.pending_action:
            response_type = "confirm_action"

        if response_type == "handoff" and current_user:
            summary = build_handoff_summary(
                conversation_id=conversation_id,
                user_id=current_user.user_id,
                reason=content, context_messages=context_messages,
            )
            metadata["handoff_summary"] = {
                "reason": summary.reason, "product_model": summary.product_model,
                "facts": summary.facts, "steps_taken": summary.steps_taken,
                "remaining": summary.remaining,
            }

        states = {
            "final_answer": "active", "ask_user": "awaiting_clarification",
            "handoff": "handoff_requested", "confirm_action": "awaiting_confirmation",
        }
        self.manager.add_message(conversation_id, "assistant", content,
                                 metadata={"action_type": response_type,
                                           "conversation_state": states.get(response_type, "active")})
        return AgentResponse(
            type=response_type, content=content, conversation_id=conversation_id,
            metadata=metadata, citations=sub_response.citations or [],
            pending_action=sub_response.pending_action,
        )

    def run(
        self,
        user_input: str,
        conversation_id: str,
        verbose: bool = False,
        current_user=None,
    ) -> AgentResponse:
        self.manager.add_message(conversation_id, "user", user_input)
        context_messages = self.manager.get_context(conversation_id)
        context = "\n".join(f"[{m.get('role', 'unknown')}]: {m.get('content', '')}" for m in context_messages) or "（无历史对话）"

        system = SystemMessage(content=_SUPERVISOR_SYSTEM_PROMPT)
        user = HumanMessage(content=f"## 对话历史\n{context}\n\n## 当前用户输入\n{user_input}")

        ai_msg: AIMessage = self._llm_with_tools.invoke([system, user])

        if not ai_msg.tool_calls:
            self.manager.add_message(conversation_id, "assistant", ai_msg.content or "无法识别您的请求，已为您转接人工。",
                                     metadata={"action_type": "handoff", "conversation_state": "handoff_requested"})
            return AgentResponse(type="handoff", content=ai_msg.content or "无法识别您的请求，已为您转接人工。",
                                 conversation_id=conversation_id, metadata={"sub_agent": "Supervisor"})

        tc = ai_msg.tool_calls[0]
        tool_name = tc["name"]
        tool_args = tc["args"]
        return self._dispatch(tool_name, tool_args, context_messages, current_user,
                              user_input, conversation_id)
