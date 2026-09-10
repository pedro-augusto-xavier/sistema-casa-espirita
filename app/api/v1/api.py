"""Junta todas as rotas da versão 1 da API."""

from fastapi import APIRouter

from app.api.v1.endpoints import pessoas

api_router = APIRouter()
api_router.include_router(pessoas.router)
