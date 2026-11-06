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
    # dado pessoal: registra QUE mudou, sem copiar o valor pro log
    assert atualizacao["dados"]["telefone"] == {"alterado": True}
    assert "21999990000" not in str(logs)


def test_editar_papel_registra_de_e_para(client: TestClient):
    p = _pessoa(client)
    client.patch(f"/api/v1/pessoas/{p['id']}", json={"papeis": ["trabalhador"]})
    logs = client.get(
        "/api/v1/auditoria",
        params={"entidade": "pessoa", "entidade_id": p["id"], "acao": "atualizar"},
    ).json()["items"]
    assert logs[0]["dados"]["papeis"] == {"de": [], "para": ["trabalhador"]}


def test_observacao_do_atendimento_nao_vai_pro_log(client: TestClient):
    p = _pessoa(client)
    at = client.post("/api/v1/atendimentos", json={"pessoa_id": p["id"]}).json()
    client.patch(
        f"/api/v1/atendimentos/{at['id']}", json={"observacao": "texto muito sensivel"}
    )
    logs = client.get(
        "/api/v1/auditoria", params={"entidade": "atendimento", "entidade_id": at["id"]}
    ).json()["items"]
    assert "texto muito sensivel" not in str(logs)
    assert any(x["dados"] == {"campos": ["observacao"]} for x in logs)


def test_editar_sem_mudanca_real_nao_gera_auditoria(client: TestClient):
    p = _pessoa(client, nome_completo="Mesmo Nome")
    total_antes = client.get(
        "/api/v1/auditoria", params={"entidade": "pessoa", "entidade_id": p["id"]}
    ).json()["total"]

    # manda o mesmo valor que já está la -- nao é uma mudança de verdade
    client.patch(f"/api/v1/pessoas/{p['id']}", json={"nome_completo": "Mesmo Nome"})

    total_depois = client.get(
        "/api/v1/auditoria", params={"entidade": "pessoa", "entidade_id": p["id"]}
    ).json()["total"]
    assert total_depois == total_antes


def test_operador_nao_ve_auditoria(client_anon: TestClient, entrar_como):
    r = client_anon.get("/api/v1/auditoria", headers=entrar_como("Op Audit"))
    assert r.status_code == 403


def test_login_fica_na_auditoria(client: TestClient, client_anon: TestClient):
    senha = client.post(
        "/api/v1/usuarios",
        json={
            "nome": "Quem Loga",
            "email": "loga@example.com",
            "papel": "operador",
        },
    ).json()["senha_gerada"]
    client_anon.post(
        "/api/v1/auth/login",
        data={"username": "Quem Loga", "password": senha},
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
    client.post(
        f"/api/v1/pessoas/{p['id']}/anexos",
        files={"arquivo": ("doc.pdf", b"%PDF-1.4 conteudo", "application/pdf")},
    )

    dump = client.get(f"/api/v1/pessoas/{p['id']}/exportar").json()
    assert dump["pessoa"]["nome_completo"] == "Exportavel Silva"
    # no export do titular vai o CPF completo
    assert dump["pessoa"]["cpf"] == "39053344705"
    assert len(dump["atendimentos"]) == 1
    assert dump["atendimentos"][0]["tratamentos"] == ["Reflexologia"]
    assert len(dump["anexos"]) == 1
    assert dump["anexos"][0]["nome_arquivo"] == "doc.pdf"


def test_exportar_mostra_quem_editou_a_ficha(client: TestClient):
    p = _pessoa(client, nome_completo="Nome Antigo")
    client.patch(f"/api/v1/pessoas/{p['id']}", json={"nome_completo": "Nome Novo"})

    dump = client.get(f"/api/v1/pessoas/{p['id']}/exportar").json()
    edicoes = dump["historico_edicoes"]
    assert any(e["acao"] == "criar" for e in edicoes)
    atualizacao = next(e for e in edicoes if e["acao"] == "atualizar")
    assert atualizacao["quem"] == "Admin de Teste"
    assert atualizacao["o_que_mudou"]["nome_completo"] == {"alterado": True}


def test_exportar_e_so_admin_e_fica_registrado(
    client: TestClient, client_anon: TestClient, entrar_como
):
    p = _pessoa(client, nome_completo="Exporta Registrado")
    r = client_anon.get(
        f"/api/v1/pessoas/{p['id']}/exportar", headers=entrar_como("Op Exporta")
    )
    assert r.status_code == 403

    client.get(f"/api/v1/pessoas/{p['id']}/exportar")
    client.post(
        f"/api/v1/pessoas/{p['id']}/exportacoes", json={"documento": "ficha_pdf"}
    )
    logs = client.get(
        "/api/v1/auditoria",
        params={"entidade": "pessoa", "entidade_id": p["id"], "acao": "exportar"},
    ).json()["items"]
    assert {x["dados"]["documento"] for x in logs} == {"lgpd_json", "ficha_pdf"}


def test_alertas_de_seguranca_contam_falhas_de_login(
    client: TestClient, client_anon: TestClient
):
    antes = client.get("/api/v1/auditoria/alertas").json()
    client_anon.post(
        "/api/v1/auth/login", data={"username": "ninguem", "password": "x"}
    )
    depois = client.get("/api/v1/auditoria/alertas").json()
    assert depois["falhas_login_24h"] == antes["falhas_login_24h"] + 1


def test_auditoria_nao_pode_ser_apagada_nem_alterada(client: TestClient, db):
    import pytest
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError

    _pessoa(client)
    with pytest.raises(DBAPIError, match="só de inserção"):
        with db.begin_nested():
            db.execute(text("DELETE FROM audit_log"))
    with pytest.raises(DBAPIError, match="só de inserção"):
        with db.begin_nested():
            db.execute(text("UPDATE audit_log SET dados = NULL"))


def test_anonimizar_apaga_dados_mas_mantem_historico(client: TestClient):
    p = _pessoa(
        client,
        nome_completo="Some Da Base",
        estado_civil="casado",
        quantidade_filhos=3,
    )
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
    # estado civil e nº de filhos também são dados pessoais
    assert anon["estado_civil"] == "nao_informado"
    assert anon["quantidade_filhos"] is None

    # o atendimento continua existindo
    assert client.get(f"/api/v1/atendimentos/{at['id']}").status_code == 200

    # segunda tentativa é rejeitada
    assert client.post(f"/api/v1/pessoas/{p['id']}/anonimizar").status_code == 409


def test_operador_nao_anonimiza(
    client: TestClient, client_anon: TestClient, entrar_como
):
    p = _pessoa(client, nome_completo="Protegida Aqui")
    r = client_anon.post(
        f"/api/v1/pessoas/{p['id']}/anonimizar", headers=entrar_como("Op Anon")
    )
    assert r.status_code == 403
