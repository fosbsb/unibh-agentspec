from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

from sqlalchemy import select

from app.models import Pedido


def avancar(client, pedido, estado_atual):
    return client.post(f"/api/pedidos/{pedido['id']}/avancar", json={"estado_atual": estado_atual})


def test_avanca_na_ordem(client, novo_pedido):
    pedido = novo_pedido()
    for atual, esperado in [
        ("recebido", "preparando"),
        ("preparando", "pronto"),
        ("pronto", "entregue"),
    ]:
        r = avancar(client, pedido, atual)
        assert r.status_code == 200
        assert r.json()["estado"] == esperado


def test_carimbos_de_tempo(client, novo_pedido):
    pedido = novo_pedido()
    corpo = avancar(client, pedido, "recebido").json()
    assert corpo["iniciado_em"] is not None and corpo["pronto_em"] is None
    corpo = avancar(client, pedido, "preparando").json()
    assert corpo["pronto_em"] is not None


def test_nao_avanca_alem_de_entregue(client, novo_pedido):
    pedido = novo_pedido()
    for atual in ("recebido", "preparando", "pronto"):
        avancar(client, pedido, atual)
    assert avancar(client, pedido, "entregue").status_code == 409


def test_estado_desatualizado_e_conflito_e_nao_altera(client, novo_pedido):
    pedido = novo_pedido()
    assert avancar(client, pedido, "recebido").status_code == 200
    r = avancar(client, pedido, "recebido")
    assert r.status_code == 409
    fila = client.get("/api/pedidos").json()["pedidos"]
    assert fila[0]["estado"] == "preparando"


def test_pedido_inexistente(client):
    r = client.post("/api/pedidos/9999/avancar", json={"estado_atual": "recebido"})
    assert r.status_code == 404


def test_estado_invalido_e_422(client, novo_pedido):
    pedido = novo_pedido()
    assert avancar(client, pedido, "cancelado").status_code == 422


def test_linha_bloqueada_por_outro_atendente_e_conflito(client, fabrica_sessao, novo_pedido):
    pedido = novo_pedido()
    with fabrica_sessao() as segurando:
        segurando.scalars(
            select(Pedido).where(Pedido.id == pedido["id"]).with_for_update()
        ).one()
        assert avancar(client, pedido, "recebido").status_code == 409
        segurando.rollback()
    assert avancar(client, pedido, "recebido").status_code == 200


def test_corrida_entre_dois_atendentes(client, novo_pedido):
    pedido = novo_pedido()
    barreira = Barrier(2)

    def tentar():
        barreira.wait()
        return avancar(client, pedido, "recebido").status_code

    with ThreadPoolExecutor(2) as pool:
        codigos = sorted(f.result() for f in [pool.submit(tentar), pool.submit(tentar)])

    assert codigos == [200, 409]
    assert client.get("/api/pedidos").json()["pedidos"][0]["estado"] == "preparando"
