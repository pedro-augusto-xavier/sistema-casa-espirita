"""Testes de auditoria e das rotas de LGPD (exportar / anonimizar)."""

from fastapi.testclient import TestClient


def _pessoa(client: TestClient, **extra) -> dict:
    base = {"nome_completo": "Ciclana de Tal", "cpf": "390.533.447-05"}
    base.update(extra)
    return client.post("/api/v1/pessoas", json=base).json()


def test_criar_pessoa_gera_registro_de_auditoria(client: TestClient):
    p = _pessoa(client)

    r = client.get(
        "/api/v1/auditoria",
        params={"entidade": "pessoa", "entidade_id": p["id"]},
    )
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["total"] >= 1
    log = corpo["items"][0]
    assert log["acao"] == "criar"
    assert log["entidade"] == "pessoa"
    assert log["usuario_nome"] == "Admin de Teste"


def test_editar_registra_o_que_mudou(client: TestClient):
    p = _pessoa(client)
    client.patch(f"/api/v1/pessoas/{p['id']}", json={"telefone": "21999990000"})

    logs = client.get(
        "/api/v1/auditoria",
        params={"entidade": "pessoa", "entidade_id": p["id"]},
    ).json()["items"]
    atualizacao = next(x for x in logs if x["acao"] == "atualizar")
    assert atualizacao["dados"]["telefone"] == "21999990000"


def test_operador_nao_ve_auditoria(client: TestClient, client_anon: TestClient):
    client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Op Audit",
            "email": "opaudit@example.com",
            "senha": "senha12345",
            "papel": "operador",
        },
    )
    token = client_anon.post(
        "/api/v1/auth/login",
        data={"username": "opaudit@example.com", "password": "senha12345"},
    ).json()["access_token"]
    r = client_anon.get(
        "/api/v1/auditoria", headers={"Authorization": f"Bearer {token}"}
    )
    assert r.status_code == 403


def test_login_fica_na_auditoria(client: TestClient, client_anon: TestClient):
    client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Quem Loga",
            "email": "loga@example.com",
            "senha": "senha12345",
            "papel": "operador",
        },
    )
    client_anon.post(
        "/api/v1/auth/login",
        data={"username": "loga@example.com", "password": "senha12345"},
    )
    logs = client.get("/api/v1/auditoria", params={"entidade": "usuario"}).json()
    assert any(x["acao"] == "login" for x in logs["items"])


def test_exportar_traz_tudo_da_pessoa(client: TestClient):
    p = _pessoa(client, nome_completo="Exportavel Silva")
    tipos = client.get("/api/v1/tipos-tratamento").json()
    reflexo = next(t["id"] for t in tipos if t["nome"] == "Reflexologia")
    client.post(
        "/api/v1/atendimentos",
        json={
            "pessoa_id": p["id"],
            "tratamentos": [{"tipo_tratamento_id": reflexo}],
        },
    )

    dump = client.get(f"/api/v1/pessoas/{p['id']}/exportar").json()
    assert dump["pessoa"]["nome_completo"] == "Exportavel Silva"
    assert len(dump["atendimentos"]) == 1
    assert dump["atendimentos"][0]["tratamentos"] == ["Reflexologia"]


def test_exportar_mostra_quem_editou_a_ficha(client: TestClient):
    p = _pessoa(client, nome_completo="Nome Antigo")
    client.patch(f"/api/v1/pessoas/{p['id']}", json={"nome_completo": "Nome Novo"})

    dump = client.get(f"/api/v1/pessoas/{p['id']}/exportar").json()
    edicoes = dump["historico_edicoes"]
    assert any(e["acao"] == "criar" for e in edicoes)
    atualizacao = next(e for e in edicoes if e["acao"] == "atualizar")
    assert atualizacao["quem"] == "Admin de Teste"
    assert atualizacao["o_que_mudou"]["nome_completo"] == "Nome Novo"


def test_anonimizar_apaga_dados_mas_mantem_historico(client: TestClient):
    p = _pessoa(client, nome_completo="Some Da Base")
    tipos = client.get("/api/v1/tipos-tratamento").json()
    reflexo = next(t["id"] for t in tipos if t["nome"] == "Reflexologia")
    at = client.post(
        "/api/v1/atendimentos",
        json={
            "pessoa_id": p["id"],
            "tratamentos": [{"tipo_tratamento_id": reflexo}],
        },
    ).json()

    r = client.post(f"/api/v1/pessoas/{p['id']}/anonimizar")
    assert r.status_code == 200
    anon = r.json()
    assert anon["nome_completo"] == "(dados removidos)"
    assert anon["cpf"] is None
    assert anon["anonimizada"] is True
    assert anon["ativo"] is False

    # o atendimento continua existindo
    assert client.get(f"/api/v1/atendimentos/{at['id']}").status_code == 200

    # segunda tentativa é rejeitada
    assert client.post(f"/api/v1/pessoas/{p['id']}/anonimizar").status_code == 409


def test_operador_nao_anonimiza(client: TestClient, client_anon: TestClient):
    p = _pessoa(client, nome_completo="Protegida Aqui")
    client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Op Anon",
            "email": "opanon@example.com",
            "senha": "senha12345",
            "papel": "operador",
        },
    )
    token = client_anon.post(
        "/api/v1/auth/login",
        data={"username": "opanon@example.com", "password": "senha12345"},
    ).json()["access_token"]
    r = client_anon.post(
        f"/api/v1/pessoas/{p['id']}/anonimizar",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
