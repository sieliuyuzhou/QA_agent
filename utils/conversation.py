import uuid
import json
from typing import Optional, List, Dict, Any

from infrastructure.database import DatabaseManager
from infrastructure.models import (
    init_tables,
    INSERT_CONVERSATION,
    INSERT_MESSAGE,
    SELECT_CONVERSATION,
    SELECT_MESSAGES_BY_CONVERSATION,
    SELECT_RECENT_MESSAGES,
    SELECT_MAX_TURN_NUMBER,
    SELECT_CONVERSATIONS_BY_USER,
    UPDATE_CONVERSATION_TITLE,
    UPDATE_CONVERSATION_TIMESTAMP,
    CLOSE_CONVERSATION,
)


class ConversationManager:
    def __init__(
        self,
        db_url: Optional[str] = None,
        max_context_turns: int = 5,
    ):
        self.db = DatabaseManager(db_url=db_url)
        self.max_context_turns = max_context_turns
        self._init_tables()

    def _init_tables(self):
        try:
            init_tables(self.db)
        except Exception:
            pass

    def create(self, user_id: str) -> str:
        conversation_id = str(uuid.uuid4())
        self.db.execute_one(
            INSERT_CONVERSATION,
            (conversation_id, user_id, None, "active"),
        )
        return conversation_id

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> int:
        turn_number = self._calculate_turn_number(conversation_id, role)
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        result = self.db.execute_one(
            INSERT_MESSAGE,
            (conversation_id, role, content, turn_number, metadata_json),
            fetch=True,
        )
        
        self.db.execute(UPDATE_CONVERSATION_TIMESTAMP, (conversation_id,))
        
        return result[0] if result else 0

    def _calculate_turn_number(self, conversation_id: str, role: str) -> int:
        result = self.db.execute_one(
            SELECT_MAX_TURN_NUMBER,
            (conversation_id,),
            fetch=True,
        )
        
        max_turn = result[0] if result and result[0] is not None else 0
        
        if role == "user":
            return max_turn + 1
        else:
            return max_turn if max_turn > 0 else 1

    def get_context(self, conversation_id: str) -> List[Dict[str, Any]]:
        limit = self.max_context_turns * 2
        
        results = self.db.execute(
            SELECT_RECENT_MESSAGES,
            (conversation_id, limit),
            fetch=True,
        )
        
        if not results:
            return []
        
        messages = []
        for row in reversed(results):
            messages.append({
                "id": row[0],
                "conversation_id": row[1],
                "role": row[2],
                "content": row[3],
                "turn_number": row[4],
                "metadata": row[5],
                "created_at": str(row[6]),
            })
        
        return messages

    def get_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        results = self.db.execute(
            SELECT_MESSAGES_BY_CONVERSATION,
            (conversation_id,),
            fetch=True,
        )
        
        if not results:
            return []
        
        messages = []
        for row in results:
            messages.append({
                "id": row[0],
                "conversation_id": row[1],
                "role": row[2],
                "content": row[3],
                "turn_number": row[4],
                "metadata": row[5],
                "created_at": str(row[6]),
            })
        
        return messages

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        result = self.db.execute_one(
            SELECT_CONVERSATION,
            (conversation_id,),
            fetch=True,
        )
        
        if not result:
            return None
        
        return {
            "conversation_id": result[0],
            "user_id": result[1],
            "title": result[2],
            "status": result[3],
            "created_at": str(result[4]),
            "updated_at": str(result[5]),
        }

    def list_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        results = self.db.execute(
            SELECT_CONVERSATIONS_BY_USER,
            (user_id,),
            fetch=True,
        )
        
        if not results:
            return []
        
        conversations = []
        for row in results:
            conversations.append({
                "conversation_id": row[0],
                "user_id": row[1],
                "title": row[2],
                "status": row[3],
                "created_at": str(row[4]),
                "updated_at": str(row[5]),
            })
        
        return conversations

    def update_title(self, conversation_id: str, title: str) -> None:
        self.db.execute(UPDATE_CONVERSATION_TITLE, (title, conversation_id))

    def close(self, conversation_id: str) -> None:
        self.db.execute(CLOSE_CONVERSATION, (conversation_id,))
