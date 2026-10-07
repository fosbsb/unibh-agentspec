def advance(client, order, from_state=None):
    return client.post(
        f"/api/pedidos/{order['id']}/avancar",
        json={"from_state": from_state or order["status"]},
    )


def test_queue_is_in_arrival_order(client, new_order):
    created = [new_order()["number"] for _ in range(3)]
    listed = [o["number"] for o in client.get("/api/pedidos").json()]
    assert listed == created == ["001", "002", "003"]


def test_order_walks_through_all_states(client, new_order):
    order = new_order()
    assert order["ready_at"] is None

    preparing = advance(client, order).json()
    assert preparing["status"] == "preparando"

    ready = advance(client, preparing).json()
    assert ready["status"] == "pronto"
    assert ready["ready_at"] is not None

    delivered = advance(client, ready).json()
    assert delivered["status"] == "entregue"


def test_delivered_and_canceled_leave_the_default_list(client, new_order):
    delivered = new_order()
    for _ in range(3):
        delivered = advance(client, delivered).json()
    canceled = new_order()
    client.post(f"/api/pedidos/{canceled['id']}/cancelar")
    open_order = new_order()

    listed = [o["number"] for o in client.get("/api/pedidos").json()]

    assert listed == [open_order["number"]]


def test_filter_by_state_is_repeatable(client, new_order):
    first, second, third = new_order(), new_order(), new_order()
    advance(client, first)
    prepared = advance(client, second).json()
    advance(client, prepared)

    response = client.get("/api/pedidos?estado=preparando&estado=pronto")

    assert [(o["number"], o["status"]) for o in response.json()] == [
        ("001", "preparando"),
        ("002", "pronto"),
    ]
    assert third["status"] == "recebido"


def test_unknown_state_filter_is_rejected(client):
    assert client.get("/api/pedidos?estado=voando").status_code == 422


def test_cancel_from_recebido_and_preparando(client, new_order):
    received = new_order()
    preparing = advance(client, new_order()).json()

    first = client.post(f"/api/pedidos/{received['id']}/cancelar")
    second = client.post(f"/api/pedidos/{preparing['id']}/cancelar")

    assert first.json()["status"] == "cancelado"
    assert second.json()["status"] == "cancelado"
    listed = client.get("/api/pedidos?estado=cancelado").json()
    assert len(listed) == 2


def test_cancel_is_refused_when_pronto(client, new_order):
    order = new_order()
    order = advance(client, order).json()
    order = advance(client, order).json()

    response = client.post(f"/api/pedidos/{order['id']}/cancelar")

    assert response.status_code == 409
    assert response.json()["detail"] == "Este pedido não pode mais ser cancelado."
    assert client.get("/api/pedidos?estado=pronto").json()[0]["id"] == order["id"]


def test_cancel_twice_is_refused(client, new_order):
    order = new_order()
    client.post(f"/api/pedidos/{order['id']}/cancelar")
    assert client.post(f"/api/pedidos/{order['id']}/cancelar").status_code == 409


def test_advance_is_refused_for_final_states(client, new_order):
    delivered = new_order()
    for _ in range(3):
        delivered = advance(client, delivered).json()
    canceled = new_order()
    client.post(f"/api/pedidos/{canceled['id']}/cancelar")

    for order, state in ((delivered, "entregue"), (canceled, "cancelado")):
        response = advance(client, order, from_state=state)
        assert response.status_code == 409
        assert response.json()["detail"] == "Este pedido não pode avançar."


def test_stale_from_state_is_refused_and_state_is_unchanged(client, new_order):
    order = new_order()

    response = advance(client, order, from_state="preparando")

    assert response.status_code == 409
    assert response.json()["detail"] == "O pedido já mudou de estado. Atualize a lista."
    assert client.get("/api/pedidos").json()[0]["status"] == "recebido"


def test_second_sequential_advance_does_not_skip_a_state(client, new_order):
    order = new_order()

    first = advance(client, order)
    second = advance(client, order)

    assert first.status_code == 200
    assert second.status_code == 409
    assert client.get("/api/pedidos").json()[0]["status"] == "preparando"


def test_unknown_order_is_404(client):
    assert client.post("/api/pedidos/999/avancar", json={"from_state": "recebido"}).status_code == 404
    assert client.post("/api/pedidos/999/cancelar").status_code == 404


def test_advance_requires_valid_from_state(client, new_order):
    order = new_order()
    url = f"/api/pedidos/{order['id']}/avancar"
    assert client.post(url, json={}).status_code == 422
    assert client.post(url, json={"from_state": "voando"}).status_code == 422
