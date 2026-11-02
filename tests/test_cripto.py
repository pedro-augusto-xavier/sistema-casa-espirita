"""Testes da criptografia dos campos sensíveis (AES-256-GCM + HMAC)."""

import base64
import hashlib
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.orm import Session, undefer

from app.core import cripto
from app.core.config import settings
from app.models.anexo import Anexo
from app.models.pessoa import Pessoa


def _chave_nova() -> str:
    return base64.b64encode(os.urandom(32)).decode()


@pytest.fixture()
def chaves_temporarias(monkeypatch):
    """Troca as chaves só durante o teste (e volta as originais no fim)."""

    def _usar(valor: str) -> None:
        monkeypatch.setattr(settings, "CHAVES_CRIPTOGRAFIA", valor)
        cripto.recarregar_chaves()

    yield _usar
    monkeypatch.undo()
    cripto.recarregar_chaves()


def test_cifrar_e_decifrar_volta_o_original():
    blob = cripto.cifrar(b"390.533.447-05", "pessoa.cpf")
    assert b"390" not in blob
    assert cripto.decifrar(blob, "pessoa.cpf") == b"390.533.447-05"


def test_mesmo_valor_gera_bytes_diferentes_a_cada_vez():
    a = cripto.cifrar(b"mesmo texto", "x")
    b = cripto.cifrar(b"mesmo texto", "x")
    assert a != b  # nonce aleatório: não dá pra ver que dois CPFs são iguais


def test_valor_de_uma_coluna_nao_abre_em_outra():
    blob = cripto.cifrar(b"segredo", "pessoa.cpf")
    with pytest.raises(cripto.ErroCriptografia):
        cripto.decifrar(blob, "atendimento.observacao")


def test_bytes_adulterados_sao_detectados():
    blob = bytearray(cripto.cifrar(b"segredo", "x"))
    blob[-1] ^= 0x01
    with pytest.raises(cripto.ErroCriptografia):
        cripto.decifrar(bytes(blob), "x")


def test_rotacao_de_chave(chaves_temporarias):
    antiga = _chave_nova()
    nova = _chave_nova()

    chaves_temporarias(f"1:{antiga}")
    blob_antigo = cripto.cifrar(b"dado de 2026", "x")
    assert cripto.id_da_chave(blob_antigo) == 1

    # chave 2 vira a ativa; a 1 continua só pra ler o que já existe
    chaves_temporarias(f"2:{nova},1:{antiga}")
    assert cripto.decifrar(blob_antigo, "x") == b"dado de 2026"
    assert cripto.id_da_chave(cripto.cifrar(b"novo", "x")) == 2

    # sem a chave 1, o dado antigo fica ilegível (por isso rotacionar antes
    # de tirar a chave antiga da lista)
    chaves_temporarias(f"2:{nova}")
    with pytest.raises(cripto.ErroCriptografia):
        cripto.decifrar(blob_antigo, "x")


def test_hmac_nao_e_um_sha256_simples():
    """Com SHA-256 puro, daria pra testar todos os CPFs possíveis e achar o
    de cada hash. Com HMAC, sem a chave não dá."""
    cpf = "39053344705"
    assert cripto.hmac_busca(cpf) == cripto.hmac_busca(cpf)
    assert cripto.hmac_busca(cpf) != hashlib.sha256(cpf.encode()).hexdigest()


def test_no_banco_o_cpf_e_as_observacoes_ficam_cifrados(
    client: TestClient, db: Session
):
    r = client.post(
        "/api/v1/pessoas",
        json={
            "nome_completo": "Cifrada Da Silva",
            "cpf": "390.533.447-05",
            "observacoes_gerais": "faz tratamento de saúde X",
        },
    )
    pessoa_id = r.json()["id"]
    cru = db.execute(
        text(
            "SELECT cpf_cifrado, cpf_hash, observacoes_gerais FROM pessoa WHERE id = :i"
        ),
        {"i": pessoa_id},
    ).one()
    assert b"39053344705" not in bytes(cru.cpf_cifrado)
    assert b"saude" not in bytes(cru.observacoes_gerais)
    assert b"tratamento" not in bytes(cru.observacoes_gerais)
    assert cru.cpf_hash == cripto.hmac_busca("39053344705")

    # pelo modelo, lê normal
    pessoa = db.get(Pessoa, pessoa_id)
    db.refresh(pessoa)
    assert pessoa.cpf == "39053344705"


