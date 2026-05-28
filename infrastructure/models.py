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
    role          VARCHAR(16) NOT NULL DEFAULT 'customer',
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

CREATE_PENDING_ACTIONS_TABLE = """
CREATE TABLE IF NOT EXISTS pending_actions (
    action_id           VARCHAR(36) PRIMARY KEY,
    conversation_id     VARCHAR(36) NOT NULL REFERENCES conversations(conversation_id),
    user_id             VARCHAR(128) NOT NULL REFERENCES mock_customers(user_id),
    action_type         VARCHAR(32) NOT NULL CHECK(action_type IN ('create_service_ticket')),
    order_id            VARCHAR(32) NOT NULL REFERENCES mock_orders(order_id),
    ticket_type         VARCHAR(32) NOT NULL,
    eligibility_code    VARCHAR(64) NOT NULL,
    eligibility_payload JSONB NOT NULL,
    issue_summary       TEXT NOT NULL,
    display_summary     TEXT NOT NULL,
    status              VARCHAR(16) NOT NULL CHECK(status IN ('pending', 'executed', 'expired', 'cancelled')),
    expires_at          TIMESTAMP NOT NULL,
    executed_ticket_id  VARCHAR(36),
    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);
"""

CREATE_SERVICE_TICKETS_TABLE = """
CREATE TABLE IF NOT EXISTS service_tickets (
    ticket_id        VARCHAR(36) PRIMARY KEY,
    user_id          VARCHAR(128) NOT NULL REFERENCES mock_customers(user_id),
    order_id         VARCHAR(32) NOT NULL REFERENCES mock_orders(order_id),
    ticket_type      VARCHAR(32) NOT NULL,
    issue_summary    TEXT NOT NULL,
    eligibility_code VARCHAR(64) NOT NULL,
    status           VARCHAR(16) NOT NULL CHECK(status IN ('submitted')),
    created_at       TIMESTAMP DEFAULT NOW(),
    updated_at       TIMESTAMP DEFAULT NOW()
);
"""

CREATE_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_turn_number ON messages(conversation_id, turn_number);
CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_mock_orders_user_id ON mock_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_pending_actions_owner ON pending_actions(user_id, conversation_id);
CREATE INDEX IF NOT EXISTS idx_service_tickets_owner ON service_tickets(user_id, order_id);
CREATE INDEX IF NOT EXISTS idx_agent_runs_conversation ON agent_runs(conversation_id);
CREATE INDEX IF NOT EXISTS idx_tool_calls_run ON tool_calls(run_id);
CREATE INDEX IF NOT EXISTS idx_risk_events_conversation ON risk_events(conversation_id);
CREATE INDEX IF NOT EXISTS idx_handoff_records_conversation ON handoff_records(conversation_id);
"""

CREATE_AGENT_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS agent_runs (
    run_id           VARCHAR(36) PRIMARY KEY,
    conversation_id  VARCHAR(36) NOT NULL REFERENCES conversations(conversation_id),
    intent           VARCHAR(32),
    workflow         VARCHAR(32),
    response_type    VARCHAR(32),
    total_steps      INTEGER,
    latency_ms       INTEGER,
    status           VARCHAR(16) NOT NULL DEFAULT 'ok',
    created_at       TIMESTAMP DEFAULT NOW()
);
"""

CREATE_TOOL_CALLS_TABLE = """
CREATE TABLE IF NOT EXISTS tool_calls (
    call_id         VARCHAR(36) PRIMARY KEY,
    run_id          VARCHAR(36) NOT NULL REFERENCES agent_runs(run_id),
    tool_name       VARCHAR(64) NOT NULL,
    input_summary   TEXT,
    output_summary  TEXT,
    status          VARCHAR(16) NOT NULL DEFAULT 'ok',
    latency_ms      INTEGER,
    created_at      TIMESTAMP DEFAULT NOW()
);
"""

CREATE_RISK_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS risk_events (
    event_id        VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) REFERENCES conversations(conversation_id),
    event_type      VARCHAR(32) NOT NULL,
    severity        VARCHAR(16) NOT NULL DEFAULT 'medium',
    summary         TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);
