"""Testes das rotas de Pessoas."""

from fastapi.testclient import TestClient

# CPF válido de teste (passa no dígito verificador)
CPF_OK = "390.533.447-05"


def _nova_pessoa(**extra) -> dict:
    base = {
        "nome_completo": "Fulano de Tal",
        "sexo": "masculino",
        "telefone": "21999998888",
        "papeis": ["assistido"],
    }
    base.update(extra)
    return base


def test_criar_e_obter_pessoa(client: TestClient):
    dados = _nova_pessoa(cpf=CPF_OK, consentimento_lgpd=True)
    r = client.post("/api/v1/pessoas", json=dados)
    assert r.status_code == 201, r.text
    criada = r.json()
    assert criada["cpf"] == "39053344705"  # normalizado
    assert criada["papeis"] == ["assistido"]
    assert criada["consentimento_em"] is not None

    r2 = client.get(f"/api/v1/pessoas/{criada['id']}")
    assert r2.status_code == 200
    assert r2.json()["nome_completo"] == "Fulano de Tal"


def test_cpf_invalido_e_rejeitado(client: TestClient):
    r = client.post("/api/v1/pessoas", json=_nova_pessoa(cpf="111.111.111-11"))
    assert r.status_code == 422


def test_cpf_duplicado_da_conflito(client: TestClient):
    client.post("/api/v1/pessoas", json=_nova_pessoa(cpf=CPF_OK))
    r = client.post("/api/v1/pessoas", json=_nova_pessoa(cpf=CPF_OK))
    assert r.status_code == 409


def test_busca_e_paginacao(client: TestClient):
    client.post("/api/v1/pessoas", json=_nova_pessoa(nome_completo="Ana Maria"))
    client.post("/api/v1/pessoas", json=_nova_pessoa(nome_completo="Bruno Alves"))

    r = client.get("/api/v1/pessoas", params={"q": "ana"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["total"] >= 1
    assert any("Ana" in p["nome_completo"] for p in corpo["items"])


def test_editar_pessoa(client: TestClient):
    criada = client.post("/api/v1/pessoas", json=_nova_pessoa()).json()
    r = client.patch(
        f"/api/v1/pessoas/{criada['id']}",
        json={"telefone": "21911112222", "papeis": ["assistido", "trabalhador"]},
    )
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["telefone"] == "21911112222"
    assert set(corpo["papeis"]) == {"assistido", "trabalhador"}


def test_desativar_some_da_listagem(client: TestClient):
    dados = _nova_pessoa(nome_completo="Some Some")
    criada = client.post("/api/v1/pessoas", json=dados).json()

    r = client.delete(f"/api/v1/pessoas/{criada['id']}")
    assert r.status_code == 204

    achados = client.get("/api/v1/pessoas", params={"q": "Some Some"}).json()
    assert achados["total"] == 0

    com_inativos = client.get(
        "/api/v1/pessoas", params={"q": "Some Some", "incluir_inativos": True}
    ).json()
    assert com_inativos["total"] == 1
