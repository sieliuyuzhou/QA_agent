from .sub_agent import SubAgentResponse

POLICY_SOURCE_ID = "Doc5-售后与保修政策"


class ConsultationHandler:
    def __init__(self, knowledge_search, policy_search=None):
        self.knowledge_search = knowledge_search
        self.policy_search = policy_search

    def run(
        self, user_message: str, context_messages: list = None,
        current_user=None, conversation_id: str = "",
    ) -> SubAgentResponse:
        is_policy_query = any(
            kw in user_message for kw in ("保修", "售后", "退换", "维修", "收费", "过保")
        )
        if is_policy_query and self.policy_search:
            result = self.policy_search(user_message)
        else:
            result = self.knowledge_search(user_message)
        if not result.citations:
            return SubAgentResponse(
                status="handoff",
                recommended_response="当前没有找到可靠知识依据，已为您转接人工进一步确认。",
                metadata={"agent": "ConsultationHandler", "workflow": "consultation"},
            )
        return SubAgentResponse(
            status="completed",
            recommended_response=result.content,
            citations=result.citations,
            metadata={"agent": "ConsultationHandler", "workflow": "consultation"},
        )
