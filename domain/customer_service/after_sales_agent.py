import re
from typing import Callable

from .context import CurrentUser
from .sub_agent import SubAgentResponse
from .ticketing import TicketActionInput, TicketEligibilityConflict, TicketNotFound
from .workflows import POLICY_SOURCE_ID, ALLOWED_REQUEST_TYPES, ALLOWED_ISSUE_CAUSES


class AfterSalesAgent:
    def __init__(
        self,
        order_service,
        policy_lookup: Callable,
        ticket_action_service,
    ):
        self.order_service = order_service
        self.policy_lookup = policy_lookup
        self.ticket_action_service = ticket_action_service

    def _extract_from_context(self, context_messages: list) -> dict:
        """从对话历史中提取订单号、办理类型和问题描述"""
        info = {}
        if not context_messages:
            return info
        user_text = " ".join(
            m.get("content", "") for m in context_messages
            if m.get("role") == "user"
        )
        # 提取订单号
        match = re.search(r'ORD-[A-Z0-9]+-[A-Z0-9]+', user_text)
        if match:
            info["order_id"] = match.group(0)
        # 推断办理类型
        if any(kw in user_text for kw in ("退货", "换货")):
            info["request_type"] = "return_or_exchange"
        elif "维修" in user_text:
            info["request_type"] = "warranty_repair"
        # 推断问题原因
        if "人为" in user_text:
            info["issue_cause"] = "human_damage"
        elif any(kw in user_text for kw in ("质量", "故障", "坏了", "不响", "离线", "异常")):
            info["issue_cause"] = "non_human_fault"
        # 默认 unknown 让 Agent 追问
        if "issue_cause" not in info:
            info["issue_cause"] = "unknown"
        # 提取包装状态
        if any(kw in user_text for kw in ("包装完好", "包装完整", "包装没问题", "包装没有损坏")):
            info["packaging_intact"] = True
        elif any(kw in user_text for kw in ("包装破损", "包装坏了", "包装损坏", "包装不完整")):
            info["packaging_intact"] = False
        # 用最新用户消息作为问题摘要
        for m in reversed(context_messages):
            if m.get("role") == "user" and m.get("content", "").strip():
                info["issue_summary"] = m["content"].strip()
                break
        return info

    def run(
        self,
        current_user: CurrentUser,
        conversation_id: str,
        payload: dict,
        user_message: str = "",
        context_messages: list = None,
    ) -> SubAgentResponse:
        action_input = self._parse_input(payload)
        turn_count = sum(1 for m in (context_messages or []) if m.get("role") == "assistant" and "eligibility" in m.get("metadata", {}).get("workflow", ""))
        if turn_count >= 3:
            return SubAgentResponse(
                status="handoff",
                recommended_response="多次尝试后仍无法完成售后办理，已为您转接人工处理。",
                metadata={**self._metadata(), "handoff_reason": "eligibility_retry_exceeded"},
            )

        if action_input is None:
            # 从对话历史补充信息
            ctx = self._extract_from_context(context_messages or [])
            merged = {**payload, **ctx}
            action_input = self._parse_input(merged)

        if action_input is None:
            return self._ask_user("请提供订单号、办理类型和问题情况，以便核对售后资格。")
        if action_input.issue_cause == "unknown":
            return self._ask_user("请确认问题是否由人为损坏导致。")

        policy = self.policy_lookup(
            f"{action_input.request_type} {action_input.issue_summary}"
        )
        citations = [
            c for c in policy.citations if c.source_id == POLICY_SOURCE_ID
        ]
        if not citations:
            return SubAgentResponse(
                status="handoff",
                recommended_response="当前没有找到可靠的售后政策依据，已为您转接人工进一步确认。",
                metadata=self._metadata(),
            )

        try:
            action = self.ticket_action_service.create_action(
                current_user.user_id, conversation_id, action_input
            )
        except TicketNotFound:
            return self._ask_user(
                "未找到当前账户可办理的订单，请核对订单号。", citations
            )
        except TicketEligibilityConflict as exc:
            return self._eligibility_response(exc, citations)

        return SubAgentResponse(
            status="completed",
            facts={"order_id": action_input.order_id, "request_type": action_input.request_type},
            decision={
                "code": action.eligibility_code,
                "policy_source": POLICY_SOURCE_ID,
            },
            recommended_response="根据售后政策，您的申请符合办理条件。请确认是否提交模拟售后工单。",
            pending_action=action,
            citations=citations,
            metadata=self._metadata(),
        )

    def _parse_input(self, payload: dict):
        if not isinstance(payload, dict):
            return None
        required = {"order_id", "request_type", "issue_cause", "issue_summary"}
        if not required.issubset(payload):
            return None
        if payload["request_type"] not in ALLOWED_REQUEST_TYPES:
            return None
        if payload["issue_cause"] not in ALLOWED_ISSUE_CAUSES:
            return None
        if not isinstance(payload["order_id"], str) or not payload["order_id"].strip():
            return None
        if not isinstance(payload["issue_summary"], str) or not payload["issue_summary"].strip():
            return None
        packaging_intact = payload.get("packaging_intact")
        if packaging_intact is not None and not isinstance(packaging_intact, bool):
            return None
        return TicketActionInput(
            order_id=payload["order_id"].strip(),
            request_type=payload["request_type"],
            issue_cause=payload["issue_cause"],
            packaging_intact=packaging_intact,
            issue_summary=payload["issue_summary"].strip(),
        )

    def _eligibility_response(self, exc, citations) -> SubAgentResponse:
        if exc.code == "requires_clarification":
            reason_codes = exc.decision.reason_codes if exc.decision else []
            if "packaging_state_missing" in reason_codes:
                return self._ask_user(
                    "您的订单在 7 天退换期内。请确认商品包装是否完好？", citations
                )
            return self._ask_user(
                "办理信息仍不完整，请补充商品状态或故障原因。", citations
            )
        suggested = {
            "return_or_exchange": "退换货",
            "warranty_repair": "保修维修",
            "paid_repair": "付费维修",
        }.get(exc.decision.recommended_service)
        if suggested:
            content = f"根据售后政策，当前申请不能直接办理。您可以明确申请{suggested}后重新评估。"
        else:
            content = "根据售后政策，当前申请不符合办理条件。"
        return SubAgentResponse(
            status="completed",
            facts={},
            decision={
                "code": exc.code,
                "reason_codes": exc.decision.reason_codes,
                "policy_source": POLICY_SOURCE_ID,
            },
            recommended_response=content,
            citations=citations,
            metadata=self._metadata(),
        )

    def _ask_user(self, content: str, citations=None) -> SubAgentResponse:
        return SubAgentResponse(
            status="awaiting_info",
            recommended_response=content,
            citations=citations or [],
            metadata=self._metadata(),
        )

    @staticmethod
    def _metadata() -> dict:
        return {"agent": "AfterSalesAgent", "workflow": "after_sales"}
