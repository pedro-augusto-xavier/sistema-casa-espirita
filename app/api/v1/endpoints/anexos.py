"""Rotas de Anexos: fotos e documentos que a equipe recebe.

Ficam em dois grupos de caminho: `/pessoas/{id}/anexos` (enviar e listar,
sempre no contexto de uma ficha) e `/anexos/{id}` (baixar e excluir um
arquivo específico, sem precisar saber de quem é).
"""

from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status

from app.api.deps import SessaoDB, UsuarioAtual
from app.core.auditoria import registrar
from app.crud import anexo as crud
from app.crud import pessoa as crud_pessoa
from app.models.enums import AcaoAuditoria
from app.schemas.anexo import AnexoOut

router = APIRouter(tags=["anexos"])


@router.post(
    "/pessoas/{pessoa_id}/anexos",
    response_model=AnexoOut,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar um arquivo (foto, PDF) para a ficha ou um item do histórico",
)
async def enviar_anexo(
    db: SessaoDB,
    pessoa_id: int,
    usuario: UsuarioAtual,
    arquivo: Annotated[UploadFile, File()],
    descricao: Annotated[str | None, Form()] = None,
    atendimento_id: Annotated[int | None, Form()] = None,
    tratamento_id: Annotated[int | None, Form()] = None,
):
    if crud_pessoa.get(db, pessoa_id) is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")

    conteudo = await arquivo.read()
    anexo = crud.criar(
        db,
        pessoa_id=pessoa_id,
        nome_arquivo=arquivo.filename or "arquivo",
        tipo_conteudo=arquivo.content_type or "application/octet-stream",
        conteudo=conteudo,
        descricao=descricao,
        atendimento_id=atendimento_id,
        tratamento_id=tratamento_id,
        enviado_por_id=usuario.id,
    )
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.criar,
        entidade="anexo",
        entidade_id=anexo.id,
        dados={"nome_arquivo": anexo.nome_arquivo, "pessoa_id": pessoa_id},
    )
    return AnexoOut.model_validate(anexo)


@router.get(
    "/pessoas/{pessoa_id}/anexos",
    response_model=list[AnexoOut],
    summary="Listar os arquivos de uma pessoa",
)
def listar_anexos(db: SessaoDB, pessoa_id: int):
    if crud_pessoa.get(db, pessoa_id) is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")
    return [AnexoOut.model_validate(a) for a in crud.listar_por_pessoa(db, pessoa_id)]


@router.get("/anexos/{anexo_id}/arquivo", summary="Baixar o arquivo original")
def baixar_anexo(db: SessaoDB, anexo_id: int):
    anexo = crud.get_com_conteudo(db, anexo_id)
    if anexo is None:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")
    return Response(
        content=anexo.conteudo,
        media_type=anexo.tipo_conteudo,
        headers={"Content-Disposition": f'inline; filename="{anexo.nome_arquivo}"'},
    )


@router.delete(
    "/anexos/{anexo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir um anexo",
)
def excluir_anexo(db: SessaoDB, anexo_id: int, usuario: UsuarioAtual):
    anexo = crud.get_meta(db, anexo_id)
    if anexo is None:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")
    pessoa_id, nome = anexo.pessoa_id, anexo.nome_arquivo
    crud.remover(db, anexo)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.excluir,
        entidade="anexo",
        entidade_id=anexo_id,
        dados={"nome_arquivo": nome, "pessoa_id": pessoa_id},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
