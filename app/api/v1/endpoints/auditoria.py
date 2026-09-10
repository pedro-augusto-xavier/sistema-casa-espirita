"""Rota de consulta ao log de auditoria: /api/v1/auditoria (só admin)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import SessaoDB, exigir_admin
from app.crud import auditoria as crud
from app.schemas.auditoria import AuditLogOut
from app.schemas.common import Page

router = APIRouter(
    prefix="/auditoria",
    tags=["auditoria"],
    dependencies=[Depends(exigir_admin)],
)


@router.get("", response_model=Page[AuditLogOut], summary="Consultar auditoria")
def listar_auditoria(
    db: SessaoDB,
    entidade: Annotated[
        str | None, Query(description="Ex: pessoa, atendimento, tratamento")
    ] = None,
    entidade_id: int | None = None,
    usuario_id: int | None = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=200)] = 50,
):
    itens, total = crud.listar(
        db,
        entidade=entidade,
        entidade_id=entidade_id,
        usuario_id=usuario_id,
        page=page,
        size=size,
    )
    return Page.create(
        items=[AuditLogOut.model_validate(a) for a in itens],
        total=total,
        page=page,
        size=size,
    )
