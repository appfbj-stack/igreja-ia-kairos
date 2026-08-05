from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.congregation import Congregation
from app.models.member import Member
from app.schemas.congregation import CongregationCreate, CongregationUpdate, CongregationOut

router = APIRouter(prefix="/congregations", tags=["Congregações"])

@router.get("/", response_model=List[CongregationOut])
def list_congregations(db: Session = Depends(get_db)):
    congs = db.query(Congregation).filter(Congregation.ativa == True).all()
    result = []
    for c in congs:
        data = CongregationOut.model_validate(c)
        data.total_membros = db.query(Member).filter(Member.congregacao_id == c.id, Member.ativo == True).count()
        result.append(data)
    return result

@router.get("/{cong_id}", response_model=CongregationOut)
def get_congregation(cong_id: int, db: Session = Depends(get_db)):
    c = db.query(Congregation).filter(Congregation.id == cong_id).first()
    if not c:
        raise HTTPException(404, "Congregação não encontrada")
    data = CongregationOut.model_validate(c)
    data.total_membros = db.query(Member).filter(Member.congregacao_id == c.id, Member.ativo == True).count()
    return data

@router.post("/", response_model=CongregationOut, status_code=201)
def create_congregation(cong: CongregationCreate, db: Session = Depends(get_db)):
    exists = db.query(Congregation).filter(Congregation.nome == cong.nome).first()
    if exists:
        raise HTTPException(400, "Já existe congregação com este nome")
    db_cong = Congregation(**cong.model_dump())
    db.add(db_cong)
    db.commit()
    db.refresh(db_cong)
    return CongregationOut.model_validate(db_cong)

@router.put("/{cong_id}", response_model=CongregationOut)
def update_congregation(cong_id: int, cong: CongregationUpdate, db: Session = Depends(get_db)):
    db_cong = db.query(Congregation).filter(Congregation.id == cong_id).first()
    if not db_cong:
        raise HTTPException(404, "Congregação não encontrada")
    for k, v in cong.model_dump(exclude_unset=True).items():
        setattr(db_cong, k, v)
    db.commit()
    db.refresh(db_cong)
    return CongregationOut.model_validate(db_cong)

@router.delete("/{cong_id}")
def deactivate_congregation(cong_id: int, db: Session = Depends(get_db)):
    db_cong = db.query(Congregation).filter(Congregation.id == cong_id).first()
    if not db_cong:
        raise HTTPException(404, "Congregação não encontrada")
    db_cong.ativa = False
    db.commit()
    return {"ok": True}
