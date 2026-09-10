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
    criado_em: datetime
