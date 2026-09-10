"""Rotas das listas de referência (só leitura por enquanto)."""

from fastapi import APIRouter

from app.api.deps import SessaoDB
from app.crud import referencias as crud
from app.models.enums import FormatoTratamento
from app.schemas.referencias import FuncaoOut, TipoTratamentoOut

router = APIRouter(tags=["referências"])


@router.get(
    "/tipos-tratamento",
    response_model=list[TipoTratamentoOut],
    summary="Listar tipos de tratamento",
)
def listar_tipos_tratamento(
    db: SessaoDB,
    formato: FormatoTratamento | None = None,
    incluir_inativos: bool = False,
):
    tipos = crud.listar_tipos_tratamento(
        db, formato=formato, apenas_ativos=not incluir_inativos
    )
    return [TipoTratamentoOut.model_validate(t) for t in tipos]


@router.get(
    "/funcoes",
    response_model=list[FuncaoOut],
    summary="Listar funções de trabalhador",
)
def listar_funcoes(db: SessaoDB, incluir_inativos: bool = False):
    funcoes = crud.listar_funcoes(db, apenas_ativos=not incluir_inativos)
    return [FuncaoOut.model_validate(f) for f in funcoes]
