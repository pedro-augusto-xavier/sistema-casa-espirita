"""Rotas de Anexos: fotos e documentos que a equipe recebe.

Ficam em dois grupos de caminho: `/pessoas/{id}/anexos` (enviar e listar,
sempre no contexto de uma ficha) e `/anexos/{id}` (baixar e excluir um
arquivo específico, sem precisar saber de quem é).
"""

import re
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status

from app.api.deps import SessaoDB, UsuarioAtual
from app.core.auditoria import registrar
from app.crud import anexo as crud
from app.crud import auditoria as crud_auditoria
from app.crud import pessoa as crud_pessoa
from app.models.enums import AcaoAuditoria
from app.schemas.anexo import AnexoOut

router = APIRouter(tags=["anexos"])

_FORA_DO_NOME_SEGURO = re.compile(r"[^A-Za-z0-9._ -]")


def _content_disposition(nome: str) -> str:
    """Nome do arquivo no cabeçalho sem dar brecha pra quebrar o cabeçalho
    (aspas, quebra de linha...). Versão ASCII + versão UTF-8 (RFC 6266)."""
    ascii_seguro = _FORA_DO_NOME_SEGURO.sub("_", nome)[:100] or "arquivo"
    return f"inline; filename=\"{ascii_seguro}\"; filename*=UTF-8''{quote(nome[:150])}"


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
    descricao: Annotated[str | None, Form(max_length=500)] = None,
    atendimento_id: Annotated[int | None, Form()] = None,
    tratamento_id: Annotated[int | None, Form()] = None,
):
    if crud_pessoa.get(db, pessoa_id) is None:
        raise HTTPException(status_code=404, detail="Pessoa não encontrada")

    # lê no máximo 1 byte além do limite: arquivo gigante não enche a memória
    conteudo = await arquivo.read(crud.TAMANHO_MAXIMO_BYTES + 1)
    anexo = crud.criar(
        db,
        pessoa_id=pessoa_id,
        nome_arquivo=arquivo.filename or "arquivo",
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
        # sem o nome do arquivo: às vezes ele é "rg_fulana.jpg"
        dados={"pessoa_id": pessoa_id, "tipo": anexo.tipo_conteudo},
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
def baixar_anexo(db: SessaoDB, anexo_id: int, usuario: UsuarioAtual):
    """Quem abriu qual arquivo fica na auditoria -- uma vez por pessoa, por
    arquivo, a cada 24 h (a ficha carrega as miniaturas toda vez que abre;
    registrar cada carregamento só encheria o log)."""
    anexo = crud.get_com_conteudo(db, anexo_id)
    if anexo is None:
        raise HTTPException(status_code=404, detail="Anexo não encontrado")
    if not crud_auditoria.registrado_recentemente(
        db,
        usuario_id=usuario.id,
        acao=AcaoAuditoria.visualizar,
        entidade="anexo",
        entidade_id=anexo_id,
    ):
        registrar(
            db,
            usuario=usuario,
            acao=AcaoAuditoria.visualizar,
            entidade="anexo",
            entidade_id=anexo_id,
            dados={"pessoa_id": anexo.pessoa_id},
        )
    return Response(
        content=anexo.conteudo,
        media_type=anexo.tipo_conteudo,
        headers={
            "Content-Disposition": _content_disposition(anexo.nome_arquivo),
            # um PDF/imagem aberto direto da API não roda script nenhum
            "Content-Security-Policy": "default-src 'none'; sandbox",
        },
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
    pessoa_id = anexo.pessoa_id
    crud.remover(db, anexo)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.excluir,
        entidade="anexo",
        entidade_id=anexo_id,
        dados={"pessoa_id": pessoa_id},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
