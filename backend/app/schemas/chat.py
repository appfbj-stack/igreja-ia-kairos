from pydantic import BaseModel
from typing import Optional, List, Any

class ChatMessage(BaseModel):
    role: str  # user | assistant
    content: str
    attachments: Optional[List[dict]] = None  # arquivos anexados (upload info)

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    attachments: Optional[List[dict]] = None  # arquivos enviados nesta mensagem

class ChatResponse(BaseModel):
    reply: str
    actions: Optional[List[dict]] = None
    data: Optional[Any] = None
    source: Optional[str] = None  # 'llm' | 'rules'
