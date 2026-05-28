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

        # 用引用构建简洁回答：带上来源标题和章节名，让用户知道信息出处
        top = result.citations[0]
        count = len(result.citations)
        answer = f"根据{top.title}中「{top.section}」的相关内容：\n{top.excerpt}"
        if count > 1:
            answer += f"\n\n（共 {count} 条相关结果，可查看引用来源查看更多信息）"

        return SubAgentResponse(
            status="completed",
            recommended_response=answer,
            citations=result.citations,
            metadata={"agent": "ConsultationHandler", "workflow": "consultation"},
        )
