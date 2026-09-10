"""Acesso ao banco para Usuário do sistema."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ErroDominio
from app.core.security import hash_senha, verificar_senha
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate


def get(db: Session, usuario_id: int) -> Usuario | None:
    return db.get(Usuario, usuario_id)


def get_by_email(db: Session, email: str) -> Usuario | None:
    return db.scalar(select(Usuario).where(Usuario.email == email.lower()))


def listar(
    db: Session, *, page: int = 1, size: int = 50
) -> tuple[list[Usuario], int]:
    stmt = select(Usuario).order_by(Usuario.nome)
    total = db.scalar(select(func.count()).select_from(Usuario)) or 0
    stmt = stmt.offset((page - 1) * size).limit(size)
    return list(db.scalars(stmt).all()), total


def criar(db: Session, dados: UsuarioCreate) -> Usuario:
    if get_by_email(db, dados.email):
        raise ErroDominio("já existe um usuário com esse e-mail")
    usuario = Usuario(
        nome=dados.nome,
        email=dados.email.lower(),
        senha_hash=hash_senha(dados.senha),
        papel=dados.papel,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def atualizar(db: Session, usuario: Usuario, dados: UsuarioUpdate) -> Usuario:
    mudancas = dados.model_dump(exclude_unset=True)
    if "senha" in mudancas:
        usuario.senha_hash = hash_senha(mudancas.pop("senha"))
    for campo, valor in mudancas.items():
        setattr(usuario, campo, valor)
    db.commit()
    db.refresh(usuario)
    return usuario


def autenticar(db: Session, email: str, senha: str) -> Usuario | None:
    usuario = get_by_email(db, email)
    if usuario is None or not usuario.ativo:
        return None
    if not verificar_senha(senha, usuario.senha_hash):
        return None
    return usuario
