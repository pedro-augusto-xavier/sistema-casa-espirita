"""Rotas de autenticação: /api/v1/auth"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import SessaoDB, UsuarioAtual
from app.core.auditoria import registrar
from app.core.config import settings
from app.core.ratelimit import limitar_tentativas
from app.core.security import criar_token_acesso, hash_senha, verificar_senha
from app.crud import usuario as crud
from app.models.enums import AcaoAuditoria
from app.schemas.usuario import Token, TrocarSenhaIn, UsuarioOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=Token,
    summary="Entrar (gera token)",
    dependencies=[Depends(limitar_tentativas)],
)
def login(
    db: SessaoDB,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    lembrar: Annotated[bool, Form()] = False,
):
    """Envie `username` (o nome do usuário) e `password`. Devolve o token Bearer.

    Com `lembrar=true` ("Manter conectado") o token dura
    LEMBRAR_TOKEN_EXPIRE_DAYS dias em vez das horas padrão."""
    usuario = crud.autenticar(db, form.username, form.password)
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome ou senha inválidos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.login,
        entidade="usuario",
        entidade_id=usuario.id,
    )
    validade = (
        timedelta(days=settings.LEMBRAR_TOKEN_EXPIRE_DAYS) if lembrar else None
    )
    token = criar_token_acesso(usuario.id, usuario.papel.value, validade)
    return Token(access_token=token)


@router.get("/me", response_model=UsuarioOut, summary="Meu usuário")
def eu(usuario: UsuarioAtual):
    return UsuarioOut.model_validate(usuario)


@router.post(
    "/trocar-senha",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Trocar a própria senha",
    dependencies=[Depends(limitar_tentativas)],
)
def trocar_senha(db: SessaoDB, usuario: UsuarioAtual, dados: TrocarSenhaIn):
    """Pra quem entrou com a senha provisória (ex: CPF) poder trocar por uma
    só sua, sem precisar pedir pra um admin."""
    if not verificar_senha(dados.senha_atual, usuario.senha_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha atual incorreta",
        )
    usuario.senha_hash = hash_senha(dados.senha_nova)
    db.commit()
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.atualizar,
        entidade="usuario",
        entidade_id=usuario.id,
        dados={"senha_alterada": True, "por_si_mesmo": True},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
