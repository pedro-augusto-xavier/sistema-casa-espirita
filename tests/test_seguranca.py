"""Testes das proteções de segurança -- o "pentest básico" do checklist,
automatizado pra rodar no CI a cada push:

- toda rota exige login (menos as públicas de propósito);
- rota de admin recusa usuário comum;
- campos extras no JSON (papel, id, ativo...) não passam;
- ' OR 1=1 -- e <script> nos campos de texto não fazem nada;
- erro interno não vaza detalhe;
- limite de tentativas por IP e por conta;
- regras de senha forte;
- verificação em duas etapas;
- cabeçalhos de segurança e a trava contra chave fraca em produção.
"""

import time

import pyotp
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.ratelimit import falhas_por_conta, falhas_por_ip
from app.core.security import hash_senha
from app.core.senhas import problema_da_senha
from app.crud import sessao as crud_sessao
from app.main import app
from app.models.enums import PapelUsuario
from app.models.usuario import Usuario
from tests.conftest import SENHA_BOA

ROTAS_PUBLICAS = {("POST", "/api/v1/auth/login")}

# Tudo que é só de administrador. Rota nova de admin entra aqui; o teste
# confere que um usuário comum leva 403 em cada uma.
PREFIXOS_SO_ADMIN = ("/api/v1/usuarios", "/api/v1/auditoria")
ROTAS_SO_ADMIN = {
    ("POST", "/api/v1/pessoas/{pessoa_id}/anonimizar"),
    ("GET", "/api/v1/pessoas/{pessoa_id}/exportar"),
}


def _rotas_da_api() -> list[tuple[str, str]]:
    """(método, caminho) de todas as rotas, lidas do esquema OpenAPI -- o
    jeito público de listar, que não depende de detalhe interno do FastAPI."""
    esquema = app.openapi()
    return [
        (metodo.upper(), caminho)
        for caminho, operacoes in esquema["paths"].items()
        if caminho.startswith("/api/v1")
        for metodo in operacoes
    ]


def _caminho_concreto(caminho: str) -> str:
    """/pessoas/{pessoa_id}/anexos -> /pessoas/1/anexos"""
    partes = [("1" if p.startswith("{") else p) for p in caminho.split("/")]
    return "/".join(partes)


# ---------- controle de acesso ----------


def test_toda_rota_exige_login(client_anon: TestClient):
    """Se alguém criar uma rota nova e esquecer a proteção, este teste quebra."""
    rotas = _rotas_da_api()
    assert len(rotas) > 30  # sanidade: achou as rotas mesmo
    for metodo, caminho in rotas:
        if (metodo, caminho) in ROTAS_PUBLICAS:
            continue
        r = client_anon.request(metodo, _caminho_concreto(caminho))
        assert r.status_code == 401, f"{metodo} {caminho} respondeu {r.status_code}"


def test_rotas_de_admin_recusam_usuario_comum(client_anon: TestClient, entrar_como):
    headers = entrar_como("Operador Comum")
    rotas_admin = [
        (m, c)
        for m, c in _rotas_da_api()
        if c.startswith(PREFIXOS_SO_ADMIN) or (m, c) in ROTAS_SO_ADMIN
    ]
    assert len(rotas_admin) >= 9
    for metodo, caminho in rotas_admin:
        r = client_anon.request(metodo, _caminho_concreto(caminho), headers=headers)
        assert r.status_code == 403, f"{metodo} {caminho} respondeu {r.status_code}"


def test_operador_nao_se_promove_a_admin(client_anon: TestClient, entrar_como):
    headers = entrar_como("Quer Ser Admin")
    eu = client_anon.get("/api/v1/auth/me", headers=headers).json()
    r = client_anon.patch(
        f"/api/v1/usuarios/{eu['id']}", json={"papel": "admin"}, headers=headers
    )
    assert r.status_code == 403
    assert (
        client_anon.get("/api/v1/auth/me", headers=headers).json()["papel"]
        == "operador"
    )


# ---------- campos extras no JSON (mass assignment) ----------


