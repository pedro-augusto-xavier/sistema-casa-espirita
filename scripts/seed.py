"""Popula as listas de referência (tipos de tratamento e funções).

Rodar:
    python -m scripts.seed

É seguro rodar várias vezes -- só insere o que ainda não existe.
"""

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.enums import FormatoTratamento
from app.models.trabalhador import FuncaoTrabalhador
from app.models.tratamento import TipoTratamento

TIPOS_TRATAMENTO = [
    ("Reflexologia", FormatoTratamento.individual),
    ("Energização", FormatoTratamento.individual),
    ("Ectoplasmia Presencial", FormatoTratamento.individual),
    ("Conversa Fraterna", FormatoTratamento.individual),
    ("Ambulatório", FormatoTratamento.individual),
    ("Grupo Despertar", FormatoTratamento.grupo),
    ("Grupo de Estudos Aberto", FormatoTratamento.grupo),
    ("Desobsessão Presencial", FormatoTratamento.caso),
    ("Desobsessão à Distância", FormatoTratamento.caso),
    ("Ectoplasmia à Distância", FormatoTratamento.caso),
]

FUNCOES = [
    "Médium",
    "Passista",
    "Dirigente",
    "Palestrante",
    "Recepção",
    "Limpeza",
    "Apoio",
    "Cambone",
]


def run() -> None:
    db = SessionLocal()
    try:
        for nome, formato in TIPOS_TRATAMENTO:
            existe = db.scalar(
                select(TipoTratamento).where(TipoTratamento.nome == nome)
            )
            if not existe:
                db.add(TipoTratamento(nome=nome, formato=formato))
                print(f"+ tipo_tratamento: {nome}")

        for nome in FUNCOES:
            existe = db.scalar(
                select(FuncaoTrabalhador).where(FuncaoTrabalhador.nome == nome)
            )
            if not existe:
                db.add(FuncaoTrabalhador(nome=nome))
                print(f"+ funcao_trabalhador: {nome}")

        db.commit()
        print("Seed concluído.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
