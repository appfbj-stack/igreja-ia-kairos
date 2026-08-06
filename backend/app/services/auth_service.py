"""
Auth service: JWT + password hashing + scope helpers.
- Pastor (sede): congregacao_id = NULL, ve TUDO
- Dirigente: congregacao_id = X, ve SEMENTE a sua
- Secretaria: mesma logica do dirigente
"""
from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from dataclasses import dataclass
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User

# =========================================================================
# Config
# =========================================================================
JWT_SECRET = os.getenv("JWT_SECRET", "kairos-igreja-troque-isso-em-prod-2024")
JWT_ALG = "HS256"
JWT_EXPIRE_HOURS = 24 * 7  # 7 dias

# password hashing (bcrypt pinado em 4.0.1 no requirements.txt)
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# bearer token
bearer = HTTPBearer(auto_error=False)


def hash_password(plain: str) -> str:
    return pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_ctx.verify(plain, hashed)
    except Exception:
        return False


def create_token(user: User) -> str:
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
        "cong_id": user.congregacao_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRE_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError as e:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"Token invalido: {e}")


# =========================================================================
# User context
# =========================================================================
@dataclass
class CurrentUser:
    id: int
    username: str
    nome: str
    role: str  # pastor | dirigente | secretaria
    congregacao_id: Optional[int]
    congregacao_nome: Optional[str] = None

    @property
    def is_pastor(self) -> bool:
        return self.role == "pastor"

    @property
    def scope_label(self) -> str:
        if self.is_pastor:
            return "Todas as congregacoes (sede)"
        return self.congregacao_nome or "Sem congregacao"


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """Dependency que valida o token e retorna o usuario logado."""
    if not creds:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Autenticacao necessaria")
    payload = decode_token(creds.credentials)
    user_id = int(payload.get("sub", 0))
    user = db.query(User).filter(User.id == user_id, User.ativo == True).first()
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario nao encontrado")
    cong_nome = None
    if user.congregacao_id:
        from app.models.congregation import Congregation
        c = db.query(Congregation).filter(Congregation.id == user.congregacao_id).first()
        if c:
            cong_nome = c.nome
    return CurrentUser(
        id=user.id,
        username=user.username,
        nome=user.nome,
        role=user.role,
        congregacao_id=user.congregacao_id,
        congregacao_nome=cong_nome,
    )


# =========================================================================
# Scope helper - aplica filtro por congregacao
# =========================================================================
def scope_query(query, model, user: CurrentUser):
    """
    Aplica filtro de escopo a uma query.
    - Pastor (sede): nao filtra, ve tudo
    - Dirigente/Secretaria: filtra por congregacao_id
    - Se a model nao tem congregacao_id (ex: AgendaItem, Patrimonio), pastor ve tudo
    """
    if user.is_pastor:
        return query
    if hasattr(model, "congregacao_id") and user.congregacao_id is not None:
        return query.filter(model.congregacao_id == user.congregacao_id)
    return query
