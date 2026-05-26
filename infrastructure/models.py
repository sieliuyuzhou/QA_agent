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

CREATE_MOCK_CUSTOMERS_TABLE = """
CREATE TABLE IF NOT EXISTS mock_customers (
    user_id       VARCHAR(128) PRIMARY KEY,
    display_name  VARCHAR(128) NOT NULL,
    status        VARCHAR(16) NOT NULL CHECK(status IN ('active', 'disabled')),
    created_at    TIMESTAMP DEFAULT NOW()
);
"""

CREATE_PRODUCTS_TABLE = """
CREATE TABLE IF NOT EXISTS products (
    product_id   VARCHAR(16) PRIMARY KEY,
    name         VARCHAR(128) NOT NULL,
    category     VARCHAR(32) NOT NULL
);
"""

CREATE_MOCK_ORDERS_TABLE = """
CREATE TABLE IF NOT EXISTS mock_orders (
    order_id      VARCHAR(32) PRIMARY KEY,
    user_id       VARCHAR(128) NOT NULL REFERENCES mock_customers(user_id),
    product_id    VARCHAR(16) NOT NULL REFERENCES products(product_id),
    purchased_at  DATE NOT NULL,
    status        VARCHAR(16) NOT NULL,
    amount        NUMERIC(10, 2) NOT NULL,
    created_at    TIMESTAMP DEFAULT NOW()
);
"""

CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_turn_number ON messages(conversation_id, turn_number);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_mock_orders_user_id ON mock_orders(user_id);
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

UPSERT_MOCK_CUSTOMER = """
INSERT INTO mock_customers (user_id, display_name, status)
VALUES (%s, %s, %s)
ON CONFLICT (user_id) DO UPDATE
SET display_name = EXCLUDED.display_name, status = EXCLUDED.status;
"""

UPSERT_PRODUCT = """
INSERT INTO products (product_id, name, category)
VALUES (%s, %s, %s)
ON CONFLICT (product_id) DO UPDATE
SET name = EXCLUDED.name, category = EXCLUDED.category;
"""

UPSERT_MOCK_ORDER = """
INSERT INTO mock_orders (order_id, user_id, product_id, purchased_at, status, amount)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (order_id) DO UPDATE
SET user_id = EXCLUDED.user_id,
    product_id = EXCLUDED.product_id,
    purchased_at = EXCLUDED.purchased_at,
    status = EXCLUDED.status,
    amount = EXCLUDED.amount;
"""


def init_tables(db_manager):
    db_manager.execute(CREATE_CONVERSATIONS_TABLE)
    db_manager.execute(CREATE_MESSAGES_TABLE)
    db_manager.execute(CREATE_MOCK_CUSTOMERS_TABLE)
    db_manager.execute(CREATE_PRODUCTS_TABLE)
    db_manager.execute(CREATE_MOCK_ORDERS_TABLE)
    db_manager.execute(CREATE_INDEXES)
