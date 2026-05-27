import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

from llm import chat_service
from infrastructure.rag import get_store
from utils import AuditRepository, ConversationManager, CustomerRepository, OrderRepository, TicketRepository
from utils.evaluation_repo import EvaluationRepository
from tools import retrieve_faq, retrieve_policy, search_faq_tool
from domain import CustomerServiceAgent
from domain.customer_service import (
    AfterSalesWorkflow,
    DiagnosisWorkflow,
    EligibilityRuleService,
    OrderQueryService,
    TicketActionService,
)
from domain.customer_service.after_sales_agent import AfterSalesAgent
from domain.customer_service.consultation_handler import ConsultationHandler
from domain.customer_service.supervisor import Supervisor
from domain.customer_service.troubleshooting_agent import TroubleshootingAgent
from domain.customer_service.ticket_query import TicketQueryService
from apps.customer_service import action_router, admin_router, order_router, router, ticket_router


conversation_manager: ConversationManager = None
agent: CustomerServiceAgent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global conversation_manager, agent
    
    db_url = os.getenv("CONVERSATION_DB_URL", "")
    max_context_turns = int(os.getenv("CONVERSATION_MAX_CONTEXT_TURNS", "5"))
    
    conversation_manager = ConversationManager(
        db_url=db_url,
        max_context_turns=max_context_turns,
    )
    
    order_service = OrderQueryService(
        OrderRepository(conversation_manager.db)
    )
    ticket_action_service = TicketActionService(
        TicketRepository(conversation_manager.db),
        order_service,
        EligibilityRuleService(),
    )
    after_sales_workflow = AfterSalesWorkflow(
        ticket_action_service, retrieve_policy
    )
    diagnosis_workflow = DiagnosisWorkflow(retrieve_faq)

    troubleshooting_agent = TroubleshootingAgent(
        llm=chat_service,
        tools=[search_faq_tool],
        max_steps=5,
    )
    after_sales_agent = AfterSalesAgent(
        order_service=order_service,
        policy_lookup=retrieve_policy,
        ticket_action_service=ticket_action_service,
    )
    consultation_handler = ConsultationHandler(
        knowledge_search=retrieve_faq,
        policy_search=retrieve_policy,
    )
    agent = Supervisor(
        llm=chat_service,
        manager=conversation_manager,
        troubleshooting_agent=troubleshooting_agent,
        after_sales_agent=after_sales_agent,
        consultation_handler=consultation_handler,
        max_steps=3,
    )
    
    app.state.conversation_manager = conversation_manager
    app.state.customer_repository = CustomerRepository(conversation_manager.db)
    app.state.order_service = order_service
    app.state.ticket_action_service = ticket_action_service
    app.state.ticket_query_service = TicketQueryService(
        TicketRepository(conversation_manager.db)
    )
    app.state.evaluation_repository = EvaluationRepository(
        conversation_manager.db
    )
    app.state.agent = agent
    
    yield
    
    if conversation_manager and conversation_manager.db:
        conversation_manager.db.close_all()


app = FastAPI(
    title="QA-agent API",
    description="QA-agent 智能客服系统",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")
app.include_router(order_router, prefix="/api")
app.include_router(action_router, prefix="/api")
app.include_router(ticket_router, prefix="/api")
app.include_router(admin_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "QA-agent API",
        "docs": "/docs",
        "endpoints": {
            "chat": "POST /api/chat",
            "create_conversation": "POST /api/conversations",
            "get_conversation": "GET /api/conversations/{id}",
            "list_conversations": "GET /api/conversations",
            "orders": "GET /api/orders",
            "tickets": "GET /api/tickets/{ticket_id}",
        }
    }


@app.get("/health")
async def health(request: Request):
    checks = {}
    manager = request.app.state.conversation_manager
    try:
        checks["database"] = "ok" if manager.db.ping() else "error"
        get_store().count()
        checks["knowledge_store"] = "ok"
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "degraded",
                "checks": checks,
                "error": type(exc).__name__,
            },
        )
    return {"status": "ok", "checks": checks}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
