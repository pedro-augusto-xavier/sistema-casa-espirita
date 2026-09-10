"""Rotas de autenticação: /api/v1/auth"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import SessaoDB, UsuarioAtual
from app.core.auditoria import registrar
from app.core.security import criar_token_acesso
from app.crud import usuario as crud
from app.models.enums import AcaoAuditoria
from app.schemas.usuario import Token, UsuarioOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token, summary="Entrar (gera token)")
def login(
    db: SessaoDB,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
):
    """Envie `username` (e-mail) e `password`. Devolve o token Bearer."""
    usuario = crud.autenticar(db, form.username, form.password)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.login,
        entidade="usuario",
        entidade_id=usuario.id,
    )
    token = criar_token_acesso(usuario.id, usuario.papel.value)
    return Token(access_token=token)


@router.get("/me", response_model=UsuarioOut, summary="Meu usuário")
def eu(usuario: UsuarioAtual):
    return UsuarioOut.model_validate(usuario)
