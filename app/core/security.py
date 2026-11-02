"""Hash de senha (bcrypt) e token de acesso (JWT).

O token carrega o id da sessão (`sid`). Ele sozinho não basta: a cada
requisição a sessão é conferida no banco (ver api/deps.py), então dá pra
cortar o acesso na hora -- sair, trocar senha, desativar usuário.
"""

from datetime import UTC, datetime

import bcrypt
import jwt

from app.core.config import settings

# bcrypt trunca em 72 bytes -- cortamos explicitamente pra não haver surpresa.
_LIMITE_BCRYPT = 72

# Hash de uma senha qualquer, usado quando o usuário digitado não existe:
# a resposta demora o mesmo tanto, e ninguém descobre quais nomes existem
# medindo o tempo do login.
_HASH_FALSO = bcrypt.hashpw(b"usuario-que-nao-existe", bcrypt.gensalt()).decode()


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


def gastar_tempo_como_se_verificasse(senha: str) -> None:
    verificar_senha(senha, _HASH_FALSO)


def criar_token_sessao(usuario_id: int, sessao_id: str, expira_em: datetime) -> str:
    payload = {
        "sub": str(usuario_id),
        "sid": sessao_id,
        "iat": datetime.now(UTC),
        "exp": expira_em,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def ler_token_acesso(token: str) -> dict:
    """Levanta jwt.PyJWTError se o token for inválido ou expirado."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
        options={"require": ["sub", "sid", "exp"]},
    )
