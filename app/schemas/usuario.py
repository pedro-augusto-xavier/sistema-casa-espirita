"""Schemas de Usuário do sistema, do login e da verificação em duas etapas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import PapelUsuario


class UsuarioCreate(BaseModel):
    # campos a mais (ex: "ativo", "mfa_ativo") são recusados, não ignorados
    model_config = ConfigDict(extra="forbid")

    nome: str = Field(min_length=3, max_length=120)
    # login é pelo nome -- e-mail é só um contato opcional.
    email: EmailStr | None = None
    # senha PROVISÓRIA (ex: 8 números do CPF): a pessoa troca no 1º acesso,
    # aí valem as regras de senha forte (core/senhas.py).
    senha: str = Field(min_length=8, max_length=128)
    papel: PapelUsuario = PapelUsuario.operador


class UsuarioUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str | None = Field(default=None, min_length=3, max_length=120)
    email: EmailStr | None = None
    # redefinir a senha também deixa ela provisória
    senha: str | None = Field(default=None, min_length=8, max_length=128)
    papel: PapelUsuario | None = None
    ativo: bool | None = None


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
