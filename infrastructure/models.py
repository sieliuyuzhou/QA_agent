CREATE_CONVERSATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS conversations (
    id               SERIAL PRIMARY KEY,
    conversation_id  VARCHAR(36) UNIQUE NOT NULL,
    user_id          VARCHAR(128),
    title            TEXT,
    status           VARCHAR(16) DEFAULT 'active',
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
);
"""

CREATE_MESSAGES_TABLE = """
CREATE TABLE IF NOT EXISTS messages (
    id               SERIAL PRIMARY KEY,
    conversation_id  VARCHAR(36) NOT NULL,
    role             VARCHAR(16) CHECK(role IN ('user', 'assistant', 'system')),
    content          TEXT,
    turn_number      INTEGER,
    metadata         JSONB,
    created_at       TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id) ON DELETE CASCADE
);
"""

CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_turn_number ON messages(conversation_id, turn_number);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
"""

INSERT_CONVERSATION = """
INSERT INTO conversations (conversation_id, user_id, title, status)
VALUES (%s, %s, %s, %s)
RETURNING conversation_id;
"""

INSERT_MESSAGE = """
INSERT INTO messages (conversation_id, role, content, turn_number, metadata)
VALUES (%s, %s, %s, %s, %s)
RETURNING id;
"""

SELECT_CONVERSATION = """
SELECT conversation_id, user_id, title, status, created_at, updated_at
FROM conversations
WHERE conversation_id = %s;
"""

SELECT_MESSAGES_BY_CONVERSATION = """
SELECT id, conversation_id, role, content, turn_number, metadata, created_at
FROM messages
WHERE conversation_id = %s
ORDER BY turn_number ASC, created_at ASC;
"""

SELECT_RECENT_MESSAGES = """
SELECT id, conversation_id, role, content, turn_number, metadata, created_at
FROM messages
WHERE conversation_id = %s
ORDER BY turn_number DESC
LIMIT %s;
"""

SELECT_MAX_TURN_NUMBER = """
SELECT MAX(turn_number) FROM messages WHERE conversation_id = %s;
"""

SELECT_CONVERSATIONS_BY_USER = """
SELECT conversation_id, user_id, title, status, created_at, updated_at
FROM conversations
WHERE user_id = %s AND status = 'active'
ORDER BY updated_at DESC;
"""

UPDATE_CONVERSATION_TITLE = """
UPDATE conversations SET title = %s, updated_at = NOW()
WHERE conversation_id = %s;
"""

UPDATE_CONVERSATION_TIMESTAMP = """
UPDATE conversations SET updated_at = NOW()
WHERE conversation_id = %s;
"""

CLOSE_CONVERSATION = """
UPDATE conversations SET status = 'closed', updated_at = NOW()
WHERE conversation_id = %s;
"""

DELETE_CONVERSATION = """
DELETE FROM conversations WHERE conversation_id = %s;
"""


def init_tables(db_manager):
    db_manager.execute(CREATE_CONVERSATIONS_TABLE)
    db_manager.execute(CREATE_MESSAGES_TABLE)
    db_manager.execute(CREATE_INDEXES)
