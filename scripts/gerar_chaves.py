"""Gera as chaves secretas que o servidor precisa (copiar pro Render).

Uso (primeira vez):
    python -m scripts.gerar_chaves

Uso (trocar a chave de criptografia -- rotação):
    python -m scripts.gerar_chaves --rotacao 2

Imprime na tela -- NÃO salva em arquivo nenhum. Copie cada valor pro painel
do Render (Environment) e feche o terminal. Essas chaves nunca vão pro Git.
"""

import argparse
import base64
import secrets


def _chave_b64() -> str:
    return base64.b64encode(secrets.token_bytes(32)).decode()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--rotacao",
        type=int,
        metavar="ID",
        help="gera só uma chave nova de criptografia com esse id (2, 3...)",
    )
    args = parser.parse_args()

    if args.rotacao:
        print("Nova chave de criptografia. No Render, ponha ela NA FRENTE da atual,")
        print("separada por vírgula (a primeira é a que cifra; as outras só leem):\n")
        print(f"    CHAVES_CRIPTOGRAFIA={args.rotacao}:{_chave_b64()},<valor atual>\n")
        print("Depois do deploy, rode: python -m scripts.rotacionar_chaves --executar")
        print("e só então tire a chave antiga da lista.")
        return

    print("Copie cada linha pro Render > Environment (uma variável por linha):\n")
    print(f"CHAVES_CRIPTOGRAFIA=1:{_chave_b64()}")
    print(f"CHAVE_HMAC={_chave_b64()}")
    print("\nGuarde uma cópia num lugar seguro FORA do computador (ex: gerenciador")
    print("de senhas). Sem a CHAVES_CRIPTOGRAFIA, os CPFs, observações e anexos")
    print("do banco -- e dos backups -- ficam ilegíveis pra sempre.")


if __name__ == "__main__":
    main()
