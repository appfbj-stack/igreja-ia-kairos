from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

class MemberBase(BaseModel):
    nome_completo: str
    foto: Optional[str] = None
    cpf: Optional[str] = None
    whatsapp: Optional[str] = None
    endereco: Optional[str] = None
    data_nascimento: Optional[date] = None
    filiacao: Optional[str] = None
    profissao: Optional[str] = None
    filhos: Optional[str] = None
    data_batismo: Optional[date] = None
    data_filiacao: Optional[date] = None
    numero_carteirinha: Optional[str] = None
    validade_carteirinha: Optional[date] = None
    congregacao_id: Optional[int] = None
    eh_obreiro: bool = False
    cargo_obreiro: Optional[str] = None
    data_consagracao: Optional[date] = None
    observacoes: Optional[str] = None

class MemberCreate(MemberBase):
    pass

class MemberUpdate(BaseModel):
    nome_completo: Optional[str] = None
    foto: Optional[str] = None
    cpf: Optional[str] = None
    whatsapp: Optional[str] = None
    endereco: Optional[str] = None
    data_nascimento: Optional[date] = None
    filiacao: Optional[str] = None
    profissao: Optional[str] = None
    filhos: Optional[str] = None
    data_batismo: Optional[date] = None
    data_filiacao: Optional[date] = None
    numero_carteirinha: Optional[str] = None
    validade_carteirinha: Optional[date] = None
    congregacao_id: Optional[int] = None
    eh_obreiro: Optional[bool] = None
    cargo_obreiro: Optional[str] = None
    data_consagracao: Optional[date] = None
    observacoes: Optional[str] = None
    ativo: Optional[bool] = None

class MemberOut(MemberBase):
    id: int
    ativo: bool
    criado_em: datetime
    atualizado_em: Optional[datetime] = None
    congregacao_nome: Optional[str] = None

    class Config:
        from_attributes = True
