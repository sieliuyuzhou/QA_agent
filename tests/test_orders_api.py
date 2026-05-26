import importlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from domain.customer_service.context import CurrentUser


class FakeCustomerRepository:
    def find_active(self, user_id):
        if user_id == "customer_alice":
            return CurrentUser("customer_alice", "Alice Test")
        return None


def _load_order_components():
    try:
        route_module = importlib.import_module("apps.customer_service.order_routes")
        context_module = importlib.import_module("domain.customer_service.context")
        order_view = context_module.OrderView
    except (ModuleNotFoundError, AttributeError):
        pytest.fail("authorized read-only order API must be implemented")
    return route_module.router, order_view


class FakeOrderService:
    def __init__(self, order_view):
        self.order_view = order_view

    def list_orders(self, user_id, status=None):
        assert user_id == "customer_alice"
        return [
            self.order_view(
                "ORD-A-X1",
                "X1",
                "X1 智能门锁",
                "smart_lock",
                "2026-05-22",
                "delivered",
                "1299.00",
            )
        ]

    def get_order(self, user_id, order_id):
        assert user_id == "customer_alice"
        if order_id == "ORD-A-X1":
            return self.list_orders(user_id)[0]
        return None


def build_client():
    router, order_view = _load_order_components()
    app = FastAPI()
    app.state.customer_repository = FakeCustomerRepository()
    app.state.order_service = FakeOrderService(order_view)
    app.include_router(router, prefix="/api")
    return TestClient(app)


def test_order_list_requires_internal_identity():
    with build_client() as client:
        response = client.get("/api/orders")

    assert response.status_code == 401


def test_current_user_can_list_owned_orders():
    with build_client() as client:
        response = client.get(
            "/api/orders",
            headers={"X-QA-User-Id": "customer_alice"},
        )

    assert response.status_code == 200
    assert response.json()["orders"][0]["order_id"] == "ORD-A-X1"


def test_unowned_order_is_not_disclosed():
    with build_client() as client:
        response = client.get(
            "/api/orders/ORD-B-X2",
            headers={"X-QA-User-Id": "customer_alice"},
        )

    assert response.status_code == 404
