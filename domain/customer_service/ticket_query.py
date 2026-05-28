from typing import Optional

from .ticketing import ServiceTicketView


class TicketQueryService:
    def __init__(self, repository):
        self.repository = repository

    def get_ticket(self, ticket_id: str, user_id: str = None) -> Optional[ServiceTicketView]:
        # user_id 为 None 时允许管理员查询任意工单
        return self.repository.get_ticket(user_id, ticket_id)
