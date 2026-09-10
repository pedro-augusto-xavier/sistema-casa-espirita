"""Dependências compartilhadas pelas rotas: sessão do banco e usuário logado."""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import ler_token_acesso
from app.models.enums import PapelUsuario
from app.models.usuario import Usuario

SessaoDB = Annotated[Session, Depends(get_db)]

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

_NAO_AUTENTICADO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Não autenticado",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_usuario_atual(db: SessaoDB, token: Annotated[str, Depends(oauth2)]) -> Usuario:
    try:
        payload = ler_token_acesso(token)
        usuario_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError) as exc:
        raise _NAO_AUTENTICADO from exc

    usuario = db.get(Usuario, usuario_id)
    if usuario is None or not usuario.ativo:
        raise _NAO_AUTENTICADO
    return usuario


UsuarioAtual = Annotated[Usuario, Depends(get_usuario_atual)]


def exigir_admin(usuario: UsuarioAtual) -> Usuario:
    if usuario.papel != PapelUsuario.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ação restrita a administradores",
        )
    return usuario


Admin = Annotated[Usuario, Depends(exigir_admin)]
