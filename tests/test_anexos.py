"""Testes de Anexos (fotos e documentos ligados à ficha ou ao histórico)."""

from fastapi.testclient import TestClient

# menor JPEG válido possível (cabeçalho SOI + EOI) -- não importa o conteúdo
# real da imagem pros nossos testes, só que os bytes cheguem íntegros.
CONTEUDO_FAKE = b"\xff\xd8\xff\xe0conteudo-de-teste\xff\xd9"


def _pessoa(client: TestClient, **extra) -> dict:
    base = {"nome_completo": "Dona Anexo Teste"}
    base.update(extra)
    return client.post("/api/v1/pessoas", json=base).json()


def _upload(client: TestClient, pessoa_id: int, **campos):
    return client.post(
        f"/api/v1/pessoas/{pessoa_id}/anexos",
        files={"arquivo": ("foto.jpg", CONTEUDO_FAKE, "image/jpeg")},
        data=campos,
    )


def test_enviar_e_listar_anexo_da_ficha(client: TestClient):
    p = _pessoa(client)

    r = _upload(client, p["id"], descricao="RG que ela trouxe")
    assert r.status_code == 201, r.text
    anexo = r.json()
    assert anexo["nome_arquivo"] == "foto.jpg"
    assert anexo["tipo_conteudo"] == "image/jpeg"
    assert anexo["tamanho_bytes"] == len(CONTEUDO_FAKE)
    assert anexo["descricao"] == "RG que ela trouxe"
    assert anexo["atendimento_id"] is None
    assert anexo["enviado_por_nome"] == "Admin de Teste"

    lista = client.get(f"/api/v1/pessoas/{p['id']}/anexos").json()
    assert len(lista) == 1
    assert lista[0]["id"] == anexo["id"]


def test_baixar_anexo_devolve_os_bytes_originais(client: TestClient):
    p = _pessoa(client)
    anexo = _upload(client, p["id"]).json()

    r = client.get(f"/api/v1/anexos/{anexo['id']}/arquivo")
    assert r.status_code == 200
    assert r.content == CONTEUDO_FAKE
    assert r.headers["content-type"] == "image/jpeg"


def test_tipo_de_arquivo_nao_aceito_e_rejeitado(client: TestClient):
    p = _pessoa(client)
    r = client.post(
        f"/api/v1/pessoas/{p['id']}/anexos",
        files={"arquivo": ("virus.exe", b"conteudo", "application/x-msdownload")},
    )
    assert r.status_code == 422


def test_tipo_e_conferido_pelo_conteudo_e_nao_pelo_nome(client: TestClient):
    """Um executável renomeado pra .jpg (e declarado como imagem) é recusado."""
    p = _pessoa(client)
    exe = b"MZ" + bytes.fromhex("9000") + b" isso e um .exe"
    r = client.post(
        f"/api/v1/pessoas/{p['id']}/anexos",
        files={"arquivo": ("foto.jpg", exe, "image/jpeg")},
    )
    assert r.status_code == 422

    # e um PNG declarado como JPEG fica registrado como PNG de verdade
    png = bytes.fromhex("89504e470d0a1a0a") + b"resto do png"
    r = client.post(
        f"/api/v1/pessoas/{p['id']}/anexos",
        files={"arquivo": ("foto.jpg", png, "image/jpeg")},
    )
    assert r.status_code == 201
    assert r.json()["tipo_conteudo"] == "image/png"


def test_download_tem_cabecalhos_seguros(client: TestClient):
    p = _pessoa(client)
    anexo = client.post(
        f"/api/v1/pessoas/{p['id']}/anexos",
        files={"arquivo": ('nome"perigoso;x=1.jpg', CONTEUDO_FAKE, "image/jpeg")},
    ).json()
    r = client.get(f"/api/v1/anexos/{anexo['id']}/arquivo")
    assert "sandbox" in r.headers["content-security-policy"]
    assert r.headers["cache-control"] == "no-store"
    # o nome não consegue fechar as aspas nem injetar outro parâmetro
    import re

    assert re.fullmatch(
        r'inline; filename="[A-Za-z0-9._ -]+"; filename\*=UTF-8\'\'\S+',
        r.headers["content-disposition"],
    )


def test_arquivo_acima_do_limite_e_rejeitado(client: TestClient):
    p = _pessoa(client)
    grande = b"0" * (8 * 1024 * 1024 + 1)
    r = client.post(
        f"/api/v1/pessoas/{p['id']}/anexos",
        files={"arquivo": ("grande.jpg", grande, "image/jpeg")},
    )
    assert r.status_code == 422


def test_anexo_ligado_a_um_atendimento(client: TestClient):
    p = _pessoa(client)
    at = client.post("/api/v1/atendimentos", json={"pessoa_id": p["id"]}).json()

    anexo = _upload(client, p["id"], atendimento_id=at["id"]).json()
    assert anexo["atendimento_id"] == at["id"]
    assert anexo["tratamento_id"] is None


def test_anexo_nao_pode_ter_dois_vinculos_ao_mesmo_tempo(client: TestClient):
    p = _pessoa(client)
    at = client.post("/api/v1/atendimentos", json={"pessoa_id": p["id"]}).json()
    tipo = next(
        t["id"]
        for t in client.get("/api/v1/tipos-tratamento").json()
        if t["nome"] == "Desobsessão Presencial"
    )
    caso = client.post(
        "/api/v1/tratamentos",
        json={"tipo_tratamento_id": tipo, "assistidos": [{"pessoa_id": p["id"]}]},
    ).json()

    r = _upload(client, p["id"], atendimento_id=at["id"], tratamento_id=caso["id"])
    assert r.status_code == 422


def test_excluir_anexo(client: TestClient):
    p = _pessoa(client)
    anexo = _upload(client, p["id"]).json()

    r = client.delete(f"/api/v1/anexos/{anexo['id']}")
    assert r.status_code == 204

    assert client.get(f"/api/v1/pessoas/{p['id']}/anexos").json() == []
    assert client.get(f"/api/v1/anexos/{anexo['id']}/arquivo").status_code == 404


def test_anonimizar_apaga_os_anexos_da_pessoa(client: TestClient):
    p = _pessoa(client)
    anexo = _upload(client, p["id"]).json()

    r = client.post(f"/api/v1/pessoas/{p['id']}/anonimizar")
    assert r.status_code == 200

    assert client.get(f"/api/v1/pessoas/{p['id']}/anexos").json() == []
    assert client.get(f"/api/v1/anexos/{anexo['id']}/arquivo").status_code == 404


def test_anexo_gera_auditoria(client: TestClient):
    p = _pessoa(client)
    anexo = _upload(client, p["id"]).json()

    r = client.get(
        "/api/v1/auditoria", params={"entidade": "anexo", "entidade_id": anexo["id"]}
    )
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["total"] >= 1
    assert corpo["items"][0]["acao"] == "criar"


def test_descricao_muito_longa_e_recusada(client: TestClient):
    p = _pessoa(client)
    r = client.post(
        f"/api/v1/pessoas/{p['id']}/anexos",
        files={"arquivo": ("foto.jpg", CONTEUDO_FAKE, "image/jpeg")},
        data={"descricao": "x" * 501},
    )
    assert r.status_code == 422
