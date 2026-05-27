from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class HandoffSummary:
    conversation_id: str
    user_id: str
    reason: str
    product_model: Optional[str] = None
    order_no: Optional[str] = None
    facts: List[str] = field(default_factory=list)
    steps_taken: List[str] = field(default_factory=list)
    remaining: Optional[str] = None


def build_handoff_summary(
    conversation_id: str,
    user_id: str,
    reason: str,
    context_messages: list,
) -> HandoffSummary:
    facts = []
    steps_taken = []
    product_model = None
    order_no = None

    for msg in context_messages:
        meta = msg.get("metadata") or {}

        if meta.get("product_model") and not product_model:
            product_model = meta["product_model"]

        if meta.get("workflow") == "diagnosis":
            symptom = meta.get("symptom")
            if symptom:
                facts.append(f"故障现象：{symptom}")

        if meta.get("workflow") == "after_sales":
            facts.append("已进入售后办理流程")

        if meta.get("action_type") == "ask_user":
            content = msg.get("content", "")
            if content:
                steps_taken.append(f"已询问：{content[:80]}")

        if meta.get("action_type") == "final_answer":
            content = msg.get("content", "")
            if content and meta.get("conversation_state") == "active":
                steps_taken.append(f"已回答：{content[:80]}")

    remaining = reason if not facts else None

    return HandoffSummary(
        conversation_id=conversation_id,
        user_id=user_id,
        reason=reason,
        product_model=product_model,
        order_no=order_no,
        facts=facts,
        steps_taken=steps_taken,
        remaining=remaining,
    )
