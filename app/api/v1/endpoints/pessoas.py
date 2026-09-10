"""Rotas de Pessoas: /api/v1/pessoas"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.deps import SessaoDB, UsuarioAtual, exigir_admin
from app.core.auditoria import registrar
from app.crud import pessoa as crud
from app.crud import tratamento as crud_tratamento
from app.models.enums import AcaoAuditoria, Papel
from app.schemas.common import Page
from app.schemas.pessoa import (
    PessoaCreate,
    PessoaListItem,
    PessoaOut,
    PessoaUpdate,
)
from app.schemas.tratamento import ItemHistorico

router = APIRouter(prefix="/pessoas", tags=["pessoas"])


@router.get("", response_model=Page[PessoaListItem], summary="Listar pessoas")
def listar_pessoas(
    db: SessaoDB,
    q: Annotated[
        str | None, Query(description="Busca por nome, telefone ou CPF")
    ] = None,
    papel: Annotated[Papel | None, Query(description="Filtrar por papel")] = None,
    incluir_inativos: bool = False,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    pessoas, total = crud.listar(
        db,
        q=q,
        papel=papel,
        apenas_ativos=not incluir_inativos,
        page=page,
        size=size,
    )
    return Page.create(
        items=[PessoaListItem.model_validate(p) for p in pessoas],
        total=total,
        page=page,
        size=size,
    )


@router.post(
    "",
    response_model=PessoaOut,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar pessoa",
)
def criar_pessoa(db: SessaoDB, dados: PessoaCreate, usuario: UsuarioAtual):
    if dados.cpf and crud.get_by_cpf(db, dados.cpf):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma pessoa com esse CPF",
        )
    pessoa = crud.criar(db, dados)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.criar,
        entidade="pessoa",
        entidade_id=pessoa.id,
    )
    return PessoaOut.model_validate(pessoa)


@router.get("/{pessoa_id}", response_model=PessoaOut, summary="Ver ficha")
def obter_pessoa(db: SessaoDB, pessoa_id: int):
    pessoa = crud.get(db, pessoa_id)
    if pessoa is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return PessoaOut.model_validate(pessoa)


@router.patch("/{pessoa_id}", response_model=PessoaOut, summary="Editar ficha")
def editar_pessoa(
    db: SessaoDB, pessoa_id: int, dados: PessoaUpdate, usuario: UsuarioAtual
):
    pessoa = crud.get(db, pessoa_id)
    if pessoa is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")

    if dados.cpf:
        existente = crud.get_by_cpf(db, dados.cpf)
        if existente and existente.id != pessoa_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Já existe outra pessoa com esse CPF",
            )

    pessoa = crud.atualizar(db, pessoa, dados)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.atualizar,
        entidade="pessoa",
        entidade_id=pessoa.id,
        dados=dados.model_dump(exclude_unset=True, mode="json"),
    )
    return PessoaOut.model_validate(pessoa)


@router.delete(
    "/{pessoa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desativar ficha (exclusão lógica)",
)
def desativar_pessoa(db: SessaoDB, pessoa_id: int, usuario: UsuarioAtual):
    pessoa = crud.get(db, pessoa_id)
    if pessoa is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    crud.desativar(db, pessoa)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.excluir,
        entidade="pessoa",
        entidade_id=pessoa_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{pessoa_id}/reativar", response_model=PessoaOut, summary="Reativar ficha"
)
def reativar_pessoa(db: SessaoDB, pessoa_id: int, usuario: UsuarioAtual):
    pessoa = crud.get(db, pessoa_id)
    if pessoa is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    pessoa = crud.reativar(db, pessoa)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.atualizar,
        entidade="pessoa",
        entidade_id=pessoa_id,
        dados={"reativada": True},
    )
    return PessoaOut.model_validate(pessoa)


@router.get(
    "/{pessoa_id}/historico",
    response_model=list[ItemHistorico],
    summary="Linha do tempo da pessoa (atendimentos, casos e evoluções)",
)
def historico_pessoa(db: SessaoDB, pessoa_id: int):
    if crud.get(db, pessoa_id) is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return [
        ItemHistorico.model_validate(i)
        for i in crud_tratamento.historico_pessoa(db, pessoa_id)
    ]


@router.get(
    "/{pessoa_id}/exportar",
    summary="LGPD -- exportar todos os dados da pessoa",
)
def exportar_pessoa(db: SessaoDB, pessoa_id: int, usuario: UsuarioAtual):
    if crud.get(db, pessoa_id) is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    dados = crud.exportar_dados(db, pessoa_id)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.atualizar,
        entidade="pessoa",
        entidade_id=pessoa_id,
        dados={"acao_lgpd": "exportacao"},
    )
    return dados


@router.post(
    "/{pessoa_id}/anonimizar",
    response_model=PessoaOut,
    summary="LGPD -- apagar dados pessoais (direito ao esquecimento)",
    dependencies=[Depends(exigir_admin)],
)
def anonimizar_pessoa(db: SessaoDB, pessoa_id: int, usuario: UsuarioAtual):
    pessoa = crud.get(db, pessoa_id)
    if pessoa is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    if pessoa.anonimizada:
        raise HTTPException(status_code=409, detail="Ficha já foi anonimizada")
    pessoa = crud.anonimizar(db, pessoa)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.excluir,
        entidade="pessoa",
        entidade_id=pessoa_id,
        dados={"acao_lgpd": "anonimizacao"},
    )
    return PessoaOut.model_validate(pessoa)
