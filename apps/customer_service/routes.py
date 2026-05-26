from fastapi import APIRouter, HTTPException, Request

from .schemas import (
    ChatRequest,
    ChatResponse,
    CitationItem,
    CreateConversationRequest,
    CreateConversationResponse,
    ConversationDetail,
    ConversationListResponse,
    ConversationListItem,
    MessageItem,
)

router = APIRouter(tags=["customer_service"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: Request, body: ChatRequest):
    agent = request.app.state.agent
    conversation_manager = request.app.state.conversation_manager
    
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")
    
    conversation_id = body.conversation_id
    if not conversation_id:
        conversation_id = conversation_manager.create(user_id="default_user")
    
    conv = conversation_manager.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    if conv["status"] == "closed":
        raise HTTPException(status_code=400, detail="会话已关闭")
    
    try:
        response = agent.run(body.message, conversation_id)
        return ChatResponse(
            type=response.type,
            content=response.content,
            conversation_id=response.conversation_id,
            citations=[
                CitationItem(
                    source_id=item.source_id,
                    title=item.title,
                    section=item.section,
                    excerpt=item.excerpt,
                )
                for item in response.citations
            ],
            metadata=response.metadata,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent 执行错误: {e}")


@router.post("/conversations", response_model=CreateConversationResponse)
async def create_conversation(request: Request, body: CreateConversationRequest):
    conversation_manager = request.app.state.conversation_manager
    
    try:
        conversation_id = conversation_manager.create(user_id=body.user_id)
        return CreateConversationResponse(
            conversation_id=conversation_id,
            user_id=body.user_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建会话失败: {e}")


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(request: Request, conversation_id: str):
    conversation_manager = request.app.state.conversation_manager
    
    conv = conversation_manager.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    messages = conversation_manager.get_history(conversation_id)
    
    return ConversationDetail(
        conversation_id=conv["conversation_id"],
        user_id=conv["user_id"],
        title=conv["title"],
        status=conv["status"],
        created_at=conv["created_at"],
        updated_at=conv["updated_at"],
        messages=[
            MessageItem(
                id=msg["id"],
                conversation_id=msg["conversation_id"],
                role=msg["role"],
                content=msg["content"],
                turn_number=msg["turn_number"],
                metadata=msg["metadata"],
                created_at=msg["created_at"],
            )
            for msg in messages
        ],
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def list_conversations(request: Request, user_id: str = None):
    conversation_manager = request.app.state.conversation_manager
    
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id 参数必填")
    
    conversations = conversation_manager.list_conversations(user_id)
    
    return ConversationListResponse(
        conversations=[
            ConversationListItem(
                conversation_id=conv["conversation_id"],
                user_id=conv["user_id"],
                title=conv["title"],
                status=conv["status"],
                created_at=conv["created_at"],
                updated_at=conv["updated_at"],
            )
            for conv in conversations
        ],
        total=len(conversations),
    )
