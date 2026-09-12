"""Acesso ao banco para Tratamento (o caso longo) e seus filhos."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import ErroDominio, NaoEncontrado
from app.models.enums import StatusTratamento
from app.models.pessoa import Pessoa
from app.models.tratamento import (
    TipoTratamento,
    Tratamento,
    TratamentoAssistido,
    TratamentoEvolucao,
)
from app.schemas.tratamento import (
    AssistidoIn,
    AssistidoUpdate,
    EvolucaoIn,
    EvolucaoUpdate,
    TratamentoCreate,
    TratamentoUpdate,
)

_CARREGAR_TUDO = (
    selectinload(Tratamento.tipo),
    selectinload(Tratamento.solicitante),
    selectinload(Tratamento.assistidos)
    .selectinload(TratamentoAssistido.pessoa)
    .selectinload(Pessoa.papeis),
    selectinload(Tratamento.evolucoes).selectinload(TratamentoEvolucao.registrado_por),
    selectinload(Tratamento.evolucoes).selectinload(TratamentoEvolucao.pessoa),
)


def _pessoa_ou_erro(db: Session, pessoa_id: int, campo: str) -> None:
    if db.get(Pessoa, pessoa_id) is None:
        raise NaoEncontrado(f"{campo}: pessoa {pessoa_id} não existe")


def get(db: Session, tratamento_id: int) -> Tratamento | None:
    stmt = (
        select(Tratamento)
        .options(*_CARREGAR_TUDO)
        .where(Tratamento.id == tratamento_id)
    )
    return db.scalar(stmt)


def listar(
    db: Session,
    *,
    status: StatusTratamento | None = None,
    tipo_tratamento_id: int | None = None,
    pessoa_id: int | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Tratamento], int]:
    stmt = select(Tratamento).options(*_CARREGAR_TUDO)

    if status is not None:
        stmt = stmt.where(Tratamento.status == status)
    if tipo_tratamento_id is not None:
        stmt = stmt.where(Tratamento.tipo_tratamento_id == tipo_tratamento_id)
    if pessoa_id is not None:
        stmt = stmt.where(
            Tratamento.assistidos.any(TratamentoAssistido.pessoa_id == pessoa_id)
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = (
        stmt.order_by(Tratamento.data_inicio.desc(), Tratamento.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(db.scalars(stmt).all()), total


def criar(db: Session, dados: TratamentoCreate) -> Tratamento:
    if db.get(TipoTratamento, dados.tipo_tratamento_id) is None:
        raise NaoEncontrado(
            f"tipo de tratamento {dados.tipo_tratamento_id} não existe"
        )
    if dados.solicitante_id is not None:
        _pessoa_ou_erro(db, dados.solicitante_id, "solicitante_id")

    tratamento = Tratamento(
        tipo_tratamento_id=dados.tipo_tratamento_id,
        solicitante_id=dados.solicitante_id,
        sessoes_previstas=dados.sessoes_previstas,
        observacao=dados.observacao,
    )
    if dados.data_inicio is not None:
        tratamento.data_inicio = dados.data_inicio

    vistos: set[int] = set()
    for item in dados.assistidos:
        if item.pessoa_id in vistos:
            continue
        _pessoa_ou_erro(db, item.pessoa_id, "assistidos")
        tratamento.assistidos.append(TratamentoAssistido(pessoa_id=item.pessoa_id))
        vistos.add(item.pessoa_id)

    db.add(tratamento)
    db.commit()
    return get(db, tratamento.id)  # type: ignore[return-value]


def atualizar(
    db: Session, tratamento: Tratamento, dados: TratamentoUpdate
) -> Tratamento:
    mudancas = dados.model_dump(exclude_unset=True)
    if "solicitante_id" in mudancas and mudancas["solicitante_id"] is not None:
        _pessoa_ou_erro(db, mudancas["solicitante_id"], "solicitante_id")

    for campo, valor in mudancas.items():
        setattr(tratamento, campo, valor)

    db.commit()
    return get(db, tratamento.id)  # type: ignore[return-value]


def remover(db: Session, tratamento: Tratamento) -> None:
    db.delete(tratamento)
    db.commit()


# ---------- assistidos ----------


def get_assistido(
    db: Session, tratamento_id: int, assistido_id: int
) -> TratamentoAssistido | None:
    stmt = select(TratamentoAssistido).where(
        TratamentoAssistido.id == assistido_id,
        TratamentoAssistido.tratamento_id == tratamento_id,
    )
    return db.scalar(stmt)


def adicionar_assistido(
    db: Session, tratamento: Tratamento, dados: AssistidoIn
) -> Tratamento:
    _pessoa_ou_erro(db, dados.pessoa_id, "pessoa_id")
    ja_tem = any(a.pessoa_id == dados.pessoa_id for a in tratamento.assistidos)
    if ja_tem:
        raise ErroDominio("essa pessoa já é assistida neste tratamento")
    db.add(
        TratamentoAssistido(
            tratamento_id=tratamento.id, pessoa_id=dados.pessoa_id
        )
    )
    db.commit()
    return get(db, tratamento.id)  # type: ignore[return-value]


def atualizar_assistido(
    db: Session, assistido: TratamentoAssistido, dados: AssistidoUpdate
) -> Tratamento:
    for campo, valor in dados.model_dump(exclude_unset=True).items():
        setattr(assistido, campo, valor)
    db.commit()
    return get(db, assistido.tratamento_id)  # type: ignore[return-value]


def remover_assistido(db: Session, assistido: TratamentoAssistido) -> None:
    db.delete(assistido)
    db.commit()


# ---------- evolução ----------


def get_evolucao(
    db: Session, tratamento_id: int, evolucao_id: int
) -> TratamentoEvolucao | None:
    stmt = select(TratamentoEvolucao).where(
        TratamentoEvolucao.id == evolucao_id,
        TratamentoEvolucao.tratamento_id == tratamento_id,
    )
    return db.scalar(stmt)


def adicionar_evolucao(
    db: Session, tratamento: Tratamento, dados: EvolucaoIn
) -> Tratamento:
    if dados.registrado_por_id is not None:
        _pessoa_ou_erro(db, dados.registrado_por_id, "registrado_por_id")
    if dados.pessoa_id is not None:
        _pessoa_ou_erro(db, dados.pessoa_id, "pessoa_id")

    evolucao = TratamentoEvolucao(
        tratamento_id=tratamento.id,
        texto=dados.texto,
        registrado_por_id=dados.registrado_por_id,
        pessoa_id=dados.pessoa_id,
    )
    if dados.data is not None:
        evolucao.data = dados.data

    db.add(evolucao)
    db.commit()
    return get(db, tratamento.id)  # type: ignore[return-value]


def atualizar_evolucao(
    db: Session, evolucao: TratamentoEvolucao, dados: EvolucaoUpdate
) -> Tratamento:
    mudancas = dados.model_dump(exclude_unset=True)
    for campo in ("registrado_por_id", "pessoa_id"):
        if campo in mudancas and mudancas[campo] is not None:
            _pessoa_ou_erro(db, mudancas[campo], campo)
    for campo, valor in mudancas.items():
        setattr(evolucao, campo, valor)
    db.commit()
    return get(db, evolucao.tratamento_id)  # type: ignore[return-value]


def remover_evolucao(db: Session, evolucao: TratamentoEvolucao) -> None:
    db.delete(evolucao)
    db.commit()


# ---------- histórico da pessoa ----------


def historico_pessoa(db: Session, pessoa_id: int) -> list[dict]:
    """Linha do tempo: atendimentos + inícios de caso + evoluções + grupos.

    `detalhes` carrega os campos completos de cada tipo, pra tela mostrar
    tudo direto (sem precisar abrir um modal só pra ler).
    """
    from app.models.atendimento import Atendimento, AtendimentoTratamento
    from app.models.grupo import Presenca, SessaoGrupo

    itens: list[dict] = []

    atendimentos = db.scalars(
        select(Atendimento)
        .options(
            selectinload(Atendimento.atendido_por),
            selectinload(Atendimento.solicitante),
            selectinload(Atendimento.tratamentos).selectinload(
                AtendimentoTratamento.tipo_tratamento
            ),
        )
        .where(Atendimento.pessoa_id == pessoa_id)
    ).all()
    for a in atendimentos:
        nomes = ", ".join(a.tratamentos_resumo) or "sem tratamento registrado"
        quem = a.atendido_por.nome_completo if a.atendido_por else None
        itens.append(
            {
                "tipo": "atendimento",
                "data": a.data,
                "titulo": f"Atendimento ({a.modalidade.value})",
                "descricao": f"{nomes}. Atendido por: {quem or '—'}.",
                "atendimento_id": a.id,
                "tratamento_id": None,
                "grupo_id": None,
                "detalhes": {
                    "modalidade": a.modalidade.value,
                    "presente": a.presente,
                    "atendido_por": quem,
                    "solicitante": (
                        a.solicitante.nome_completo if a.solicitante else None
                    ),
                    "observacao": a.observacao,
                    "tratamentos": [
                        {
                            "nome": t.tipo_tratamento.nome,
                            "modalidade": t.modalidade.value if t.modalidade else None,
                            "sessoes_previstas": t.sessoes_previstas,
                            "sessoes_realizadas": t.sessoes_realizadas,
                            "observacao": t.observacao,
                        }
                        for t in a.tratamentos
                    ],
                },
            }
        )

    casos = db.scalars(
        select(Tratamento)
        .options(
            selectinload(Tratamento.tipo), selectinload(Tratamento.solicitante)
        )
        .where(
            Tratamento.assistidos.any(
                TratamentoAssistido.pessoa_id == pessoa_id
            )
        )
    ).all()
    for t in casos:
        itens.append(
            {
                "tipo": "tratamento_inicio",
                "data": t.data_inicio,
                "titulo": f"Início de tratamento: {t.tipo.nome}",
                "descricao": t.observacao,
                "atendimento_id": None,
                "tratamento_id": t.id,
                "grupo_id": None,
                "detalhes": {
                    "tipo_nome": t.tipo.nome,
                    "solicitante": (
                        t.solicitante.nome_completo if t.solicitante else None
                    ),
                    "sessoes_previstas": t.sessoes_previstas,
                    "status": t.status.value,
                    "observacao": t.observacao,
                },
            }
        )

    evolucoes = db.scalars(
        select(TratamentoEvolucao)
        .options(
            selectinload(TratamentoEvolucao.tratamento).selectinload(Tratamento.tipo),
            selectinload(TratamentoEvolucao.registrado_por),
        )
        .where(TratamentoEvolucao.pessoa_id == pessoa_id)
    ).all()
    for e in evolucoes:
        itens.append(
            {
                "tipo": "evolucao",
                "data": e.data,
                "titulo": "Evolução do tratamento",
                "descricao": e.texto,
                "atendimento_id": None,
                "tratamento_id": e.tratamento_id,
                "grupo_id": None,
                "detalhes": {
                    "tipo_nome": e.tratamento.tipo.nome,
                    "texto": e.texto,
                    "registrado_por": (
                        e.registrado_por.nome_completo if e.registrado_por else None
                    ),
                },
            }
        )

    sessoes = db.scalars(
        select(SessaoGrupo)
        .options(
            selectinload(SessaoGrupo.tipo_tratamento),
            selectinload(SessaoGrupo.responsavel),
        )
        .where(SessaoGrupo.presencas.any(Presenca.pessoa_id == pessoa_id))
    ).all()
    for s in sessoes:
        itens.append(
            {
                "tipo": "grupo",
                "data": s.data,
                "titulo": f"Grupo: {s.tipo_tratamento.nome}",
                "descricao": s.observacao,
                "atendimento_id": None,
                "tratamento_id": None,
                "grupo_id": s.id,
                "detalhes": {
                    "tipo_nome": s.tipo_tratamento.nome,
                    "responsavel": (
                        s.responsavel.nome_completo if s.responsavel else None
                    ),
                    "observacao": s.observacao,
                },
            }
        )

    itens.sort(key=lambda i: i["data"], reverse=True)
    return itens
