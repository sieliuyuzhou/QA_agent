import json

from infrastructure.models import (
    CREATE_AGENT_RUNS_TABLE,
    CREATE_HANDOFF_RECORDS_TABLE,
    CREATE_RISK_EVENTS_TABLE,
    CREATE_TOOL_CALLS_TABLE,
    INSERT_AGENT_RUN,
    INSERT_HANDOFF_RECORD,
    INSERT_RISK_EVENT,
    INSERT_TOOL_CALL,
    SELECT_AGENT_RUNS_BY_CONVERSATION,
    SELECT_HANDOFF_RECORDS_BY_CONVERSATION,
    SELECT_TOOL_CALLS_BY_RUN,
)
from utils.audit import AuditRepository


class FakeDB:
    def __init__(self):
        self.calls = []

    def execute(self, query, params=None, fetch=False):
        self.calls.append({"query": query, "params": params, "fetch": fetch})
        return [] if fetch else None


def test_schema_constants_are_valid_sql():
    for sql in [
        CREATE_AGENT_RUNS_TABLE,
        CREATE_TOOL_CALLS_TABLE,
        CREATE_RISK_EVENTS_TABLE,
        CREATE_HANDOFF_RECORDS_TABLE,
    ]:
        assert "CREATE TABLE" in sql
        assert "IF NOT EXISTS" in sql


def test_insert_agent_run_calls_db():
    db = FakeDB()
    repo = AuditRepository(db)

    repo.insert_agent_run(
        "run-1", "conv-1", "consultation", "knowledge_answer",
        "final_answer", 2, 1500, "ok",
    )

    assert len(db.calls) == 1
    assert db.calls[0]["query"] == INSERT_AGENT_RUN
    assert db.calls[0]["params"][0] == "run-1"
    assert db.calls[0]["params"][1] == "conv-1"


def test_insert_tool_call_calls_db():
    db = FakeDB()
    repo = AuditRepository(db)

    repo.insert_tool_call(
        "call-1", "run-1", "search_faq", "X1 WiFi", "FAQ results", "ok", 200,
    )

    assert len(db.calls) == 1
    assert db.calls[0]["query"] == INSERT_TOOL_CALL
    assert db.calls[0]["params"][2] == "search_faq"


def test_insert_risk_event_calls_db():
    db = FakeDB()
    repo = AuditRepository(db)

    repo.insert_risk_event(
        "evt-1", "conv-1", "unauthorized_access", "high", "越权查询订单",
    )

    assert len(db.calls) == 1
    assert db.calls[0]["query"] == INSERT_RISK_EVENT
    assert db.calls[0]["params"][3] == "high"


def test_insert_handoff_record_serializes_lists_as_json():
    db = FakeDB()
    repo = AuditRepository(db)

    repo.insert_handoff_record(
        "rec-1", "conv-1", "user-1", "用户要求人工", "X1",
        ["故障现象：离线"], ["已询问：型号"], "排障无效",
    )

    assert len(db.calls) == 1
    params = db.calls[0]["params"]
    assert params[0] == "rec-1"
    assert json.loads(params[5]) == ["故障现象：离线"]
    assert json.loads(params[6]) == ["已询问：型号"]


def test_get_agent_runs_queries_by_conversation():
    db = FakeDB()
    repo = AuditRepository(db)

    repo.get_agent_runs("conv-1")

    assert len(db.calls) == 1
    assert db.calls[0]["query"] == SELECT_AGENT_RUNS_BY_CONVERSATION
    assert db.calls[0]["fetch"] is True
    assert db.calls[0]["params"] == ("conv-1",)


def test_get_tool_calls_queries_by_run():
    db = FakeDB()
    repo = AuditRepository(db)

    repo.get_tool_calls("run-1")

    assert len(db.calls) == 1
    assert db.calls[0]["query"] == SELECT_TOOL_CALLS_BY_RUN
    assert db.calls[0]["params"] == ("run-1",)


def test_get_handoff_records_queries_by_conversation():
    db = FakeDB()
    repo = AuditRepository(db)

    repo.get_handoff_records("conv-1")

    assert len(db.calls) == 1
    assert db.calls[0]["query"] == SELECT_HANDOFF_RECORDS_BY_CONVERSATION
    assert db.calls[0]["params"] == ("conv-1",)
