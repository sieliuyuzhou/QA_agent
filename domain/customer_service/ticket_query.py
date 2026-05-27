from typing import Optional

from .ticketing import ServiceTicketView


class TicketQueryService:
    def __init__(self, repository):
        self.repository = repository

    def get_ticket(self, user_id: str, ticket_id: str) -> Optional[ServiceTicketView]:
        return self.repository.get_ticket(user_id, ticket_id)
