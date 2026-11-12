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


# ---------- #11: caso aberto/alterado pelo atendimento ----------


def test_atendimento_que_abre_e_altera_caso_fica_na_auditoria_do_caso(
    client: TestClient, entrar_como
):
    op = entrar_como("Op Caso")
    p = _pessoa(client, "Pessoa P Caso")
    q = _pessoa(client, "Pessoa Q Caso")
    r_ = _pessoa(client, "Pessoa R Caso")
    desob = _id_tipo(client, "Desobsessão Presencial")

    # 1) abre o caso (sem nº de sessões ainda)
    r = client.post(
        "/api/v1/atendimentos",
        json={
            "pessoa_id": p,
            "tratamentos": [
                {"tipo_tratamento_id": desob, "assistidos": [{"pessoa_id": q}]}
            ],
        },
        headers=op,
    )
    assert r.status_code == 201, r.text
    at1 = r.json()["id"]
    t = client.get("/api/v1/tratamentos", params={"pessoa_id": p}).json()["items"][0][
        "id"
    ]

    # 2) outro atendimento: acrescenta R e completa o nº de sessões
    r = client.post(
        "/api/v1/atendimentos",
        json={
            "pessoa_id": p,
            "tratamentos": [
                {
                    "tipo_tratamento_id": desob,
                    "sessoes_previstas": 3,
                    "assistidos": [{"pessoa_id": q}, {"pessoa_id": r_}],
                }
            ],
        },
        headers=op,
    )
    assert r.status_code == 201, r.text
    at2 = r.json()["id"]

    # 3) um atendimento que não muda o caso (Q já é assistida) não grava nada
    # nele. Sem assistidos não serve: aí a própria P entraria como assistida.
    r = client.post(
        "/api/v1/atendimentos",
        json={
            "pessoa_id": p,
            "tratamentos": [
                {"tipo_tratamento_id": desob, "assistidos": [{"pessoa_id": q}]}
            ],
        },
        headers=op,
    )
    assert r.status_code == 201, r.text

    linhas = _auditoria(client, entidade="tratamento", entidade_id=t)
    assert [(i["acao"], i["dados"]) for i in linhas] == [
        ("criar", {"atendimento_id": at1}),
        ("atualizar", {"assistido_adicionado": r_, "atendimento_id": at2}),
        ("atualizar", {"campos": ["sessoes_previstas"], "atendimento_id": at2}),
    ]
    assert {i["usuario_nome"] for i in linhas} == {"Op Caso"}

    # apagar o atendimento não apaga o rastro do caso
    assert client.delete(f"/api/v1/atendimentos/{at1}", headers=op).status_code == 204
    assert len(_auditoria(client, entidade="tratamento", entidade_id=t)) == 3


def test_corrigir_data_do_atendimento_que_abriu_o_caso_move_o_inicio(
    client: TestClient, entrar_como
):
    op = entrar_como("Op Data")
    p = _pessoa(client, "Pessoa Data Errada")
    desob = _id_tipo(client, "Desobsessão Presencial")
    tratamentos = [{"tipo_tratamento_id": desob, "sessoes_previstas": 7}]
    r = client.post(
        "/api/v1/atendimentos",
        json={"pessoa_id": p, "data": "2002-02-02", "tratamentos": tratamentos},
        headers=op,
    )
    assert r.status_code == 201, r.text
    at = r.json()["id"]
    [caso] = client.get("/api/v1/tratamentos", params={"pessoa_id": p}).json()["items"]
    assert caso["data_inicio"] == "2002-02-02"

    # a tela manda o atendimento inteiro de volta, com a data certa
    r = client.patch(
        f"/api/v1/atendimentos/{at}",
        json={"data": "2026-11-02", "tratamentos": tratamentos},
        headers=op,
    )
    assert r.status_code == 200, r.text

    caso = client.get(f"/api/v1/tratamentos/{caso['id']}").json()
    assert caso["data_inicio"] == "2026-11-02"
    assert caso["sessoes_realizadas"] == 1
    linhas = _auditoria(client, entidade="tratamento", entidade_id=caso["id"])
    assert linhas[-1]["dados"] == {"campos": ["data_inicio"], "atendimento_id": at}
    assert linhas[-1]["usuario_nome"] == "Op Data"

    # mexer de novo em outra coisa, sem trocar a data, não move nada
    r = client.patch(
        f"/api/v1/atendimentos/{at}",
        json={"data": "2026-11-02", "observacao": "x"},
        headers=op,
    )
    assert r.status_code == 200, r.text
    assert len(_auditoria(client, entidade="tratamento", entidade_id=caso["id"])) == 2
