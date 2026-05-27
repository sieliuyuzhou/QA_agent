from .base_agent import BaseReActAgent
from .sub_agent import SubAgentResponse

SYSTEM_PROMPT = """你是一个专业的智能家居故障排查专家。

## 可用工具
{tools}

## 允许动作
- Action: search_faq[检索关键词]：检索排障知识。
- Action: AskUser[澄清问题]：缺少型号或故障现象时询问用户。
- Action: Handoff[转人工原因]：知识库无匹配内容或无法解决时转人工。
- Action: Finish[最终答案]：已有充分排障依据时回答。

必须一次只输出一个 Action。回答必须基于检索到的知识依据，不得编造排障步骤。
"""


class TroubleshootingAgent(BaseReActAgent):
    def __init__(self, llm, tools: list, max_steps: int = 5):
        super().__init__(llm, tools, max_steps)

    def _get_system_prompt(self) -> str:
        tools_desc = self._build_tools_description()
        return SYSTEM_PROMPT.format(tools=tools_desc or "（无）")

    def _handle_terminal_action(
        self, action_name: str, action_input: str, citations: list, step: int
    ) -> SubAgentResponse:
        status_map = {
            "Finish": "completed",
            "AskUser": "awaiting_info",
            "Handoff": "handoff",
        }
        status = status_map[action_name]

        facts = {}
        for c in citations:
            if hasattr(c, "source_id"):
                facts.setdefault("knowledge_source", c.source_id)

        return SubAgentResponse(
            status=status,
            facts=facts,
            recommended_response=action_input,
            citations=citations,
            metadata={
                "agent": "TroubleshootingAgent",
                "workflow": "diagnosis",
                "steps_taken": step + 1,
            },
        )

    def run(
        self,
        user_message: str,
        context_messages: list,
        current_user=None,
        conversation_id: str = "",
        extracted_facts: dict = None,
    ) -> SubAgentResponse:
        return self.run_react_loop(
            user_input=user_message,
            context_messages=context_messages,
            current_user=current_user,
            conversation_id=conversation_id,
        )
