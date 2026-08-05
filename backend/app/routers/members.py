from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import os
import shutil
from app.database import get_db
from app.models.member import Member
from app.models.congregation import Congregation
from app.schemas.member import MemberCreate, MemberUpdate, MemberOut

router = APIRouter(prefix="/members", tags=["Membros"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "members")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_model=List[MemberOut])
def list_members(
    q: Optional[str] = Query(None, description="Busca por nome, CPF ou WhatsApp"),
    congregacao_id: Optional[int] = None,
    eh_obreiro: Optional[bool] = None,
    ativo: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Member).filter(Member.ativo == ativo)
    if q:
        search = f"%{q}%"
        query = query.filter(
            (Member.nome_completo.ilike(search)) |
            (Member.cpf.ilike(search)) |
            (Member.whatsapp.ilike(search))
        )
    if congregacao_id:
        query = query.filter(Member.congregacao_id == congregacao_id)
    if eh_obreiro is not None:
        query = query.filter(Member.eh_obreiro == eh_obreiro)
    
    members = query.order_by(Member.nome_completo).offset(skip).limit(limit).all()
    result = []
    for m in members:
        data = MemberOut.model_validate(m)
        if m.congregacao:
            data.congregacao_nome = m.congregacao.nome
        result.append(data)
    return result

@router.get("/count")
def count_members(congregacao_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Member).filter(Member.ativo == True)
    if congregacao_id:
        query = query.filter(Member.congregacao_id == congregacao_id)
    return {"total": query.count()}

@router.get("/aniversariantes")
def aniversariantes(
    periodo: str = Query("dia", description="dia | semana | mes"),
    db: Session = Depends(get_db)
):
    from datetime import datetime, timedelta
    hoje = date.today()
    members = db.query(Member).filter(Member.ativo == True, Member.data_nascimento.isnot(None)).all()
    
    result = []
    for m in members:
        if not m.data_nascimento:
            continue
        aniv = m.data_nascimento.replace(year=hoje.year)
        if aniv < hoje and periodo != "mes":
            aniv = m.data_nascimento.replace(year=hoje.year + 1)
        
        if periodo == "dia" and aniv == hoje:
            result.append({"id": m.id, "nome": m.nome_completo, "data": str(m.data_nascimento), "whatsapp": m.whatsapp})
        elif periodo == "semana":
            fim = hoje + timedelta(days=7)
            if hoje <= aniv <= fim:
                result.append({"id": m.id, "nome": m.nome_completo, "data": str(m.data_nascimento), "whatsapp": m.whatsapp})
        elif periodo == "mes" and m.data_nascimento.month == hoje.month:
            result.append({"id": m.id, "nome": m.nome_completo, "data": str(m.data_nascimento), "whatsapp": m.whatsapp})
    
    return {"periodo": periodo, "total": len(result), "aniversariantes": result}

@router.get("/{member_id}", response_model=MemberOut)
def get_member(member_id: int, db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise HTTPException(404, "Membro não encontrado")
    data = MemberOut.model_validate(m)
    if m.congregacao:
        data.congregacao_nome = m.congregacao.nome
    return data

@router.post("/", response_model=MemberOut, status_code=201)
def create_member(member: MemberCreate, db: Session = Depends(get_db)):
    if member.cpf:
        exists = db.query(Member).filter(Member.cpf == member.cpf).first()
        if exists:
            raise HTTPException(400, "CPF já cadastrado")
    db_member = Member(**member.model_dump())
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return MemberOut.model_validate(db_member)

@router.put("/{member_id}", response_model=MemberOut)
def update_member(member_id: int, member: MemberUpdate, db: Session = Depends(get_db)):
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if not db_member:
        raise HTTPException(404, "Membro não encontrado")
    for k, v in member.model_dump(exclude_unset=True).items():
        setattr(db_member, k, v)
    db.commit()
    db.refresh(db_member)
    return MemberOut.model_validate(db_member)

@router.delete("/{member_id}")
def archive_member(member_id: int, db: Session = Depends(get_db)):
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if not db_member:
        raise HTTPException(404, "Membro não encontrado")
    db_member.ativo = False
    db.commit()
    return {"ok": True, "message": "Membro arquivado"}

@router.post("/{member_id}/foto")
async def upload_foto(member_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    db_member = db.query(Member).filter(Member.id == member_id).first()
    if not db_member:
        raise HTTPException(404, "Membro não encontrado")
    ext = os.path.splitext(file.filename)[1] or ".jpg"
    filename = f"member_{member_id}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    db_member.foto = f"/uploads/members/{filename}"
    db.commit()
    return {"foto": db_member.foto}
