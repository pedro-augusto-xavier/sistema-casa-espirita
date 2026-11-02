"""Acesso ao banco para Usuário do sistema."""

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ErroDominio
from app.core.security import (
    gastar_tempo_como_se_verificasse,
    hash_senha,
    verificar_senha,
)
from app.crud import sessao as crud_sessao
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate


def get(db: Session, usuario_id: int) -> Usuario | None:
    return db.get(Usuario, usuario_id)


def get_by_email(db: Session, email: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(Usuario.email == email.lower()))


def get_by_nome(
    db: Session, nome: str, *, apenas_ativos: bool = True
) -> Usuario | None:
    """Login é pelo nome -- comparação ignora maiúscula/minúscula e espaços
    nas pontas. Só olha usuários ativos por padrão (é o que importa pro
    login, e evita que um nome de alguém desligado trave pra sempre)."""
    stmt = select(Usuario).where(func.lower(Usuario.nome) == nome.strip().lower())
    if apenas_ativos:
        stmt = stmt.where(Usuario.ativo.is_(True))
    return db.scalar(stmt)


def listar(
    db: Session, *, page: int = 1, size: int = 50
) -> tuple[list[Usuario], int]:
    stmt = select(Usuario).order_by(Usuario.nome)
    total = db.scalar(select(func.count()).select_from(Usuario)) or 0
    stmt = stmt.offset((page - 1) * size).limit(size)
    return list(db.scalars(stmt).all()), total


def criar(db: Session, dados: UsuarioCreate) -> Usuario:
    if dados.email and get_by_email(db, dados.email):
        raise ErroDominio("já existe um usuário com esse e-mail")
    if get_by_nome(db, dados.nome):
        raise ErroDominio("já existe um usuário ativo com esse nome")
    usuario = Usuario(
        nome=dados.nome,
        email=dados.email.lower() if dados.email else None,
        senha_hash=hash_senha(dados.senha),
        # quem define essa senha é o admin -- a pessoa troca no 1º acesso
        senha_provisoria=True,
        papel=dados.papel,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def atualizar(db: Session, usuario: Usuario, dados: UsuarioUpdate) -> Usuario:
    mudancas = dados.model_dump(exclude_unset=True)

    if "nome" in mudancas:
        existente = get_by_nome(db, mudancas["nome"])
        if existente and existente.id != usuario.id:
            raise ErroDominio("já existe um usuário ativo com esse nome")

    if "email" in mudancas and mudancas["email"]:
        existente = get_by_email(db, mudancas["email"])
        if existente and existente.id != usuario.id:
            raise ErroDominio("já existe um usuário com esse e-mail")
        mudancas["email"] = mudancas["email"].lower()

    corta_acesso = False
    if "senha" in mudancas:
        usuario.senha_hash = hash_senha(mudancas.pop("senha"))
        usuario.senha_provisoria = True
        usuario.senha_alterada_em = datetime.now(UTC)
        corta_acesso = True
    if mudancas.get("ativo") is False:
        corta_acesso = True

    for campo, valor in mudancas.items():
        setattr(usuario, campo, valor)
    db.commit()

    # senha redefinida ou usuário desligado: quem estava logado cai na hora
    if corta_acesso:
        crud_sessao.revogar_todas(db, usuario.id)

    db.refresh(usuario)
    return usuario


def trocar_senha_propria(
    db: Session, usuario: Usuario, senha_nova: str, *, sessao_atual: str
) -> None:
    usuario.senha_hash = hash_senha(senha_nova)
    usuario.senha_provisoria = False
    usuario.senha_alterada_em = datetime.now(UTC)
    db.commit()
    # se alguém mais estava usando a senha antiga, perde o acesso
    crud_sessao.revogar_todas(db, usuario.id, exceto=sessao_atual)


def zerar_mfa(db: Session, usuario: Usuario) -> None:
    usuario.mfa_ativo = False
    usuario.mfa_segredo = None
    usuario.mfa_ultimo_passo = None
    db.commit()


def autenticar(db: Session, nome: str, senha: str) -> Usuario | None:
    usuario = get_by_nome(db, nome)
    if usuario is None:
        # mesmo tempo de resposta de "senha errada" -- não entrega quais
        # nomes existem
        gastar_tempo_como_se_verificasse(senha)
        return None
    if not verificar_senha(senha, usuario.senha_hash):
        return None
    return usuario
