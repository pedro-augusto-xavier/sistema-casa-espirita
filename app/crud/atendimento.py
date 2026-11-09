"""Acesso ao banco para Atendimento (a visita avulsa)."""

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.errors import NaoEncontrado
from app.crud.anexo import remover_ligados as remover_anexos_ligados
from app.crud.pessoa import alguma_anonimizada, exigir_nao_anonimizada
from app.models.atendimento import Atendimento, AtendimentoTratamento
from app.models.enums import FormatoTratamento, StatusTratamento, TipoVinculo
from app.models.pessoa import Pessoa
from app.models.tratamento import TipoTratamento, Tratamento, TratamentoAssistido
from app.schemas.atendimento import (
    AtendimentoCreate,
    AtendimentoTratamentoIn,
    AtendimentoUpdate,
)

_CARREGAR_TUDO = (
    selectinload(Atendimento.pessoa).selectinload(Pessoa.papeis),
    selectinload(Atendimento.atendido_por),
    selectinload(Atendimento.solicitante),
    selectinload(Atendimento.tratamentos).selectinload(
        AtendimentoTratamento.tipo_tratamento
    ),
)


def get(db: Session, atendimento_id: int) -> Atendimento | None:
    stmt = (
        select(Atendimento)
        .options(*_CARREGAR_TUDO)
        .where(Atendimento.id == atendimento_id)
    )
    return db.scalar(stmt)


