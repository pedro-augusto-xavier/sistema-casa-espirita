"""Junta todas as rotas da versão 1 da API.

Rotas públicas (sem login), de propósito -- e SÓ estas:
  - POST /api/v1/auth/login
  - GET  /health e GET /   (status, sem dado nenhum)
O teste `test_toda_rota_exige_login` confere isso automaticamente: se
alguém criar uma rota nova e esquecer a proteção, o CI quebra.

Todo o resto exige usuário logado, com sessão válida e sem pendência
(senha provisória trocada, verificação em duas etapas configurada quando
obrigatória). As rotas de /auth exigem login também, mas aceitam quem tem
pendência -- é lá que ela é resolvida.
"""

from fastapi import APIRouter, Depends

from app.api.deps import exigir_sem_pendencias
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

protegidas = APIRouter(dependencies=[Depends(exigir_sem_pendencias)])
protegidas.include_router(pessoas.router)
protegidas.include_router(atendimentos.router)
protegidas.include_router(tratamentos.router)
protegidas.include_router(anexos.router)
protegidas.include_router(agenda.router)
protegidas.include_router(referencias.router)
protegidas.include_router(usuarios.router)
protegidas.include_router(auditoria.router)

api_router.include_router(protegidas)
