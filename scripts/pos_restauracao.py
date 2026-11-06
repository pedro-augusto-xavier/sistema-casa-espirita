"""Refaz as revogações de acesso depois de restaurar o banco de produção
INTEIRO a partir de um backup (branch/PITR do Neon ou artefato do GitHub
num banco novo). Roteiro completo: docs/BACKUP.md.

O banco restaurado não sabe do que aconteceu depois do snapshot: sessões
encerradas, contas desativadas, senhas e MFA redefinidos, papéis rebaixados
voltam a valer. Este script corrige isso no banco do DATABASE_URL (o
restaurado):

  --banco-antigo URL --desde "AAAA-MM-DD HH:MM"
      Compara cada usuário com o banco de ANTES da restauração e aplica o
      mais restritivo: desativado em qualquer um -> desativado; papel -> o
      menor; senha ou MFA diferentes -> senha provisória nova e MFA zerado
      (não dá pra saber se a mudança foi da pessoa ou de quem invadiu).
      Mostra a auditoria de usuários do banco antigo desde --desde (UTC, o
      horário do backup) pra você conferir.

  --sem-banco-antigo
      O banco antigo se perdeu: toda conta ativa recebe senha provisória
      nova e MFA zerado (cada pessoa refaz o acesso).

Nos dois casos: todas as sessões são revogadas, a época de credencial de
todo mundo muda e fica um registro na auditoria. No fim mostra a SECRET_KEY
nova e o SESSOES_VALIDAS_DESDE pra colocar no Render.

Sem --executar só mostra o que faria. Não precisa das chaves de
criptografia: o segredo do MFA é comparado cifrado, como está no banco.

Uso (com DATABASE_URL = banco restaurado; comandos prontos em BACKUP.md):
    python -m scripts.pos_restauracao --banco-antigo "<url>" --desde "AAAA-MM-DD HH:MM"
    python -m scripts.pos_restauracao --sem-banco-antigo
    (confere a saída e repete com --executar)
"""

import argparse
import secrets
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import create_engine, insert, text, update
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.security import hash_senha
from app.crud.usuario import VALIDADE_SENHA_PROVISORIA
from app.models.enums import AcaoAuditoria, PapelUsuario
from app.models.usuario import AuditLog, SessaoUsuario, Usuario


@dataclass(frozen=True)
class Acesso:
    """Colunas de acesso de um usuário, cruas como estão no banco."""

    id: int
    nome: str
    ativo: bool
    papel: str
    senha_hash: str
    mfa_ativo: bool
    mfa_segredo: bytes | None  # cifrado


@dataclass
class Acao:
    usuario_id: int
    nome: str
    desativar: bool = False
    rebaixar: bool = False
    nova_senha: bool = False
    motivos: list[str] = field(default_factory=list)


def ler_acessos(conn) -> dict[int, Acesso]:  # noqa: ANN001 -- Session ou Connection
    linhas = conn.execute(
        text(
            "SELECT id, nome, ativo, papel, senha_hash, mfa_ativo, mfa_segredo "
            "FROM usuario"
        )
    )
    return {
        linha.id: Acesso(
            *linha[:6], bytes(linha.mfa_segredo) if linha.mfa_segredo else None
        )
        for linha in linhas
    }


def decidir(
    restaurado: dict[int, Acesso], antigo: dict[int, Acesso] | None
) -> list[Acao]:
    """O que fazer em cada usuário do banco restaurado. `antigo` None =
    sem banco antigo (toda conta ativa refaz o acesso)."""
    acoes = []
    for r in sorted(restaurado.values(), key=lambda u: u.id):
        acao = Acao(r.id, r.nome)
        a = antigo.get(r.id) if antigo is not None else None
        if not r.ativo:
            pass  # já está sem acesso; reativar gera senha nova
        elif antigo is None:
            acao.nova_senha = True
            acao.motivos.append("sem banco antigo: refaz o acesso")
        elif a is None:
            acao.nova_senha = True
            acao.motivos.append("não existe no banco antigo")
        else:
            if not a.ativo:
                acao.desativar = True
                acao.motivos.append("foi desativado depois do backup")
            if r.papel == PapelUsuario.admin.value and a.papel != r.papel:
                acao.rebaixar = True
                acao.motivos.append("deixou de ser admin depois do backup")
            if not acao.desativar and (
                r.senha_hash != a.senha_hash
                or r.mfa_ativo != a.mfa_ativo
                or r.mfa_segredo != a.mfa_segredo
            ):
                acao.nova_senha = True
                acao.motivos.append("senha ou duas etapas mudou depois do backup")
        if acao.motivos:
            acoes.append(acao)
    return acoes


def aplicar(
    db: Session, acoes: list[Acao], *, agora: datetime
) -> list[tuple[str, str]]:
    """Aplica as ações, troca a época de credencial de todo mundo e revoga
    todas as sessões. Não faz commit. Devolve (nome, senha provisória)."""
    senhas = []
    for acao in acoes:
        valores: dict = {}
        if acao.desativar:
            valores["ativo"] = False
        if acao.rebaixar:
            valores["papel"] = PapelUsuario.operador
        if acao.nova_senha:
            senha = secrets.token_urlsafe(12)  # igual a crud.usuario
            valores.update(
                senha_hash=hash_senha(senha),
                senha_provisoria=True,
                senha_provisoria_expira_em=agora + VALIDADE_SENHA_PROVISORIA,
                senha_alterada_em=agora,
                mfa_ativo=False,
                mfa_segredo=None,
                mfa_ultimo_passo=None,
            )
            senhas.append((acao.nome, senha))
        db.execute(
            update(Usuario).where(Usuario.id == acao.usuario_id).values(**valores)
        )
    db.execute(update(Usuario).values(epoca_credencial=agora))
    db.execute(
        update(SessaoUsuario)
        .where(SessaoUsuario.revogada_em.is_(None))
        .values(revogada_em=agora)
    )
    db.execute(
        insert(AuditLog).values(
            usuario_id=None,
            acao=AcaoAuditoria.atualizar,
            entidade="usuario",
            dados={
                "pos_restauracao": True,
                "desativados": sum(a.desativar for a in acoes),
                "rebaixados": sum(a.rebaixar for a in acoes),
                "senhas_novas": len(senhas),
            },
        )
    )
    return senhas


