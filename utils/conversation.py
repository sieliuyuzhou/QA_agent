from typing import Optional


class ConversationManager:
    def __init__(
        self,
        db_url: Optional[str] = None,
        max_context_turns: int = 5,
    ):
        self.db_url = db_url
        self.max_context_turns = max_context_turns

    def create(self, user_id: str) -> str:
        raise NotImplementedError("将在步骤3实现")

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> int:
        raise NotImplementedError("将在步骤3实现")

    def get_context(self, conversation_id: str) -> list[dict]:
        raise NotImplementedError("将在步骤3实现")

    def get_history(self, conversation_id: str) -> list[dict]:
        raise NotImplementedError("将在步骤3实现")

    def list_conversations(self, user_id: str) -> list[dict]:
        raise NotImplementedError("将在步骤3实现")

    def close(self, conversation_id: str) -> None:
        raise NotImplementedError("将在步骤3实现")
