"""Confere que as migrations de criptografia vão e voltam sem perder dado.

Roda no CI, num banco vazio e descartável:
  1. sobe o banco até a versão de ANTES da criptografia;
  2. grava dados de exemplo no formato antigo (tudo em texto puro);
  3. upgrade até a última versão -> tudo cifrado, e decifra pro original;
  4. downgrade de volta -> tudo em texto puro, igual ao original;
  5. upgrade de novo -> cifrado e legível outra vez.
No fim apaga os dados de exemplo (menos a auditoria, que é imutável).

Uso (NUNCA no banco de produção -- o script se recusa se o banco já tiver
tabelas):
    CONFIRMO_BANCO_DESCARTAVEL=1 python -m tests.verificar_migracoes
"""

import json
import os
import sys

from alembic.config import Config
from sqlalchemy import create_engine, text

from alembic import command
from app.core.config import settings
from app.core.cripto import decifrar, hmac_busca

ANTES_DA_CRIPTOGRAFIA = "c8985d0345aa"
ANTES_DA_REATIVACAO = "3f1a9c2e7b54"  # 1352e867c028 vem logo depois
USUARIOS = (
    "Usuario Antigo",
    "Usuario Inativo",
    "Usuario Reativado Sem Senha",
    "Usuario Com Senha Propria",
)

CPF = "11122233344"
ARQUIVO = bytes.fromhex("ffd8ffe0") + b" foto de exemplo"
TEXTOS = {
    # (tabela, coluna): (valor original, contexto da criptografia)
    ("pessoa", "observacoes_gerais"): ("obs da ficha", "pessoa.observacoes_gerais"),
    ("atendimento", "observacao"): ("obs do atendimento", "atendimento.observacao"),
    ("atendimento_tratamento", "observacao"): (
        "obs do tratamento do dia",
        "atendimento_tratamento.observacao",
    ),
    ("tratamento", "situacao_final"): ("situacao final", "tratamento.situacao_final"),
    ("tratamento", "observacao"): ("obs do caso", "tratamento.observacao"),
    ("tratamento_assistido", "situacao_final"): (
        "situacao do assistido",
        "tratamento_assistido.situacao_final",
    ),
    ("tratamento_evolucao", "texto"): ("diario: limpeza", "tratamento_evolucao.texto"),
    ("anexo", "nome_arquivo"): ("exame_fulana.jpg", "anexo.nome_arquivo"),
    ("anexo", "descricao"): ("laudo do medico", "anexo.descricao"),
}

motor = create_engine(settings.DATABASE_URL)
alembic_cfg = Config("alembic.ini")


def falhar(mensagem: str) -> None:
    sys.exit(f"FALHOU: {mensagem}")


def checar(condicao: bool, mensagem: str) -> None:
    if not condicao:
        falhar(mensagem)


def valor(sql: str, **params):
    with motor.connect() as c:
        return c.execute(text(sql), params).scalar()


def recusar_banco_que_nao_seja_descartavel() -> None:
    if os.environ.get("CONFIRMO_BANCO_DESCARTAVEL") != "1":
        falhar("defina CONFIRMO_BANCO_DESCARTAVEL=1 (e use um banco vazio)")
    if valor("SELECT to_regclass('public.alembic_version')") is not None:
        falhar("o banco já tem tabelas -- este script só roda em banco vazio")


