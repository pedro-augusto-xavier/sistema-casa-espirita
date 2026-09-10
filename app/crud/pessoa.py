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


def reativar(db: Session, pessoa: Pessoa) -> Pessoa:
    pessoa.ativo = True
    db.commit()
    db.refresh(pessoa)
    return get(db, pessoa.id)  # type: ignore[return-value]
