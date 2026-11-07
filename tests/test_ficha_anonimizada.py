"""Ficha anonimizada (LGPD) é terminal.

- Ninguém (nem o admin) edita, reativa ou liga registro novo a ela.
- Registros antigos ligados a ela só o admin corrige; o operador recebe 409
  (poderia reidentificar a pessoa escrevendo no texto).

Só dados fictícios.
"""

import pytest
from fastapi.testclient import TestClient

PDF_MINIMO = b"%PDF-1.4\n%%EOF"


def _tipo(client: TestClient, nome: str) -> int:
    tipos = client.get("/api/v1/tipos-tratamento").json()
    return next(t["id"] for t in tipos if t["nome"] == nome)


@pytest.fixture()
def cenario(client: TestClient, client_anon: TestClient, entrar_como) -> dict:
    """Titular com atendimento, caso e diário, já anonimizada pelo admin, e
    uma pessoa comum (Outra) com o próprio caso."""
    titular = client.post(
        "/api/v1/pessoas",
        json={"nome_completo": "Titular Ficticio", "cpf": "390.533.447-05"},
    ).json()
    outra = client.post(
        "/api/v1/pessoas", json={"nome_completo": "Outra Ficticia"}
    ).json()

    at = client.post(
        "/api/v1/atendimentos",
        json={"pessoa_id": titular["id"], "observacao": "nota ficticia"},
    ).json()
    # atendimento da Outra feito pela titular (ex: trabalhadora que saiu)
    at_outra = client.post(
        "/api/v1/atendimentos",
        json={"pessoa_id": outra["id"], "atendido_por_id": titular["id"]},
    ).json()

    desob = _tipo(client, "Desobsessão Presencial")
    caso = client.post(
        "/api/v1/tratamentos",
        json={
            "tipo_tratamento_id": desob,
            "solicitante_id": titular["id"],
            "assistidos": [{"pessoa_id": titular["id"]}],
        },
    ).json()
    caso = client.post(
        f"/api/v1/tratamentos/{caso['id']}/evolucoes",
        json={"texto": "diario ficticio", "pessoa_id": titular["id"]},
    ).json()
    caso_outra = client.post(
        "/api/v1/tratamentos",
        json={
            "tipo_tratamento_id": desob,
            "solicitante_id": outra["id"],
            "assistidos": [{"pessoa_id": outra["id"]}],
        },
    ).json()

    r = client.post(f"/api/v1/pessoas/{titular['id']}/anonimizar")
    assert r.status_code == 200

    return {
        "titular": titular["id"],
        "outra": outra["id"],
        "at": at["id"],
        "at_outra": at_outra["id"],
        "desob": desob,
        "caso": caso["id"],
        "assistido": caso["assistidos"][0]["id"],
        "evolucao": caso["evolucoes"][0]["id"],
        "caso_outra": caso_outra["id"],
        "op": entrar_como("Op Reverte"),
    }


def _anonimizada_409(r) -> None:
    assert r.status_code == 409, r.text
    assert "anonimizada" in r.json()["detail"]


# ---------- a própria ficha ----------


def test_ninguem_edita_nem_reativa_ficha_anonimizada(
    client: TestClient, client_anon: TestClient, cenario: dict
):
    pid = cenario["titular"]
    reidentifica = {
        "nome_completo": "Titular Ficticio",
        "cpf": "390.533.447-05",
        "telefone": "21999990000",
    }
    for headers in (cenario["op"], None):  # operador e admin
        c = client_anon if headers else client
        _anonimizada_409(
            c.patch(f"/api/v1/pessoas/{pid}", json=reidentifica, headers=headers)
        )
        _anonimizada_409(c.post(f"/api/v1/pessoas/{pid}/reativar", headers=headers))

    ficha = client.get(f"/api/v1/pessoas/{pid}").json()
    assert ficha["nome_completo"] == "(dados removidos)"
    assert ficha["cpf"] is None
    assert ficha["telefone"] is None
    assert ficha["ativo"] is False
    assert ficha["anonimizada"] is True

    at = client.get(f"/api/v1/atendimentos/{cenario['at']}").json()
    assert at["pessoa"]["nome_completo"] == "(dados removidos)"


# ---------- registros novos ligados a ela ----------


