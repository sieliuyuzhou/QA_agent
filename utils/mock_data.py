from typing import Optional

from domain.customer_service.context import CurrentUser
from infrastructure.models import SELECT_ACTIVE_MOCK_CUSTOMER


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
