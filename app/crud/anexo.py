"""Acesso ao banco para Anexo (fotos e documentos enviados)."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload, undefer

from app.core.errors import ErroDominio, NaoEncontrado
from app.models.anexo import Anexo
from app.models.atendimento import Atendimento
from app.models.pessoa import Pessoa
from app.models.tratamento import Tratamento

# Foto de celular ou documento escaneado -- não precisa de mais que isso.
TAMANHO_MAXIMO_BYTES = 8 * 1024 * 1024

TIPOS_PERMITIDOS = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/heic",
    "image/heif",
    "application/pdf",
}

_CARREGAR_LISTA = (selectinload(Anexo.enviado_por),)


def listar_por_pessoa(db: Session, pessoa_id: int) -> list[Anexo]:
    stmt = (
        select(Anexo)
        .options(*_CARREGAR_LISTA)
        .where(Anexo.pessoa_id == pessoa_id)
        .order_by(Anexo.criado_em.desc())
    )
    return list(db.scalars(stmt).all())


def get_meta(db: Session, anexo_id: int) -> Anexo | None:
    """Só os metadados -- não carrega o arquivo (`conteudo` é deferred)."""
    stmt = select(Anexo).options(*_CARREGAR_LISTA).where(Anexo.id == anexo_id)
    return db.scalar(stmt)


def get_com_conteudo(db: Session, anexo_id: int) -> Anexo | None:
    stmt = select(Anexo).options(undefer(Anexo.conteudo)).where(Anexo.id == anexo_id)
    return db.scalar(stmt)


def criar(
    db: Session,
    *,
    pessoa_id: int,
    nome_arquivo: str,
    tipo_conteudo: str,
    conteudo: bytes,
    descricao: str | None,
    atendimento_id: int | None,
    tratamento_id: int | None,
    enviado_por_id: int | None,
) -> Anexo:
    if db.get(Pessoa, pessoa_id) is None:
        raise NaoEncontrado(f"pessoa {pessoa_id} não existe")
    if atendimento_id is not None and tratamento_id is not None:
        raise ErroDominio(
            "um anexo só pode estar ligado a um atendimento OU a um tratamento"
        )
    if atendimento_id is not None and db.get(Atendimento, atendimento_id) is None:
        raise NaoEncontrado(f"atendimento {atendimento_id} não existe")
    if tratamento_id is not None and db.get(Tratamento, tratamento_id) is None:
        raise NaoEncontrado(f"tratamento {tratamento_id} não existe")

    if tipo_conteudo not in TIPOS_PERMITIDOS:
        raise ErroDominio(
            "tipo de arquivo não aceito -- envie foto (jpg, png, webp, heic) ou PDF"
        )
    if not conteudo:
        raise ErroDominio("o arquivo está vazio")
    if len(conteudo) > TAMANHO_MAXIMO_BYTES:
        raise ErroDominio("arquivo maior que 8 MB -- tente uma foto mais leve")

    anexo = Anexo(
        pessoa_id=pessoa_id,
        atendimento_id=atendimento_id,
        tratamento_id=tratamento_id,
        nome_arquivo=(nome_arquivo or "arquivo")[:255],
        tipo_conteudo=tipo_conteudo,
        tamanho_bytes=len(conteudo),
        conteudo=conteudo,
        descricao=descricao,
        enviado_por_id=enviado_por_id,
    )
    db.add(anexo)
    db.commit()
    db.refresh(anexo)
    return get_meta(db, anexo.id)  # type: ignore[return-value]


def remover(db: Session, anexo: Anexo) -> None:
    db.delete(anexo)
    db.commit()


def remover_todos_da_pessoa(db: Session, pessoa_id: int) -> None:
    """LGPD -- usado na anonimização. Foto/documento é dado pessoal como
    qualquer outro (mais sensível que a maioria, na verdade)."""
    anexos = db.scalars(select(Anexo).where(Anexo.pessoa_id == pessoa_id)).all()
    for anexo in anexos:
        db.delete(anexo)
    db.commit()
