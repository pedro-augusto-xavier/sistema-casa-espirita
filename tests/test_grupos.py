"""Testes das sessões de grupo (Grupo Despertar, Grupo de Estudos)."""

from fastapi.testclient import TestClient


def _pessoa(client: TestClient, nome: str) -> int:
    return client.post("/api/v1/pessoas", json={"nome_completo": nome}).json()["id"]


def _tipo_grupo(client: TestClient, nome: str = "Grupo Despertar") -> int:
    tipos = client.get("/api/v1/tipos-tratamento", params={"formato": "grupo"}).json()
    return next(t["id"] for t in tipos if t["nome"] == nome)


def test_criar_sessao_com_presentes(client: TestClient):
    tipo = _tipo_grupo(client)
    responsavel = _pessoa(client, "Dirigente do Grupo")
    p1 = _pessoa(client, "Participante Um")
    p2 = _pessoa(client, "Participante Dois")

    r = client.post(
        "/api/v1/grupos",
        json={
            "tipo_tratamento_id": tipo,
            "data": "2026-05-10",
            "responsavel_id": responsavel,
            "presentes": [{"pessoa_id": p1}, {"pessoa_id": p2}],
        },
    )
    assert r.status_code == 201, r.text
    sessao = r.json()
    assert sessao["tipo_nome"] == "Grupo Despertar"
    assert sessao["responsavel"]["nome_completo"] == "Dirigente do Grupo"
    assert len(sessao["presencas"]) == 2


def test_listar_filtra_por_tipo_e_data(client: TestClient):
    tipo = _tipo_grupo(client)
    client.post(
        "/api/v1/grupos", json={"tipo_tratamento_id": tipo, "data": "2026-01-05"}
    )
    client.post(
        "/api/v1/grupos", json={"tipo_tratamento_id": tipo, "data": "2026-02-05"}
    )

    r = client.get(
        "/api/v1/grupos", params={"tipo_tratamento_id": tipo, "de": "2026-02-01"}
    )
    corpo = r.json()
    assert corpo["total"] == 1
    assert corpo["items"][0]["data"] == "2026-02-05"


def test_editar_substitui_presentes(client: TestClient):
    tipo = _tipo_grupo(client)
    p1 = _pessoa(client, "Fulano")
    p2 = _pessoa(client, "Ciclano")
    sessao = client.post(
        "/api/v1/grupos",
        json={"tipo_tratamento_id": tipo, "presentes": [{"pessoa_id": p1}]},
    ).json()

    r = client.patch(
        f"/api/v1/grupos/{sessao['id']}",
        json={"presentes": [{"pessoa_id": p2}]},
    )
    assert r.status_code == 200
    nomes = [p["pessoa"]["nome_completo"] for p in r.json()["presencas"]]
    assert nomes == ["Ciclano"]


def test_excluir_sessao(client: TestClient):
    tipo = _tipo_grupo(client)
    sessao = client.post("/api/v1/grupos", json={"tipo_tratamento_id": tipo}).json()
    assert client.delete(f"/api/v1/grupos/{sessao['id']}").status_code == 204
    assert client.get(f"/api/v1/grupos/{sessao['id']}").status_code == 404


def test_grupo_aparece_no_historico_da_pessoa(client: TestClient):
    tipo = _tipo_grupo(client, "Grupo de Estudos Aberto")
    pessoa = _pessoa(client, "Frequentadora do Grupo")
    client.post(
        "/api/v1/grupos",
        json={
            "tipo_tratamento_id": tipo,
            "data": "2026-04-01",
            "presentes": [{"pessoa_id": pessoa}],
        },
    )

    hist = client.get(f"/api/v1/pessoas/{pessoa}/historico").json()
    assert len(hist) == 1
    assert hist[0]["tipo"] == "grupo"
    assert "Grupo de Estudos Aberto" in hist[0]["titulo"]