"""

CREATE_HANDOFF_RECORDS_TABLE = """
CREATE TABLE IF NOT EXISTS handoff_records (
    record_id        VARCHAR(36) PRIMARY KEY,
    conversation_id  VARCHAR(36) NOT NULL REFERENCES conversations(conversation_id),
    user_id          VARCHAR(128) NOT NULL,
    reason           TEXT NOT NULL,
    product_model    VARCHAR(32),
    facts            JSONB DEFAULT '[]',
    steps_taken      JSONB DEFAULT '[]',
    remaining        TEXT,
    created_at       TIMESTAMP DEFAULT NOW()
);
"""

CREATE_EVALUATION_CASES_TABLE = """
CREATE TABLE IF NOT EXISTS evaluation_cases (
    case_id                 VARCHAR(32) PRIMARY KEY,
    category                VARCHAR(64) NOT NULL,
    input_text              TEXT NOT NULL,
    expected_response_type  VARCHAR(32) NOT NULL,
    required_source_ids     JSONB DEFAULT '[]',
    required_content_kw     JSONB DEFAULT '[]',
    description             TEXT,
    enabled                 BOOLEAN DEFAULT TRUE,
    created_at              TIMESTAMP DEFAULT NOW()
);
"""

CREATE_EVALUATION_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS evaluation_runs (
    eval_run_id     VARCHAR(36) PRIMARY KEY,
    case_id         VARCHAR(32) NOT NULL REFERENCES evaluation_cases(case_id),
    actual_type     VARCHAR(32),
    passed          BOOLEAN NOT NULL,
    failure_reason  TEXT,
    model_version   VARCHAR(64),
    latency_ms      INTEGER,
    created_at      TIMESTAMP DEFAULT NOW()
);
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

SELECT_ALL_CONVERSATIONS = """
SELECT conversation_id, user_id, title, status, created_at, updated_at
FROM conversations
ORDER BY updated_at DESC;
"""

SELECT_ACTIVE_MOCK_CUSTOMER = """
SELECT user_id, display_name, role, status
FROM mock_customers
WHERE user_id = %s AND status = 'active';
"""

SELECT_ORDERS_BY_USER = """
SELECT o.order_id, p.product_id, p.name, p.category, o.purchased_at,
       o.status, o.amount
FROM mock_orders o
JOIN products p ON p.product_id = o.product_id
WHERE o.user_id = %s AND (%s IS NULL OR o.status = %s)
ORDER BY o.purchased_at DESC, o.order_id ASC;
"""

SELECT_ORDER_BY_ID_AND_USER = """
SELECT o.order_id, p.product_id, p.name, p.category, o.purchased_at,
       o.status, o.amount
FROM mock_orders o
JOIN products p ON p.product_id = o.product_id
WHERE o.order_id = %s AND o.user_id = %s;
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
INSERT INTO mock_customers (user_id, display_name, role, status)
VALUES (%s, %s, %s, %s)
ON CONFLICT (user_id) DO UPDATE
SET display_name = EXCLUDED.display_name, role = EXCLUDED.role, status = EXCLUDED.status;
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

INSERT_PENDING_ACTION = """
INSERT INTO pending_actions (
    action_id, conversation_id, user_id, action_type, order_id, ticket_type,
    eligibility_code, eligibility_payload, issue_summary, display_summary,
    status, expires_at
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
"""

SELECT_PENDING_ACTION_FOR_UPDATE = """
SELECT action_id, conversation_id, user_id, action_type, order_id, ticket_type,
       eligibility_code, eligibility_payload, issue_summary, display_summary,
       status, expires_at, executed_ticket_id
FROM pending_actions
WHERE action_id = %s AND conversation_id = %s AND user_id = %s
FOR UPDATE;
"""

INSERT_SERVICE_TICKET = """
INSERT INTO service_tickets (
    ticket_id, user_id, order_id, ticket_type, issue_summary,
    eligibility_code, status
)
VALUES (%s, %s, %s, %s, %s, %s, %s);
"""

