from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CongregationBase(BaseModel):
    nome: str
    endereco: Optional[str] = None
    dirigente: Optional[str] = None
    telefone: Optional[str] = None
    observacoes: Optional[str] = None

class CongregationCreate(CongregationBase):
    pass

class CongregationUpdate(BaseModel):
    nome: Optional[str] = None
    endereco: Optional[str] = None
    dirigente: Optional[str] = None
    telefone: Optional[str] = None
    observacoes: Optional[str] = None
    ativa: Optional[bool] = None

class CongregationOut(CongregationBase):
    id: int
    ativa: bool
    criado_em: datetime
    total_membros: Optional[int] = 0

    class Config:
        from_attributes = True
