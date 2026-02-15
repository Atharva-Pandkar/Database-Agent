from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from .decomposer import TaskGraph

class ChatMessageBase(BaseModel):
    message: str = Field(..., description="The content of the chat message")
    
class ChatMessageRequest(ChatMessageBase):
    pass

class ChatMessageResponse(ChatMessageBase):
    id: str = Field(..., description="Unique identifier for the message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Time when the message was processed")
    response: str = Field(..., description="Response from the backend")
    task_graph: Optional[TaskGraph] = Field(None, description="Task graph generated from the message")

class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageResponse] = Field(default_factory=list, description="List of chat messages")