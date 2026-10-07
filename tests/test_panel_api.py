from datetime import timedelta

from app.config import utcnow
from app.models import Order


def advance(client, order_id, from_state):
    response = client.post(
        f"/api/pedidos/{order_id}/avancar", json={"from_state": from_state}
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_panel_shows_only_preparing_and_ready(client, new_order):
    received = new_order()
    preparing = new_order()
    ready = new_order()
    delivered = new_order()
    canceled = new_order()

    advance(client, preparing["id"], "recebido")
    advance(client, ready["id"], "recebido")
    advance(client, ready["id"], "preparando")
    advance(client, delivered["id"], "recebido")
    advance(client, delivered["id"], "preparando")
    advance(client, delivered["id"], "pronto")
    client.post(f"/api/pedidos/{canceled['id']}/cancelar")

    panel = client.get("/api/painel").json()

    assert [o["number"] for o in panel["preparing"]] == [preparing["number"]]
    assert [o["number"] for o in panel["ready"]] == [ready["number"]]
    listed = {o["id"] for o in panel["preparing"] + panel["ready"]}
    assert {received["id"], delivered["id"], canceled["id"]}.isdisjoint(listed)


def test_ready_list_shows_newest_first(client, new_order):
    first, second = new_order(), new_order()
    for order in (first, second):
        advance(client, order["id"], "recebido")
        advance(client, order["id"], "preparando")

    panel = client.get("/api/painel").json()

    assert [o["number"] for o in panel["ready"]] == [second["number"], first["number"]]


def test_average_is_null_without_ready_orders(client, new_order):
    new_order()
    assert client.get("/api/painel").json()["avg_prep_seconds"] is None


def test_average_prep_time_uses_ready_at_minus_created_at(client, db, new_order):
    order = new_order()
    advance(client, order["id"], "recebido")
    advance(client, order["id"], "preparando")

    row = db.get(Order, order["id"])
    row.created_at = utcnow() - timedelta(seconds=120)
    row.ready_at = row.created_at + timedelta(seconds=120)
    db.commit()

    assert client.get("/api/painel").json()["avg_prep_seconds"] == 120


def test_average_ignores_orders_from_other_days(client, db, new_order):
    order = new_order()
    advance(client, order["id"], "recebido")
    advance(client, order["id"], "preparando")

    row = db.get(Order, order["id"])
    row.order_date = row.order_date - timedelta(days=1)
    db.commit()

    assert client.get("/api/painel").json()["avg_prep_seconds"] is None
