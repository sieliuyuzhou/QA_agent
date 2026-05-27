import pytest

from domain.customer_service.context import CurrentUser, OrderView
from tools.mock_orders import build_mock_order_tool


class FakeOrderService:
    def __init__(self):
        self.calls = []

    def get_order(self, user_id, order_id):
        self.calls.append((user_id, order_id))
        if order_id == "ORD-A-X1":
            return OrderView(
                "ORD-A-X1",
                "X1",
                "X1 智能门锁",
                "smart_lock",
                "2026-05-22",
                "delivered",
                "1299.00",
            )
        return None


def test_mock_order_tool_uses_bound_current_user_and_returns_order_facts():
    service = FakeOrderService()
    tool = build_mock_order_tool(CurrentUser("customer_alice", "Alice Test"), service)

    result = tool.run({"order_id": "ORD-A-X1"})

    assert service.calls == [("customer_alice", "ORD-A-X1")]
    assert result["status"] == "found"
    assert result["order"]["order_id"] == "ORD-A-X1"


def test_mock_order_tool_returns_one_not_found_result_for_inaccessible_order():
    service = FakeOrderService()
    tool = build_mock_order_tool(CurrentUser("customer_alice", "Alice Test"), service)

    result = tool.run({"order_id": "ORD-B-X2"})

    assert service.calls == [("customer_alice", "ORD-B-X2")]
    assert result == {"status": "not_found", "order": None}


def test_mock_order_tool_does_not_expose_user_id_as_tool_parameter():
    tool = build_mock_order_tool(CurrentUser("customer_alice", "Alice Test"), FakeOrderService())

    assert [parameter.name for parameter in tool.parameters] == ["order_id"]


def test_mock_order_tool_rejects_attempt_to_supply_another_user_id():
    service = FakeOrderService()
    tool = build_mock_order_tool(CurrentUser("customer_alice", "Alice Test"), service)

    with pytest.raises(TypeError):
        tool.run({"order_id": "ORD-B-X2", "user_id": "customer_bob"})

    assert service.calls == []