def listar(
    db: Session,
    *,
    pessoa_id: int | None = None,
    atendido_por_id: int | None = None,
    de: date | None = None,
    ate: date | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Atendimento], int]:
    stmt = select(Atendimento).options(*_CARREGAR_TUDO)

    if pessoa_id is not None:
        stmt = stmt.where(Atendimento.pessoa_id == pessoa_id)
    if atendido_por_id is not None:
        stmt = stmt.where(Atendimento.atendido_por_id == atendido_por_id)
    if de is not None:
        stmt = stmt.where(Atendimento.data >= de)
    if ate is not None:
        stmt = stmt.where(Atendimento.data <= ate)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = (
        stmt.order_by(Atendimento.data.desc(), Atendimento.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(db.scalars(stmt).all()), total


def _checa_pessoa(db: Session, pessoa_id: int | None, campo: str) -> None:
    if pessoa_id is None:
        return
    pessoa = db.get(Pessoa, pessoa_id)
    if pessoa is None:
        raise NaoEncontrado(f"{campo}: pessoa {pessoa_id} não existe")
    exigir_nao_anonimizada(pessoa, campo)


def ligado_a_anonimizada(db: Session, atendimento: Atendimento) -> bool:
    return alguma_anonimizada(
        db,
        (
            atendimento.pessoa_id,
            atendimento.atendido_por_id,
            atendimento.solicitante_id,
        ),
    )


def _monta_tratamentos(
    db: Session, itens: list[AtendimentoTratamentoIn]
) -> list[AtendimentoTratamento]:
    ids = {i.tipo_tratamento_id for i in itens}
    existentes = set(
        db.scalars(
            select(TipoTratamento.id).where(TipoTratamento.id.in_(ids))
        ).all()
    )
    faltando = ids - existentes
    if faltando:
        raise NaoEncontrado(
            f"tipo(s) de tratamento inexistente(s): {sorted(faltando)}"
        )
    return [
        AtendimentoTratamento(
            tipo_tratamento_id=i.tipo_tratamento_id,
            modalidade=i.modalidade,
            sessoes_previstas=i.sessoes_previstas,
            sessoes_realizadas=i.sessoes_realizadas,
            observacao=i.observacao,
        )
        for i in itens
    ]


@dataclass
class MudancaNoCaso:
    """O que o atendimento fez num caso, pra rota registrar na auditoria com
    entidade="tratamento" (como fazem as rotas de /tratamentos)."""

    caso: Tratamento
    aberto_agora: bool = False
    assistidos_adicionados: list[int] = field(default_factory=list)
    sessoes_previstas_preenchidas: bool = False


def _abre_fichas_de_acompanhamento(
    db: Session, dados: AtendimentoCreate, itens: list[AtendimentoTratamentoIn]
) -> list[MudancaNoCaso]:
    """Tratamentos de formato "caso" (Desobsessão etc.) têm uma pasta própria:
    na capa, o Responsável (quem vem à casa receber o tratamento) e os
    Assistidos (por quem ele pediu -- filhos, amigos, ele mesmo); dentro,
    nº de vezes, diário e situação final.

    Quando um deles é marcado no atendimento, a pessoa atendida vira o
    responsável. Se ela ainda não tem a pasta aberta, abrimos uma; se já
    tem, só acrescentamos assistidos novos e completamos o nº de vezes."""
    mudancas: list[MudancaNoCaso] = []
    if not itens:
        return mudancas
    tipos_caso = set(
        db.scalars(
            select(TipoTratamento.id).where(
                TipoTratamento.id.in_({i.tipo_tratamento_id for i in itens}),
                TipoTratamento.formato == FormatoTratamento.caso,
            )
        ).all()
    )
    for item in itens:
        if item.tipo_tratamento_id not in tipos_caso:
            continue

        # dedup por pessoa, mantendo o primeiro vínculo informado pra ela
        vinculos: dict[int, TipoVinculo | None] = {}
        for ref in item.assistidos:
            vinculos.setdefault(ref.pessoa_id, ref.vinculo_com_responsavel)
        if not vinculos:
            vinculos[dados.pessoa_id] = None
        elif dados.pessoa_id in vinculos:
            vinculos[dados.pessoa_id] = None  # não tem vínculo consigo mesma
        for pessoa_id in vinculos:
            _checa_pessoa(db, pessoa_id, "assistidos")

        aberto = db.scalar(
            select(Tratamento).where(
                Tratamento.tipo_tratamento_id == item.tipo_tratamento_id,
                Tratamento.status == StatusTratamento.em_andamento,
                (Tratamento.solicitante_id == dados.pessoa_id)
                | Tratamento.assistidos.any(
                    TratamentoAssistido.pessoa_id == dados.pessoa_id
                ),
            )
        )
        if aberto is not None:
            mudanca = MudancaNoCaso(caso=aberto)
            if aberto.sessoes_previstas is None and item.sessoes_previstas:
                aberto.sessoes_previstas = item.sessoes_previstas
                mudanca.sessoes_previstas_preenchidas = True
            ja_tem = {a.pessoa_id for a in aberto.assistidos}
            for pessoa_id in vinculos:
                if pessoa_id not in ja_tem:
                    aberto.assistidos.append(
                        TratamentoAssistido(
                            pessoa_id=pessoa_id,
                            vinculo_com_responsavel=vinculos[pessoa_id],
                        )
                    )
                    mudanca.assistidos_adicionados.append(pessoa_id)
            if mudanca.sessoes_previstas_preenchidas or mudanca.assistidos_adicionados:
                mudancas.append(mudanca)
            continue

        ficha = Tratamento(
            tipo_tratamento_id=item.tipo_tratamento_id,
            solicitante_id=dados.pessoa_id,  # o responsável é quem foi atendido
            sessoes_previstas=item.sessoes_previstas,
            observacao=item.observacao,
            assistidos=[
                TratamentoAssistido(
                    pessoa_id=pessoa_id, vinculo_com_responsavel=vinculo
                )
                for pessoa_id, vinculo in vinculos.items()
            ],
        )
        if dados.data is not None:
            ficha.data_inicio = dados.data
        db.add(ficha)
        mudancas.append(MudancaNoCaso(caso=ficha, aberto_agora=True))
    return mudancas


def criar(
    db: Session, dados: AtendimentoCreate
) -> tuple[Atendimento, list[MudancaNoCaso]]:
    _checa_pessoa(db, dados.pessoa_id, "pessoa_id")
    _checa_pessoa(db, dados.atendido_por_id, "atendido_por_id")
    _checa_pessoa(db, dados.solicitante_id, "solicitante_id")

    payload = dados.model_dump(exclude={"tratamentos", "data"})
    atendimento = Atendimento(**payload)
    if dados.data is not None:
        atendimento.data = dados.data

    atendimento.tratamentos = _monta_tratamentos(db, dados.tratamentos)
    casos = _abre_fichas_de_acompanhamento(db, dados, dados.tratamentos)

    db.add(atendimento)
    db.commit()
    return get(db, atendimento.id), casos  # type: ignore[return-value]


def _acompanha_inicio_dos_casos(
    db: Session, atendimento: Atendimento, data_antiga: date
) -> list[int]:
    """Corrigir a data do atendimento que abriu um caso corrige o início do
    caso junto: o caso nasce com a data dele (_abre_fichas_de_acompanhamento)
    e o nº de vezes só conta atendimentos a partir do início -- sem isso, o
    atendimento que abriu o caso podia ficar antes dele e deixar de contar.
    Devolve os ids dos casos mexidos, pra rota registrar na auditoria."""
    tipos = [t.tipo_tratamento_id for t in atendimento.tratamentos]
    if not tipos:
        return []
    casos = db.scalars(
        select(Tratamento).where(
            Tratamento.solicitante_id == atendimento.pessoa_id,
            Tratamento.tipo_tratamento_id.in_(tipos),
            Tratamento.data_inicio == data_antiga,
        )
    ).all()
    for caso in casos:
        caso.data_inicio = atendimento.data
    return [caso.id for caso in casos]


def atualizar(
    db: Session, atendimento: Atendimento, dados: AtendimentoUpdate
) -> tuple[Atendimento, list[int]]:
    data_antiga = atendimento.data
    mudancas = dados.model_dump(exclude_unset=True, exclude={"tratamentos"})

    for campo in ("atendido_por_id", "solicitante_id"):
        # só confere vínculo NOVO: reenviar o mesmo valor (a tela manda tudo)
        # não pode travar a edição de um registro antigo
        if campo in mudancas and mudancas[campo] != getattr(atendimento, campo):
            _checa_pessoa(db, mudancas[campo], campo)

    for campo, valor in mudancas.items():
        setattr(atendimento, campo, valor)

    if dados.tratamentos is not None:
        atendimento.tratamentos = _monta_tratamentos(db, dados.tratamentos)

    casos_movidos: list[int] = []
    if atendimento.data != data_antiga:
        casos_movidos = _acompanha_inicio_dos_casos(db, atendimento, data_antiga)

    db.commit()
    return get(db, atendimento.id), casos_movidos  # type: ignore[return-value]


def remover(db: Session, atendimento: Atendimento) -> list[tuple[int, int]]:
    """Devolve (id, pessoa_id) dos anexos apagados junto, pra auditoria."""
    anexos = remover_anexos_ligados(db, atendimento_id=atendimento.id)
    db.delete(atendimento)
    db.commit()
    return anexos
