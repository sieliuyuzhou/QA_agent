from fastapi import APIRouter, Depends, HTTPException, Request

from domain.customer_service.context import CurrentUser
from domain.customer_service.ticketing import (
    TicketActionConflict,
    TicketActionInput,
    TicketEligibilityConflict,
    TicketNotFound,
)

from .dependencies import get_current_user
from .routes import _require_owned_conversation
from .schemas import (
    ConfirmTicketResponse,
    CreatePendingActionResponse,
    CreateTicketActionRequest,
    PendingActionItem,
    ServiceTicketItem,
)


router = APIRouter(tags=["actions"])


@router.post(
    "/conversations/{conversation_id}/actions",
    response_model=CreatePendingActionResponse,
)
async def create_ticket_action(
    request: Request,
    conversation_id: str,
    body: CreateTicketActionRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_owned_conversation(
        request.app.state.conversation_manager, conversation_id, current_user
    )

    try:
        action = request.app.state.ticket_action_service.create_action(
            current_user.user_id,
            conversation_id,
            TicketActionInput(
                order_id=body.order_id,
                request_type=body.request_type,
                issue_cause=body.issue_cause,
                packaging_intact=body.packaging_intact,
                issue_summary=body.issue_summary,
            ),
        )
    except TicketNotFound:
        raise HTTPException(status_code=404, detail="订单不存在")
    except TicketEligibilityConflict as exc:
        raise HTTPException(status_code=409, detail={"code": exc.code})

    return CreatePendingActionResponse(
        content="请确认是否提交模拟售后工单。",
        conversation_id=conversation_id,
        pending_action=PendingActionItem(
            action_id=action.action_id,
            action_type=action.action_type,
            display_summary=action.display_summary,
            expires_at=action.expires_at.isoformat(),
        ),
    )


@router.post(
    "/conversations/{conversation_id}/actions/{action_id}/confirm",
    response_model=ConfirmTicketResponse,
)
async def confirm_ticket_action(
    request: Request,
    conversation_id: str,
    action_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    _require_owned_conversation(
        request.app.state.conversation_manager, conversation_id, current_user
    )

    try:
        result = request.app.state.ticket_action_service.confirm_action(
            current_user.user_id, conversation_id, action_id
        )
    except TicketNotFound:
        raise HTTPException(status_code=404, detail="待确认动作不存在")
    except (TicketActionConflict, TicketEligibilityConflict) as exc:
        raise HTTPException(status_code=409, detail={"code": exc.code})

    ticket = result.ticket
    return ConfirmTicketResponse(
        content="模拟售后工单已提交。",
        conversation_id=conversation_id,
        ticket=ServiceTicketItem(
            ticket_id=ticket.ticket_id,
            order_id=ticket.order_id,
            ticket_type=ticket.ticket_type,
            status=ticket.status,
        ),
        idempotent_replay=result.idempotent_replay,
    )
