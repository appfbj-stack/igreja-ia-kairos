from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import process_message
from app.services.llm_service import LLMConfig

router = APIRouter(prefix="/chat", tags=["Chat IA"])

@router.get("/status")
def chat_status():
    """Retorna se o LLM esta ativo e qual provedor. Usado pelo frontend no header."""
    cfg = LLMConfig.from_env()
    return {
        "llm_active": cfg.is_configured and cfg.provider != "rules",
        "provider": cfg.provider,
        "model": cfg.model,
    }

@router.post("/", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    history = [h.model_dump() for h in (req.history or [])]
    result = process_message(req.message, db, history=history, attachments=req.attachments)
    return ChatResponse(
        reply=result.get("reply", ""),
        actions=result.get("actions"),
        data=result.get("data"),
        source=result.get("source"),
    )