def test_ninguem_liga_registro_novo_a_ficha_anonimizada(
    client: TestClient, client_anon: TestClient, cenario: dict
):
    pid, outra = cenario["titular"], cenario["outra"]
    for headers in (cenario["op"], None):  # operador e admin
        c = client_anon if headers else client

        _anonimizada_409(
            c.post(
                f"/api/v1/pessoas/{pid}/anexos",
                files={"arquivo": ("doc.pdf", PDF_MINIMO, "application/pdf")},
                headers=headers,
            )
        )

        for corpo in (
            {"pessoa_id": pid},
            {"pessoa_id": outra, "solicitante_id": pid},
            {"pessoa_id": outra, "atendido_por_id": pid},
        ):
            _anonimizada_409(
                c.post("/api/v1/atendimentos", json=corpo, headers=headers)
            )

        for corpo in (
            {"tipo_tratamento_id": cenario["desob"], "solicitante_id": pid},
            {
                "tipo_tratamento_id": cenario["desob"],
                "assistidos": [{"pessoa_id": pid}],
            },
        ):
            _anonimizada_409(c.post("/api/v1/tratamentos", json=corpo, headers=headers))

        caso_outra = cenario["caso_outra"]
        _anonimizada_409(
            c.post(
                f"/api/v1/tratamentos/{caso_outra}/assistidos",
                json={"pessoa_id": pid},
                headers=headers,
            )
        )
        _anonimizada_409(
            c.post(
                f"/api/v1/tratamentos/{caso_outra}/evolucoes",
                json={"texto": "x", "pessoa_id": pid},
                headers=headers,
            )
        )
        # trocar um vínculo de registro existente para a ficha anonimizada
        _anonimizada_409(
            c.patch(
                f"/api/v1/tratamentos/{caso_outra}",
                json={"solicitante_id": pid},
                headers=headers,
            )
        )

    # nada foi criado na ficha
    assert client.get(f"/api/v1/pessoas/{pid}/anexos").json() == []


# ---------- registros antigos: só o admin corrige ----------


def _edicoes_de_registro_antigo(cenario: dict) -> list[tuple[str, str, dict]]:
    caso = cenario["caso"]
    return [
        ("patch", f"/api/v1/atendimentos/{cenario['at']}", {"observacao": "corrigida"}),
        # o próprio registro não é da titular, mas ela é quem atendeu
        (
            "patch",
            f"/api/v1/atendimentos/{cenario['at_outra']}",
            {"observacao": "corrigida"},
        ),
        ("patch", f"/api/v1/tratamentos/{caso}", {"observacao": "corrigida"}),
        (
            "patch",
            f"/api/v1/tratamentos/{caso}/evolucoes/{cenario['evolucao']}",
            {"texto": "corrigido"},
        ),
        (
            "patch",
            f"/api/v1/tratamentos/{caso}/assistidos/{cenario['assistido']}",
            {"situacao_final": "corrigida"},
        ),
        ("post", f"/api/v1/tratamentos/{caso}/evolucoes", {"texto": "nova nota"}),
    ]


def test_operador_nao_edita_registro_antigo_de_ficha_anonimizada(
    client_anon: TestClient, cenario: dict
):
    for metodo, url, corpo in _edicoes_de_registro_antigo(cenario):
        r = getattr(client_anon, metodo)(url, json=corpo, headers=cenario["op"])
        assert r.status_code == 409, (url, r.text)
        assert "só o admin" in r.json()["detail"]


def test_admin_edita_registro_antigo_de_ficha_anonimizada(
    client: TestClient, cenario: dict
):
    for metodo, url, corpo in _edicoes_de_registro_antigo(cenario):
        r = getattr(client, metodo)(url, json=corpo)
        assert r.status_code in (200, 201), (url, r.text)

    at = client.get(f"/api/v1/atendimentos/{cenario['at']}").json()
    assert at["observacao"] == "corrigida"
    assert at["pessoa"]["nome_completo"] == "(dados removidos)"


def test_admin_reenvia_vinculo_antigo_sem_travar(client: TestClient, cenario: dict):
    """A tela manda o formulário inteiro: reenviar o mesmo atendido_por_id
    (a ficha anonimizada) não é vínculo novo."""
    r = client.patch(
        f"/api/v1/atendimentos/{cenario['at_outra']}",
        json={"atendido_por_id": cenario["titular"], "observacao": "ok"},
    )
    assert r.status_code == 200, r.text


def test_operador_segue_editando_registro_comum(client_anon: TestClient, cenario: dict):
    r = client_anon.patch(
        f"/api/v1/tratamentos/{cenario['caso_outra']}",
        json={"observacao": "normal"},
        headers=cenario["op"],
    )
    assert r.status_code == 200, r.text
