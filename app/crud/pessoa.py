"""Acesso ao banco para Pessoa. As rotas chamam estas funções -- assim a
lógica de banco fica separada da lógica HTTP e dá pra testar isolado.
"""

from datetime import UTC, date, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.validators import so_digitos
from app.models.enums import EstadoCivil, Papel
from app.models.pessoa import Pessoa, PessoaPapel
from app.schemas.pessoa import PessoaCreate, PessoaUpdate


def get(db: Session, pessoa_id: int) -> Pessoa | None:
    stmt = (
        select(Pessoa)
        .options(selectinload(Pessoa.papeis))
        .where(Pessoa.id == pessoa_id)
    )
    return db.scalar(stmt)


def get_by_cpf(db: Session, cpf: str) -> Pessoa | None:
    return db.scalar(select(Pessoa).where(Pessoa.cpf == so_digitos(cpf)))


def listar(
    db: Session,
    *,
    q: str | None = None,
    papel: Papel | None = None,
    apenas_ativos: bool = True,
    page: int = 1,
    size: int = 20,
) -> tuple[list[Pessoa], int]:
    stmt = select(Pessoa).options(selectinload(Pessoa.papeis))

    if apenas_ativos:
        stmt = stmt.where(Pessoa.ativo.is_(True))

    if q:
        termo = f"%{q.strip()}%"
        condicoes = [
            Pessoa.nome_completo.ilike(termo),
            Pessoa.telefone.ilike(termo),
        ]
        digitos = so_digitos(q)
        if digitos:
            condicoes.append(Pessoa.cpf.ilike(f"%{digitos}%"))
        stmt = stmt.where(or_(*condicoes))

    if papel is not None:
        stmt = stmt.where(Pessoa.papeis.any(PessoaPapel.papel == papel))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = (
        stmt.order_by(Pessoa.nome_completo)
        .offset((page - 1) * size)
        .limit(size)
    )
    pessoas = list(db.scalars(stmt).all())
    return pessoas, total


def _aplica_papeis(pessoa: Pessoa, papeis: list[Papel]) -> None:
    desejados = set(papeis)
    atuais = {p.papel for p in pessoa.papeis}

    for pp in list(pessoa.papeis):
        if pp.papel not in desejados:
            pessoa.papeis.remove(pp)
    for papel in desejados - atuais:
        pessoa.papeis.append(PessoaPapel(papel=papel))


def criar(db: Session, dados: PessoaCreate) -> Pessoa:
    payload = dados.model_dump(exclude={"papeis"})
    pessoa = Pessoa(**payload)

    if dados.consentimento_lgpd:
        pessoa.consentimento_em = datetime.now(UTC)

    _aplica_papeis(pessoa, dados.papeis)

    db.add(pessoa)
    db.commit()
    db.refresh(pessoa)
    return get(db, pessoa.id)  # type: ignore[return-value]


def _serializa(valor: object) -> object:
    """Deixa o valor pronto pra guardar em JSON (audit_log.dados)."""
    if isinstance(valor, date | datetime):
        return valor.isoformat()
    return getattr(valor, "value", valor)


def atualizar(
    db: Session, pessoa: Pessoa, dados: PessoaUpdate
) -> tuple[Pessoa, dict[str, dict[str, object]]]:
    """Atualiza e devolve também o que mudou (de/para), pra auditoria."""
    mudancas = dados.model_dump(exclude_unset=True, exclude={"papeis"})

    alteracoes: dict[str, dict[str, object]] = {}
    for campo, valor_novo in mudancas.items():
        valor_antigo = getattr(pessoa, campo)
        if valor_antigo != valor_novo:
            alteracoes[campo] = {
                "de": _serializa(valor_antigo),
                "para": _serializa(valor_novo),
            }

    if "consentimento_lgpd" in mudancas:
        novo = mudancas["consentimento_lgpd"]
        if novo and not pessoa.consentimento_lgpd:
            pessoa.consentimento_em = datetime.now(UTC)
        elif not novo:
            pessoa.consentimento_em = None

    for campo, valor in mudancas.items():
        setattr(pessoa, campo, valor)

    if dados.papeis is not None:
        papeis_antigos = sorted(p.papel.value for p in pessoa.papeis)
        _aplica_papeis(pessoa, dados.papeis)
        papeis_novos = sorted(p.value for p in dados.papeis)
        if papeis_antigos != papeis_novos:
            alteracoes["papeis"] = {"de": papeis_antigos, "para": papeis_novos}

    db.commit()
    db.refresh(pessoa)
    return get(db, pessoa.id), alteracoes  # type: ignore[return-value]


def desativar(db: Session, pessoa: Pessoa) -> None:
    """Exclusão lógica -- a ficha continua no banco, só sai das listas."""
    pessoa.ativo = False
    db.commit()


