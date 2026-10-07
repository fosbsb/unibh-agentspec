from datetime import date

import pytest
from sqlalchemy import func, select

from app.models import Pedido


def test_criar_pedido(client):
    r = client.post(
        "/api/pedidos",
        json={"itens": [{"produto_id": 1, "quantidade": 2}, {"produto_id": 7, "quantidade": 1}]},
    )
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["numero"] == "001"
    assert corpo["estado"] == "recebido"
    assert corpo["total_centavos"] == 2 * 2490 + 990
    assert corpo["itens"][0]["subtotal_centavos"] == 4980


def test_numeros_sequenciais(novo_pedido):
    assert [novo_pedido()["numero"] for _ in range(3)] == ["001", "002", "003"]


def test_numero_reinicia_no_dia_seguinte(dia, novo_pedido):
    dia(date(2026, 10, 6))
    novo_pedido()
    novo_pedido()
    dia(date(2026, 10, 7))
    assert novo_pedido()["numero"] == "001"


@pytest.mark.parametrize(
    "itens",
    [
        [],
        [{"produto_id": 1, "quantidade": 0}],
        [{"produto_id": 1, "quantidade": 100}],
        [{"produto_id": 999, "quantidade": 1}],
        [{"produto_id": "x", "quantidade": 1}],
    ],
)
def test_pedido_invalido_nao_grava(client, fabrica_sessao, itens):
    r = client.post("/api/pedidos", json={"itens": itens})
    assert r.status_code == 422
    with fabrica_sessao() as s:
        assert s.scalar(select(func.count()).select_from(Pedido)) == 0


def test_produto_inexistente_nao_consome_numero(client, novo_pedido):
    client.post("/api/pedidos", json={"itens": [{"produto_id": 999, "quantidade": 1}]})
    assert novo_pedido()["numero"] == "001"


def test_total_do_cliente_e_ignorado(client):
    r = client.post(
        "/api/pedidos",
        json={"itens": [{"produto_id": 4, "quantidade": 1}], "total_centavos": 1},
    )
    assert r.status_code == 201
    assert r.json()["total_centavos"] == 1490
