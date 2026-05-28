from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Request

from domain.customer_service.context import CurrentUser
from .dependencies import get_current_user
from .admin_dependencies import require_admin
from .schemas import TicketItem

router = APIRouter(tags=["tickets"])


@router.get("/tickets/{ticket_id}", response_model=TicketItem)
async def get_ticket(
    request: Request,
    ticket_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    ticket_query_service = request.app.state.ticket_query_service
    # 管理员可查看任意工单
    if current_user.role == "admin":
        ticket = ticket_query_service.get_ticket(ticket_id)
    else:
        ticket = ticket_query_service.get_ticket(ticket_id, current_user.user_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")
    return TicketItem(**asdict(ticket))
