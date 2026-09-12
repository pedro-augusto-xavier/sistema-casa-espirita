"""Testes das rotas de Atendimentos e das listas de referência."""

from fastapi.testclient import TestClient


def _cria_pessoa(client: TestClient, nome: str = "Paciente Um") -> int:
    r = client.post("/api/v1/pessoas", json={"nome_completo": nome})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _id_tipo(client: TestClient, nome: str) -> int:
    tipos = client.get("/api/v1/tipos-tratamento").json()
    return next(t["id"] for t in tipos if t["nome"] == nome)


def test_listas_de_referencia_vem_do_seed(client: TestClient):
    tipos = client.get("/api/v1/tipos-tratamento").json()
    nomes = {t["nome"] for t in tipos}
    assert "Desobsessão Presencial" in nomes
    assert "Reflexologia" in nomes

    so_grupo = client.get(
        "/api/v1/tipos-tratamento", params={"formato": "grupo"}
    ).json()
    assert all(t["formato"] == "grupo" for t in so_grupo)

    funcoes = client.get("/api/v1/funcoes").json()
    assert "Médium" in {f["nome"] for f in funcoes}


def test_criar_atendimento_com_tratamentos(client: TestClient):
    pessoa = _cria_pessoa(client)
    medium = _cria_pessoa(client, "Tia Maria")
    reflexo = _id_tipo(client, "Reflexologia")
    energiz = _id_tipo(client, "Energização")

    corpo = {
        "pessoa_id": pessoa,
        "atendido_por_id": medium,
        "data": "2026-06-29",
        "observacao": "Fazer a mesa separada",
        "tratamentos": [
            {"tipo_tratamento_id": reflexo},
            {
                "tipo_tratamento_id": energiz,
                "sessoes_previstas": 7,
                "modalidade": "distancia",
            },
        ],
    }
    r = client.post("/api/v1/atendimentos", json=corpo)
    assert r.status_code == 201, r.text
    dados = r.json()
    assert dados["pessoa"]["id"] == pessoa
    assert dados["atendido_por"]["nome_completo"] == "Tia Maria"
    assert len(dados["tratamentos"]) == 2
    nomes = {t["tipo_tratamento_nome"] for t in dados["tratamentos"]}
    assert nomes == {"Reflexologia", "Energização"}


def test_marcar_desobsessao_abre_ficha_de_acompanhamento(client: TestClient):
    """Marcar um tipo 'caso' no atendimento abre o caso (a ficha de papel)
    uma vez só; os atendimentos seguintes contam como sessões."""
    pessoa = _cria_pessoa(client, "Bernardo Pinto")
    vovo = _cria_pessoa(client, "Vovó Xica")
    desob = _id_tipo(client, "Desobsessão Presencial")

    r = client.post(
        "/api/v1/atendimentos",
        json={
            "pessoa_id": pessoa,
            "data": "2026-08-06",
            "solicitante_id": vovo,
            "tratamentos": [{"tipo_tratamento_id": desob, "sessoes_previstas": 3}],
        },
    )
    assert r.status_code == 201, r.text

    fichas = client.get("/api/v1/tratamentos", params={"pessoa_id": pessoa}).json()
    assert fichas["total"] == 1
    ficha = client.get(f"/api/v1/tratamentos/{fichas['items'][0]['id']}").json()
    assert ficha["tipo_nome"] == "Desobsessão Presencial"
    assert ficha["solicitante"]["nome_completo"] == "Vovó Xica"
    assert ficha["sessoes_previstas"] == 3
    assert ficha["sessoes_realizadas"] == 1
    assert ficha["data_inicio"] == "2026-08-06"
    assert [a["pessoa"]["id"] for a in ficha["assistidos"]] == [pessoa]

    # segunda vez: não abre outra ficha, só conta mais uma sessão
    r = client.post(
        "/api/v1/atendimentos",
        json={
            "pessoa_id": pessoa,
            "data": "2026-08-13",
            "tratamentos": [{"tipo_tratamento_id": desob}],
        },
    )
    assert r.status_code == 201, r.text
    fichas = client.get("/api/v1/tratamentos", params={"pessoa_id": pessoa}).json()
    assert fichas["total"] == 1
    assert fichas["items"][0]["sessoes_realizadas"] == 2

    # anotação geral no diário aparece no histórico da pessoa
    client.post(
        f"/api/v1/tratamentos/{ficha['id']}/evolucoes",
        json={"texto": "Limpeza + doação + 3 choques", "data": "2026-08-20"},
    )
    historico = client.get(f"/api/v1/pessoas/{pessoa}/historico").json()
    tipos = [h["tipo"] for h in historico]
    assert tipos.count("atendimento") == 2
    assert "tratamento_inicio" in tipos
    assert "evolucao" in tipos


def test_atendimento_com_pessoa_inexistente_da_404(client: TestClient):
    r = client.post("/api/v1/atendimentos", json={"pessoa_id": 999999})
    assert r.status_code == 404


def test_atendimento_com_tipo_tratamento_inexistente_da_404(client: TestClient):
    pessoa = _cria_pessoa(client)
    r = client.post(
        "/api/v1/atendimentos",
        json={"pessoa_id": pessoa, "tratamentos": [{"tipo_tratamento_id": 999999}]},
    )
    assert r.status_code == 404


def test_listar_filtra_por_pessoa(client: TestClient):
    p1 = _cria_pessoa(client, "Pessoa A")
    p2 = _cria_pessoa(client, "Pessoa B")
    client.post("/api/v1/atendimentos", json={"pessoa_id": p1})
    client.post("/api/v1/atendimentos", json={"pessoa_id": p1})
    client.post("/api/v1/atendimentos", json={"pessoa_id": p2})

    r = client.get("/api/v1/atendimentos", params={"pessoa_id": p1})
    corpo = r.json()
    assert corpo["total"] == 2
    assert all(a["pessoa"]["id"] == p1 for a in corpo["items"])


def test_editar_substitui_tratamentos(client: TestClient):
    pessoa = _cria_pessoa(client)
    t1 = _id_tipo(client, "Reflexologia")
    t2 = _id_tipo(client, "Conversa Fraterna")

    criado = client.post(
        "/api/v1/atendimentos",
        json={"pessoa_id": pessoa, "tratamentos": [{"tipo_tratamento_id": t1}]},
    ).json()

    r = client.patch(
        f"/api/v1/atendimentos/{criado['id']}",
        json={
            "observacao": "retorno em 15 dias",
            "tratamentos": [{"tipo_tratamento_id": t2}],
        },
    )
    assert r.status_code == 200
    dados = r.json()
    assert dados["observacao"] == "retorno em 15 dias"
    nomes = [t["tipo_tratamento_nome"] for t in dados["tratamentos"]]
    assert nomes == ["Conversa Fraterna"]


def test_excluir_atendimento(client: TestClient):
    pessoa = _cria_pessoa(client)
    criado = client.post("/api/v1/atendimentos", json={"pessoa_id": pessoa}).json()

    assert client.delete(f"/api/v1/atendimentos/{criado['id']}").status_code == 204
    assert client.get(f"/api/v1/atendimentos/{criado['id']}").status_code == 404
