from typing import Literal, Optional, List
from pydantic import BaseModel, Field, ConfigDict


class ChatRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "conversation_id": "",
                    "message": "怎么重置WiFi？"
                },
                {
                    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                    "message": "还有其他方法吗？"
                }
            ]
        }
    )
    
    conversation_id: str = Field(default="", description="会话ID，为空时自动创建新会话")
    message: str = Field(..., description="用户消息", min_length=1)


class CitationItem(BaseModel):
    source_id: str = Field(..., description="来源标识")
    title: str = Field(..., description="来源标题")
    section: str = Field(..., description="来源章节或问题")
    excerpt: str = Field(..., description="支持回答的来源摘录")


class ChatResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "type": "final_answer",
                    "content": "根据FAQ，重置WiFi的方法是：1. 长按设备背面的重置按钮10秒...",
                    "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
                }
            ]
        }
    )
    
    type: Literal["final_answer", "ask_user", "handoff"] = Field(
        ..., description="响应类型：最终回答、澄清问题或人工转接"
    )
    content: str = Field(..., description="响应内容")
    conversation_id: str = Field(..., description="会话ID")
    citations: List[CitationItem] = Field(default_factory=list, description="知识来源引用")
    metadata: Optional[dict] = Field(default=None, description="Agent 执行元数据")


class OrderItem(BaseModel):
    order_id: str
    product_id: str
    product_name: str
    category: str
    purchased_at: str
    status: str
    amount: str


class OrderListResponse(BaseModel):
    orders: List[OrderItem] = Field(default_factory=list)
    total: int


class CreateConversationRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "user_id": "user_12345"
                },
                {
                    "user_id": "test_user"
                }
            ]
        }
    )
    
    user_id: str = Field(..., description="用户标识", min_length=1)


class CreateConversationResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                    "user_id": "user_12345"
                }
            ]
        }
    )
    
    conversation_id: str = Field(..., description="会话ID")
    user_id: str = Field(..., description="用户标识")


class MessageItem(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "id": 1,
                    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                    "role": "user",
                    "content": "怎么重置WiFi？",
                    "turn_number": 1,
                    "metadata": None,
                    "created_at": "2024-01-15 10:30:00"
                }
            ]
        }
    )
    
    id: int
    conversation_id: str
    role: str
    content: str
    turn_number: int
    metadata: Optional[dict] = None
    created_at: str


class ConversationDetail(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                    "user_id": "user_12345",
                    "title": "WiFi重置咨询",
                    "status": "active",
                    "created_at": "2024-01-15 10:00:00",
                    "updated_at": "2024-01-15 10:30:00",
                    "messages": [
                        {
                            "id": 1,
                            "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                            "role": "user",
                            "content": "怎么重置WiFi？",
                            "turn_number": 1,
                            "metadata": None,
                            "created_at": "2024-01-15 10:30:00"
                        }
                    ]
                }
            ]
        }
    )
    
    conversation_id: str
    user_id: Optional[str]
    title: Optional[str]
    status: str
    created_at: str
    updated_at: str
    messages: List[MessageItem] = []


class ConversationListItem(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                    "user_id": "user_12345",
                    "title": "WiFi重置咨询",
                    "status": "active",
                    "created_at": "2024-01-15 10:00:00",
                    "updated_at": "2024-01-15 10:30:00"
                }
            ]
        }
    )
    
    conversation_id: str
    user_id: Optional[str]
    title: Optional[str]
    status: str
    created_at: str
    updated_at: str


class ConversationListResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "conversations": [
                        {
                            "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
                            "user_id": "user_12345",
                            "title": "WiFi重置咨询",
                            "status": "active",
                            "created_at": "2024-01-15 10:00:00",
                            "updated_at": "2024-01-15 10:30:00"
                        }
                    ],
                    "total": 1
                }
            ]
        }
    )
    
    conversations: List[ConversationListItem]
    total: int
