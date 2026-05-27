from fastapi import FastAPI
from fastapi.testclient import TestClient

from domain.customer_service.context import CurrentUser
from domain.customer_service.ticketing import ServiceTicketView
from domain.customer_service.ticket_query import TicketQueryService
from apps.customer_service.dependencies import get_current_user
from apps.customer_service.ticket_routes import router


class FakeTicketRepo:
    def __init__(self, tickets=None):
        self.tickets = tickets or {}

    def get_ticket(self, user_id, ticket_id):
        key = (user_id, ticket_id)
        return self.tickets.get(key)


ALICE_TICKET = ServiceTicketView(
    ticket_id="TKT-001",
    user_id="customer_alice",
    order_id="ORD-A-X1",
    ticket_type="warranty_repair",
    issue_summary="门锁无法开机",
    eligibility_code="eligible_for_warranty_repair",
    status="submitted",
)


def _app(current_user, repo_tickets=None):
    app = FastAPI()
    app.include_router(router)

    repo = FakeTicketRepo(repo_tickets or {})
    app.state.ticket_query_service = TicketQueryService(repo)

    app.dependency_overrides[get_current_user] = lambda: current_user
    return app


def test_get_own_ticket_returns_ticket():
    app = _app(
        CurrentUser("customer_alice", "Alice"),
        {("customer_alice", "TKT-001"): ALICE_TICKET},
    )
    client = TestClient(app)

    response = client.get("/tickets/TKT-001")

    assert response.status_code == 200
    data = response.json()
    assert data["ticket_id"] == "TKT-001"
    assert data["user_id"] == "customer_alice"
    assert data["order_id"] == "ORD-A-X1"
    assert data["ticket_type"] == "warranty_repair"
    assert data["status"] == "submitted"


def test_get_other_user_ticket_returns_404():
    app = _app(
        CurrentUser("customer_bob", "Bob"),
        {("customer_alice", "TKT-001"): ALICE_TICKET},
    )
    client = TestClient(app)

    response = client.get("/tickets/TKT-001")

    assert response.status_code == 404


def test_get_nonexistent_ticket_returns_404():
    app = _app(CurrentUser("customer_alice", "Alice"))
    client = TestClient(app)

    response = client.get("/tickets/TKT-999")

    assert response.status_code == 404
