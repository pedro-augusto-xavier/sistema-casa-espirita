"""Gera e define a senha do usuário de banco do app (`app_casa`).

A senha nasce e fica só no seu computador:
  - é gerada aqui (aleatória, longa);
  - o banco recebe só o "hash" SCRAM dela (como o `\\password` do psql faz),
    então ela não aparece em log nem em histórico de comando do Neon;
  - o script testa o login com ela e imprime a URL pronta pro Render.

Uso (PowerShell): três comandos, no mesmo terminal. A URL é a DATABASE_URL
ATUAL do Render (a do dono do banco, `neondb_owner`) -- copie pelo ícone de
olho no Render:

    $env:DONO_DATABASE_URL="<url atual>"
    .\\.venv\\Scripts\\python.exe -m scripts.senha_do_app
    Remove-Item Env:\\DONO_DATABASE_URL

Pode rodar de novo quando quiser trocar a senha do app (rotação).
"""

import base64
import hashlib
import hmac
import os
import secrets
import sys

import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url

USUARIO_DO_APP = "app_casa"
_ITERACOES = 4096


def _b64(dados: bytes) -> str:
    return base64.b64encode(dados).decode()


def verificador_scram(senha: str) -> str:
    """O formato que o Postgres guarda (RFC 5802 / 7677): quem tiver isso
    consegue conferir a senha, mas não descobrir qual é."""
    sal = os.urandom(16)
    salgada = hashlib.pbkdf2_hmac("sha256", senha.encode(), sal, _ITERACOES)
    chave_cliente = hmac.new(salgada, b"Client Key", hashlib.sha256).digest()
    chave_guardada = hashlib.sha256(chave_cliente).digest()
    chave_servidor = hmac.new(salgada, b"Server Key", hashlib.sha256).digest()
    return (
        f"SCRAM-SHA-256${_ITERACOES}:{_b64(sal)}"
        f"${_b64(chave_guardada)}:{_b64(chave_servidor)}"
    )


def _para_psycopg(url: str) -> str:
    """postgresql+psycopg://... -> postgresql://... (o psycopg puro não
    entende o '+psycopg' do SQLAlchemy)."""
    return url.replace("postgresql+psycopg://", "postgresql://", 1).replace(
        "postgres://", "postgresql://", 1
    )


def definir_senha(url_dono: str, usuario: str = USUARIO_DO_APP) -> str:
    """Define uma senha nova pro `usuario`, testa e devolve a URL dele."""
    senha = secrets.token_urlsafe(32)  # ~190 bits, só letras, números, - e _
    with psycopg.connect(_para_psycopg(url_dono), autocommit=True) as conexao:
        conexao.execute(
            sql.SQL("ALTER ROLE {} PASSWORD {}").format(
                sql.Identifier(usuario), sql.Literal(verificador_scram(senha))
            )
        )

    url_app = (
        make_url(_para_psycopg(url_dono))
        .set(username=usuario, password=senha)
        .render_as_string(hide_password=False)
    )
    with psycopg.connect(url_app) as conexao:
        quem = conexao.execute("SELECT current_user").fetchone()[0]
    if quem != usuario:
        sys.exit(f"Algo deu errado: conectou como {quem}, não como {usuario}.")
    return url_app


def main() -> None:
    url_dono = os.environ.get("DONO_DATABASE_URL", "").strip()
    if not url_dono:
        sys.exit(
            "Defina DONO_DATABASE_URL (a DATABASE_URL atual do Render)"
            " -- ver o topo do arquivo."
        )
    url_app = definir_senha(url_dono)
    print("\nSenha nova definida e testada. Login como app_casa funcionou.\n")
    print("No Render > Environment:")
    print("  1. Crie MIGRATIONS_DATABASE_URL com o valor ATUAL de DATABASE_URL.")
    print("  2. Troque DATABASE_URL por esta (copie a linha inteira):\n")
    print(url_app)
    print("\nDepois feche este terminal. A senha só fica guardada no Render.")


if __name__ == "__main__":
    main()
