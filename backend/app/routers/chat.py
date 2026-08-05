from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import process_message

router = APIRouter(prefix="/chat", tags=["Chat IA"])

@router.post("/", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    history = [h.model_dump() for h in (req.history or [])]
    result = process_message(req.message, db, history=history)
    return ChatResponse(
        reply=result.get("reply", ""),
        actions=result.get("actions"),
        data=result.get("data")
    )
