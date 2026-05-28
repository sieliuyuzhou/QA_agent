from infrastructure.models import (
    INSERT_EVALUATION_RUN,
    SELECT_EVALUATION_RUNS,
)


class EvaluationRepository:
    def __init__(self, db):
        self.db = db

    def insert_run(self, eval_run_id, case_id, actual_type, passed,
                   failure_reason=None, model_version=None, latency_ms=None):
        self.db.execute(
            INSERT_EVALUATION_RUN,
            (eval_run_id, case_id, actual_type, passed, failure_reason,
             model_version, latency_ms),
        )

    def get_runs(self, case_id=None):
        return self.db.execute(
            SELECT_EVALUATION_RUNS,
            (case_id, case_id),
            fetch=True,
        )