_CAMPOS_PESSOAIS = (
    "cpf",
    "telefone",
    "data_nascimento",
    "logradouro",
    "numero",
    "complemento",
    "bairro",
    "cidade",
    "uf",
    "cep",
    "como_conheceu",
    "observacoes_gerais",
    "quantidade_filhos",
)


def anonimizar(db: Session, pessoa: Pessoa) -> Pessoa:
    """LGPD -- direito ao esquecimento.

    Apaga os dados pessoais mas mantém a linha (e os vínculos com atendimentos)
    para o histórico não ficar órfão.
    """
    from app.crud.anexo import remover_todos_da_pessoa

    pessoa.nome_completo = "(dados removidos)"
    for campo in _CAMPOS_PESSOAIS:
        setattr(pessoa, campo, None)
    pessoa.estado_civil = EstadoCivil.nao_informado  # coluna não aceita nulo
    pessoa.anonimizada = True
    pessoa.ativo = False
    pessoa.consentimento_lgpd = False
    pessoa.consentimento_em = None
    pessoa.papeis.clear()
    db.commit()

    # fotos e documentos são dado pessoal também -- e mais sensível que a
    # maioria dos campos de texto que acabamos de apagar.
    remover_todos_da_pessoa(db, pessoa.id)

    return get(db, pessoa.id)  # type: ignore[return-value]


def exportar_dados(db: Session, pessoa_id: int) -> dict:
    """Reúne tudo que o sistema guarda sobre a pessoa (direito de acesso),
    incluindo quem alterou a ficha dela e quando.
    """
    from app.models.anexo import Anexo
    from app.models.atendimento import Atendimento
    from app.models.tratamento import TratamentoAssistido, TratamentoEvolucao
    from app.models.usuario import AuditLog

    pessoa = get(db, pessoa_id)
    if pessoa is None:
        return {}

    edicoes = db.scalars(
        select(AuditLog)
        .options(selectinload(AuditLog.usuario))
        .where(AuditLog.entidade == "pessoa", AuditLog.entidade_id == pessoa_id)
        .order_by(AuditLog.criado_em.desc())
    ).all()

    atendimentos = db.scalars(
        select(Atendimento)
        .options(selectinload(Atendimento.tratamentos))
        .where(Atendimento.pessoa_id == pessoa_id)
    ).all()

    participacoes = db.scalars(
        select(TratamentoAssistido).where(
            TratamentoAssistido.pessoa_id == pessoa_id
        )
    ).all()

    evolucoes = db.scalars(
        select(TratamentoEvolucao).where(
            TratamentoEvolucao.pessoa_id == pessoa_id
        )
    ).all()

    anexos = db.scalars(select(Anexo).where(Anexo.pessoa_id == pessoa_id)).all()

    def _dict(obj, campos):
        return {c: getattr(obj, c) for c in campos}

    return {
        "pessoa": _dict(
            pessoa,
            [
                "id",
                "nome_completo",
                "data_nascimento",
                "sexo",
                "cpf",
                "telefone",
                "estado_civil",
                "quantidade_filhos",
                "logradouro",
                "numero",
                "complemento",
                "bairro",
                "cidade",
                "uf",
                "cep",
                "como_conheceu",
                "observacoes_gerais",
                "consentimento_lgpd",
                "consentimento_em",
                "ativo",
                "anonimizada",
                "criado_em",
                "atualizado_em",
            ],
        ),
        "papeis": [p.papel.value for p in pessoa.papeis],
        "atendimentos": [
            {
                **_dict(
                    a,
                    [
                        "id",
                        "data",
                        "modalidade",
                        "presente",
                        "ordem_chegada",
                        "observacao",
                        "retorno_previsto",
                    ],
                ),
                "tratamentos": [t.tipo_tratamento_nome for t in a.tratamentos],
            }
            for a in atendimentos
        ],
        "tratamentos_como_assistido": [
            _dict(
                p,
                [
                    "id",
                    "tratamento_id",
                    "status",
                    "situacao_final",
                    "data_conclusao",
                ],
            )
            for p in participacoes
        ],
        "evolucoes": [
            _dict(e, ["id", "tratamento_id", "data", "texto"]) for e in evolucoes
        ],
        # metadados só -- não embute o conteúdo do arquivo no export.
        "anexos": [
            _dict(
                a,
                [
                    "id",
                    "nome_arquivo",
                    "tipo_conteudo",
                    "tamanho_bytes",
                    "descricao",
                    "criado_em",
                ],
            )
            for a in anexos
        ],
        "historico_edicoes": [
            {
                "quem": e.usuario_nome,
                "acao": e.acao.value,
                "quando": e.criado_em,
                "o_que_mudou": e.dados,
            }
            for e in edicoes
        ],
    }


def reativar(db: Session, pessoa: Pessoa) -> Pessoa:
    pessoa.ativo = True
    db.commit()
    db.refresh(pessoa)
    return get(db, pessoa.id)  # type: ignore[return-value]
