from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os

from app.database import init_db, SessionLocal
from app.models.congregation import Congregation
from app.models.user import User
from app.routers import members, congregations, agenda, pdfs, chat, import_export, backup, upload, transcribe, tts

app = FastAPI(
    title="Kairos Igreja",
    description="Sistema inteligente de gestão pastoral com assistente por chat",
    version="1.0.0-mvp"
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

@app.on_event("startup")
def on_startup():
    init_db()
    # Seed inicial
    db = SessionLocal()
    try:
        if db.query(Congregation).count() == 0:
            sede = Congregation(
                nome="Sede",
                endereco="Endereço da Sede",
                dirigente="Pastor Presidente",
                telefone=""
            )
            db.add(sede)
            db.add(Congregation(nome="Congregação Exemplo", endereco="", dirigente="", telefone=""))
            db.commit()
            print("✅ Congregações iniciais criadas")
    finally:
        db.close()

@app.get("/")
def root():
    return {
        "app": "Kairos Igreja",
        "version": "1.0.0-mvp",
        "docs": "/docs",
        "status": "online"
    }

@app.get("/api/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