def test_campos_extras_no_cadastro_de_usuario_sao_recusados(client: TestClient):
    for extra in ({"ativo": False}, {"mfa_ativo": True}, {"senha_provisoria": False}):
        r = client.post(
            "/api/v1/usuarios",
            json={"nome": "Campo Extra", **extra},
        )
        assert r.status_code == 422, extra


def test_campos_internos_da_pessoa_nao_sao_aceitos(client: TestClient):
    r = client.post(
        "/api/v1/pessoas",
        json={
            "nome_completo": "Tentou Injetar",
            "id": 999999,
            "anonimizada": True,
            "ativo": False,
            "consentimento_em": "2020-01-01T00:00:00Z",
            "cpf_hash": "abc",
        },
    )
    assert r.status_code == 201, r.text
    p = r.json()
    assert p["id"] != 999999
    assert p["anonimizada"] is False
    assert p["ativo"] is True
    assert p["consentimento_em"] is None

    # na edição, campo desconhecido é erro
    r = client.patch(f"/api/v1/pessoas/{p['id']}", json={"anonimizada": True})
    assert r.status_code == 422


# ---------- injeção ----------


def test_sql_injection_na_busca_nao_faz_nada(client: TestClient):
    client.post("/api/v1/pessoas", json={"nome_completo": "Pessoa Comum"})
    for termo in ("' OR 1=1 --", "'; DROP TABLE pessoa; --", '" OR ""="'):
        r = client.get("/api/v1/pessoas", params={"q": termo})
        assert r.status_code == 200
        assert r.json()["total"] == 0
    # a tabela continua lá
    assert (
        client.get("/api/v1/pessoas", params={"q": "Pessoa Comum"}).json()["total"] >= 1
    )


def test_script_no_texto_e_guardado_como_texto(client: TestClient):
    """A API guarda e devolve o texto como veio (JSON, sem interpretar). Quem
    mostra é o React, que escapa tudo -- e a CSP do site bloqueia script
    inline de qualquer jeito."""
    xss = "<script>alert(1)</script><img src=x onerror=alert(1)>"
    r = client.post(
        "/api/v1/pessoas", json={"nome_completo": xss, "observacoes_gerais": xss}
    )
    assert r.status_code == 201
    assert r.json()["nome_completo"] == xss
    assert r.headers["content-type"].startswith("application/json")


# ---------- erros não vazam detalhe ----------


def test_erro_interno_devolve_mensagem_generica(
    db: Session, usuario_admin: Usuario, monkeypatch
):
    from app.core.database import get_db
    from app.crud import pessoa as crud_pessoa

    def explode(*args, **kwargs):
        raise RuntimeError("detalhe interno: SELECT * FROM pessoa WHERE senha=...")

    monkeypatch.setattr(crud_pessoa, "listar", explode)
    app.dependency_overrides[get_db] = lambda: db
    token = crud_sessao.abrir(db, usuario_admin)
    try:
        with TestClient(
            app,
            raise_server_exceptions=False,
            headers={"Authorization": f"Bearer {token}"},
        ) as c:
            r = c.get("/api/v1/pessoas")
    finally:
        app.dependency_overrides.clear()
    assert r.status_code == 500
    assert "SELECT" not in r.text
    assert "Traceback" not in r.text
    assert "Erro interno" in r.json()["detail"]


def test_erro_de_validacao_nao_devolve_o_valor_enviado(client: TestClient):
    segredo = "minha-senha-secreta-" * 10  # passa do máximo de 128
    r = client.post(
        "/api/v1/auth/trocar-senha",
        json={"senha_atual": segredo, "senha_nova": "x"},
    )
    assert r.status_code == 422
    assert "minha-senha-secreta" not in r.text


# ---------- limite de tentativas ----------


def _login(client: TestClient, nome: str, senha: str, ip: str):
    return client.post(
        "/api/v1/auth/login",
        data={"username": nome, "password": senha},
        headers={"CF-Connecting-IP": ip},
    )


