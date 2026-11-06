"""Rotas de autenticação: /api/v1/auth

Única rota pública de propósito: POST /auth/login. As outras exigem token,
mas aceitam quem ainda tem pendência (senha provisória, verificação em duas
etapas por configurar) -- é aqui que a pessoa resolve isso.
"""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import SessaoAtual, SessaoDB, UsuarioAtual
from app.core import mfa
from app.core.auditoria import registrar
from app.core.contexto import ip_atual
from app.core.ratelimit import (
    chave_conta,
    chave_ip,
    chave_usuario,
    falhas_por_conta,
    falhas_por_ip,
)
from app.core.security import verificar_senha
from app.core.senhas import problema_da_senha
from app.crud import sessao as crud_sessao
from app.crud import usuario as crud
from app.models.enums import AcaoAuditoria
from app.models.usuario import Usuario
from app.schemas.usuario import (
    MfaCodigoIn,
    MfaDesativarIn,
    MfaInicioOut,
    Token,
    TrocarSenhaIn,
    UsuarioEu,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _erro(codigo_http: int, codigo: str, mensagem: str) -> HTTPException:
    """Erro com um código que o front reconhece (ex: pedir o código MFA)."""
    return HTTPException(
        status_code=codigo_http,
        detail={"codigo": codigo, "mensagem": mensagem},
        headers={"WWW-Authenticate": "Bearer"}
        if codigo_http == status.HTTP_401_UNAUTHORIZED
        else None,
    )


def _registrar_falha_de_login(
    db: SessaoDB, alvo: Usuario | None, motivo: str, chaves: list[str]
) -> None:
    falhas_por_ip.registrar_falha(chaves[0])
    falhas_por_conta.registrar_falha(chaves[1])
    registrar(
        db,
        usuario=None,
        acao=AcaoAuditoria.login_falha,
        entidade="usuario",
        entidade_id=alvo.id if alvo else None,
        # nunca o nome digitado nem a senha: às vezes a pessoa digita a
        # senha no campo do nome, e isso iria parar no log.
        dados={"motivo": motivo},
    )


@router.post("/login", response_model=Token, summary="Entrar (gera token)")
def login(
    db: SessaoDB,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    lembrar: Annotated[bool, Form()] = False,
    codigo: Annotated[str | None, Form(max_length=10)] = None,
):
    """Envie `username` (o nome do usuário) e `password` -- e, se a pessoa
    tiver verificação em duas etapas, o `codigo` do aplicativo autenticador.

    Com `lembrar=true` ("Manter conectado") a sessão dura
    LEMBRAR_TOKEN_EXPIRE_DAYS dias em vez das horas padrão."""
    chaves = [chave_ip(ip_atual()), chave_conta(form.username)]
    falhas_por_ip.exigir_liberado(chaves[0])
    falhas_por_conta.exigir_liberado(chaves[1])

    usuario = crud.autenticar(db, form.username, form.password)
    if usuario is None:
        alvo = crud.get_by_nome(db, form.username)
        _registrar_falha_de_login(
            db, alvo, "senha" if alvo else "usuario_inexistente", chaves
        )
        # mesma mensagem pra "nome não existe" e "senha errada"
        raise _erro(
            status.HTTP_401_UNAUTHORIZED,
            "credenciais",
            "Nome ou senha incorretos.",
        )

    if usuario.senha_provisoria_vencida:
        _registrar_falha_de_login(db, usuario, "senha_provisoria_vencida", chaves)
        raise _erro(
            status.HTTP_401_UNAUTHORIZED,
            "senha_provisoria_vencida",
            "Essa senha provisória venceu. Peça ao administrador para "
            "redefinir a sua senha.",
        )

    if usuario.mfa_ativo:
        if not codigo:
            raise _erro(
                status.HTTP_401_UNAUTHORIZED,
                "mfa_necessario",
                "Digite o código de 6 números do aplicativo autenticador.",
            )
        passo = mfa.verificar(
            usuario.mfa_segredo or "", codigo, usuario.mfa_ultimo_passo
        )
        if passo is None:
            _registrar_falha_de_login(db, usuario, "codigo_mfa", chaves)
            raise _erro(
                status.HTTP_401_UNAUTHORIZED,
                "mfa_invalido",
                "Código inválido ou já usado. Confira o aplicativo e tente de novo.",
            )
        usuario.mfa_ultimo_passo = passo

    falhas_por_conta.limpar(chaves[1])
    usuario.ultimo_login_em = datetime.now(UTC)
    db.commit()
    crud_sessao.limpar_antigas(db)
    token = crud_sessao.abrir(db, usuario, lembrar=lembrar)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.login,
        entidade="usuario",
        entidade_id=usuario.id,
        dados={"manter_conectado": lembrar, "duas_etapas": usuario.mfa_ativo},
    )
    return Token(access_token=token, pendencias=usuario.pendencias)


