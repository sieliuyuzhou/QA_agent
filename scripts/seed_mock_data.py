import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.database import DatabaseManager
from infrastructure.models import (
    UPSERT_MOCK_CUSTOMER,
    UPSERT_MOCK_ORDER,
    UPSERT_PRODUCT,
)


CUSTOMERS = [
    ("customer_alice", "Alice Test", "active"),
    ("customer_bob", "Bob Test", "active"),
    ("customer_disabled", "Disabled Test", "disabled"),
]

PRODUCTS = [
    ("X1", "X1 智能门锁", "smart_lock"),
    ("X2", "X2 智能门锁", "smart_lock"),
    ("C1", "C1 智能摄像头", "camera"),
    ("G2", "G2 智能网关", "gateway"),
]

ORDERS = [
    ("ORD-A-X1", "customer_alice", "X1", "2026-05-22", "delivered", "1299.00"),
    ("ORD-A-C1", "customer_alice", "C1", "2026-03-01", "completed", "399.00"),
    ("ORD-B-X2", "customer_bob", "X2", "2026-05-20", "delivered", "1599.00"),
    ("ORD-B-G2", "customer_bob", "G2", "2025-10-10", "completed", "299.00"),
]


def seed_mock_data(db) -> None:
    for row in CUSTOMERS:
        db.execute(UPSERT_MOCK_CUSTOMER, row)
    for row in PRODUCTS:
        db.execute(UPSERT_PRODUCT, row)
    for row in ORDERS:
        db.execute(UPSERT_MOCK_ORDER, row)


def main() -> int:
    load_dotenv()
    db = DatabaseManager(os.getenv("CONVERSATION_DB_URL", ""))
    try:
        seed_mock_data(db)
        print("[SUCCESS] QA-agent mock customer and order data seeded.")
        return 0
    finally:
        db.close_all()


if __name__ == "__main__":
    raise SystemExit(main())