def _criar(client: TestClient, nome: str) -> str:
    """Admin cria o usuário; devolve a senha provisória gerada."""
    r = client.post("/api/v1/usuarios", json={"nome": nome})
    assert r.status_code == 201, r.text
    return r.json()["senha_gerada"]


def test_conta_e_bloqueada_mesmo_trocando_de_ip(client: TestClient, client_anon):
    senha = _criar(client, "Alvo Unico")
    for i in range(falhas_por_conta.limite):
        assert (
            _login(client_anon, "Alvo Unico", "chute", f"198.51.100.{i}").status_code
            == 401
        )
    # 6ª tentativa, de outro IP e com a senha CERTA: ainda bloqueada
    r = _login(client_anon, "Alvo Unico", senha, "198.51.100.200")
    assert r.status_code == 429


def test_ip_e_bloqueado_mesmo_trocando_de_nome(client_anon: TestClient):
    for i in range(falhas_por_ip.limite):
        assert (
            _login(client_anon, f"nome {i}", "chute", "203.0.113.9").status_code == 401
        )
    assert _login(client_anon, "outro nome", "chute", "203.0.113.9").status_code == 429


def test_acertar_a_senha_nao_gasta_tentativa(client: TestClient, client_anon):
    senha = _criar(client, "Entra Sempre")
    for _ in range(falhas_por_ip.limite + 2):
        assert (
            _login(client_anon, "Entra Sempre", senha, "192.0.2.1").status_code == 200
        )


def test_login_fica_na_auditoria_com_ip(client: TestClient, client_anon: TestClient):
    senha = _criar(client, "Loga Com Ip")
    _login(client_anon, "Loga Com Ip", senha, "203.0.113.77")
    _login(client_anon, "Loga Com Ip", "errada", "203.0.113.78")

    logs = client.get("/api/v1/auditoria", params={"entidade": "usuario"}).json()[
        "items"
    ]
    sucesso = next(x for x in logs if x["acao"] == "login")
    falha = next(x for x in logs if x["acao"] == "login_falha")
    assert sucesso["ip"] == "203.0.113.77"
    assert falha["ip"] == "203.0.113.78"
    # o log da falha não guarda o que foi digitado
    assert "errada" not in str(falha["dados"])


# ---------- senha forte ----------


@pytest.mark.parametrize(
    ("senha", "trecho_do_erro"),
    [
        ("curta1", "10 caracteres"),
        ("1234567890", "muito usada"),
        ("senha12345", "muito usada"),
        ("aaaaaaaaaaaa", "repetido"),
        ("39053344705", "uma letra"),
        ("amoreperdao-123", "nome da casa"),
        ("Casa Espírita 1", "nome da casa"),
        ("monica-rego-2026", "seu nome"),
    ],
)
def test_senhas_fracas_sao_recusadas(senha: str, trecho_do_erro: str):
    problema = problema_da_senha(senha, nome="Monica Rego")
    assert problema is not None
    assert trecho_do_erro in problema


def test_senha_boa_passa():
    assert problema_da_senha("girassol amarelo na janela", nome="Monica Rego") is None
    assert problema_da_senha(SENHA_BOA, nome="Monica Rego") is None


def test_trocar_senha_aplica_as_regras(client: TestClient, client_anon: TestClient):
    senha = _criar(client, "Regra Senha")
    token = _login(client_anon, "Regra Senha", senha, "192.0.2.5").json()[
        "access_token"
    ]
    headers = {"Authorization": f"Bearer {token}"}
    fraca = client_anon.post(
        "/api/v1/auth/trocar-senha",
        json={"senha_atual": senha, "senha_nova": "12345678901"},
        headers=headers,
    )
    assert fraca.status_code == 422
    igual = client_anon.post(
        "/api/v1/auth/trocar-senha",
        json={"senha_atual": senha, "senha_nova": senha},
        headers=headers,
    )
    assert igual.status_code == 422
    errada = client_anon.post(
        "/api/v1/auth/trocar-senha",
        json={"senha_atual": "chutada", "senha_nova": SENHA_BOA},
        headers=headers,
    )
    assert errada.status_code == 401


