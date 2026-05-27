import json
import re

from .agent import AgentResponse
from .handoff import build_handoff_summary
from .sub_agent import SubAgentResponse

SUPERVISOR_SYSTEM_PROMPT = """你是一个客服 Supervisor，负责判断用户意图并路由到正确的处理器。

## 可用路由
- Action: RouteConsultation[用户消息]：产品功能、使用方法、政策咨询类问题。
- Action: RouteTroubleshooting[用户消息]：故障描述、设备异常、排障类问题。
- Action: RouteAfterSales[{{"order_id":"订单号","request_type":"warranty_repair","issue_cause":"non_human_fault","packaging_intact":null,"issue_summary":"问题摘要"}}]：退换、维修、售后申请。必须从用户消息中提取结构化信息，使用 JSON 格式参数。
- Action: AskUser[澄清问题]：信息不足无法判断意图时。
- Action: Handoff[转人工原因]：用户主动要求人工、投诉或风险升级。

## RouteAfterSales 提取规则
当用户提出售后请求时，必须从消息中提取：
- order_id: 订单号（如 ORD-A-X1）
- request_type: 办理类型（return_or_exchange/warranty_repair/paid_repair）
- issue_cause: 故障原因（non_human_fault/human_damage/unknown）
- issue_summary: 问题描述

示例：
用户："我的订单 ORD-A-X1 要申请保修维修，产品无法开机，不是人为损坏"
→ Action: RouteAfterSales[{{"order_id":"ORD-A-X1","request_type":"warranty_repair","issue_cause":"non_human_fault","issue_summary":"无法开机"}}]

用户："我要退货"（缺少订单号和原因）
→ Action: AskUser[请提供订单号和退货原因，以便为您核对售后资格。]

必须一次只输出一个 Action。
"""


class Supervisor:
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

    def _parse_route(self, output: str):
        thought_match = re.search(
            r"Thought:\s*(.+?)(?=Action:|$)", output, re.DOTALL | re.IGNORECASE
        )
        thought = thought_match.group(1).strip() if thought_match else ""

        action_match = re.search(
            r"Action:\s*(.+?)(?=$)", output, re.DOTALL | re.IGNORECASE
        )
        action_str = action_match.group(1).strip() if action_match else ""

        m = re.match(r"(\w+)\s*\[(.+)\]", action_str, re.DOTALL)
        if m:
            return thought, m.group(1).strip(), m.group(2).strip()
        return thought, action_str, ""

    def _transform_response(
        self, sub_response: SubAgentResponse, agent_name: str, conversation_id: str,
        context_messages: list, current_user, final_answer: str,
    ) -> AgentResponse:
        status_type_map = {
            "completed": "final_answer",
            "awaiting_info": "ask_user",
            "handoff": "handoff",
        }
        response_type = status_type_map.get(sub_response.status, "final_answer")

        content = sub_response.recommended_response or final_answer
        metadata = {"sub_agent": agent_name, **(sub_response.metadata or {})}

        if sub_response.pending_action:
            response_type = "confirm_action"

        if response_type == "handoff" and current_user:
            summary = build_handoff_summary(
                conversation_id=conversation_id,
                user_id=current_user.user_id,
                reason=content,
                context_messages=context_messages,
            )
            metadata["handoff_summary"] = {
                "reason": summary.reason,
                "product_model": summary.product_model,
                "facts": summary.facts,
                "steps_taken": summary.steps_taken,
                "remaining": summary.remaining,
            }

        states = {
            "final_answer": "active",
            "ask_user": "awaiting_clarification",
            "handoff": "handoff_requested",
            "confirm_action": "awaiting_confirmation",
        }

        self.manager.add_message(
            conversation_id, "assistant", content,
            metadata={
                "action_type": response_type,
                "conversation_state": states.get(response_type, "active"),
            },
        )

        return AgentResponse(
            type=response_type,
            content=content,
            conversation_id=conversation_id,
            metadata=metadata,
            citations=sub_response.citations or [],
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
        context = "\n".join(
            f"[{m.get('role', 'unknown')}]: {m.get('content', '')}"
            for m in context_messages
        ) or "（无历史对话）"

        output = self.llm.chat(
            f"## 对话历史\n{context}\n\n## 当前用户输入\n{user_input}",
            system_prompt=SUPERVISOR_SYSTEM_PROMPT,
        )
        thought, action_name, action_input = self._parse_route(output)

        if action_name in ("AskUser",):
            self.manager.add_message(
                conversation_id, "assistant", action_input,
                metadata={"action_type": "ask_user", "conversation_state": "awaiting_clarification"},
            )
            return AgentResponse(
                type="ask_user", content=action_input,
                conversation_id=conversation_id,
                metadata={"sub_agent": "Supervisor"},
            )

        if action_name == "Handoff":
            content = action_input or "已为您转接人工。"
            summary = build_handoff_summary(
                conversation_id=conversation_id,
                user_id=current_user.user_id if current_user else "unknown",
                reason=content, context_messages=context_messages,
            )
            self.manager.add_message(
                conversation_id, "assistant", content,
                metadata={"action_type": "handoff", "conversation_state": "handoff_requested"},
            )
            return AgentResponse(
                type="handoff", content=content,
                conversation_id=conversation_id,
                metadata={
                    "sub_agent": "Supervisor",
                    "handoff_summary": {
                        "reason": summary.reason,
                        "product_model": summary.product_model,
                        "facts": summary.facts,
                        "steps_taken": summary.steps_taken,
                        "remaining": summary.remaining,
                    },
                },
            )

        if action_name == "RouteConsultation":
            sub = self.consultation_handler.run(
                user_message=action_input, context_messages=context_messages,
                current_user=current_user, conversation_id=conversation_id,
            )
            return self._transform_response(
                sub, "ConsultationHandler", conversation_id,
                context_messages, current_user, action_input,
            )

        if action_name == "RouteTroubleshooting":
            sub = self.troubleshooting_agent.run(
                user_message=action_input, context_messages=context_messages,
                current_user=current_user, conversation_id=conversation_id,
            )
            return self._transform_response(
                sub, "TroubleshootingAgent", conversation_id,
                context_messages, current_user, action_input,
            )

        if action_name == "RouteAfterSales":
            try:
                payload = json.loads(action_input)
            except (json.JSONDecodeError, TypeError):
                payload = {}
            sub = self.after_sales_agent.run(
                current_user=current_user, conversation_id=conversation_id,
                payload=payload, user_message=user_input,
                context_messages=context_messages,
            )
            return self._transform_response(
                sub, "AfterSalesAgent", conversation_id,
                context_messages, current_user, action_input,
            )

        self.manager.add_message(
            conversation_id, "assistant", "无法识别您的请求，已为您转接人工。",
            metadata={"action_type": "handoff", "conversation_state": "handoff_requested"},
        )
        return AgentResponse(
            type="handoff",
            content="无法识别您的请求，已为您转接人工。",
            conversation_id=conversation_id,
            metadata={"sub_agent": "Supervisor"},
        )