def gravar_formato_antigo() -> None:
    with motor.begin() as c:
        def inserir(sql: str, **params) -> int:
            return c.execute(text(sql + " RETURNING id"), params).scalar()

        pessoa = inserir(
            "INSERT INTO pessoa (nome_completo, sexo, cpf, observacoes_gerais, "
            "estado_civil, ativo, anonimizada, consentimento_lgpd, criado_em, "
            "atualizado_em) VALUES ('Migracao Teste', 'nao_informado', :cpf, :obs, "
            "'nao_informado', true, false, false, now(), now())",
            cpf=CPF,
            obs=TEXTOS[("pessoa", "observacoes_gerais")][0],
        )
        tipo = inserir(
            "INSERT INTO tipo_tratamento (nome, formato, ativo) "
            "VALUES ('Tipo Teste Migracao', 'caso', true)"
        )
        atendimento = inserir(
            "INSERT INTO atendimento (pessoa_id, data, presente, modalidade, "
            "observacao, criado_em, atualizado_em) VALUES (:p, current_date, true, "
            "'presencial', :obs, now(), now())",
            p=pessoa,
            obs=TEXTOS[("atendimento", "observacao")][0],
        )
        inserir(
            "INSERT INTO atendimento_tratamento (atendimento_id, tipo_tratamento_id, "
            "sessoes_realizadas, observacao) VALUES (:a, :t, 0, :obs)",
            a=atendimento,
            t=tipo,
            obs=TEXTOS[("atendimento_tratamento", "observacao")][0],
        )
        tratamento = inserir(
            "INSERT INTO tratamento (tipo_tratamento_id, solicitante_id, data_inicio, "
            "status, situacao_final, observacao, criado_em, atualizado_em) VALUES "
            "(:t, :p, current_date, 'em_andamento', :sit, :obs, now(), now())",
            t=tipo,
            p=pessoa,
            sit=TEXTOS[("tratamento", "situacao_final")][0],
            obs=TEXTOS[("tratamento", "observacao")][0],
        )
        inserir(
            "INSERT INTO tratamento_assistido (tratamento_id, pessoa_id, status, "
            "situacao_final) VALUES (:t, :p, 'ativo', :sit)",
            t=tratamento,
            p=pessoa,
            sit=TEXTOS[("tratamento_assistido", "situacao_final")][0],
        )
        inserir(
            "INSERT INTO tratamento_evolucao (tratamento_id, data, texto, criado_em) "
            "VALUES (:t, current_date, :texto, now())",
            t=tratamento,
            texto=TEXTOS[("tratamento_evolucao", "texto")][0],
        )
        inserir(
            "INSERT INTO anexo (pessoa_id, nome_arquivo, tipo_conteudo, tamanho_bytes, "
            "conteudo, descricao, criado_em) VALUES (:p, :nome, 'image/jpeg', :tam, "
            ":conteudo, :desc, now())",
            p=pessoa,
            nome=TEXTOS[("anexo", "nome_arquivo")][0],
            tam=len(ARQUIVO),
            conteudo=ARQUIVO,
            desc=TEXTOS[("anexo", "descricao")][0],
        )
        inserir(
            "INSERT INTO usuario (nome, senha_hash, papel, ativo, criado_em) "
            "VALUES ('Usuario Antigo', 'x', 'operador', true, now())"
        )
        # desativado quando 0adbab7209a9 rodou: o backfill dela pulava
        inserir(
            "INSERT INTO usuario (nome, senha_hash, papel, ativo, criado_em) "
            "VALUES ('Usuario Inativo', 'x', 'operador', false, now())"
        )
        inserir(
            "INSERT INTO audit_log (acao, entidade, entidade_id, dados, criado_em) "
            "VALUES ('atualizar', 'pessoa', :p, CAST(:dados AS jsonb), now())",
            p=pessoa,
            dados=json.dumps({"cpf": {"de": None, "para": CPF}, "ativo": True}),
        )


def gravar_antes_da_reativacao() -> None:
    """Estados possíveis entre 0adbab7209a9 e 1352e867c028."""
    with motor.begin() as c:
        # reativado por PATCH {"ativo": true}: voltou com a senha antiga
        c.execute(
            text(
                "INSERT INTO usuario (nome, senha_hash, papel, ativo, criado_em, "
                "senha_provisoria) VALUES ('Usuario Reativado Sem Senha', 'x', "
                "'admin', true, now(), false)"
            )
        )
        # já criou a senha dele pelas regras novas: não pode ser afetado
        c.execute(
            text(
                "INSERT INTO usuario (nome, senha_hash, papel, ativo, criado_em, "
                "senha_provisoria, senha_alterada_em) VALUES "
                "('Usuario Com Senha Propria', 'x', 'operador', true, now(), "
                "false, now())"
            )
        )


def senha_provisoria_de(nome: str) -> tuple[bool, str]:
    """(senha_provisoria, 'vencida' | 'valendo' | 'sem prazo')"""
    with motor.connect() as c:
        return tuple(
            c.execute(
                text(
                    "SELECT senha_provisoria, CASE "
                    "WHEN senha_provisoria_expira_em IS NULL THEN 'sem prazo' "
                    "WHEN senha_provisoria_expira_em <= now() THEN 'vencida' "
                    "ELSE 'valendo' END FROM usuario WHERE nome = :n"
                ),
                {"n": nome},
            ).one()
        )


def conferir_reativacao() -> None:
    checar(
        senha_provisoria_de("Usuario Reativado Sem Senha") == (True, "vencida"),
        "conta reativada com a senha antiga continua entrando com ela",
    )
    checar(
        senha_provisoria_de("Usuario Com Senha Propria") == (False, "sem prazo"),
        "a migração mexeu em quem já tinha senha própria",
    )


