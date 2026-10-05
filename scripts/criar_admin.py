"""Cria (ou promove) um usuário administrador.

Uso:
    python -m scripts.criar_admin --nome "Tia Fulana" --senha "trocar123" \
        [--email tia@casa.org]

Login no sistema é feito pelo nome -- se já existir um usuário ativo com
esse nome, só atualiza (vira admin, troca a senha se informada, garante
que está ativo). E-mail é opcional, só um contato.
"""

import argparse

from app.core.database import SessionLocal
from app.crud import usuario as crud
from app.models.enums import PapelUsuario
from app.schemas.usuario import UsuarioCreate


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria um usuário administrador")
    parser.add_argument("--nome", required=True)
    parser.add_argument("--senha", required=True)
    parser.add_argument("--email", default=None)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        existente = crud.get_by_nome(db, args.nome)
        if existente:
            from app.schemas.usuario import UsuarioUpdate

            crud.atualizar(
                db,
                existente,
                UsuarioUpdate(
                    papel=PapelUsuario.admin, senha=args.senha, ativo=True
                ),
            )
            print(f"Usuario {args.nome} atualizado para admin.")
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
        print(f"Admin {args.nome} criado.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
