"""Dependências compartilhadas pelas rotas: sessão do banco e usuário logado.

Camadas de acesso:
  1. `get_sessao_atual` / `UsuarioAtual`: token válido + sessão aberta no
     banco + usuário ativo. É o que as rotas de /auth usam (inclusive quem
     ainda tem pendência, pra conseguir resolvê-la).
  2. `exigir_sem_pendencias`: além disso, nada pendente (senha provisória
     trocada, verificação em duas etapas configurada quando obrigatória).
     Aplicada em TODAS as rotas de dados (ver api/v1/api.py).
  3. `exigir_admin`: só administradores.
"""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import ler_token_acesso
from app.crud import sessao as crud_sessao
from app.models.enums import PapelUsuario
from app.models.usuario import SessaoUsuario, Usuario

SessaoDB = Annotated[Session, Depends(get_db)]

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

_NAO_AUTENTICADO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Não autenticado",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_sessao_atual(
    db: SessaoDB, token: Annotated[str, Depends(oauth2)]
) -> SessaoUsuario:
    try:
        payload = ler_token_acesso(token)
        usuario_id = int(payload["sub"])
        sessao_id = str(payload["sid"])
    except (jwt.PyJWTError, KeyError, ValueError, TypeError) as exc:
        raise _NAO_AUTENTICADO from exc

    sessao = crud_sessao.obter_valida(db, sessao_id, usuario_id)
    if sessao is None or not sessao.usuario.ativo:
        raise _NAO_AUTENTICADO
    crud_sessao.marcar_uso(db, sessao)
    return sessao


SessaoAtual = Annotated[SessaoUsuario, Depends(get_sessao_atual)]


def get_usuario_atual(sessao: SessaoAtual) -> Usuario:
    return sessao.usuario


UsuarioAtual = Annotated[Usuario, Depends(get_usuario_atual)]


def exigir_sem_pendencias(usuario: UsuarioAtual) -> Usuario:
    if usuario.pendencias:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "codigo": "pendencia",
                "mensagem": "Antes de continuar, termine a configuração do seu acesso.",
                "pendencias": usuario.pendencias,
            },
        )
    return usuario


def exigir_admin(usuario: UsuarioAtual) -> Usuario:
    if usuario.papel != PapelUsuario.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ação restrita a administradores",
        )
    return usuario


Admin = Annotated[Usuario, Depends(exigir_admin)]