def test_trocar_senha_exige_token(client_anon: TestClient):
    r = client_anon.post(
        "/api/v1/auth/trocar-senha",
        json={"senha_atual": "x", "senha_nova": "umasenhaboa1"},
    )
    assert r.status_code == 401


# ---------- verificação em duas etapas ----------


def _proximo_codigo(segredo: str) -> str:
    """Código do PRÓXIMO intervalo de 30s: o atual já foi usado pra ativar."""
    return pyotp.TOTP(segredo).at(time.time() + 30)


def test_duas_etapas_opcional_pra_operador(client_anon: TestClient, entrar_como):
    headers = entrar_como("Quer Duas Etapas")

    inicio = client_anon.post("/api/v1/auth/mfa/iniciar", headers=headers)
    assert inicio.status_code == 200
    segredo = inicio.json()["segredo"]
    assert inicio.json()["uri"].startswith("otpauth://totp/")

    errado = client_anon.post(
        "/api/v1/auth/mfa/ativar", json={"codigo": "000000"}, headers=headers
    )
    assert errado.status_code == 422
    ok = client_anon.post(
        "/api/v1/auth/mfa/ativar",
        json={"codigo": pyotp.TOTP(segredo).now()},
        headers=headers,
    )
    assert ok.status_code == 204, ok.text

    # login agora pede o código
    base = {"username": "Quer Duas Etapas", "password": SENHA_BOA}
    sem_codigo = client_anon.post("/api/v1/auth/login", data=base)
    assert sem_codigo.status_code == 401
    assert sem_codigo.json()["detail"]["codigo"] == "mfa_necessario"

    codigo_errado = client_anon.post(
        "/api/v1/auth/login", data={**base, "codigo": "123456"}
    )
    assert codigo_errado.json()["detail"]["codigo"] == "mfa_invalido"

    codigo = _proximo_codigo(segredo)
    com_codigo = client_anon.post("/api/v1/auth/login", data={**base, "codigo": codigo})
    assert com_codigo.status_code == 200, com_codigo.text

    # o mesmo código não serve duas vezes
    repetido = client_anon.post("/api/v1/auth/login", data={**base, "codigo": codigo})
    assert repetido.status_code == 401

    # operador pode desligar (com a senha)
    novo = {"Authorization": f"Bearer {com_codigo.json()['access_token']}"}
    r = client_anon.post(
        "/api/v1/auth/mfa/desativar", json={"senha": SENHA_BOA}, headers=novo
    )
    assert r.status_code == 204
    assert client_anon.post("/api/v1/auth/login", data=base).status_code == 200


def _admin_sem_mfa(db: Session) -> dict[str, str]:
    admin = Usuario(
        nome="Admin Novo",
        senha_hash=hash_senha(SENHA_BOA),
        papel=PapelUsuario.admin,
        senha_provisoria=False,
    )
    db.add(admin)
    db.flush()
    return {"Authorization": f"Bearer {crud_sessao.abrir(db, admin)}"}


def test_admin_e_obrigado_a_configurar_duas_etapas(
    client_anon: TestClient, db: Session
):
    headers = _admin_sem_mfa(db)

    eu = client_anon.get("/api/v1/auth/me", headers=headers).json()
    assert eu["pendencias"] == ["configurar_mfa"]
    assert client_anon.get("/api/v1/pessoas", headers=headers).status_code == 403

    segredo = client_anon.post("/api/v1/auth/mfa/iniciar", headers=headers).json()[
        "segredo"
    ]
    client_anon.post(
        "/api/v1/auth/mfa/ativar",
        json={"codigo": pyotp.TOTP(segredo).now()},
        headers=headers,
    )
    assert client_anon.get("/api/v1/pessoas", headers=headers).status_code == 200

    # e não pode desligar
    r = client_anon.post(
        "/api/v1/auth/mfa/desativar", json={"senha": SENHA_BOA}, headers=headers
    )
    assert r.status_code == 403


