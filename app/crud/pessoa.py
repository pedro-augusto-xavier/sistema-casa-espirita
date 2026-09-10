"""Acesso ao banco para Pessoa. As rotas chamam estas funções -- assim a
lógica de banco fica separada da lógica HTTP e dá pra testar isolado.
"""

from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.validators import so_digitos
from app.models.enums import Papel
from app.models.pessoa import Pessoa, PessoaPapel
from app.schemas.pessoa import PessoaCreate, PessoaUpdate


def get(db: Session, pessoa_id: int) -> Pessoa | None:
    stmt = (
        select(Pessoa)
        .options(selectinload(Pessoa.papeis))
        .where(Pessoa.id == pessoa_id)
    )
    return db.scalar(stmt)


def get_by_cpf(db: Session, cpf: str) -> Pessoa | None:
    return db.scalar(select(Pessoa).where(Pessoa.cpf == so_digitos(cpf)))


def listar(
    db: Session,
    *,
    q: str | None = None,
    papel: Papel | None = None,
    apenas_ativos: bool = True,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Pessoa], int]:
    stmt = select(Pessoa).options(selectinload(Pessoa.papeis))

    if apenas_ativos:
        stmt = stmt.where(Pessoa.ativo.is_(True))

    if q:
        termo = f"%{q.strip()}%"
        condicoes = [
            Pessoa.nome_completo.ilike(termo),
            Pessoa.telefone.ilike(termo),
        ]
        digitos = so_digitos(q)
        if digitos:
            condicoes.append(Pessoa.cpf.ilike(f"%{digitos}%"))
        stmt = stmt.where(or_(*condicoes))

    if papel is not None:
        stmt = stmt.where(Pessoa.papeis.any(PessoaPapel.papel == papel))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = (
        stmt.order_by(Pessoa.nome_completo)
        .offset((page - 1) * size)
        .limit(size)
    )
    pessoas = list(db.scalars(stmt).all())
    return pessoas, total


def _aplica_papeis(pessoa: Pessoa, papeis: list[Papel]) -> None:
    desejados = set(papeis)
    atuais = {p.papel for p in pessoa.papeis}

    for pp in list(pessoa.papeis):
        if pp.papel not in desejados:
            pessoa.papeis.remove(pp)
    for papel in desejados - atuais:
        pessoa.papeis.append(PessoaPapel(papel=papel))


def criar(db: Session, dados: PessoaCreate) -> Pessoa:
    payload = dados.model_dump(exclude={"papeis"})
    pessoa = Pessoa(**payload)

    if dados.consentimento_lgpd:
        pessoa.consentimento_em = datetime.now(UTC)

    _aplica_papeis(pessoa, dados.papeis)

    db.add(pessoa)
    db.commit()
    db.refresh(pessoa)
    return get(db, pessoa.id)  # type: ignore[return-value]


def atualizar(db: Session, pessoa: Pessoa, dados: PessoaUpdate) -> Pessoa:
    mudancas = dados.model_dump(exclude_unset=True, exclude={"papeis"})

    if "consentimento_lgpd" in mudancas:
        novo = mudancas["consentimento_lgpd"]
        if novo and not pessoa.consentimento_lgpd:
            pessoa.consentimento_em = datetime.now(UTC)
        elif not novo:
            pessoa.consentimento_em = None

    for campo, valor in mudancas.items():
        setattr(pessoa, campo, valor)

    if dados.papeis is not None:
        _aplica_papeis(pessoa, dados.papeis)

    db.commit()
    db.refresh(pessoa)
    return get(db, pessoa.id)  # type: ignore[return-value]


def desativar(db: Session, pessoa: Pessoa) -> None:
    """Exclusão lógica -- a ficha continua no banco, só sai das listas."""
    pessoa.ativo = False
    db.commit()


_CAMPOS_PESSOAIS = (
    "cpf",
    "telefone",
    "data_nascimento",
    "logradouro",
    "numero",
    "complemento",
    "bairro",
    "cidade",
    "uf",
    "cep",
    "como_conheceu",
    "observacoes_gerais",
)


def anonimizar(db: Session, pessoa: Pessoa) -> Pessoa:
    """LGPD -- direito ao esquecimento.

    Apaga os dados pessoais mas mantém a linha (e os vínculos com atendimentos)
    para o histórico não ficar órfão.
    """
    pessoa.nome_completo = "(dados removidos)"
    for campo in _CAMPOS_PESSOAIS:
        setattr(pessoa, campo, None)
    pessoa.anonimizada = True
    pessoa.ativo = False
    pessoa.consentimento_lgpd = False
    pessoa.consentimento_em = None
    pessoa.papeis.clear()
    db.commit()
    return get(db, pessoa.id)  # type: ignore[return-value]


def exportar_dados(db: Session, pessoa_id: int) -> dict:
    """Reúne tudo que o sistema guarda sobre a pessoa (direito de acesso)."""
    from app.models.atendimento import Atendimento
    from app.models.tratamento import TratamentoAssistido, TratamentoEvolucao

    pessoa = get(db, pessoa_id)
    if pessoa is None:
        return {}

    atendimentos = db.scalars(
        select(Atendimento)
        .options(selectinload(Atendimento.tratamentos))
        .where(Atendimento.pessoa_id == pessoa_id)
    ).all()

    participacoes = db.scalars(
        select(TratamentoAssistido).where(
            TratamentoAssistido.pessoa_id == pessoa_id
        )
    ).all()

    evolucoes = db.scalars(
        select(TratamentoEvolucao).where(
            TratamentoEvolucao.pessoa_id == pessoa_id
        )
    ).all()

    def _dict(obj, campos):
        return {c: getattr(obj, c) for c in campos}

    return {
        "pessoa": _dict(
            pessoa,
            [
                "id",
                "nome_completo",
                "data_nascimento",
                "sexo",
                "cpf",
                "telefone",
                "logradouro",
                "numero",
                "complemento",
                "bairro",
                "cidade",
                "uf",
                "cep",
                "como_conheceu",
                "observacoes_gerais",
                "consentimento_lgpd",
                "consentimento_em",
                "ativo",
                "anonimizada",
                "criado_em",
                "atualizado_em",
            ],
        ),
        "papeis": [p.papel.value for p in pessoa.papeis],
        "atendimentos": [
            {
                **_dict(
                    a,
                    [
                        "id",
                        "data",
                        "modalidade",
                        "presente",
                        "ordem_chegada",
                        "observacao",
                        "retorno_previsto",
                    ],
                ),
                "tratamentos": [t.tipo_tratamento_nome for t in a.tratamentos],
            }
            for a in atendimentos
        ],
        "tratamentos_como_assistido": [
            _dict(
                p,
                [
                    "id",
                    "tratamento_id",
                    "status",
                    "situacao_final",
                    "data_conclusao",
                ],
            )
            for p in participacoes
        ],
        "evolucoes": [
            _dict(e, ["id", "tratamento_id", "data", "texto"]) for e in evolucoes
        ],
    }


def reativar(db: Session, pessoa: Pessoa) -> Pessoa:
    pessoa.ativo = True
    db.commit()
    db.refresh(pessoa)
    return get(db, pessoa.id)  # type: ignore[return-value]
