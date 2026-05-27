import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

from llm import chat_service
from infrastructure.rag import get_store
from utils import ConversationManager, CustomerRepository, OrderRepository, TicketRepository
from tools import search_faq_tool
from domain import CustomerServiceAgent
from domain.customer_service import EligibilityRuleService, OrderQueryService, TicketActionService
from apps.customer_service import action_router, order_router, router


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
    
    agent = CustomerServiceAgent(
        llm=chat_service,
        conversation_manager=conversation_manager,
        tools=[search_faq_tool],
        max_steps=5,
    )
    
    app.state.conversation_manager = conversation_manager
    app.state.customer_repository = CustomerRepository(conversation_manager.db)
    app.state.order_service = OrderQueryService(
        OrderRepository(conversation_manager.db)
    )
    app.state.ticket_action_service = TicketActionService(
        TicketRepository(conversation_manager.db),
        app.state.order_service,
        EligibilityRuleService(),
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
