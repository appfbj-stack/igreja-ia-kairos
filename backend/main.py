from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os

from app.database import init_db, SessionLocal
from app.models.congregation import Congregation
from app.models.user import User
from app.services.auth_service import hash_password
from app.routers import (
    members, congregations, agenda, pdfs, chat, import_export,
    backup, upload, transcribe, tts, auth,
)

app = FastAPI(
    title="Kairos Igreja",
    description="Sistema inteligente de gestao pastoral com assistente por chat",
    version="1.0.0-mvp",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static uploads
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_DIR, "members"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(members.router, prefix="/api")
app.include_router(congregations.router, prefix="/api")
app.include_router(agenda.router, prefix="/api")
app.include_router(pdfs.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(import_export.router, prefix="/api")
app.include_router(backup.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(transcribe.router, prefix="/api")
app.include_router(tts.router, prefix="/api")


def _seed():
    """Cria dados iniciais: congregacoes + usuarios padrao."""
    db = SessionLocal()
    try:
        # Congregacoes
        if db.query(Congregation).count() == 0:
            sede = Congregation(
                nome="Sede",
                endereco="Endereco da Sede",
                dirigente="Pastor Presidente",
                telefone="",
            )
            db.add(sede)
            db.flush()
            sede_id = sede.id
            db.add(Congregation(nome="Congregacao Norte", endereco="", dirigente="", telefone=""))
            db.add(Congregation(nome="Congregacao Sul", endereco="", dirigente="", telefone=""))
            db.commit()
            print("OK Congregacoes iniciais criadas")
        else:
            sede = db.query(Congregation).filter(Congregation.nome == "Sede").first()
            sede_id = sede.id if sede else None

        # Usuarios padrao
        if db.query(User).count() == 0 and sede_id:
            defaults = [
                {"username": "pastor", "nome": "Pastor Presidente", "password": "pastor123", "role": "pastor", "congregacao_id": None},
                {"username": "dirigente.sede", "nome": "Dirigente da Sede", "password": "dirigente123", "role": "dirigente", "congregacao_id": sede_id},
            ]
            # Pega as outras congregacoes
            outras = db.query(Congregation).filter(Congregation.nome != "Sede").all()
            for i, c in enumerate(outras, start=1):
                defaults.append({
                    "username": f"dirigente.norte" if i == 1 else f"dirigente.sul",
                    "nome": f"Dirigente {c.nome}",
                    "password": "dirigente123",
                    "role": "dirigente",
                    "congregacao_id": c.id,
                })
            for u in defaults:
                db.add(User(
                    username=u["username"],
                    nome=u["nome"],
                    hashed_password=hash_password(u["password"]),
                    role=u["role"],
                    congregacao_id=u["congregacao_id"],
                ))
            db.commit()
            print(f"OK {len(defaults)} usuarios padrao criados")
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    init_db()
    _seed()


@app.get("/")
def root():
    return {
        "app": "Kairos Igreja",
        "version": "1.0.0-mvp",
        "docs": "/docs",
        "status": "online",
    }


@app.get("/api/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
