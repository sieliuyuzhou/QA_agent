import importlib

import pytest

from infrastructure.models import init_tables


class CaptureDB:
    def __init__(self):
        self.calls = []

    def execute(self, query, params=None, fetch=False):
        self.calls.append((query, params))
        return []


def _load_seed_module():
    try:
        return importlib.import_module("scripts.seed_mock_data")
    except ModuleNotFoundError:
        pytest.fail("scripts.seed_mock_data must provide deterministic mock data")


def test_init_tables_creates_mock_business_tables():
    db = CaptureDB()

    init_tables(db)

    sql = "\n".join(query for query, _ in db.calls)
    assert "mock_customers" in sql
    assert "products" in sql
    assert "mock_orders" in sql


def test_seed_data_has_two_customers_and_all_supported_products():
    seed_module = _load_seed_module()

    assert {row[0] for row in seed_module.CUSTOMERS} >= {
        "customer_alice",
        "customer_bob",
    }
    assert {row[0] for row in seed_module.PRODUCTS} == {"X1", "X2", "C1", "G2"}
    assert {row[1] for row in seed_module.ORDERS} >= {
        "customer_alice",
        "customer_bob",
    }


def test_seed_mock_data_uses_idempotent_inserts():
    seed_module = _load_seed_module()
    db = CaptureDB()

    seed_module.seed_mock_data(db)

    sql = "\n".join(query for query, _ in db.calls)
    assert "ON CONFLICT" in sql
    assert len(db.calls) == (
        len(seed_module.CUSTOMERS)
        + len(seed_module.PRODUCTS)
        + len(seed_module.ORDERS)
    )


class RowDB:
    def __init__(self, row):
        self.row = row
        self.calls = []

    def execute_one(self, query, params=None, fetch=False):
        self.calls.append((query, params, fetch))
        return self.row


def _load_mock_repository():
    try:
        module = importlib.import_module("utils.mock_data")
    except ModuleNotFoundError:
        pytest.fail("utils.mock_data must resolve internal test customers")
    return module.CustomerRepository


def test_customer_repository_returns_active_user_context():
    repository_type = _load_mock_repository()
    db = RowDB(("customer_alice", "Alice Test", "active"))

    user = repository_type(db).find_active("customer_alice")

    assert user.user_id == "customer_alice"
    assert user.display_name == "Alice Test"
    assert db.calls[0][1] == ("customer_alice",)


def test_customer_repository_rejects_missing_user():
    repository_type = _load_mock_repository()

    assert repository_type(RowDB(None)).find_active("unknown") is None
