"""Schemas de Usuário do sistema, do login e da verificação em duas etapas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import PapelUsuario


class UsuarioCreate(BaseModel):
    # campos a mais (ex: "ativo", "mfa_ativo") são recusados, não ignorados
    model_config = ConfigDict(extra="forbid")

    nome: str = Field(min_length=3, max_length=120)
    # login é pelo nome -- e-mail é só um contato opcional.
    email: EmailStr | None = None
    # sem campo de senha: o servidor gera a provisória (ver UsuarioComSenhaOut)
    papel: PapelUsuario = PapelUsuario.operador


class UsuarioUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str | None = Field(default=None, min_length=3, max_length=120)
    email: EmailStr | None = None
    # senha não se edita aqui: POST /usuarios/{id}/redefinir-senha
    papel: PapelUsuario | None = None
    # aqui só desativa -- reativar é POST /usuarios/{id}/reativar, que gera
    # senha nova
    ativo: Literal[False] | None = None


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr | None
    papel: PapelUsuario
    ativo: bool
    criado_em: datetime
    senha_provisoria: bool
    mfa_ativo: bool
    mfa_obrigatorio: bool
    ultimo_login_em: datetime | None


class UsuarioComSenhaOut(UsuarioOut):
    """Resposta de criar/redefinir senha: a senha provisória gerada aparece
    só aqui, uma vez. O admin repassa pra pessoa."""

    senha_gerada: str
    senha_expira_em: datetime


class UsuarioEu(UsuarioOut):
    """O /auth/me: o usuário e o que ele ainda precisa resolver."""

    pendencias: list[str]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    pendencias: list[str] = Field(default_factory=list)


class TrocarSenhaIn(BaseModel):
    senha_atual: str = Field(max_length=128)
    # as regras (tamanho, senhas comuns...) estão em core/senhas.py
    senha_nova: str = Field(min_length=1, max_length=128)


class MfaInicioOut(BaseModel):
    segredo: str
    uri: str


class MfaCodigoIn(BaseModel):
    codigo: str = Field(min_length=6, max_length=10)


class MfaDesativarIn(BaseModel):
    senha: str = Field(max_length=128)
