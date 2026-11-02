"""Schema de leitura do log de auditoria."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models.enums import AcaoAuditoria


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int | None
    usuario_nome: str | None
    acao: AcaoAuditoria
    entidade: str
    entidade_id: int | None
    dados: dict[str, Any] | None
    ip: str | None
    criado_em: datetime


class AlertasSeguranca(BaseModel):
    """Resumo pra quem administra bater o olho: tem algo estranho?"""

    falhas_login_24h: int
    contas_com_falhas_24h: int
    exportacoes_7d: int
    cpfs_vistos_7d: int
    acessos_fora_de_hora_7d: int
    alerta: bool
