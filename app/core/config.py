"""Configuração central da aplicação.

Lê as variáveis do arquivo .env (ou do ambiente do sistema) e valida os tipos.
Em qualquer lugar do código usamos:  from app.core.config import settings
"""

import json
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.chaves import CHAVE_HMAC_DEV, CHAVES_DEV, ler_chave_hmac, ler_chaves

_CHAVE_PADRAO_INSEGURA = "dev-inseguro-troque-no-.env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Banco de dados
    DATABASE_URL: str
    # Opcional: URL de um usuário do banco com mais permissão, só pras
    # migrations (criar/alterar tabelas). Assim o app em si pode rodar com um
    # usuário que só lê e grava dados -- ver docs/SEGURANCA.md.
    MIGRATIONS_DATABASE_URL: str | None = None

    # Segurança / JWT
    SECRET_KEY: str = _CHAVE_PADRAO_INSEGURA
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    # validade do token quando a pessoa marca "Manter conectado" no login
    LEMBRAR_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # Criptografia dos campos sensíveis (CPF, observações, anexos).
    # Formato e rotação: ver app/core/chaves.py. NUNCA no Git.
    CHAVES_CRIPTOGRAFIA: str = CHAVES_DEV
    # Chave separada pro "índice" do CPF (achar duplicado e buscar sem
    # precisar decifrar). Diferente da de criptografia de propósito.
    CHAVE_HMAC: str = CHAVE_HMAC_DEV

    # Verificação em duas etapas (aplicativo autenticador):
    #   "admin"   -> obrigatória pra administradores (padrão)
    #   "todos"   -> obrigatória pra todo mundo
    #   "ninguem" -> opcional pra todos
    MFA_OBRIGATORIO: Literal["admin", "todos", "ninguem"] = "admin"

    # App
    APP_ENV: str = "dev"

    # Origens autorizadas a chamar a API pelo navegador (o front em dev).
    # Fica como texto puro (não lista) porque pydantic-settings tenta ler
    # variável de ambiente de tipo lista como JSON antes de qualquer
    # validação nossa -- e "a,b,c" não é JSON válido. Guardamos como string
    # e convertemos na propriedade abaixo.
    CORS_ORIGINS_RAW: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="CORS_ORIGINS",
    )

    @field_validator("DATABASE_URL", "MIGRATIONS_DATABASE_URL")
    @classmethod
    def _driver_psycopg(cls, v: str | None) -> str | None:
        """Provedores (Neon, Render, Railway...) dão a URL sem o driver.
        O SQLAlchemy precisa do 'postgresql+psycopg://' explícito.
        """
        if v is None:
            return v
        for prefixo in ("postgres://", "postgresql://"):
            if v.startswith(prefixo):
                return "postgresql+psycopg://" + v[len(prefixo) :]
        return v

    @property
    def CORS_ORIGINS(self) -> list[str]:
        bruto = self.CORS_ORIGINS_RAW.strip()
        if bruto.startswith("["):
            return json.loads(bruto)
        return [origem.strip() for origem in bruto.split(",") if origem.strip()]

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "dev"

    @model_validator(mode="after")
    def _recusa_chave_fraca_em_producao(self) -> "Settings":
        """Fora do dev, não deixa o app nem subir com a chave de exemplo (ou
        uma chave curta demais) -- é melhor quebrar o deploy do que assinar
        tokens de sessão com um segredo previsível."""
        if not self.is_dev and (
            self.SECRET_KEY == _CHAVE_PADRAO_INSEGURA or len(self.SECRET_KEY) < 32
        ):
            raise ValueError(
                "SECRET_KEY fraca ou não configurada (APP_ENV != dev). Gere uma "
                "com: python -c \"import secrets; print(secrets.token_hex(32))\" "
                "e defina a variável SECRET_KEY no ambiente de produção."
            )
        return self

    @model_validator(mode="after")
    def _valida_chaves_de_criptografia(self) -> "Settings":
        """Mesma ideia da SECRET_KEY: chave mal formatada derruba o deploy, e
        fora do dev as chaves de exemplo (que estão no Git) são recusadas."""
        try:
            _, chaves = ler_chaves(self.CHAVES_CRIPTOGRAFIA)
            chave_hmac = ler_chave_hmac(self.CHAVE_HMAC)
        except ValueError as exc:
            raise ValueError(f"CHAVES_CRIPTOGRAFIA/CHAVE_HMAC inválida: {exc}") from exc

        if chave_hmac in chaves.values():
            raise ValueError(
                "CHAVE_HMAC tem que ser diferente das chaves de criptografia"
            )
        if not self.is_dev and (
            self.CHAVES_CRIPTOGRAFIA == CHAVES_DEV or self.CHAVE_HMAC == CHAVE_HMAC_DEV
        ):
            raise ValueError(
                "CHAVES_CRIPTOGRAFIA e CHAVE_HMAC não configuradas (APP_ENV != dev). "
                "Gere com: python -m scripts.gerar_chaves e defina as duas "
                "variáveis no ambiente de produção."
            )
        return self


settings = Settings()  # type: ignore[call-arg]
