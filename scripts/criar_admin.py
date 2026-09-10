"""Cria (ou promove) um usuário administrador.

Uso:
    python -m scripts.criar_admin --nome "Tia Fulana" --email tia@casa.org \
        --senha "trocar123"

Se o e-mail já existir, apenas vira admin e (opcionalmente) troca a senha.
"""

import argparse

from app.core.database import SessionLocal
from app.crud import usuario as crud
from app.models.enums import PapelUsuario
from app.schemas.usuario import UsuarioCreate


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria um usuário administrador")
    parser.add_argument("--nome", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--senha", required=True)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        existente = crud.get_by_email(db, args.email)
        if existente:
            from app.schemas.usuario import UsuarioUpdate

            crud.atualizar(
                db,
                existente,
                UsuarioUpdate(
                    papel=PapelUsuario.admin, senha=args.senha, ativo=True
                ),
            )
            print(f"Usuário {args.email} atualizado para admin.")
            return

        crud.criar(
            db,
            UsuarioCreate(
                nome=args.nome,
                email=args.email,
                senha=args.senha,
                papel=PapelUsuario.admin,
            ),
        )
        print(f"Admin {args.email} criado.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
