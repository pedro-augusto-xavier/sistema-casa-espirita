"""Rotas de Tratamentos (casos): /api/v1/tratamentos

Um "caso" tem assistidos (sub-recurso) e um diário de evolução (sub-recurso).
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.deps import SessaoDB
from app.crud import tratamento as crud
from app.models.enums import StatusTratamento
from app.schemas.common import Page
from app.schemas.tratamento import (
    AssistidoIn,
    AssistidoUpdate,
    EvolucaoIn,
    EvolucaoUpdate,
    TratamentoCreate,
    TratamentoListItem,
    TratamentoOut,
    TratamentoUpdate,
)

router = APIRouter(prefix="/tratamentos", tags=["tratamentos"])


def _obter(db: SessaoDB, tratamento_id: int):
    tratamento = crud.get(db, tratamento_id)
    if tratamento is None:
        raise HTTPException(status_code=404, detail="Tratamento não encontrado")
    return tratamento


@router.get("", response_model=Page[TratamentoListItem], summary="Listar casos")
def listar_tratamentos(
    db: SessaoDB,
    status_: Annotated[
        StatusTratamento | None, Query(alias="status", description="Filtrar por status")
    ] = None,
    tipo_tratamento_id: int | None = None,
    pessoa_id: Annotated[
        int | None, Query(description="Casos em que a pessoa é assistida")
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    itens, total = crud.listar(
        db,
        status=status_,
        tipo_tratamento_id=tipo_tratamento_id,
        pessoa_id=pessoa_id,
        page=page,
        size=size,
    )
    return Page.create(
        items=[TratamentoListItem.model_validate(t) for t in itens],
        total=total,
        page=page,
        size=size,
    )


@router.post(
    "",
    response_model=TratamentoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir caso de tratamento",
)
def criar_tratamento(db: SessaoDB, dados: TratamentoCreate):
    return TratamentoOut.model_validate(crud.criar(db, dados))


@router.get("/{tratamento_id}", response_model=TratamentoOut, summary="Ver caso")
def obter_tratamento(db: SessaoDB, tratamento_id: int):
    return TratamentoOut.model_validate(_obter(db, tratamento_id))


@router.patch("/{tratamento_id}", response_model=TratamentoOut, summary="Editar caso")
def editar_tratamento(db: SessaoDB, tratamento_id: int, dados: TratamentoUpdate):
    tratamento = _obter(db, tratamento_id)
    return TratamentoOut.model_validate(crud.atualizar(db, tratamento, dados))


@router.delete(
    "/{tratamento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir caso",
)
def excluir_tratamento(db: SessaoDB, tratamento_id: int):
    crud.remover(db, _obter(db, tratamento_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- assistidos ----------


@router.post(
    "/{tratamento_id}/assistidos",
    response_model=TratamentoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar assistido ao caso",
)
def adicionar_assistido(db: SessaoDB, tratamento_id: int, dados: AssistidoIn):
    tratamento = _obter(db, tratamento_id)
    return TratamentoOut.model_validate(
        crud.adicionar_assistido(db, tratamento, dados)
    )


@router.patch(
    "/{tratamento_id}/assistidos/{assistido_id}",
    response_model=TratamentoOut,
    summary="Atualizar assistido (concluir, situação final)",
)
def atualizar_assistido(
    db: SessaoDB, tratamento_id: int, assistido_id: int, dados: AssistidoUpdate
):
    assistido = crud.get_assistido(db, tratamento_id, assistido_id)
    if assistido is None:
        raise HTTPException(status_code=404, detail="Assistido não encontrado")
    return TratamentoOut.model_validate(
        crud.atualizar_assistido(db, assistido, dados)
    )


@router.delete(
    "/{tratamento_id}/assistidos/{assistido_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover assistido do caso",
)
def remover_assistido(db: SessaoDB, tratamento_id: int, assistido_id: int):
    assistido = crud.get_assistido(db, tratamento_id, assistido_id)
    if assistido is None:
        raise HTTPException(status_code=404, detail="Assistido não encontrado")
    crud.remover_assistido(db, assistido)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- evolução (diário) ----------


@router.post(
    "/{tratamento_id}/evolucoes",
    response_model=TratamentoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Adicionar entrada no diário de evolução",
)
def adicionar_evolucao(db: SessaoDB, tratamento_id: int, dados: EvolucaoIn):
    tratamento = _obter(db, tratamento_id)
    return TratamentoOut.model_validate(
        crud.adicionar_evolucao(db, tratamento, dados)
    )


@router.patch(
    "/{tratamento_id}/evolucoes/{evolucao_id}",
    response_model=TratamentoOut,
    summary="Editar entrada do diário",
)
def editar_evolucao(
    db: SessaoDB, tratamento_id: int, evolucao_id: int, dados: EvolucaoUpdate
):
    evolucao = crud.get_evolucao(db, tratamento_id, evolucao_id)
    if evolucao is None:
        raise HTTPException(status_code=404, detail="Evolução não encontrada")
    return TratamentoOut.model_validate(
        crud.atualizar_evolucao(db, evolucao, dados)
    )


@router.delete(
    "/{tratamento_id}/evolucoes/{evolucao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir entrada do diário",
)
def excluir_evolucao(db: SessaoDB, tratamento_id: int, evolucao_id: int):
    evolucao = crud.get_evolucao(db, tratamento_id, evolucao_id)
    if evolucao is None:
        raise HTTPException(status_code=404, detail="Evolução não encontrada")
    crud.remover_evolucao(db, evolucao)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
