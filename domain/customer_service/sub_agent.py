from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .context import CurrentUser


@dataclass(frozen=True)
class SubAgentInput:
    conversation_id: str
    current_user: CurrentUser
    user_message: str
    context_messages: List[str] = field(default_factory=list)
    extracted_facts: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubAgentResponse:
    status: str  # "completed" | "awaiting_info" | "handoff"
    facts: Dict[str, Any] = field(default_factory=dict)
    decision: Optional[Dict[str, Any]] = None
    recommended_response: str = ""
    pending_action: Any = None
    citations: list = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