def test_anexo_fica_cifrado_no_banco(client: TestClient, db: Session):
    p = client.post("/api/v1/pessoas", json={"nome_completo": "Com Anexo"}).json()
    conteudo = b"%PDF-1.4 exame de sangue de fulana"
    anexo = client.post(
        f"/api/v1/pessoas/{p['id']}/anexos",
        files={"arquivo": ("exame.pdf", conteudo, "application/pdf")},
    ).json()

    cru = db.execute(
        text("SELECT conteudo FROM anexo WHERE id = :i"), {"i": anexo["id"]}
    ).scalar_one()
    assert b"exame de sangue" not in bytes(cru)

    lido = db.scalar(
        select(Anexo).options(undefer(Anexo.conteudo)).where(Anexo.id == anexo["id"])
    )
    assert lido.conteudo == conteudo
    assert client.get(f"/api/v1/anexos/{anexo['id']}/arquivo").content == conteudo


def test_script_de_rotacao_recifra_tudo_com_a_chave_nova(
    client: TestClient, db: Session, chaves_temporarias
):
    chaves_atuais = settings.CHAVES_CRIPTOGRAFIA
    from scripts.rotacionar_chaves import rotacionar

    p = client.post(
        "/api/v1/pessoas",
        json={"nome_completo": "Rotaciona Eu", "cpf": "39053344705"},
    ).json()

    # chave 2 entra na frente; a atual (id 1) fica só pra leitura
    chaves_temporarias(f"2:{_chave_nova()},{chaves_atuais}")
    antes = rotacionar(db, executar=False)
    assert antes["pessoa.cpf_cifrado"][1] >= 1

    rotacionar(db, executar=True)
    depois = rotacionar(db, executar=False)
    assert set(depois["pessoa.cpf_cifrado"]) == {2}

    cru = db.execute(
        text("SELECT cpf_cifrado FROM pessoa WHERE id = :i"), {"i": p["id"]}
    ).scalar_one()
    assert cripto.id_da_chave(bytes(cru)) == 2
    assert cripto.decifrar(bytes(cru), "pessoa.cpf") == b"39053344705"


def test_nome_e_descricao_do_anexo_ficam_cifrados(client: TestClient, db: Session):
    p = client.post("/api/v1/pessoas", json={"nome_completo": "Anexo Com Nome"}).json()
    anexo = client.post(
        f"/api/v1/pessoas/{p['id']}/anexos",
        files={"arquivo": ("exame_fulana.pdf", b"%PDF-1.4 x", "application/pdf")},
        data={"descricao": "laudo do psiquiatra"},
    ).json()

    cru = db.execute(
        text("SELECT nome_arquivo, descricao FROM anexo WHERE id = :i"),
        {"i": anexo["id"]},
    ).one()
    assert b"exame" not in bytes(cru.nome_arquivo)
    assert b"psiquiatra" not in bytes(cru.descricao)

    # pela API continua tudo legível
    assert anexo["nome_arquivo"] == "exame_fulana.pdf"
    assert anexo["descricao"] == "laudo do psiquiatra"
    lista = client.get(f"/api/v1/pessoas/{p['id']}/anexos").json()
    assert lista[0]["nome_arquivo"] == "exame_fulana.pdf"


def test_health_confirma_que_a_chave_abre_os_dados(client: TestClient):
    client.post(
        "/api/v1/pessoas", json={"nome_completo": "Saude Ok", "cpf": "39053344705"}
    )
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"api": "ok", "banco": "ok", "cripto": "ok"}


def test_health_falha_com_a_chave_errada(client: TestClient, chaves_temporarias):
    """Simula alguém colar outra chave no Render: o /health responde 503 e o
    Render não põe essa versão no ar."""
    client.post(
        "/api/v1/pessoas", json={"nome_completo": "Chave Trocada", "cpf": "39053344705"}
    )
    chaves_temporarias(f"1:{_chave_nova()}")  # mesmo id, chave diferente

    r = client.get("/health")
    assert r.status_code == 503
    assert r.json() == {"api": "ok", "banco": "ok", "cripto": "erro"}
