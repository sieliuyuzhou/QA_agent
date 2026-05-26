from dataclasses import asdict
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from domain.customer_service.context import CurrentUser
from .dependencies import get_current_user
from .schemas import OrderItem, OrderListResponse

router = APIRouter(tags=["orders"])


def _to_item(order) -> OrderItem:
    return OrderItem(**asdict(order))


@router.get("/orders", response_model=OrderListResponse)
async def list_orders(
    request: Request,
    status: Optional[str] = None,
    current_user: CurrentUser = Depends(get_current_user),
):
    orders = request.app.state.order_service.list_orders(current_user.user_id, status)
    return OrderListResponse(
        orders=[_to_item(item) for item in orders],
        total=len(orders),
    )


@router.get("/orders/{order_id}", response_model=OrderItem)
async def get_order(
    request: Request,
    order_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    order = request.app.state.order_service.get_order(current_user.user_id, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")
    return _to_item(order)
