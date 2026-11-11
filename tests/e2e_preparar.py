"""Prepara o banco pro teste de ponta a ponta (frontend/e2e): cria (ou
reaproveita) um operador sem pendência nenhuma, com a senha de E2E_SENHA.

NUNCA rodar contra produção -- só num banco descartável (CI ou local):
    python -m tests.e2e_preparar
"""

import os

from sqlalchemy import select

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import hash_senha
from app.models.enums import PapelUsuario
from app.models.usuario import Usuario

NOME = "Operador E2E"


def main() -> None:
    if settings.APP_ENV not in ("dev", "ci"):
        raise SystemExit("Recusado: só roda com APP_ENV=dev ou ci (banco descartável).")
    senha = os.environ["E2E_SENHA"]
    with SessionLocal() as db:
        u = db.scalar(select(Usuario).where(Usuario.nome == NOME))
        if u is None:
            u = Usuario(nome=NOME, papel=PapelUsuario.operador, senha_hash="")
            db.add(u)
        u.senha_hash = hash_senha(senha)
        u.senha_provisoria = False
        u.ativo = True
        db.commit()
    print(f"{NOME} pronto.")


if __name__ == "__main__":
    main()
