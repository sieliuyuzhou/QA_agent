from typing import Optional

from .context import OrderView


class OrderQueryService:
    def __init__(self, repository):
        self.repository = repository

    def list_orders(
        self, user_id: str, status: Optional[str] = None
    ) -> list[OrderView]:
        return self.repository.list_for_user(user_id, status=status)

    def get_order(self, user_id: str, order_id: str) -> Optional[OrderView]:
        return self.repository.get_for_user(user_id, order_id)
