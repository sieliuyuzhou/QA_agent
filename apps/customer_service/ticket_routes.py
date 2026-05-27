from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException, Request

from domain.customer_service.context import CurrentUser
from .dependencies import get_current_user
from .schemas import TicketItem

router = APIRouter(tags=["tickets"])


@router.get("/tickets/{ticket_id}", response_model=TicketItem)
async def get_ticket(
    request: Request,
    ticket_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    ticket_query_service = request.app.state.ticket_query_service
    ticket = ticket_query_service.get_ticket(current_user.user_id, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")
    return TicketItem(**asdict(ticket))
