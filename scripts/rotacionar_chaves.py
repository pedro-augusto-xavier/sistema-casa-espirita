"""Recifra tudo com a chave ATIVA (a primeira de CHAVES_CRIPTOGRAFIA).

Quando usar: depois de pôr uma chave nova na frente da lista (ver
docs/SEGURANCA.md, "Se a chave vazar"). Enquanto houver dado cifrado com a
chave antiga, ela não pode sair da lista.

Uso:
    python -m scripts.rotacionar_chaves              # só mostra o que falta
    python -m scripts.rotacionar_chaves --executar   # recifra de verdade
    python -m scripts.rotacionar_chaves --executar --recalcular-hash
        (--recalcular-hash: depois de trocar a CHAVE_HMAC)

Em produção, rode com a DATABASE_URL e as chaves do Render no ambiente
(numa linha só, sem salvar em arquivo).
"""

import argparse
from collections import Counter

from sqlalchemy import column, select, table, text, update
from sqlalchemy.orm import Session

from app.core import cripto
from app.core.database import SessionLocal

# (tabela, coluna, contexto) -- tudo que é cifrado no banco
COLUNAS_CIFRADAS = [
    ("pessoa", "cpf_cifrado", "pessoa.cpf"),
    ("pessoa", "observacoes_gerais", "pessoa.observacoes_gerais"),
    ("atendimento", "observacao", "atendimento.observacao"),
    ("atendimento_tratamento", "observacao", "atendimento_tratamento.observacao"),
    ("tratamento", "situacao_final", "tratamento.situacao_final"),
    ("tratamento", "observacao", "tratamento.observacao"),
    ("tratamento_assistido", "situacao_final", "tratamento_assistido.situacao_final"),
    ("tratamento_evolucao", "texto", "tratamento_evolucao.texto"),
    ("anexo", "conteudo", "anexo.conteudo"),
    ("usuario", "mfa_segredo", "usuario.mfa_segredo"),
]


def rotacionar(
    db: Session, *, executar: bool, recalcular_hash: bool = False
) -> dict[str, Counter]:
    """Devolve, por coluna, quantos valores estavam em cada id de chave."""
    ativa = cripto.id_chave_ativa()
    relatorio: dict[str, Counter] = {}

    for nome_tabela, coluna, contexto in COLUNAS_CIFRADAS:
        # SQL montado pelo SQLAlchemy (sem juntar texto), um arquivo por vez
        t = table(nome_tabela, column("id"), column(coluna))
        valor = t.c[coluna]
        contagem: Counter = Counter()
        ids = db.execute(
            select(t.c.id).where(valor.is_not(None)).order_by(t.c.id)
        ).scalars().all()
        for id_ in ids:
            blob = bytes(db.execute(select(valor).where(t.c.id == id_)).scalar_one())
            contagem[cripto.id_da_chave(blob)] += 1
            if executar and cripto.id_da_chave(blob) != ativa:
                novo = cripto.cifrar(cripto.decifrar(blob, contexto), contexto)
                db.execute(update(t).where(t.c.id == id_).values({coluna: novo}))
        relatorio[f"{nome_tabela}.{coluna}"] = contagem

    if executar and recalcular_hash:
        for id_, cifrado in db.execute(
            text("SELECT id, cpf_cifrado FROM pessoa WHERE cpf_cifrado IS NOT NULL")
        ).all():
            cpf = cripto.decifrar(bytes(cifrado), "pessoa.cpf").decode()
            db.execute(
                text("UPDATE pessoa SET cpf_hash = :h WHERE id = :id"),
                {"h": cripto.hmac_busca(cpf), "id": id_},
            )

    if executar:
        db.commit()
    return relatorio


def main() -> None:
    parser = argparse.ArgumentParser(description="Recifra os dados com a chave ativa")
    parser.add_argument("--executar", action="store_true")
    parser.add_argument("--recalcular-hash", action="store_true")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        relatorio = rotacionar(
            db, executar=args.executar, recalcular_hash=args.recalcular_hash
        )
    finally:
        db.close()

    ativa = cripto.id_chave_ativa()
    print(f"Chave ativa: {ativa}\n")
    for coluna, contagem in relatorio.items():
        resumo = ", ".join(f"chave {k}: {v}" for k, v in sorted(contagem.items()))
        print(f"  {coluna:45} {resumo or '(vazio)'}")
    if not args.executar:
        print("\nNada foi alterado. Rode com --executar pra recifrar.")
    else:
        print("\nPronto. Confira de novo (sem --executar):")
        print("tudo deve estar na chave ativa.")


if __name__ == "__main__":
    main()
