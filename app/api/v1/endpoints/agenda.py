"""Rotas de Agenda: /api/v1/agenda"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.deps import SessaoDB, UsuarioAtual
from app.core.auditoria import registrar
from app.crud import agenda as crud
from app.models.enums import AcaoAuditoria, TipoEvento
from app.schemas.agenda import (
    EventoAgendaCreate,
    EventoAgendaListItem,
    EventoAgendaOut,
    EventoAgendaUpdate,
)
from app.schemas.common import Page

router = APIRouter(prefix="/agenda", tags=["agenda"])


def _obter(db: SessaoDB, evento_id: int):
    evento = crud.get(db, evento_id)
    if evento is None:
        raise HTTPException(status_code=404, detail="Evento não encontrado")
    return evento


@router.get("", response_model=Page[EventoAgendaListItem], summary="Listar agenda")
def listar_agenda(
    db: SessaoDB,
    tipo: TipoEvento | None = None,
    de: Annotated[datetime | None, Query(description="A partir de (>=)")] = None,
    ate: Annotated[datetime | None, Query(description="Até (<=)")] = None,
    incluir_inativos: bool = False,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    itens, total = crud.listar(
        db,
        tipo=tipo,
        de=de,
        ate=ate,
        apenas_ativos=not incluir_inativos,
        page=page,
        size=size,
    )
    return Page.create(
        items=[EventoAgendaListItem.model_validate(e) for e in itens],
        total=total,
        page=page,
        size=size,
    )


@router.post(
    "",
    response_model=EventoAgendaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Criar evento",
)
def criar_evento(db: SessaoDB, dados: EventoAgendaCreate, usuario: UsuarioAtual):
    evento = crud.criar(db, dados)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.criar,
        entidade="evento_agenda",
        entidade_id=evento.id,
    )
    return EventoAgendaOut.model_validate(evento)


@router.get("/{evento_id}", response_model=EventoAgendaOut, summary="Ver evento")
def obter_evento(db: SessaoDB, evento_id: int):
    return EventoAgendaOut.model_validate(_obter(db, evento_id))


@router.patch("/{evento_id}", response_model=EventoAgendaOut, summary="Editar evento")
def editar_evento(
    db: SessaoDB, evento_id: int, dados: EventoAgendaUpdate, usuario: UsuarioAtual
):
    evento = _obter(db, evento_id)
    evento = crud.atualizar(db, evento, dados)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.atualizar,
        entidade="evento_agenda",
        entidade_id=evento_id,
        dados=dados.model_dump(exclude_unset=True, mode="json"),
    )
    return EventoAgendaOut.model_validate(evento)


@router.delete(
    "/{evento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir evento",
)
def excluir_evento(db: SessaoDB, evento_id: int, usuario: UsuarioAtual):
    evento = _obter(db, evento_id)
    crud.remover(db, evento)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.excluir,
        entidade="evento_agenda",
        entidade_id=evento_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
