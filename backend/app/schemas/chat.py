from pydantic import BaseModel
from typing import Optional, List, Any

class ChatMessage(BaseModel):
    role: str  # user | assistant
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    reply: str
    actions: Optional[List[dict]] = None
    data: Optional[Any] = None
