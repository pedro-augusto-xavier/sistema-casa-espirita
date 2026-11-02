"""Cria (ou recupera) um usuário administrador -- é a "chave mestra" pra
quando ninguém mais consegue entrar.

Uso:
    python -m scripts.criar_admin --nome "Tia Fulana" --senha "trocar123" \
        [--email tia@casa.org] [--resetar-mfa]

Login no sistema é pelo nome -- se já existir um usuário ativo com esse
nome, só atualiza (vira admin, troca a senha, garante que está ativo e
encerra as sessões abertas). E-mail é opcional, só um contato.

A senha definida aqui é PROVISÓRIA: no próximo login a pessoa cria a dela.
--resetar-mfa: zera a verificação em duas etapas (celular perdido) -- no
próximo login o sistema pede pra configurar de novo.
"""

import argparse

from app.core.database import SessionLocal
from app.crud import sessao as crud_sessao
from app.crud import usuario as crud
from app.models.enums import PapelUsuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria um usuário administrador")
    parser.add_argument("--nome", required=True)
    parser.add_argument("--senha", required=True)
    parser.add_argument("--email", default=None)
    parser.add_argument("--resetar-mfa", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        existente = crud.get_by_nome(db, args.nome)
        if existente:
            crud.atualizar(
                db,
                existente,
                UsuarioUpdate(papel=PapelUsuario.admin, senha=args.senha, ativo=True),
            )
            if args.resetar_mfa:
                crud.zerar_mfa(db, existente)
            crud_sessao.revogar_todas(db, existente.id)
            print(f"Usuario {args.nome} atualizado para admin (senha provisoria).")
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
        print(f"Admin {args.nome} criado (senha provisoria).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
