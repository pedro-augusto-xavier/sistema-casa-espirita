"""Schema de saída de Anexo. O upload em si não usa schema de entrada --
chega como multipart/form-data (arquivo + campos), lido direto na rota.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AnexoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pessoa_id: int
    atendimento_id: int | None
    tratamento_id: int | None
    nome_arquivo: str
    tipo_conteudo: str
    tamanho_bytes: int
    descricao: str | None
    enviado_por_nome: str | None
    criado_em: datetime
