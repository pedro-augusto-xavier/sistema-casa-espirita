"""Schemas de Usuário do sistema e do token de login."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import PapelUsuario


class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=128)
    papel: PapelUsuario = PapelUsuario.operador


class UsuarioUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str | None = Field(default=None, min_length=3, max_length=120)
    senha: str | None = Field(default=None, min_length=8, max_length=128)
    papel: PapelUsuario | None = None
    ativo: bool | None = None


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: EmailStr
    papel: PapelUsuario
    ativo: bool
    criado_em: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
