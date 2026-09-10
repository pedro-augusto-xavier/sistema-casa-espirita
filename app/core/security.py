"""Hash de senha (bcrypt) e token de acesso (JWT)."""

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings

# bcrypt trunca em 72 bytes -- cortamos explicitamente pra não haver surpresa.
_LIMITE_BCRYPT = 72


def hash_senha(senha: str) -> str:
    senha_bytes = senha.encode("utf-8")[:_LIMITE_BCRYPT]
    return bcrypt.hashpw(senha_bytes, bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, hash_armazenado: str) -> bool:
    try:
        return bcrypt.checkpw(
            senha.encode("utf-8")[:_LIMITE_BCRYPT],
            hash_armazenado.encode("utf-8"),
        )
    except ValueError:
        return False


def criar_token_acesso(usuario_id: int, papel: str) -> str:
    agora = datetime.now(UTC)
    payload = {
        "sub": str(usuario_id),
        "papel": papel,
        "iat": agora,
        "exp": agora + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def ler_token_acesso(token: str) -> dict:
    """Levanta jwt.PyJWTError se o token for inválido ou expirado."""
    return jwt.decode(
        token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
    )
