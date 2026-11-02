"""Registro de auditoria: quem fez o quê, quando e de qual IP.

As rotas de escrita chamam `registrar(...)` depois de uma operação bem-sucedida.
As linhas de audit_log nunca são editadas nem apagadas (o banco recusa).

Regra de ouro: NÃO guardar aqui senha, token, CPF, nem o conteúdo das
observações -- o log é pra saber quem mexeu em quê, não uma segunda cópia
dos dados (que ficaria fora da criptografia e da anonimização).
"""

from typing import Any

from sqlalchemy.orm import Session

from app.core.contexto import ip_atual
from app.models.enums import AcaoAuditoria
from app.models.usuario import AuditLog, Usuario


def registrar(
    db: Session,
    *,
    usuario: Usuario | None,
    acao: AcaoAuditoria,
    entidade: str,
    entidade_id: int | None = None,
    dados: dict[str, Any] | None = None,
) -> None:
    db.add(
        AuditLog(
            usuario_id=usuario.id if usuario else None,
            acao=acao,
            entidade=entidade,
            entidade_id=entidade_id,
            dados=dados,
            ip=ip_atual(),
        )
    )
    db.commit()


def campos_alterados(dados: dict[str, Any]) -> dict[str, list[str]]:
    """Pra auditar uma edição sem copiar o conteúdo: só os nomes dos campos."""
    return {"campos": sorted(dados.keys())}
