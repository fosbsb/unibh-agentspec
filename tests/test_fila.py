from datetime import timedelta

from sqlalchemy import select

from app import relogio
from app.models import Pedido


def avancar(client, pedido, atual):
    return client.post(f"/api/pedidos/{pedido['id']}/avancar", json={"estado_atual": atual})


def test_fila_em_ordem_de_chegada_sem_entregues(client, novo_pedido):
    a, b, c = novo_pedido(), novo_pedido(), novo_pedido()
    for atual in ("recebido", "preparando", "pronto"):
        avancar(client, a, atual)
    fila = client.get("/api/pedidos").json()["pedidos"]
    assert [p["numero"] for p in fila] == [b["numero"], c["numero"]]


def test_fila_traz_itens_e_total(client, novo_pedido):
    novo_pedido([{"produto_id": 2, "quantidade": 3}])
    pedido = client.get("/api/pedidos").json()["pedidos"][0]
    assert pedido["itens"][0]["nome"] == "X-Bacon"
    assert pedido["total_centavos"] == 3 * 2990


def test_tempo_medio_sem_pedidos_prontos_e_nulo(client, novo_pedido):
    novo_pedido()
    assert client.get("/api/pedidos").json()["tempo_medio_preparo_segundos"] is None


def test_tempo_medio_de_preparo(client, fabrica_sessao, novo_pedido):
    ids = [novo_pedido()["id"], novo_pedido()["id"]]
    inicio = relogio.agora()
    with fabrica_sessao() as s:
        for pedido_id, minutos in zip(ids, (4, 6)):
            p = s.scalars(select(Pedido).where(Pedido.id == pedido_id)).one()
            p.estado = "pronto"
            p.iniciado_em = inicio
            p.pronto_em = inicio + timedelta(minutes=minutos)
        s.commit()
    assert client.get("/api/pedidos").json()["tempo_medio_preparo_segundos"] == 300
