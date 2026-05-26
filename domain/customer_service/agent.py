from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentResponse:
    type: str
    content: str
    conversation_id: str
    metadata: Optional[dict] = None


class CustomerServiceAgent:
    def __init__(
        self,
        llm,
        conversation_manager,
        tools: list,
        system_prompt: Optional[str] = None,
        max_steps: int = 5,
    ):
        self.llm = llm
        self.conversation_manager = conversation_manager
        self.tools = tools
        self.system_prompt = system_prompt
        self.max_steps = max_steps

    def run(self, user_input: str, conversation_id: str) -> AgentResponse:
        raise NotImplementedError("将在步骤5实现")
