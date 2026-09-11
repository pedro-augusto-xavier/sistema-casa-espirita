"""Configuração central da aplicação.

Lê as variáveis do arquivo .env (ou do ambiente do sistema) e valida os tipos.
Em qualquer lugar do código usamos:  from app.core.config import settings
"""

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

    @property
    def is_dev(self) -> bool:
        return self.APP_ENV == "dev"


settings = Settings()  # type: ignore[call-arg]
