"""
Upload de arquivos para o chat.
- Imagens (jpg/png): retorna base64 + metadados (LLM com vision pode ler)
- Excel/CSV: parseia e retorna JSON com as primeiras linhas + contagem
- Outros: retorna metadados basicos
"""
import os
import uuid
import base64
import shutil
import json
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/upload", tags=["Upload"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "chat")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
ALLOWED_DATA = {".xlsx", ".xls", ".csv"}
ALLOWED_TEXT = {".txt", ".md"}
ALLOWED_AUDIO = {".mp3", ".wav", ".m4a", ".ogg"}


@router.post("/")
async def upload(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename:
        raise HTTPException(400, "Arquivo sem nome")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (ALLOWED_IMAGE | ALLOWED_DATA | ALLOWED_TEXT | ALLOWED_AUDIO):
        raise HTTPException(400, f"Tipo nao suportado: {ext}")

    # Salva o arquivo
    unique = f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}{ext}"
    path = os.path.join(UPLOAD_DIR, unique)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    size = os.path.getsize(path)

    info: dict = {
        "filename": file.filename,
        "saved_as": unique,
        "url": f"/uploads/chat/{unique}",
        "size_bytes": size,
        "type": _classify(ext),
    }

    # Se for imagem, devolve em base64 (LLM com vision pode usar)
    if ext in ALLOWED_IMAGE:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        info["base64"] = b64
        info["mime"] = _guess_mime(ext)
    # Se for planilha, parseia e devolve resumo
    elif ext in ALLOWED_DATA:
        try:
            import pandas as pd
            if ext == ".csv":
                df = pd.read_csv(path)
            else:
                df = pd.read_excel(path)
            info["rows"] = len(df)
            info["columns"] = list(df.columns)
            # Devolve ate 5 linhas de exemplo para o LLM entender
            info["preview"] = json.loads(df.head(5).to_json(orient="records", force_ascii=False))
            # Heuristica: se tem coluna "nome" e algo parecido com cpf/whatsapp, sugere importacao
            cols_lower = [c.strip().lower() for c in df.columns]
            if any(c in cols_lower for c in ["nome", "nome_completo", "name"]):
                info["looks_like"] = "membros"
        except Exception as e:
            info["parse_error"] = str(e)
    # Se for texto, le conteudo
    elif ext in ALLOWED_TEXT:
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read(5000)  # primeiros 5KB
            info["content_preview"] = content
        except Exception as e:
            info["read_error"] = str(e)

    return info


def _classify(ext: str) -> str:
    if ext in ALLOWED_IMAGE:
        return "image"
    if ext in ALLOWED_DATA:
        return "spreadsheet"
    if ext in ALLOWED_TEXT:
        return "text"
    if ext in ALLOWED_AUDIO:
        return "audio"
    return "other"


def _guess_mime(ext: str) -> str:
    return {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif",
    }.get(ext, "application/octet-stream")
