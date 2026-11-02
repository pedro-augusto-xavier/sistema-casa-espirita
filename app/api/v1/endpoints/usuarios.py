"""Rotas de gestão de usuários do sistema: /api/v1/usuarios (só admin)."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.deps import SessaoDB, UsuarioAtual, exigir_admin
from app.core.auditoria import registrar
from app.crud import sessao as crud_sessao
from app.crud import usuario as crud
from app.models.enums import AcaoAuditoria, PapelUsuario
from app.schemas.common import Page
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate

router = APIRouter(
    prefix="/usuarios",
    tags=["usuários"],
    dependencies=[Depends(exigir_admin)],
)


def _obter(db: SessaoDB, usuario_id: int):
    usuario = crud.get(db, usuario_id)
    if usuario is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario


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
def criar_usuario(db: SessaoDB, dados: UsuarioCreate, atual: UsuarioAtual):
    """A senha informada aqui é provisória: no primeiro acesso a pessoa é
    obrigada a criar uma só dela."""
    usuario = crud.criar(db, dados)
    registrar(
        db,
        usuario=atual,
        acao=AcaoAuditoria.criar,
        entidade="usuario",
        entidade_id=usuario.id,
        dados={"papel": usuario.papel.value},
    )
    return UsuarioOut.model_validate(usuario)


@router.get("/{usuario_id}", response_model=UsuarioOut, summary="Ver usuário")
def obter_usuario(db: SessaoDB, usuario_id: int):
    return UsuarioOut.model_validate(_obter(db, usuario_id))


@router.patch("/{usuario_id}", response_model=UsuarioOut, summary="Editar usuário")
def editar_usuario(
    db: SessaoDB, usuario_id: int, dados: UsuarioUpdate, atual: UsuarioAtual
):
    """Redefinir a senha deixa ela provisória e derruba as sessões abertas;
    desativar também corta o acesso na hora."""
    usuario = _obter(db, usuario_id)

    # ninguém se tranca pra fora sem querer (e o sistema nunca fica sem admin
    # por um clique errado)
    if usuario_id == atual.id and (
        dados.ativo is False
        or (dados.papel is not None and dados.papel != PapelUsuario.admin)
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Você não pode desativar nem tirar o administrador de si mesmo.",
        )

    papel_antes = usuario.papel
    usuario = crud.atualizar(db, usuario, dados)
    campos = dados.model_dump(exclude_unset=True, mode="json")
    campos.pop("senha", None)  # nunca logar senha
    if "papel" in campos:
        campos["papel"] = {"de": papel_antes.value, "para": usuario.papel.value}
    registrar(
        db,
        usuario=atual,
        acao=AcaoAuditoria.atualizar,
        entidade="usuario",
        entidade_id=usuario_id,
        dados={**campos, "senha_alterada": "senha" in dados.model_fields_set},
    )
    return UsuarioOut.model_validate(usuario)


@router.post(
    "/{usuario_id}/resetar-mfa",
    response_model=UsuarioOut,
    summary="Zerar a verificação em duas etapas (celular perdido, trocado...)",
)
def resetar_mfa(db: SessaoDB, usuario_id: int, atual: UsuarioAtual):
    """A pessoa configura de novo no próximo acesso (se for obrigatória pra
    ela) ou quando quiser. As sessões abertas dela são encerradas."""
    usuario = _obter(db, usuario_id)
    crud.zerar_mfa(db, usuario)
    crud_sessao.revogar_todas(db, usuario.id)
    registrar(
        db,
        usuario=atual,
        acao=AcaoAuditoria.atualizar,
        entidade="usuario",
        entidade_id=usuario_id,
        dados={"duas_etapas": "zerada_pelo_admin"},
    )
    db.refresh(usuario)
    return UsuarioOut.model_validate(usuario)


@router.post(
    "/{usuario_id}/encerrar-sessoes",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desconectar a pessoa de todos os aparelhos",
)
def encerrar_sessoes(db: SessaoDB, usuario_id: int, atual: UsuarioAtual):
    usuario = _obter(db, usuario_id)
    crud_sessao.revogar_todas(db, usuario.id)
    registrar(
        db,
        usuario=atual,
        acao=AcaoAuditoria.atualizar,
        entidade="usuario",
        entidade_id=usuario_id,
        dados={"sessoes_encerradas": True},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
