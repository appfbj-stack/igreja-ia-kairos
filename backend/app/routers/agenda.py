from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
from app.database import get_db
from app.models.agenda import AgendaItem
from app.schemas.agenda import AgendaCreate, AgendaUpdate, AgendaOut

router = APIRouter(prefix="/agenda", tags=["Agenda Pastoral"])

@router.get("/", response_model=List[AgendaOut])
def list_agenda(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    tipo: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AgendaItem).filter(AgendaItem.concluido == False)
    if from_date:
        query = query.filter(AgendaItem.data_hora >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        query = query.filter(AgendaItem.data_hora <= datetime.combine(to_date, datetime.max.time()))
    if tipo:
        query = query.filter(AgendaItem.tipo == tipo)
    return query.order_by(AgendaItem.data_hora).all()

@router.get("/proximos")
def proximos(dias: int = 7, db: Session = Depends(get_db)):
    agora = datetime.utcnow()
    fim = agora + timedelta(days=dias)
    items = db.query(AgendaItem).filter(
        AgendaItem.concluido == False,
        AgendaItem.data_hora >= agora,
        AgendaItem.data_hora <= fim
    ).order_by(AgendaItem.data_hora).all()
    return items

@router.post("/", response_model=AgendaOut, status_code=201)
def create_agenda(item: AgendaCreate, db: Session = Depends(get_db)):
    db_item = AgendaItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/{item_id}", response_model=AgendaOut)
def update_agenda(item_id: int, item: AgendaUpdate, db: Session = Depends(get_db)):
    db_item = db.query(AgendaItem).filter(AgendaItem.id == item_id).first()
    if not db_item:
        raise HTTPException(404, "Item não encontrado")
    for k, v in item.model_dump(exclude_unset=True).items():
        setattr(db_item, k, v)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/{item_id}")
def delete_agenda(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(AgendaItem).filter(AgendaItem.id == item_id).first()
    if not db_item:
        raise HTTPException(404, "Item não encontrado")
    db.delete(db_item)
    db.commit()
    return {"ok": True}
