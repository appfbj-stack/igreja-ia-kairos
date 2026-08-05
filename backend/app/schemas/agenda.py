from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AgendaBase(BaseModel):
    titulo: str
    descricao: Optional[str] = None
    data_hora: datetime
    tipo: str = "compromisso"
    local: Optional[str] = None
    lembrete: bool = True

class AgendaCreate(AgendaBase):
    pass

class AgendaUpdate(BaseModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    data_hora: Optional[datetime] = None
    tipo: Optional[str] = None
    local: Optional[str] = None
    lembrete: Optional[bool] = None
    concluido: Optional[bool] = None

class AgendaOut(AgendaBase):
    id: int
    concluido: bool
    criado_em: datetime

    class Config:
        from_attributes = True
