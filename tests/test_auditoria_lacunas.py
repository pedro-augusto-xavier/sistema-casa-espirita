"""Escritas feitas "de carona" em outra rota também ficam na auditoria.

- Excluir atendimento ou caso apaga os anexos ligados: cada anexo apagado
  ganha a própria linha `excluir`, com o vínculo (achado #10).
- Registrar atendimento que abre ou altera um caso grava as linhas com
  entidade="tratamento", como as rotas de /tratamentos (achado #11).
"""

from fastapi.testclient import TestClient

CONTEUDO_FAKE = b"\xff\xd8\xff\xe0conteudo-de-teste\xff\xd9"


def _pessoa(client: TestClient, nome: str) -> int:
    r = client.post("/api/v1/pessoas", json={"nome_completo": nome})
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _id_tipo(client: TestClient, nome: str) -> int:
    tipos = client.get("/api/v1/tipos-tratamento").json()
    return next(t["id"] for t in tipos if t["nome"] == nome)


def _upload(client: TestClient, pessoa_id: int, headers: dict, **campos) -> int:
    r = client.post(
        f"/api/v1/pessoas/{pessoa_id}/anexos",
        files={"arquivo": ("foto.jpg", CONTEUDO_FAKE, "image/jpeg")},
        data=campos,
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _auditoria(client: TestClient, **filtros) -> list[dict]:
    """Lida como admin (o fixture `client`), da mais antiga pra mais nova."""
    r = client.get("/api/v1/auditoria", params={"size": 200, **filtros})
    assert r.status_code == 200, r.text
    return sorted(r.json()["items"], key=lambda i: i["id"])


# ---------- #10: anexos apagados em cascata ----------


def test_criar_anexo_registra_o_vinculo(client: TestClient, entrar_como):
    op = entrar_como("Op Vinculo")
    p = _pessoa(client, "Pessoa Vinculo")
    at = client.post("/api/v1/atendimentos", json={"pessoa_id": p}, headers=op)
    assert at.status_code == 201, at.text
    no_atendimento = _upload(client, p, op, atendimento_id=at.json()["id"])
    solto = _upload(client, p, op)

    [criar] = _auditoria(client, entidade="anexo", entidade_id=no_atendimento)
    assert criar["acao"] == "criar"
    assert criar["dados"] == {
        "pessoa_id": p,
        "tipo": "image/jpeg",
        "atendimento_id": at.json()["id"],
    }
    # sem vínculo, nada de chave vazia
    [criar] = _auditoria(client, entidade="anexo", entidade_id=solto)
    assert criar["dados"] == {"pessoa_id": p, "tipo": "image/jpeg"}


def test_excluir_atendimento_registra_cada_anexo_apagado(
    client: TestClient, entrar_como
):
    op = entrar_como("Op Exclui Atendimento")
    p = _pessoa(client, "Pessoa P Anexo")
    q = _pessoa(client, "Pessoa Q Anexo")
    at = client.post("/api/v1/atendimentos", json={"pessoa_id": q}, headers=op)
    assert at.status_code == 201, at.text
    at_id = at.json()["id"]
    # um anexo da própria Q e um de P ligado ao atendimento de Q
    da_q = _upload(client, q, op, atendimento_id=at_id)
    da_p = _upload(client, p, op, atendimento_id=at_id)
    fora = _upload(client, q, op)  # sem vínculo: não pode sumir

    assert client.delete(f"/api/v1/atendimentos/{at_id}", headers=op).status_code == 204

    assert client.get(f"/api/v1/anexos/{da_q}/arquivo").status_code == 404
    assert client.get(f"/api/v1/anexos/{da_p}/arquivo").status_code == 404
    assert client.get(f"/api/v1/anexos/{fora}/arquivo").status_code == 200

    for anexo_id, dono in ((da_q, q), (da_p, p)):
        excluir = [
            i
            for i in _auditoria(client, entidade="anexo", entidade_id=anexo_id)
            if i["acao"] == "excluir"
        ]
        assert len(excluir) == 1, f"anexo {anexo_id} sumiu sem registro"
        assert excluir[0]["usuario_nome"] == "Op Exclui Atendimento"
        assert excluir[0]["dados"] == {"pessoa_id": dono, "atendimento_id": at_id}

    assert not [
        i
        for i in _auditoria(client, entidade="anexo", entidade_id=fora)
        if i["acao"] == "excluir"
    ]


def test_excluir_caso_registra_cada_anexo_apagado(client: TestClient, entrar_como):
    op = entrar_como("Op Exclui Caso")
    p = _pessoa(client, "Pessoa Caso Anexo")
    caso = client.post(
        "/api/v1/tratamentos",
        json={
            "tipo_tratamento_id": _id_tipo(client, "Desobsessão Presencial"),
            "assistidos": [{"pessoa_id": p}],
        },
        headers=op,
    )
    assert caso.status_code == 201, caso.text
    t = caso.json()["id"]
    anexo_id = _upload(client, p, op, tratamento_id=t)

    assert client.delete(f"/api/v1/tratamentos/{t}", headers=op).status_code == 204

    assert client.get(f"/api/v1/anexos/{anexo_id}/arquivo").status_code == 404
    excluir = [
        i
        for i in _auditoria(client, entidade="anexo", entidade_id=anexo_id)
        if i["acao"] == "excluir"
    ]
    assert len(excluir) == 1, "anexo sumiu sem registro"
    assert excluir[0]["usuario_nome"] == "Op Exclui Caso"
    assert excluir[0]["dados"] == {"pessoa_id": p, "tratamento_id": t}

