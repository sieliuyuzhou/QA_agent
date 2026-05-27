from fastapi import APIRouter, Depends, HTTPException, Request

from domain.customer_service.context import CurrentUser
from .admin_dependencies import require_admin
from .schemas import ConversationDetail, MessageItem

router = APIRouter(tags=["admin"])


@router.get("/admin/conversations")
async def list_all_conversations(
    request: Request,
    admin: CurrentUser = Depends(require_admin),
):
    manager = request.app.state.conversation_manager
    conversations = manager.list_all_conversations()
    return {"conversations": conversations, "total": len(conversations)}


@router.get("/admin/conversations/{conversation_id}")
async def get_conversation_detail(
    request: Request,
    conversation_id: str,
    admin: CurrentUser = Depends(require_admin),
):
    manager = request.app.state.conversation_manager
    conv = manager.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = manager.get_history(conversation_id)
    return {
        "conversation": conv,
        "messages": [
            {
                "id": msg["id"],
                "role": msg["role"],
                "content": msg["content"],
                "metadata": msg["metadata"],
                "turn_number": msg["turn_number"],
                "created_at": str(msg["created_at"]),
            }
            for msg in messages
        ],
    }


@router.get("/admin/tickets")
async def list_all_tickets(
    request: Request,
    admin: CurrentUser = Depends(require_admin),
):
    repo = request.app.state.ticket_action_service.repository
    rows = repo.db.execute(
        "SELECT ticket_id, user_id, order_id, ticket_type, issue_summary, "
        "eligibility_code, status, created_at FROM service_tickets "
        "ORDER BY created_at DESC;",
        fetch=True,
    )
    tickets = [
        {
            "ticket_id": r[0], "user_id": r[1], "order_id": r[2],
            "ticket_type": r[3], "issue_summary": r[4],
            "eligibility_code": r[5], "status": r[6],
            "created_at": str(r[7]),
        }
        for r in (rows or [])
    ]
    return {"tickets": tickets, "total": len(tickets)}


@router.get("/admin/evaluations")
async def list_evaluation_runs(
    request: Request,
    case_id: str = None,
    admin: CurrentUser = Depends(require_admin),
):
    eval_repo = request.app.state.evaluation_repository
    rows = eval_repo.get_runs(case_id)
    runs = [
        {
            "eval_run_id": r[0], "case_id": r[1], "actual_type": r[2],
            "passed": r[3], "failure_reason": r[4],
            "model_version": r[5], "latency_ms": r[6],
            "created_at": str(r[7]),
        }
        for r in (rows or [])
    ]
    total = len(runs)
    passed_count = sum(1 for r in runs if r["passed"])
    return {
        "runs": runs,
        "total": total,
        "passed": passed_count,
        "failed": total - passed_count,
    }