def conferir_cifrado() -> None:
    cpf_cru = bytes(valor("SELECT cpf_cifrado FROM pessoa WHERE cpf_hash IS NOT NULL"))
    checar(CPF.encode() not in cpf_cru, "CPF continua em texto puro")
    checar(decifrar(cpf_cru, "pessoa.cpf").decode() == CPF, "CPF não decifra")
    checar(
        valor("SELECT cpf_hash FROM pessoa WHERE cpf_cifrado IS NOT NULL")
        == hmac_busca(CPF),
        "cpf_hash errado",
    )
    for (tabela, coluna), (original, contexto) in TEXTOS.items():
        cru = bytes(valor(f"SELECT {coluna} FROM {tabela} WHERE {coluna} IS NOT NULL"))
        checar(original.encode() not in cru, f"{tabela}.{coluna} em texto puro")
        checar(
            decifrar(cru, contexto).decode() == original,
            f"{tabela}.{coluna} não decifra pro original",
        )
    arquivo = bytes(valor("SELECT conteudo FROM anexo"))
    checar(arquivo != ARQUIVO, "anexo em texto puro")
    checar(decifrar(arquivo, "anexo.conteudo") == ARQUIVO, "anexo não decifra")

    checar(
        senha_provisoria_de("Usuario Antigo") == (True, "valendo"),
        "usuário existente não ficou com senha provisória (com prazo)",
    )
    checar(
        senha_provisoria_de("Usuario Inativo") == (True, "vencida"),
        "conta inativa escapou da senha provisória",
    )
    dados = valor("SELECT dados FROM audit_log WHERE entidade = 'pessoa'")
    checar(dados["cpf"] == {"alterado": True}, "auditoria ainda guarda o CPF")
    checar(dados["ativo"] is True, "auditoria perdeu campo que não é pessoal")
    try:
        with motor.begin() as c:
            c.execute(text("DELETE FROM audit_log"))
        falhar("o banco deixou apagar a auditoria")
    except Exception as exc:  # noqa: BLE001 -- o esperado é o trigger recusar
        checar("só de inserção" in str(exc), f"erro inesperado: {exc}")


def conferir_texto_puro() -> None:
    cpf = valor("SELECT cpf FROM pessoa WHERE cpf IS NOT NULL")
    checar(cpf == CPF, "CPF não voltou")
    for (tabela, coluna), (original, _) in TEXTOS.items():
        checar(
            valor(f"SELECT {coluna} FROM {tabela} WHERE {coluna} IS NOT NULL")
            == original,
            f"{tabela}.{coluna} não voltou pro original",
        )
    checar(bytes(valor("SELECT conteudo FROM anexo")) == ARQUIVO, "anexo não voltou")


def apagar_dados_de_exemplo() -> None:
    with motor.begin() as c:
        c.execute(text("DELETE FROM tratamento"))
        c.execute(text("DELETE FROM pessoa"))
        c.execute(
            text("DELETE FROM tipo_tratamento WHERE nome = 'Tipo Teste Migracao'")
        )
        c.execute(
            text("DELETE FROM usuario WHERE nome = ANY(:nomes)"),
            {"nomes": list(USUARIOS)},
        )


def main() -> None:
    recusar_banco_que_nao_seja_descartavel()

    command.upgrade(alembic_cfg, ANTES_DA_CRIPTOGRAFIA)
    gravar_formato_antigo()
    print("ok: dados de exemplo no formato antigo")

    command.upgrade(alembic_cfg, ANTES_DA_REATIVACAO)
    gravar_antes_da_reativacao()

    command.upgrade(alembic_cfg, "head")
    conferir_cifrado()
    print("ok: upgrade cifrou tudo e decifra pro original")
    conferir_reativacao()
    print("ok: contas inativas e reativadas sem senha nova ficaram vencidas")

    command.downgrade(alembic_cfg, ANTES_DA_CRIPTOGRAFIA)
    conferir_texto_puro()
    print("ok: downgrade devolveu tudo em texto puro, igual ao original")

    command.upgrade(alembic_cfg, "head")
    conferir_cifrado()
    print("ok: upgrade de novo")

    apagar_dados_de_exemplo()
    print("MIGRATIONS REVERSÍVEIS: tudo certo")


if __name__ == "__main__":
    main()
