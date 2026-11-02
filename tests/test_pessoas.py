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
    # LGPD: a ficha devolve o CPF mascarado...
    assert criada["cpf"] == "***.533.447-**"
    assert criada["papeis"] == ["assistido"]
    assert criada["consentimento_em"] is not None

    r2 = client.get(f"/api/v1/pessoas/{criada['id']}")
    assert r2.status_code == 200
    assert r2.json()["nome_completo"] == "Fulano de Tal"
    assert r2.json()["cpf"] == "***.533.447-**"

    # ...e o completo (normalizado) só pela rota própria
    r3 = client.get(f"/api/v1/pessoas/{criada['id']}/cpf")
    assert r3.json() == {"cpf": "39053344705"}


def test_ver_cpf_completo_fica_na_auditoria(client: TestClient):
    criada = client.post("/api/v1/pessoas", json=_nova_pessoa(cpf=CPF_OK)).json()
    client.get(f"/api/v1/pessoas/{criada['id']}/cpf", params={"motivo": "editar"})

    logs = client.get(
        "/api/v1/auditoria",
        params={
            "entidade": "pessoa",
            "entidade_id": criada["id"],
            "acao": "visualizar",
        },
    ).json()["items"]
    assert len(logs) == 1
    assert logs[0]["dados"] == {"campo": "cpf", "motivo": "editar"}
    assert logs[0]["usuario_nome"] == "Admin de Teste"


def test_cpf_mascarado_nao_pode_ser_gravado_por_cima(client: TestClient):
    """Se a tela mandar de volta o CPF como recebeu (mascarado), a API recusa
    em vez de gravar só os números do meio."""
    criada = client.post("/api/v1/pessoas", json=_nova_pessoa(cpf=CPF_OK)).json()
    r = client.patch(f"/api/v1/pessoas/{criada['id']}", json={"cpf": criada["cpf"]})
    assert r.status_code == 422
    assert (
        client.get(f"/api/v1/pessoas/{criada['id']}/cpf").json()["cpf"] == "39053344705"
    )


def test_busca_pelo_cpf_completo(client: TestClient):
    criada = client.post(
        "/api/v1/pessoas", json=_nova_pessoa(nome_completo="Acha Pelo Cpf", cpf=CPF_OK)
    ).json()
    achados = client.get("/api/v1/pessoas", params={"q": CPF_OK}).json()
    assert [p["id"] for p in achados["items"]] == [criada["id"]]


def test_cpf_e_opcional(client: TestClient):
    """Maioria das pessoas atendidas não tem CPF em mãos -- não pode travar
    o cadastro por causa disso."""
    r = client.post("/api/v1/pessoas", json=_nova_pessoa())
    assert r.status_code == 201, r.text
    assert r.json()["cpf"] is None

    # várias pessoas sem CPF ao mesmo tempo não pode dar conflito de duplicado
    r2 = client.post("/api/v1/pessoas", json=_nova_pessoa(nome_completo="Outra Pessoa"))
    assert r2.status_code == 201, r2.text
    assert r2.json()["cpf"] is None


def test_cpf_com_digito_errado_e_aceito(client: TestClient):
    """Não confere dígito verificador -- CPF copiado errado da ficha não
    pode travar o cadastro."""
    r = client.post("/api/v1/pessoas", json=_nova_pessoa(cpf="123.456.789-00"))
    assert r.status_code == 201, r.text
    completo = client.get(f"/api/v1/pessoas/{r.json()['id']}/cpf").json()
    assert completo["cpf"] == "12345678900"


def test_cpf_com_mais_de_11_numeros_e_rejeitado(client: TestClient):
    r = client.post("/api/v1/pessoas", json=_nova_pessoa(cpf="123456789012"))
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


def test_papel_voluntario_estado_civil_e_quantidade_de_filhos(client: TestClient):
    dados = _nova_pessoa(
        papeis=["voluntario"],
        estado_civil="casado",
        quantidade_filhos=2,
    )
    r = client.post("/api/v1/pessoas", json=dados)
    assert r.status_code == 201, r.text
    criada = r.json()
    assert criada["papeis"] == ["voluntario"]
    assert criada["estado_civil"] == "casado"
    assert criada["quantidade_filhos"] == 2

    # não informado por padrão quando não vem no corpo
    outra = client.post("/api/v1/pessoas", json=_nova_pessoa()).json()
    assert outra["estado_civil"] == "nao_informado"
    assert outra["quantidade_filhos"] is None

    # editar depois
    r2 = client.patch(
        f"/api/v1/pessoas/{criada['id']}",
        json={"estado_civil": "viuvo", "quantidade_filhos": 0},
    )
    assert r2.status_code == 200
    assert r2.json()["estado_civil"] == "viuvo"
    assert r2.json()["quantidade_filhos"] == 0


def test_quantidade_de_filhos_negativa_e_rejeitada(client: TestClient):
    r = client.post("/api/v1/pessoas", json=_nova_pessoa(quantidade_filhos=-1))
    assert r.status_code == 422


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
