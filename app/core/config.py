"""Configuração central da aplicação.

Lê as variáveis do arquivo .env (ou do ambiente do sistema) e valida os tipos.
Em qualquer lugar do código usamos:  from app.core.config import settings
"""

from pydantic import field_validator
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

    # Origens autorizadas a chamar a API pelo navegador (o front em dev)
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

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

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _origins_por_virgula(cls, v: object) -> object:
        """Deixa configurar como lista JSON OU como 'a,b,c' (mais fácil
        de colar no painel de variáveis de ambiente do host)."""
        if isinstance(v, str) and not v.strip().startswith("["):
            return [origem.strip() for origem in v.split(",") if origem.strip()]
        return v

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "dev"


settings = Settings()  # type: ignore[call-arg]
