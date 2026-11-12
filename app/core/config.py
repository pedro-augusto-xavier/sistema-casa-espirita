"""Configuração central da aplicação.

Lê as variáveis do arquivo .env (ou do ambiente do sistema) e valida os tipos.
Em qualquer lugar do código usamos:  from app.core.config import settings
"""

import json
from datetime import UTC, datetime, timedelta
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
        # Erro de validação sem os valores: as migrations rodam num GitHub
        # Actions de log público, e o pydantic mostraria pedaços da URL do
        # banco e das chaves.
        hide_input_in_errors=True,
    )

    # Banco de dados. Na API (Render) é o usuário restrito app_casa; quem
    # roda as migrations (workflow de deploy ou o seu PC) põe aqui a URL do
    # dono do banco -- ela nunca vai pro Render (ver docs/SEGURANCA.md).
    DATABASE_URL: str

    # Segurança / JWT
    SECRET_KEY: str = _CHAVE_PADRAO_INSEGURA
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    # validade do token quando a pessoa marca "Manter conectado" no login
    LEMBRAR_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"
    # Época de revogação guardada FORA do banco: todo token emitido antes
    # dela é recusado, venha da sessão que vier. Serve pra derrubar todo
    # mundo depois de restaurar um backup (o banco restaurado não sabe das
    # revogações feitas depois do snapshot) -- ver docs/BACKUP.md. Data e
    # hora ISO; sem fuso = UTC. Vazia = desligada.
    SESSOES_VALIDAS_DESDE: datetime | None = None

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

    # App. Obrigatório, sem padrão: se faltar no Render, a API não sobe --
    # com padrão "dev", todas as travas de produção (chaves, /docs, HSTS,
    # SQL no log) cairiam em silêncio (achado #3). Local: APP_ENV=dev no .env.
    APP_ENV: str

    # Cabeçalho que traz o IP real de quem acessa, preenchido pelo proxy da
    # frente (no Render, a Cloudflare). Vazio = não tem proxy: vale o IP da
    # conexão. Ver app/core/contexto.py.
    IP_CLIENTE_CABECALHO: str = "cf-connecting-ip"

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

    @field_validator("SESSOES_VALIDAS_DESDE", mode="before")
    @classmethod
    def _vazio_e_desligado(cls, v: object) -> object:
        if isinstance(v, str) and not v.strip():
            return None
        return v

    @field_validator("SESSOES_VALIDAS_DESDE")
    @classmethod
    def _epoca_em_utc_e_nao_no_futuro(cls, v: datetime | None) -> datetime | None:
        """Data no futuro é quase sempre erro de digitação (e recusaria
        todo login até lá) -- melhor o app nem subir. 10 min de folga pro
        relógio do computador que gerou o valor."""
        if v is None:
            return v
        if v.tzinfo is None:
            v = v.replace(tzinfo=UTC)
        if v > datetime.now(UTC) + timedelta(minutes=10):
            raise ValueError(
                "SESSOES_VALIDAS_DESDE está no futuro. Use a data e hora "
                "(UTC) que o scripts.pos_restauracao mostrou."
            )
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
