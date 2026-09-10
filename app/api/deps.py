"""Dependências compartilhadas pelas rotas.

Por enquanto só a sessão do banco. A dependência de usuário logado
entra aqui quando fizermos a autenticação.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

SessaoDB = Annotated[Session, Depends(get_db)]
