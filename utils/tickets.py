import json

from domain.customer_service.ticketing import PendingActionView, ServiceTicketView
from infrastructure.models import (
    INSERT_PENDING_ACTION,
    INSERT_SERVICE_TICKET,
    SELECT_PENDING_ACTION_FOR_UPDATE,
    SELECT_SERVICE_TICKET_BY_ID_AND_USER,
    UPDATE_PENDING_ACTION_EXECUTED,
)


def _to_pending_action(row) -> PendingActionView:
    payload = row[7] if isinstance(row[7], dict) else json.loads(row[7])
    return PendingActionView(
        action_id=row[0],
        conversation_id=row[1],
        user_id=row[2],
        action_type=row[3],
        order_id=row[4],
        ticket_type=row[5],
        eligibility_code=row[6],
        eligibility_payload=payload,
        issue_summary=row[8],
        display_summary=row[9],
        status=row[10],
        expires_at=row[11],
        executed_ticket_id=row[12],
    )


def _to_service_ticket(row) -> ServiceTicketView:
    return ServiceTicketView(
        ticket_id=row[0],
        user_id=row[1],
        order_id=row[2],
        ticket_type=row[3],
        issue_summary=row[4],
        eligibility_code=row[5],
        status=row[6],
    )


class TicketRepository:
    def __init__(self, db):
        self.db = db

    def create_action(self, action: PendingActionView) -> PendingActionView:
        self.db.execute(
            INSERT_PENDING_ACTION,
            (
                action.action_id,
                action.conversation_id,
                action.user_id,
                action.action_type,
                action.order_id,
                action.ticket_type,
                action.eligibility_code,
                json.dumps(action.eligibility_payload),
                action.issue_summary,
                action.display_summary,
                action.status,
                action.expires_at,
            ),
        )
        return action

    def confirm_with_lock(self, user_id, conversation_id, action_id, build_ticket):
        conn = self.db.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    SELECT_PENDING_ACTION_FOR_UPDATE,
                    (action_id, conversation_id, user_id),
                )
                row = cur.fetchone()
                if row is None:
                    conn.commit()
                    return None, False
                action = _to_pending_action(row)
                if action.status == "executed" and action.executed_ticket_id:
                    cur.execute(
                        SELECT_SERVICE_TICKET_BY_ID_AND_USER,
                        (action.executed_ticket_id, user_id),
                    )
                    ticket_row = cur.fetchone()
                    conn.commit()
                    return _to_service_ticket(ticket_row), True

                ticket = build_ticket(action)
                cur.execute(
                    INSERT_SERVICE_TICKET,
                    (
                        ticket.ticket_id,
                        ticket.user_id,
                        ticket.order_id,
                        ticket.ticket_type,
                        ticket.issue_summary,
                        ticket.eligibility_code,
                        ticket.status,
                    ),
                )
                cur.execute(
                    UPDATE_PENDING_ACTION_EXECUTED,
                    (ticket.ticket_id, action.action_id),
                )
                conn.commit()
                return ticket, False
        except Exception:
            conn.rollback()
            raise
        finally:
            self.db.return_connection(conn)
