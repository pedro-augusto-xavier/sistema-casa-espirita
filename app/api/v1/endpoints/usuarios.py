"""Rotas de gestão de usuários do sistema: /api/v1/usuarios (só admin)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import SessaoDB, exigir_admin
from app.crud import usuario as crud
from app.schemas.common import Page
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate

router = APIRouter(
    prefix="/usuarios",
    tags=["usuários"],
    dependencies=[Depends(exigir_admin)],
)


@router.get("", response_model=Page[UsuarioOut], summary="Listar usuários")
def listar_usuarios(
    db: SessaoDB,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 50,
):
    itens, total = crud.listar(db, page=page, size=size)
    return Page.create(
        items=[UsuarioOut.model_validate(u) for u in itens],
        total=total,
        page=page,
        size=size,
    )


@router.post(
    "",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED,
    summary="Criar usuário",
)
def criar_usuario(db: SessaoDB, dados: UsuarioCreate):
    return UsuarioOut.model_validate(crud.criar(db, dados))


@router.get("/{usuario_id}", response_model=UsuarioOut, summary="Ver usuário")
def obter_usuario(db: SessaoDB, usuario_id: int):
    usuario = crud.get(db, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return UsuarioOut.model_validate(usuario)


@router.patch("/{usuario_id}", response_model=UsuarioOut, summary="Editar usuário")
def editar_usuario(db: SessaoDB, usuario_id: int, dados: UsuarioUpdate):
    usuario = crud.get(db, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return UsuarioOut.model_validate(crud.atualizar(db, usuario, dados))
