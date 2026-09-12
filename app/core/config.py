"""Configuração central da aplicação.

Lê as variáveis do arquivo .env (ou do ambiente do sistema) e valida os tipos.
Em qualquer lugar do código usamos:  from app.core.config import settings
"""

import json

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Banco de dados
    DATABASE_URL: str

    # Segurança / JWT
    SECRET_KEY: str = "dev-inseguro-troque-no-.env"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    ALGORITHM: str = "HS256"

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

    @field_validator("DATABASE_URL")
    @classmethod
    def _driver_psycopg(cls, v: str) -> str:
        """Provedores (Neon, Render, Railway...) dão a URL sem o driver.
        O SQLAlchemy precisa do 'postgresql+psycopg://' explícito.
        """
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


settings = Settings()  # type: ignore[call-arg]
