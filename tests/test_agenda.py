"""Testes da agenda (eventos + escala de trabalhadores)."""

from fastapi.testclient import TestClient


def _pessoa(client: TestClient, nome: str) -> int:
    return client.post("/api/v1/pessoas", json={"nome_completo": nome}).json()["id"]


def test_criar_evento_com_escala(client: TestClient):
    medium = _pessoa(client, "Tia Maria")
    r = client.post(
        "/api/v1/agenda",
        json={
            "titulo": "Trabalho de terça",
            "tipo": "trabalho",
            "data_inicio": "2026-06-30T19:00:00-03:00",
            "recorrencia": "semanal:terca",
            "escalados": [{"pessoa_id": medium, "funcao": "médium"}],
        },
    )
    assert r.status_code == 201, r.text
    evento = r.json()
    assert evento["titulo"] == "Trabalho de terça"
    assert len(evento["escalas"]) == 1
    assert evento["escalas"][0]["funcao"] == "médium"


def test_listar_filtra_por_tipo_e_periodo(client: TestClient):
    client.post(
        "/api/v1/agenda",
        json={
            "titulo": "Palestra pública",
            "tipo": "palestra",
            "data_inicio": "2026-07-01T20:00:00-03:00",
        },
    )
    client.post(
        "/api/v1/agenda",
        json={
            "titulo": "Trabalho",
            "tipo": "trabalho",
            "data_inicio": "2026-07-02T19:00:00-03:00",
        },
    )

    r = client.get("/api/v1/agenda", params={"tipo": "palestra"})
    corpo = r.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["titulo"] == "Palestra pública"


def test_editar_evento_substitui_escala(client: TestClient):
    p1 = _pessoa(client, "Fulano")
    p2 = _pessoa(client, "Ciclano")
    evento = client.post(
        "/api/v1/agenda",
        json={
            "titulo": "Evento",
            "tipo": "outro",
            "data_inicio": "2026-08-01T10:00:00-03:00",
            "escalados": [{"pessoa_id": p1}],
        },
    ).json()

    r = client.patch(
        f"/api/v1/agenda/{evento['id']}",
        json={"escalados": [{"pessoa_id": p2, "funcao": "apoio"}]},
    )
    assert r.status_code == 200
    escalas = r.json()["escalas"]
    assert len(escalas) == 1
    assert escalas[0]["pessoa"]["nome_completo"] == "Ciclano"
    assert escalas[0]["funcao"] == "apoio"


def test_excluir_evento(client: TestClient):
    evento = client.post(
        "/api/v1/agenda",
        json={
            "titulo": "Evento a remover",
            "tipo": "outro",
            "data_inicio": "2026-09-01T10:00:00-03:00",
        },
    ).json()
    assert client.delete(f"/api/v1/agenda/{evento['id']}").status_code == 204
    assert client.get(f"/api/v1/agenda/{evento['id']}").status_code == 404


def test_inativo_some_da_listagem_por_padrao(client: TestClient):
    evento = client.post(
        "/api/v1/agenda",
        json={
            "titulo": "Cancelado",
            "tipo": "outro",
            "data_inicio": "2026-10-01T10:00:00-03:00",
        },
    ).json()
    client.patch(f"/api/v1/agenda/{evento['id']}", json={"ativo": False})

    ativos = client.get("/api/v1/agenda").json()
    assert not any(e["id"] == evento["id"] for e in ativos["items"])

    com_inativos = client.get(
        "/api/v1/agenda", params={"incluir_inativos": True}
    ).json()
    assert any(e["id"] == evento["id"] for e in com_inativos["items"])
