"""Testes dos casos de Tratamento (Desobsessão), assistidos, evolução e histórico."""

from fastapi.testclient import TestClient


def _pessoa(client: TestClient, nome: str) -> int:
    return client.post("/api/v1/pessoas", json={"nome_completo": nome}).json()["id"]


def _tipo_caso(client: TestClient, nome: str = "Desobsessão Presencial") -> int:
    tipos = client.get("/api/v1/tipos-tratamento", params={"formato": "caso"}).json()
    return next(t["id"] for t in tipos if t["nome"] == nome)


def test_abrir_caso_com_assistidos(client: TestClient):
    tipo = _tipo_caso(client)
    mae = _pessoa(client, "Marcela Araujo")
    pai = _pessoa(client, "Renerio Vasconcelos")
    filho = _pessoa(client, "Jorge Luiz")

    corpo = {
        "tipo_tratamento_id": tipo,
        "solicitante_id": mae,
        "sessoes_previstas": 3,
        "assistidos": [{"pessoa_id": pai}, {"pessoa_id": filho}, {"pessoa_id": mae}],
    }
    r = client.post("/api/v1/tratamentos", json=corpo)
    assert r.status_code == 201, r.text
    caso = r.json()
    assert caso["tipo_nome"] == "Desobsessão Presencial"
    assert caso["solicitante"]["nome_completo"] == "Marcela Araujo"
    assert caso["status"] == "em_andamento"
    assert len(caso["assistidos"]) == 3


def test_diario_de_evolucao(client: TestClient):
    tipo = _tipo_caso(client, "Desobsessão à Distância")
    assistido = _pessoa(client, "Altamiro Dias")
    trabalhador = _pessoa(client, "Vovo Xica")

    caso = client.post(
        "/api/v1/tratamentos",
        json={"tipo_tratamento_id": tipo, "assistidos": [{"pessoa_id": assistido}]},
    ).json()

    r = client.post(
        f"/api/v1/tratamentos/{caso['id']}/evolucoes",
        json={
            "data": "2026-08-08",
            "texto": "Irmão que foi abandonado pelo assistido. Iniciar tratamento.",
            "registrado_por_id": trabalhador,
            "pessoa_id": assistido,
        },
    )
    assert r.status_code == 201, r.text
    atualizado = r.json()
    assert len(atualizado["evolucoes"]) == 1
    ev = atualizado["evolucoes"][0]
    assert ev["registrado_por"]["nome_completo"] == "Vovo Xica"
    assert ev["data"] == "2026-08-08"


def test_concluir_um_assistido_por_vez(client: TestClient):
    tipo = _tipo_caso(client)
    a = _pessoa(client, "Assistido A")
    b = _pessoa(client, "Assistido B")
    caso = client.post(
        "/api/v1/tratamentos",
        json={
            "tipo_tratamento_id": tipo,
            "assistidos": [{"pessoa_id": a}, {"pessoa_id": b}],
        },
    ).json()

    aid = caso["assistidos"][0]["id"]
    r = client.patch(
        f"/api/v1/tratamentos/{caso['id']}/assistidos/{aid}",
        json={
            "status": "concluido",
            "situacao_final": "harmonizado",
            "data_conclusao": "2026-09-01",
        },
    )
    assert r.status_code == 200
    assistidos = {x["id"]: x for x in r.json()["assistidos"]}
    assert assistidos[aid]["status"] == "concluido"
    outro = caso["assistidos"][1]["id"]
    assert assistidos[outro]["status"] == "ativo"


def test_assistido_duplicado_da_422(client: TestClient):
    tipo = _tipo_caso(client)
    p = _pessoa(client, "Repetido")
    caso = client.post(
        "/api/v1/tratamentos",
        json={"tipo_tratamento_id": tipo, "assistidos": [{"pessoa_id": p}]},
    ).json()
    r = client.post(
        f"/api/v1/tratamentos/{caso['id']}/assistidos", json={"pessoa_id": p}
    )
    assert r.status_code == 422


def test_fechar_caso(client: TestClient):
    tipo = _tipo_caso(client)
    caso = client.post("/api/v1/tratamentos", json={"tipo_tratamento_id": tipo}).json()
    r = client.patch(
        f"/api/v1/tratamentos/{caso['id']}",
        json={"status": "concluido", "situacao_final": "encerrado"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "concluido"


def test_historico_junta_tudo_por_data(client: TestClient):
    pessoa = _pessoa(client, "Historico Teste")
    reflexo = client.get("/api/v1/tipos-tratamento").json()
    reflexo_id = next(t["id"] for t in reflexo if t["nome"] == "Reflexologia")

    client.post(
        "/api/v1/atendimentos",
        json={
            "pessoa_id": pessoa,
            "data": "2026-01-10",
            "tratamentos": [{"tipo_tratamento_id": reflexo_id}],
        },
    )

    tipo = _tipo_caso(client)
    caso = client.post(
        "/api/v1/tratamentos",
        json={
            "tipo_tratamento_id": tipo,
            "data_inicio": "2026-02-01",
            "assistidos": [{"pessoa_id": pessoa}],
        },
    ).json()
    client.post(
        f"/api/v1/tratamentos/{caso['id']}/evolucoes",
        json={"data": "2026-03-15", "texto": "melhora", "pessoa_id": pessoa},
    )

    hist = client.get(f"/api/v1/pessoas/{pessoa}/historico").json()
    assert len(hist) == 3
    # ordenado da data mais recente para a mais antiga
    datas = [h["data"] for h in hist]
    assert datas == sorted(datas, reverse=True)
    tipos = {h["tipo"] for h in hist}
    assert tipos == {"atendimento", "tratamento_inicio", "evolucao"}

    # cada item traz os detalhes completos, não só o resumo em texto
    por_tipo = {h["tipo"]: h for h in hist}
    detalhes_atendimento = por_tipo["atendimento"]["detalhes"]
    assert detalhes_atendimento["tratamentos"][0]["nome"] == "Reflexologia"
    detalhes_caso = por_tipo["tratamento_inicio"]["detalhes"]
    assert detalhes_caso["tipo_nome"] == "Desobsessão Presencial"
    assert por_tipo["evolucao"]["detalhes"]["texto"] == "melhora"
