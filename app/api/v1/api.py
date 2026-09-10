"""Junta todas as rotas da versão 1 da API."""

from fastapi import APIRouter

from app.api.v1.endpoints import atendimentos, pessoas, referencias

api_router = APIRouter()
api_router.include_router(pessoas.router)
api_router.include_router(atendimentos.router)
api_router.include_router(referencias.router)
