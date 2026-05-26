from typing import Optional

from domain.customer_service.context import CurrentUser, OrderView
from infrastructure.models import (
    SELECT_ACTIVE_MOCK_CUSTOMER,
    SELECT_ORDER_BY_ID_AND_USER,
    SELECT_ORDERS_BY_USER,
)


class CustomerRepository:
    def __init__(self, db):
        self.db = db

    def find_active(self, user_id: str) -> Optional[CurrentUser]:
        row = self.db.execute_one(
            SELECT_ACTIVE_MOCK_CUSTOMER,
            (user_id,),
            fetch=True,
        )
        if not row:
            return None
        return CurrentUser(user_id=row[0], display_name=row[1])


def _to_order_view(row) -> OrderView:
    return OrderView(
        order_id=row[0],
        product_id=row[1],
        product_name=row[2],
        category=row[3],
        purchased_at=str(row[4]),
        status=row[5],
        amount=str(row[6]),
    )


class OrderRepository:
    def __init__(self, db):
        self.db = db

    def list_for_user(self, user_id: str, status: Optional[str] = None) -> list[OrderView]:
        rows = self.db.execute(
            SELECT_ORDERS_BY_USER,
            (user_id, status, status),
            fetch=True,
        )
        return [_to_order_view(row) for row in rows]

    def get_for_user(self, user_id: str, order_id: str) -> Optional[OrderView]:
        row = self.db.execute_one(
            SELECT_ORDER_BY_ID_AND_USER,
            (order_id, user_id),
            fetch=True,
        )
        return _to_order_view(row) if row else None
