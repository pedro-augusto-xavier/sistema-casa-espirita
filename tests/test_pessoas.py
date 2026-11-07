"""Testes das rotas de Pessoas."""

from fastapi.testclient import TestClient

from app.core.ratelimit import buscas_cpf_sem_acerto
from app.core.validators import cpf_valido

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


def _com_dv(nove: str) -> str:
    """Completa 9 dígitos com os 2 verificadores (mesma conta de cpf_valido)."""
    cpf = nove
    for tamanho in (9, 10):
        soma = sum(int(cpf[i]) * (tamanho + 1 - i) for i in range(tamanho))
        digito = (soma * 10) % 11
        cpf += str(0 if digito == 10 else digito)
    return cpf


def _cpfs_vistos(client: TestClient) -> int:
    return client.get("/api/v1/auditoria/alertas").json()["cpfs_vistos_7d"]


def _cpf_visto_na_busca(client: TestClient, pessoa_id: int) -> list[dict]:
    return client.get(
        "/api/v1/auditoria",
        params={"entidade": "pessoa", "entidade_id": pessoa_id, "acao": "visualizar"},
    ).json()["items"]


def test_busca_por_cpf_nao_e_oraculo_sem_auditoria(client: TestClient, entrar_como):
    """Achado #8: a ficha mostra 6 dos 11 dígitos e os 2 verificadores saem
    dos 9 primeiros -- sobram 1.000 palpites. Testar um por um na busca tem
    que dar 429 bem antes do acerto (e o 429 vale até pro palpite certo)."""
    alvo = client.post(
        "/api/v1/pessoas", json=_nova_pessoa(nome_completo="Alvo Oraculo", cpf=CPF_OK)
    ).json()
    cpfs_antes = _cpfs_vistos(client)
    op = entrar_como("Operadora Teste")

    mascara = client.get(f"/api/v1/pessoas/{alvo['id']}", headers=op).json()["cpf"]
    assert mascara == "***.533.447-**"
    meio = mascara[4:7] + mascara[8:11]

    bloqueou_em = acertou_em = None
    for p in range(1000):
        palpite = _com_dv(f"{p:03d}{meio}")
        r = client.get(
            "/api/v1/pessoas",
            params={"q": palpite, "incluir_inativos": "true", "size": 100},
            headers=op,
        )
        if r.status_code == 429:
            bloqueou_em = p
            break
        assert r.status_code == 200, r.text
        if alvo["id"] in [i["id"] for i in r.json()["items"]]:
            acertou_em = p
            break

    assert acertou_em is None
    assert bloqueou_em == buscas_cpf_sem_acerto.limite  # o certo seria p=390
    r = client.get("/api/v1/pessoas", params={"q": CPF_OK}, headers=op)
    assert r.status_code == 429
    assert _cpf_visto_na_busca(client, alvo["id"]) == []
    assert _cpfs_vistos(client) == cpfs_antes


def test_busca_pelo_cpf_completo_fica_na_auditoria(client: TestClient, entrar_como):
    """Achar pelo CPF completo confirma o CPF: conta como ver o CPF."""
    dados = _nova_pessoa(nome_completo="Achada Pela Busca", cpf=CPF_OK)
    alvo = client.post("/api/v1/pessoas", json=dados).json()
    cpfs_antes = _cpfs_vistos(client)
    op = entrar_como("Operadora Busca")

    r = client.get("/api/v1/pessoas", params={"q": CPF_OK}, headers=op)
    assert [p["id"] for p in r.json()["items"]] == [alvo["id"]]

    logs = _cpf_visto_na_busca(client, alvo["id"])
    assert len(logs) == 1
    assert logs[0]["dados"] == {"campo": "cpf", "motivo": "busca"}
    assert logs[0]["usuario_nome"] == "Operadora Busca"
    assert _cpfs_vistos(client) == cpfs_antes + 1

    # buscar pelo nome não é ver o CPF
    client.get("/api/v1/pessoas", params={"q": "Achada Pela"}, headers=op)
    assert len(_cpf_visto_na_busca(client, alvo["id"])) == 1


def test_acerto_em_cpf_com_digito_errado_tambem_fica_na_auditoria(
    client: TestClient, entrar_como
):
    """O cadastro aceita CPF com DV errado; achar um desses pela busca também
    é ver o CPF (só não gasta tentativa quando erra)."""
    dados = _nova_pessoa(nome_completo="Dv Errado", cpf="123.456.789-00")
    alvo = client.post("/api/v1/pessoas", json=dados).json()
    op = entrar_como("Operadora Dv")

    r = client.get("/api/v1/pessoas", params={"q": "12345678900"}, headers=op)
    assert [p["id"] for p in r.json()["items"]] == [alvo["id"]]
    logs = _cpf_visto_na_busca(client, alvo["id"])
    assert [log["dados"] for log in logs] == [{"campo": "cpf", "motivo": "busca"}]


def test_limite_da_busca_por_cpf_e_por_usuario(
    client: TestClient, client_anon: TestClient, entrar_como
):
    op = entrar_como("Operadora Um")
    outra = entrar_como("Operadora Dois")
    for p in range(buscas_cpf_sem_acerto.limite):
        r = client.get(
            "/api/v1/pessoas", params={"q": _com_dv(f"{p:03d}987654")}, headers=op
        )
        assert r.status_code == 200, r.text
    bloqueada = client.get(
        "/api/v1/pessoas", params={"q": _com_dv("999987654")}, headers=op
    )
    assert bloqueada.status_code == 429

    # o bloqueio é só da busca por CPF, e só dessa pessoa
    por_nome = client.get("/api/v1/pessoas", params={"q": "Fulano"}, headers=op)
    assert por_nome.status_code == 200
    params = {"q": _com_dv("999987654")}
    r = client.get("/api/v1/pessoas", params=params, headers=outra)
    assert r.status_code == 200
    # e não trava a troca de senha (que tem o próprio limite)
    r = client_anon.post(
        "/api/v1/auth/trocar-senha",
        json={
            "senha_atual": "senha-errada-qualquer",
            "senha_nova": "outra-senha-bem-longa",
        },
        headers=op,
    )
    assert r.status_code == 401, r.text


def test_telefone_de_11_digitos_nao_gasta_tentativa(client: TestClient, entrar_como):
    """Telefone com DDD tem 11 números, mas não passa no DV de CPF: buscar
    telefone não pode levar a recepção ao 429."""
    telefone = "21999998888"
    assert not cpf_valido(telefone)
    dados = _nova_pessoa(nome_completo="Acha Pelo Fone", telefone=telefone)
    pessoa = client.post("/api/v1/pessoas", json=dados).json()
    op = entrar_como("Operadora Fone")

    for _ in range(buscas_cpf_sem_acerto.limite + 1):
        r = client.get("/api/v1/pessoas", params={"q": telefone}, headers=op)
        assert r.status_code == 200, r.text
        assert pessoa["id"] in [p["id"] for p in r.json()["items"]]


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