def listar_auditoria(conn, desde: datetime) -> list:  # noqa: ANN001
    """Tudo que a auditoria registrou sobre usuários desde o backup."""
    return list(
        conn.execute(
            text(
                "SELECT a.criado_em, a.acao, a.entidade_id, alvo.nome AS alvo, "
                "quem.nome AS quem, a.dados, a.ip "
                "FROM audit_log a "
                "LEFT JOIN usuario alvo ON alvo.id = a.entidade_id "
                "LEFT JOIN usuario quem ON quem.id = a.usuario_id "
                "WHERE a.entidade = 'usuario' AND a.criado_em >= :desde "
                "ORDER BY a.criado_em"
            ),
            {"desde": desde},
        )
    )


def _com_driver(url: str) -> str:
    """Mesma conversão do config.py: URL do Neon vem sem o driver."""
    for prefixo in ("postgres://", "postgresql://"):
        if url.startswith(prefixo):
            return "postgresql+psycopg://" + url[len(prefixo) :]
    return url


def _ler_desde(valor: str) -> datetime:
    data = datetime.fromisoformat(valor)
    return data if data.tzinfo else data.replace(tzinfo=UTC)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refaz as revogações de acesso depois de restaurar um backup"
    )
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--banco-antigo", metavar="URL")
    grupo.add_argument("--sem-banco-antigo", action="store_true")
    parser.add_argument("--desde", help='horário do backup, em UTC: "AAAA-MM-DD HH:MM"')
    parser.add_argument("--executar", action="store_true")
    args = parser.parse_args()
    if args.banco_antigo and not args.desde:
        parser.error("--desde é obrigatório com --banco-antigo")
    engine.echo = False  # roda sem APP_ENV (dev), mas o SQL só polui a saída

    alvo = make_url(settings.DATABASE_URL)
    print(f"Banco restaurado (DATABASE_URL): {alvo.host}/{alvo.database}")

    antigo = None
    if args.banco_antigo:
        url_antigo = make_url(_com_driver(args.banco_antigo))
        if (url_antigo.host, url_antigo.database) == (alvo.host, alvo.database):
            sys.exit("O banco antigo é o mesmo do DATABASE_URL. Confira as URLs.")
        print(
            f"Banco antigo (só leitura):       {url_antigo.host}/{url_antigo.database}"
        )
        motor = create_engine(url_antigo)
        try:
            with motor.connect() as conn:
                conn.execute(text("SET TRANSACTION READ ONLY"))
                antigo = ler_acessos(conn)
                auditoria = listar_auditoria(conn, _ler_desde(args.desde))
        finally:
            motor.dispose()

        print(f"\nAuditoria de usuários no banco antigo desde {args.desde} UTC:")
        for linha in auditoria:
            print(
                f"  {linha.criado_em:%Y-%m-%d %H:%M} UTC  {linha.acao:<12} "
                f"alvo={linha.alvo or linha.entidade_id or '-'}  "
                f"por={linha.quem or '-'}  {linha.dados or ''}  ip={linha.ip or '-'}"
            )
        if not auditoria:
            print("  (nada)")

    with SessionLocal() as db:
        restaurado = ler_acessos(db)
        acoes = decidir(restaurado, antigo)

        if antigo is not None:
            novos = [antigo[i].nome for i in sorted(set(antigo) - set(restaurado))]
            if novos:
                print(
                    "\nCriados depois do backup (não existem no restaurado; "
                    f"recrie se precisar): {', '.join(novos)}"
                )

        print("\nO que muda no banco restaurado:")
        for acao in acoes:
            print(f"  {acao.nome}: {'; '.join(acao.motivos)}")
        if not acoes:
            print("  nenhuma conta muda")
        print("  + todas as sessões revogadas e a época de credencial de todos trocada")

        if not args.executar:
            print("\nSimulação: nada foi alterado. Rode de novo com --executar.")
            return

        confirmacao = input(
            f"\nDigite o nome do banco ({alvo.database}) pra confirmar: "
        ).strip()
        if confirmacao != alvo.database:
            sys.exit("Não confere. Nada foi alterado.")

        agora = datetime.now(UTC).replace(microsecond=0)
        senhas = aplicar(db, acoes, agora=agora)
        db.commit()

    print("\nFeito.")
    if senhas:
        print(
            "\nSenhas provisórias (valem 72h e aparecem só agora; "
            "repasse a cada pessoa):"
        )
        for nome, senha in senhas:
            print(f"  {nome}: {senha}")
    print("\nNo Render (Environment), troque/crie e salve (o serviço reinicia):")
    print(f"  SECRET_KEY={secrets.token_hex(32)}")
    print(f"  SESSOES_VALIDAS_DESDE={agora.isoformat().replace('+00:00', 'Z')}")


if __name__ == "__main__":
    main()
