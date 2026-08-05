from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    nome = Column(String(200), nullable=False)
    hashed_password = Column(String(200), nullable=False)
    role = Column(String(50), default="secretaria")  # pastor, dirigente, secretaria
    congregacao_id = Column(Integer, nullable=True)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, default=datetime.utcnow)