def test_duas_etapas_pode_virar_opcional_pela_configuracao(
    client_anon: TestClient, db: Session, monkeypatch
):
    monkeypatch.setattr(settings, "MFA_OBRIGATORIO", "ninguem")
    headers = _admin_sem_mfa(db)
    assert client_anon.get("/api/v1/pessoas", headers=headers).status_code == 200


def test_admin_zera_as_duas_etapas_de_quem_perdeu_o_celular(
    client: TestClient, client_anon: TestClient, entrar_como
):
    headers = entrar_como("Perdeu O Celular")
    segredo = client_anon.post("/api/v1/auth/mfa/iniciar", headers=headers).json()[
        "segredo"
    ]
    client_anon.post(
        "/api/v1/auth/mfa/ativar",
        json={"codigo": pyotp.TOTP(segredo).now()},
        headers=headers,
    )
    eu = client_anon.get("/api/v1/auth/me", headers=headers).json()
    assert eu["mfa_ativo"] is True

    r = client.post(f"/api/v1/usuarios/{eu['id']}/resetar-mfa")
    assert r.status_code == 200
    assert r.json()["mfa_ativo"] is False
    # as sessões dela caíram
    assert client_anon.get("/api/v1/auth/me", headers=headers).status_code == 401


# ---------- cabeçalhos e configuração ----------


def test_resposta_tem_cabecalhos_de_seguranca(client: TestClient):
    r = client.get("/api/v1/pessoas")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"
    assert "referrer-policy" in r.headers
    assert r.headers["content-security-policy"].startswith("default-src 'none'")
    assert r.headers["cache-control"] == "no-store"


def _settings_prod(**extra):
    from app.core.config import Settings

    base = {
        "DATABASE_URL": "postgresql+psycopg://u:p@localhost/db",
        "SECRET_KEY": "x" * 40,
        "APP_ENV": "production",
        "CHAVES_CRIPTOGRAFIA": "1:" + "A" * 43 + "=",
        "CHAVE_HMAC": "B" * 43 + "=",
    }
    base.update(extra)
    return Settings(**base)


def test_settings_de_producao_validas_passam():
    s = _settings_prod()
    assert s.APP_ENV == "production"


def test_settings_recusa_chave_padrao_fora_do_dev():
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        _settings_prod(SECRET_KEY="dev-inseguro-troque-no-.env")


def test_settings_recusa_chave_curta_fora_do_dev():
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        _settings_prod(SECRET_KEY="curta")


def test_settings_recusa_chaves_de_criptografia_de_exemplo_fora_do_dev():
    from app.core.chaves import CHAVE_HMAC_DEV, CHAVES_DEV

    with pytest.raises(ValidationError, match="CHAVES_CRIPTOGRAFIA"):
        _settings_prod(CHAVES_CRIPTOGRAFIA=CHAVES_DEV)
    with pytest.raises(ValidationError, match="CHAVE_HMAC"):
        _settings_prod(CHAVE_HMAC=CHAVE_HMAC_DEV)


def test_settings_recusa_chave_de_criptografia_mal_formada():
    for ruim in ("semid", "1:curta==", "0:" + "A" * 43 + "=", "x:" + "A" * 43 + "="):
        with pytest.raises(ValidationError, match="CHAVES_CRIPTOGRAFIA"):
            _settings_prod(CHAVES_CRIPTOGRAFIA=ruim)


def test_settings_recusa_hmac_igual_a_chave_de_criptografia():
    with pytest.raises(ValidationError, match="diferente"):
        _settings_prod(CHAVE_HMAC="A" * 43 + "=")


def test_settings_aceita_chave_fraca_em_dev():
    """Em dev, a chave de exemplo passa -- não pode travar quem tá clonando
    o repo e rodando local pela primeira vez."""
    from app.core.config import Settings

    s = Settings(
        DATABASE_URL="postgresql+psycopg://u:p@localhost/db",
        SECRET_KEY="dev-inseguro-troque-no-.env",
        APP_ENV="dev",
    )
    assert s.SECRET_KEY == "dev-inseguro-troque-no-.env"
