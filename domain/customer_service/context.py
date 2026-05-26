from dataclasses import dataclass


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    display_name: str


@dataclass(frozen=True)
class OrderView:
    order_id: str
    product_id: str
    product_name: str
    category: str
    purchased_at: str
    status: str
    amount: str
