import json

from infrastructure.models import (
    INSERT_AGENT_RUN,
    INSERT_HANDOFF_RECORD,
    INSERT_RISK_EVENT,
    INSERT_TOOL_CALL,
    SELECT_AGENT_RUNS_BY_CONVERSATION,
    SELECT_HANDOFF_RECORDS_BY_CONVERSATION,
    SELECT_TOOL_CALLS_BY_RUN,
)


class AuditRepository:
    def __init__(self, db):
        self.db = db

    def insert_agent_run(self, run_id, conversation_id, intent, workflow,
                         response_type, total_steps, latency_ms, status="ok"):
        self.db.execute(
            INSERT_AGENT_RUN,
            (run_id, conversation_id, intent, workflow, response_type,
             total_steps, latency_ms, status),
        )

    def insert_tool_call(self, call_id, run_id, tool_name, input_summary,
                         output_summary, status="ok", latency_ms=None):
        self.db.execute(
            INSERT_TOOL_CALL,
            (call_id, run_id, tool_name, input_summary, output_summary,
             status, latency_ms),
        )

    def insert_risk_event(self, event_id, conversation_id, event_type,
                          severity, summary):
        self.db.execute(
            INSERT_RISK_EVENT,
            (event_id, conversation_id, event_type, severity, summary),
        )

    def insert_handoff_record(self, record_id, conversation_id, user_id,
                              reason, product_model, facts, steps_taken,
                              remaining):
        self.db.execute(
            INSERT_HANDOFF_RECORD,
            (record_id, conversation_id, user_id, reason, product_model,
             json.dumps(facts), json.dumps(steps_taken), remaining),
        )

    def get_agent_runs(self, conversation_id):
        return self.db.execute(
            SELECT_AGENT_RUNS_BY_CONVERSATION,
            (conversation_id,),
            fetch=True,
        )

    def get_tool_calls(self, run_id):
        return self.db.execute(
            SELECT_TOOL_CALLS_BY_RUN,
            (run_id,),
            fetch=True,
        )

    def get_handoff_records(self, conversation_id):
        return self.db.execute(
            SELECT_HANDOFF_RECORDS_BY_CONVERSATION,
            (conversation_id,),
            fetch=True,
        )
