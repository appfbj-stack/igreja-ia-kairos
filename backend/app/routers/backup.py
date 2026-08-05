from fastapi import APIRouter
from fastapi.responses import FileResponse
import os
import shutil
from datetime import datetime

router = APIRouter(prefix="/backup", tags=["Backup"])

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "kairos.db")
BACKUP_DIR = os.path.join(BASE_DIR, "data", "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

@router.post("/criar")
def criar_backup():
    if not os.path.exists(DB_PATH):
        return {"ok": False, "message": "Banco ainda não existe"}
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = os.path.join(BACKUP_DIR, f"kairos_backup_{ts}.db")
    shutil.copy2(DB_PATH, dest)
    return {"ok": True, "arquivo": dest, "mensagem": f"Backup criado: kairos_backup_{ts}.db"}

@router.get("/download")
def download_backup():
    if not os.path.exists(DB_PATH):
        return {"ok": False, "message": "Banco não encontrado"}
    return FileResponse(DB_PATH, filename=f"kairos_{datetime.now().strftime('%Y%m%d')}.db", media_type="application/octet-stream")
