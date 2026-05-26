import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

from llm import chat_service
from utils import ConversationManager
from tools import search_faq_tool
from domain import CustomerServiceAgent
from apps.customer_service.routes import router


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
    app.state.agent = agent
    
    yield
    
    if conversation_manager and conversation_manager.db:
        conversation_manager.db.close_all()


app = FastAPI(
    title="智能客服 API",
    description="基于 ReAct Agent 的智能客服系统",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "智能客服 API",
        "docs": "/docs",
        "endpoints": {
            "chat": "POST /api/chat",
            "create_conversation": "POST /api/conversations",
            "get_conversation": "GET /api/conversations/{id}",
            "list_conversations": "GET /api/conversations",
        }
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
