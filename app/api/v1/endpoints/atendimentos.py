"""Rotas de Atendimentos: /api/v1/atendimentos"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.api.deps import (
    SessaoDB,
    UsuarioAtual,
    barrar_operador_em_ficha_anonimizada,
)
from app.core.auditoria import campos_alterados, registrar
from app.crud import atendimento as crud
from app.models.enums import AcaoAuditoria
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
def criar_atendimento(db: SessaoDB, dados: AtendimentoCreate, usuario: UsuarioAtual):
    atendimento, casos = crud.criar(db, dados)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.criar,
        entidade="atendimento",
        entidade_id=atendimento.id,
    )
    # o caso aberto/alterado aqui fica no rastro do caso, como nas rotas de
    # /tratamentos; o atendimento_id liga os dois mesmo se ele for excluído
    vinculo = {"atendimento_id": atendimento.id}
    for mudanca in casos:
        caso_id = mudanca.caso.id
        if mudanca.aberto_agora:
            _registrar_caso(db, usuario, AcaoAuditoria.criar, caso_id, vinculo)
            continue
        for pessoa_id in mudanca.assistidos_adicionados:
            _registrar_caso(
                db,
                usuario,
                AcaoAuditoria.atualizar,
                caso_id,
                {"assistido_adicionado": pessoa_id, **vinculo},
            )
        if mudanca.sessoes_previstas_preenchidas:
            _registrar_caso(
                db,
                usuario,
                AcaoAuditoria.atualizar,
                caso_id,
                {"campos": ["sessoes_previstas"], **vinculo},
            )
    return AtendimentoOut.model_validate(atendimento)


def _registrar_caso(db, usuario, acao, caso_id, dados) -> None:
    registrar(
        db,
        usuario=usuario,
        acao=acao,
        entidade="tratamento",
        entidade_id=caso_id,
        dados=dados,
    )


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
def editar_atendimento(
    db: SessaoDB,
    atendimento_id: int,
    dados: AtendimentoUpdate,
    usuario: UsuarioAtual,
):
    atendimento = crud.get(db, atendimento_id)
    if atendimento is None:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado")
    barrar_operador_em_ficha_anonimizada(
        usuario, crud.ligado_a_anonimizada(db, atendimento)
    )
    atendimento, casos_movidos = crud.atualizar(db, atendimento, dados)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.atualizar,
        entidade="atendimento",
        entidade_id=atendimento.id,
        # só os nomes dos campos: a observação é sensível e fica cifrada
        dados=campos_alterados(dados.model_dump(exclude_unset=True)),
    )
    # corrigir a data do atendimento que abriu o caso move o início do caso
    for caso_id in casos_movidos:
        _registrar_caso(
            db,
            usuario,
            AcaoAuditoria.atualizar,
            caso_id,
            {"campos": ["data_inicio"], "atendimento_id": atendimento.id},
        )
    return AtendimentoOut.model_validate(atendimento)


@router.delete(
    "/{atendimento_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir atendimento",
)
def excluir_atendimento(db: SessaoDB, atendimento_id: int, usuario: UsuarioAtual):
    atendimento = crud.get(db, atendimento_id)
    if atendimento is None:
        raise HTTPException(status_code=404, detail="Atendimento não encontrado")
    anexos_apagados = crud.remover(db, atendimento)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.excluir,
        entidade="atendimento",
        entidade_id=atendimento_id,
    )
    for anexo_id, pessoa_id in anexos_apagados:
        registrar(
            db,
            usuario=usuario,
            acao=AcaoAuditoria.excluir,
            entidade="anexo",
            entidade_id=anexo_id,
            dados={"pessoa_id": pessoa_id, "atendimento_id": atendimento_id},
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
