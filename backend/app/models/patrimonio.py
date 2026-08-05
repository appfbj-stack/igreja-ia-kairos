from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Date, ForeignKey, Boolean
from datetime import datetime
from app.database import Base

class Patrimonio(Base):
    __tablename__ = "patrimonio"

    id = Column(Integer, primary_key=True, index=True)
    item = Column(String(200), nullable=False)
    categoria = Column(String(100), nullable=True)
    foto = Column(String(500), nullable=True)
    valor = Column(Float, nullable=True)
    data_aquisicao = Column(Date, nullable=True)
    local = Column(String(200), nullable=True)
    responsavel = Column(String(200), nullable=True)
    congregacao_id = Column(Integer, ForeignKey("congregations.id"), nullable=True)
    observacoes = Column(Text, nullable=True)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
