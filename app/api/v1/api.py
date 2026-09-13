"""Junta todas as rotas da versão 1 da API.

`auth` é público (é onde se pega o token). Todo o resto exige usuário logado.
"""

from fastapi import APIRouter, Depends

from app.api.deps import get_usuario_atual
from app.api.v1.endpoints import (
    agenda,
    anexos,
    atendimentos,
    auditoria,
    auth,
    pessoas,
    referencias,
    tratamentos,
    usuarios,
)

api_router = APIRouter()

api_router.include_router(auth.router)

protegidas = APIRouter(dependencies=[Depends(get_usuario_atual)])
protegidas.include_router(pessoas.router)
protegidas.include_router(atendimentos.router)
protegidas.include_router(tratamentos.router)
protegidas.include_router(anexos.router)
protegidas.include_router(agenda.router)
protegidas.include_router(referencias.router)
protegidas.include_router(usuarios.router)
protegidas.include_router(auditoria.router)

api_router.include_router(protegidas)
