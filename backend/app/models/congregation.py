from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Congregation(Base):
    __tablename__ = "congregations"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False, unique=True)
    endereco = Column(String(300), nullable=True)
    dirigente = Column(String(200), nullable=True)
    telefone = Column(String(20), nullable=True)
    observacoes = Column(Text, nullable=True)
    ativa = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    membros = relationship("Member", back_populates="congregacao")