SELECT_SERVICE_TICKET_BY_ID_AND_USER = """
SELECT ticket_id, user_id, order_id, ticket_type, issue_summary,
       eligibility_code, status
FROM service_tickets
WHERE ticket_id = %s AND user_id = %s;
"""

SELECT_SERVICE_TICKET_BY_ID = """
SELECT ticket_id, user_id, order_id, ticket_type, issue_summary,
       eligibility_code, status
FROM service_tickets
WHERE ticket_id = %s;
"""

UPDATE_PENDING_ACTION_EXECUTED = """
UPDATE pending_actions
SET status = 'executed', executed_ticket_id = %s, updated_at = NOW()
WHERE action_id = %s AND status = 'pending';
"""

INSERT_AGENT_RUN = """
INSERT INTO agent_runs (run_id, conversation_id, intent, workflow, response_type, total_steps, latency_ms, status)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
"""

INSERT_TOOL_CALL = """
INSERT INTO tool_calls (call_id, run_id, tool_name, input_summary, output_summary, status, latency_ms)
VALUES (%s, %s, %s, %s, %s, %s, %s);
"""

INSERT_RISK_EVENT = """
INSERT INTO risk_events (event_id, conversation_id, event_type, severity, summary)
VALUES (%s, %s, %s, %s, %s);
"""

INSERT_HANDOFF_RECORD = """
INSERT INTO handoff_records (record_id, conversation_id, user_id, reason, product_model, facts, steps_taken, remaining)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
"""

SELECT_AGENT_RUNS_BY_CONVERSATION = """
SELECT run_id, conversation_id, intent, workflow, response_type, total_steps, latency_ms, status, created_at
FROM agent_runs
WHERE conversation_id = %s
ORDER BY created_at ASC;
"""

SELECT_TOOL_CALLS_BY_RUN = """
SELECT call_id, run_id, tool_name, input_summary, output_summary, status, latency_ms, created_at
FROM tool_calls
WHERE run_id = %s
ORDER BY created_at ASC;
"""

SELECT_HANDOFF_RECORDS_BY_CONVERSATION = """
SELECT record_id, conversation_id, user_id, reason, product_model, facts, steps_taken, remaining, created_at
FROM handoff_records
WHERE conversation_id = %s
ORDER BY created_at ASC;
"""

INSERT_EVALUATION_RUN = """
INSERT INTO evaluation_runs (eval_run_id, case_id, actual_type, passed, failure_reason, model_version, latency_ms)
VALUES (%s, %s, %s, %s, %s, %s, %s);
"""

SELECT_EVALUATION_RUNS = """
SELECT eval_run_id, case_id, actual_type, passed, failure_reason, model_version, latency_ms, created_at
FROM evaluation_runs
WHERE (%s IS NULL OR case_id = %s)
ORDER BY created_at DESC;
"""


def init_tables(db_manager):
    db_manager.execute(CREATE_CONVERSATIONS_TABLE)
    db_manager.execute(CREATE_MESSAGES_TABLE)
    db_manager.execute(CREATE_MOCK_CUSTOMERS_TABLE)
    db_manager.execute(CREATE_PRODUCTS_TABLE)
    db_manager.execute(CREATE_MOCK_ORDERS_TABLE)
    db_manager.execute(CREATE_PENDING_ACTIONS_TABLE)
    db_manager.execute(CREATE_SERVICE_TICKETS_TABLE)
    db_manager.execute(CREATE_AGENT_RUNS_TABLE)
    db_manager.execute(CREATE_TOOL_CALLS_TABLE)
    db_manager.execute(CREATE_RISK_EVENTS_TABLE)
    db_manager.execute(CREATE_HANDOFF_RECORDS_TABLE)
    db_manager.execute(CREATE_EVALUATION_CASES_TABLE)
    db_manager.execute(CREATE_EVALUATION_RUNS_TABLE)
    db_manager.execute(CREATE_INDEXES)
    db_manager.execute(
        "ALTER TABLE mock_customers ADD COLUMN IF NOT EXISTS "
        "role VARCHAR(16) NOT NULL DEFAULT 'customer';"
    )
