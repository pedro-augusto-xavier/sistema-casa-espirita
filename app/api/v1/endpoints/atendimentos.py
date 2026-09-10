"""Rotas de Atendimentos: /api/v1/atendimentos"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.deps import SessaoDB
from app.crud import atendimento as crud
from app.schemas.atendimento import (
    AtendimentoCreate,
    AtendimentoListItem,
    AtendimentoOut,
    AtendimentoUpdate,
)
from app.schemas.common import Page

router = APIRouter(prefix="/atendimentos", tags=["atendimentos"])


@router.get("", response_model=Page[AtendimentoListItem], summary="Listar atendimentos")
def listar_atendimentos(
    db: SessaoDB,
    pessoa_id: int | None = None,
    atendido_por_id: int | None = None,
    de: Annotated[date | None, Query(description="Data inicial (>=)")] = None,
    ate: Annotated[date | None, Query(description="Data final (<=)")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    itens, total = crud.listar(
        db,
        pessoa_id=pessoa_id,
        atendido_por_id=atendido_por_id,
        de=de,
        ate=ate,
        page=page,
        size=size,
    )
    return Page.create(
        items=[AtendimentoListItem.model_validate(a) for a in itens],
        total=total,
        page=page,
        size=size,
    )


@router.post(
    "",
    response_model=AtendimentoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar atendimento",
)
def criar_atendimento(db: SessaoDB, dados: AtendimentoCreate):
    return AtendimentoOut.model_validate(crud.criar(db, dados))


@router.get(
    "/{atendimento_id}", response_model=AtendimentoOut, summary="Ver atendimento"
)
def obter_atendimento(db: SessaoDB, atendimento_id: int):
    atendimento = crud.get(db, atendimento_id)
    if atendimento is None:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado")
    return AtendimentoOut.model_validate(atendimento)


@router.patch(
    "/{atendimento_id}", response_model=AtendimentoOut, summary="Editar atendimento"
)
def editar_atendimento(db: SessaoDB, atendimento_id: int, dados: AtendimentoUpdate):
    atendimento = crud.get(db, atendimento_id)
    if atendimento is None:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado")
    return AtendimentoOut.model_validate(crud.atualizar(db, atendimento, dados))


@router.delete(
    "/{atendimento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir atendimento",
)
def excluir_atendimento(db: SessaoDB, atendimento_id: int):
    atendimento = crud.get(db, atendimento_id)
    if atendimento is None:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado")
    crud.remover(db, atendimento)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
