from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Date
from datetime import datetime
from app.database import Base

class AgendaItem(Base):
    __tablename__ = "agenda"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descricao = Column(Text, nullable=True)
    data_hora = Column(DateTime, nullable=False, index=True)
    tipo = Column(String(50), default="compromisso")  # compromisso, culto, reuniao, visita, lembrete
    local = Column(String(200), nullable=True)
    lembrete = Column(Boolean, default=True)
    concluido = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)
