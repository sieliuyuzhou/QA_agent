from datetime import datetime, timedelta

from domain.customer_service.ticketing import PendingActionView, ServiceTicketView
from infrastructure.models import init_tables
from utils.tickets import TicketRepository


class CaptureDB:
    def __init__(self):
        self.calls = []

    def execute(self, query, params=None, fetch=False):
        self.calls.append(query)


def test_init_tables_creates_pending_action_and_ticket_tables():
    db = CaptureDB()

    init_tables(db)

    sql = "\n".join(db.calls)
    assert "pending_actions" in sql
    assert "service_tickets" in sql
    assert "executed_ticket_id" in sql


class FakeCursor:
    def __init__(self, rows):
        self.rows = list(rows)
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query, params=None):
        self.calls.append((query, params))

    def fetchone(self):
        return self.rows.pop(0) if self.rows else None


class FakeConnection:
    def __init__(self, rows):
        self.cursor_value = FakeCursor(rows)
        self.commits = 0
        self.rollbacks = 0

    def cursor(self):
        return self.cursor_value

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1


class TransactionDB:
    def __init__(self, rows):
        self.connection = FakeConnection(rows)
        self.returned = []

    def get_connection(self):
        return self.connection

    def return_connection(self, conn):
        self.returned.append(conn)


def pending_row(status="pending", ticket_id=None):
    return (
        "act-1",
        "alice-conv",
        "customer_alice",
        "create_service_ticket",
        "ORD-A-C1",
        "warranty_repair",
        "eligible_for_warranty_repair",
        {"request_type": "warranty_repair", "issue_cause": "non_human_fault"},
        "无法开机",
        "为订单 ORD-A-C1 创建保修维修工单",
        status,
        datetime(2026, 5, 27, 12, 30),
        ticket_id,
    )


def ticket_row():
    return (
        "ticket-1",
        "customer_alice",
        "ORD-A-C1",
        "warranty_repair",
        "无法开机",
        "eligible_for_warranty_repair",
        "submitted",
    )


def build_ticket(_action):
    return ServiceTicketView(
        "ticket-1",
        "customer_alice",
        "ORD-A-C1",
        "warranty_repair",
        "无法开机",
        "eligible_for_warranty_repair",
    )


def test_confirmation_locks_action_and_updates_it_with_new_ticket():
    db = TransactionDB([pending_row()])
    repository = TicketRepository(db)

    ticket, replay = repository.confirm_with_lock(
        "customer_alice", "alice-conv", "act-1", build_ticket
    )

    sql = "\n".join(query for query, _ in db.connection.cursor_value.calls)
    assert "FOR UPDATE" in sql
    assert "INSERT INTO service_tickets" in sql
    assert "UPDATE pending_actions" in sql
    assert ticket.ticket_id == "ticket-1"
    assert replay is False
    assert db.connection.commits == 1


def test_confirming_executed_action_returns_existing_ticket_without_insert():
    db = TransactionDB([pending_row("executed", "ticket-1"), ticket_row()])
    repository = TicketRepository(db)

    ticket, replay = repository.confirm_with_lock(
        "customer_alice", "alice-conv", "act-1", build_ticket
    )

    sql = "\n".join(query for query, _ in db.connection.cursor_value.calls)
    assert "INSERT INTO service_tickets" not in sql
    assert ticket.ticket_id == "ticket-1"
    assert replay is True
