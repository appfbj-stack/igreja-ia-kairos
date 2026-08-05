from sqlalchemy import Column, Integer, String, Boolean, Date, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String(200), nullable=False, index=True)
    foto = Column(String(500), nullable=True)
    cpf = Column(String(14), unique=True, nullable=True, index=True)
    whatsapp = Column(String(20), nullable=True)
    endereco = Column(String(300), nullable=True)
    data_nascimento = Column(Date, nullable=True)
    filiacao = Column(String(200), nullable=True)  # pai/mãe
    profissao = Column(String(100), nullable=True)
    filhos = Column(Text, nullable=True)
    data_batismo = Column(Date, nullable=True)
    data_filiacao = Column(Date, nullable=True)
    numero_carteirinha = Column(String(50), nullable=True)
    validade_carteirinha = Column(Date, nullable=True)
    congregacao_id = Column(Integer, ForeignKey("congregations.id"), nullable=True)
    eh_obreiro = Column(Boolean, default=False)
    cargo_obreiro = Column(String(100), nullable=True)
    data_consagracao = Column(Date, nullable=True)
    observacoes = Column(Text, nullable=True)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    congregacao = relationship("Congregation", back_populates="membros")