@router.post(
    "/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Sair (encerra a sessão)"
)
def logout(db: SessaoDB, sessao: SessaoAtual):
    crud_sessao.revogar(db, sessao)
    registrar(
        db,
        usuario=sessao.usuario,
        acao=AcaoAuditoria.logout,
        entidade="usuario",
        entidade_id=sessao.usuario_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UsuarioEu, summary="Meu usuário")
def eu(usuario: UsuarioAtual):
    return UsuarioEu.model_validate(usuario)


@router.post(
    "/trocar-senha",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Trocar a própria senha",
)
def trocar_senha(
    db: SessaoDB, usuario: UsuarioAtual, sessao: SessaoAtual, dados: TrocarSenhaIn
):
    """Exige a senha atual. É também como quem entrou com a senha
    provisória cria a sua -- e as outras sessões abertas com a senha antiga
    são encerradas."""
    limite = chave_usuario(usuario.id)
    falhas_por_conta.exigir_liberado(limite)
    if not verificar_senha(dados.senha_atual, usuario.senha_hash):
        falhas_por_conta.registrar_falha(limite)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha atual incorreta",
        )

    problema = problema_da_senha(dados.senha_nova, nome=usuario.nome)
    if problema is None and dados.senha_nova == dados.senha_atual:
        problema = "A senha nova precisa ser diferente da atual."
    if problema:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=problema
        )

    era_provisoria = usuario.senha_provisoria
    crud.trocar_senha_propria(db, usuario, dados.senha_nova, sessao_atual=sessao.id)
    falhas_por_conta.limpar(limite)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.atualizar,
        entidade="usuario",
        entidade_id=usuario.id,
        dados={
            "senha_alterada": True,
            "por_si_mesmo": True,
            "era_provisoria": era_provisoria,
        },
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ---------- verificação em duas etapas ----------


@router.post(
    "/mfa/iniciar",
    response_model=MfaInicioOut,
    summary="Começar a configurar a verificação em duas etapas",
)
def mfa_iniciar(db: SessaoDB, usuario: UsuarioAtual):
    """Gera um segredo novo e devolve o conteúdo do QR code. Só passa a
    valer depois que a pessoa confirma com um código (/mfa/ativar)."""
    if usuario.mfa_ativo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A verificação em duas etapas já está ativa.",
        )
    segredo = mfa.novo_segredo()
    usuario.mfa_segredo = segredo
    usuario.mfa_ultimo_passo = None
    db.commit()
    return MfaInicioOut(
        segredo=segredo, uri=mfa.uri_de_configuracao(segredo, usuario.nome)
    )


@router.post(
    "/mfa/ativar",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Confirmar o código e ligar a verificação em duas etapas",
)
def mfa_ativar(
    db: SessaoDB, usuario: UsuarioAtual, sessao: SessaoAtual, dados: MfaCodigoIn
):
    if usuario.mfa_ativo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A verificação em duas etapas já está ativa.",
        )
    if not usuario.mfa_segredo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Comece pela leitura do QR code.",
        )
    limite = chave_usuario(usuario.id)
    falhas_por_conta.exigir_liberado(limite)
    passo = mfa.verificar(usuario.mfa_segredo, dados.codigo, None)
    if passo is None:
        falhas_por_conta.registrar_falha(limite)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                "Código não confere. Veja se o horário do celular está certo "
                "e tente de novo."
            ),
        )
    usuario.mfa_ativo = True
    usuario.mfa_ultimo_passo = passo
    db.commit()
    falhas_por_conta.limpar(limite)
    # quem estiver logado em outro lugar (sem o código) perde o acesso
    crud_sessao.revogar_todas(db, usuario.id, exceto=sessao.id)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.atualizar,
        entidade="usuario",
        entidade_id=usuario.id,
        dados={"duas_etapas": "ativada"},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/mfa/desativar",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Desligar a verificação em duas etapas (se não for obrigatória)",
)
def mfa_desativar(db: SessaoDB, usuario: UsuarioAtual, dados: MfaDesativarIn):
    if usuario.mfa_obrigatorio:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pro seu perfil a verificação em duas etapas é obrigatória.",
        )
    limite = chave_usuario(usuario.id)
    falhas_por_conta.exigir_liberado(limite)
    if not verificar_senha(dados.senha, usuario.senha_hash):
        falhas_por_conta.registrar_falha(limite)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha incorreta",
        )
    crud.zerar_mfa(db, usuario)
    registrar(
        db,
        usuario=usuario,
        acao=AcaoAuditoria.atualizar,
        entidade="usuario",
        entidade_id=usuario.id,
        dados={"duas_etapas": "desativada"},
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
