from dataclasses import asdict

from domain.customer_service.context import CurrentUser

from .base import Tool, ToolParameter


def build_mock_order_tool(current_user: CurrentUser, order_service) -> Tool:
    def get_mock_order(order_id: str) -> dict:
        order = order_service.get_order(current_user.user_id, order_id)
        if order is None:
            return {"status": "not_found", "order": None}
        return {"status": "found", "order": asdict(order)}

    return Tool(
        name="get_mock_order",
        description="读取当前用户可访问的一笔模拟订单。",
        func=get_mock_order,
        parameters=[ToolParameter("order_id", "string", "模拟订单编号")],
    )
