"""
Endpoints de autenticacao.
- POST /api/auth/login  - username + password, retorna JWT
- GET  /api/auth/me     - dados do usuario logado
- POST /api/auth/logout - (stateless, mas mantemos pra simetria)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth_service import (
    verify_password, create_token, get_current_user, CurrentUser,
)

router = APIRouter(prefix="/auth", tags=["Autenticacao"])


class LoginRequest(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    nome: str
    role: str
    congregacao_id: int | None = None
    congregacao_nome: str | None = None

    class Config:
        from_attributes = True


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Autentica e retorna JWT + dados do usuario."""
    user = db.query(User).filter(User.username == req.username, User.ativo == True).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Usuario ou senha invalidos")
    token = create_token(user)
    cong_nome = None
    if user.congregacao_id:
        from app.models.congregation import Congregation
        c = db.query(Congregation).filter(Congregation.id == user.congregacao_id).first()
        if c:
            cong_nome = c.nome
    return {
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "nome": user.nome,
            "role": user.role,
            "congregacao_id": user.congregacao_id,
            "congregacao_nome": cong_nome,
        },
    }


@router.get("/me")
def me(user: CurrentUser = Depends(get_current_user)):
    """Retorna dados do usuario logado (valida o token)."""
    return {
        "id": user.id,
        "username": user.username,
        "nome": user.nome,
        "role": user.role,
        "congregacao_id": user.congregacao_id,
        "congregacao_nome": user.congregacao_nome,
    }


@router.post("/logout")
def logout():
    """JWT e stateless - logout e' apenas client-side (limpar localStorage)."""
    return {"ok": True, "message": "Logout feito no cliente"}
