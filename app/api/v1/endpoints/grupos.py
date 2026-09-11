"""Rotas de Grupos (Grupo Despertar, Grupo de Estudos): /api/v1/grupos"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.deps import SessaoDB, UsuarioAtual
from app.core.auditoria import registrar
from app.crud import grupo as crud
from app.models.enums import AcaoAuditoria
from app.schemas.common import Page
from app.schemas.grupo import (
    SessaoGrupoCreate,
    SessaoGrupoListItem,
    SessaoGrupoOut,
    SessaoGrupoUpdate,
)

router = APIRouter(prefix="/grupos", tags=["grupos"])


def _obter(db: SessaoDB, sessao_id: int):
    sessao = crud.get(db, sessao_id)
    if sessao is None:
        raise HTTPException(status_code=404, detail="Sessão de grupo não encontrada")
    return sessao


@router.get(
    "", response_model=Page[SessaoGrupoListItem], summary="Listar sessões de grupo"
)
def listar_grupos(
    db: SessaoDB,
    tipo_tratamento_id: int | None = None,
    de: Annotated[date | None, Query(description="Data inicial (>=)")] = None,
    ate: Annotated[date | None, Query(description="Data final (<=)")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    itens, total = crud.listar(
        db, tipo_tratamento_id=tipo_tratamento_id, de=de, ate=ate, page=page, size=size
    )
    return Page.create(
        items=[SessaoGrupoListItem.model_validate(s) for s in itens],
        total=total,
        page=page,
        size=size,
    )


@router.post(
    "",
    response_model=SessaoGrupoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar sessão de grupo",
)
def criar_grupo(db: SessaoDB, dados: SessaoGrupoCreate, usuario: UsuarioAtual):
    sessao = crud.criar(db, dados)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.criar,
        entidade="sessao_grupo",
        entidade_id=sessao.id,
    )
    return SessaoGrupoOut.model_validate(sessao)


@router.get("/{sessao_id}", response_model=SessaoGrupoOut, summary="Ver sessão")
def obter_grupo(db: SessaoDB, sessao_id: int):
    return SessaoGrupoOut.model_validate(_obter(db, sessao_id))


@router.patch("/{sessao_id}", response_model=SessaoGrupoOut, summary="Editar sessão")
def editar_grupo(
    db: SessaoDB, sessao_id: int, dados: SessaoGrupoUpdate, usuario: UsuarioAtual
):
    sessao = _obter(db, sessao_id)
    sessao = crud.atualizar(db, sessao, dados)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.atualizar,
        entidade="sessao_grupo",
        entidade_id=sessao_id,
        dados=dados.model_dump(exclude_unset=True, mode="json"),
    )
    return SessaoGrupoOut.model_validate(sessao)


@router.delete(
    "/{sessao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir sessão de grupo",
)
def excluir_grupo(db: SessaoDB, sessao_id: int, usuario: UsuarioAtual):
    sessao = _obter(db, sessao_id)
    crud.remover(db, sessao)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.excluir,
        entidade="sessao_grupo",
        entidade_id=sessao_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
