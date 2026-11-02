"""Sessões de login: abrir, conferir e encerrar."""

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.contexto import ip_atual, user_agent_atual
from app.core.security import criar_token_sessao
from app.models.usuario import SessaoUsuario, Usuario

# não grava "último uso" a cada clique -- de 5 em 5 minutos basta
_INTERVALO_ULTIMO_USO = timedelta(minutes=5)
# sessões vencidas ficam um tempo (dá pra ver de onde a pessoa entrou) e
# depois somem
_GUARDAR_VENCIDAS_POR = timedelta(days=30)


def _agora() -> datetime:
    return datetime.now(UTC)


def abrir(db: Session, usuario: Usuario, *, lembrar: bool = False) -> str:
    """Cria a sessão e devolve o token pra mandar pro navegador."""
    agora = _agora()
    validade = (
        timedelta(days=settings.LEMBRAR_TOKEN_EXPIRE_DAYS)
        if lembrar
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    sessao = SessaoUsuario(
        id=secrets.token_urlsafe(32),
        usuario_id=usuario.id,
        criada_em=agora,
        expira_em=agora + validade,
        ultimo_uso_em=agora,
        ip=ip_atual(),
        user_agent=user_agent_atual(),
    )
    db.add(sessao)
    db.commit()
    return criar_token_sessao(usuario.id, sessao.id, sessao.expira_em)


def obter_valida(db: Session, sessao_id: str, usuario_id: int) -> SessaoUsuario | None:
    sessao = db.get(SessaoUsuario, sessao_id)
    if (
        sessao is None
        or sessao.usuario_id != usuario_id
        or sessao.revogada_em is not None
        or sessao.expira_em <= _agora()
    ):
        return None
    return sessao


def marcar_uso(db: Session, sessao: SessaoUsuario) -> None:
    agora = _agora()
    ultimo = sessao.ultimo_uso_em
    if ultimo is None or agora - ultimo > _INTERVALO_ULTIMO_USO:
        sessao.ultimo_uso_em = agora
        db.commit()


def revogar(db: Session, sessao: SessaoUsuario) -> None:
    if sessao.revogada_em is None:
        sessao.revogada_em = _agora()
        db.commit()


def revogar_todas(db: Session, usuario_id: int, *, exceto: str | None = None) -> None:
    """Encerra todas as sessões do usuário (menos, opcionalmente, a atual)."""
    stmt = (
        update(SessaoUsuario)
        .where(
            SessaoUsuario.usuario_id == usuario_id,
            SessaoUsuario.revogada_em.is_(None),
        )
        .values(revogada_em=_agora())
    )
    if exceto is not None:
        stmt = stmt.where(SessaoUsuario.id != exceto)
    db.execute(stmt)
    db.commit()


def ativas_do_usuario(db: Session, usuario_id: int) -> list[SessaoUsuario]:
    stmt = (
        select(SessaoUsuario)
        .where(
            SessaoUsuario.usuario_id == usuario_id,
            SessaoUsuario.revogada_em.is_(None),
            SessaoUsuario.expira_em > _agora(),
        )
        .order_by(SessaoUsuario.ultimo_uso_em.desc())
    )
    return list(db.scalars(stmt).all())


def limpar_antigas(db: Session) -> None:
    db.execute(
        delete(SessaoUsuario).where(
            SessaoUsuario.expira_em < _agora() - _GUARDAR_VENCIDAS_POR
        )
    )
    db.commit()
