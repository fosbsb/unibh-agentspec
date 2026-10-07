import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date

import pytest
from sqlalchemy import select

from app import services
from app.database import SessionLocal
from app.domain import OrderLocked, OrderStatus, StaleState
from app.models import Order


@pytest.fixture
def order_id(db, ids):
    order = services.create_order(db, [(ids["Hambúrguer clássico"], 1)], date(2026, 5, 1))
    return order.id


def test_two_simultaneous_advances_move_the_order_once(order_id):
    barrier = threading.Barrier(2)

    def attempt(_):
        with SessionLocal() as session:
            barrier.wait()
            try:
                services.advance_order(session, order_id, OrderStatus.RECEBIDO)
                return "ok"
            except (OrderLocked, StaleState) as error:
                return type(error).__name__

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, range(2)))

    assert results.count("ok") == 1
    assert results.count("ok") + sum(r in ("OrderLocked", "StaleState") for r in results) == 2
    with SessionLocal() as session:
        assert session.get(Order, order_id).status is OrderStatus.PREPARANDO


def test_locked_row_is_refused_immediately_without_waiting(order_id):
    holder = SessionLocal()
    holder.execute(select(Order).where(Order.id == order_id).with_for_update())
    try:
        with SessionLocal() as other:
            started = time.monotonic()
            with pytest.raises(OrderLocked):
                services.advance_order(other, order_id, OrderStatus.RECEBIDO)
            assert time.monotonic() - started < 2
    finally:
        holder.rollback()
        holder.close()

    with SessionLocal() as session:
        assert (
            services.advance_order(session, order_id, OrderStatus.RECEBIDO).status
            is OrderStatus.PREPARANDO
        )


def test_locked_row_returns_409_through_the_api(client, order_id):
    holder = SessionLocal()
    holder.execute(select(Order).where(Order.id == order_id).with_for_update())
    try:
        response = client.post(
            f"/api/pedidos/{order_id}/avancar", json={"from_state": "recebido"}
        )
    finally:
        holder.rollback()
        holder.close()

    assert response.status_code == 409
    assert "Outro atendente" in response.json()["detail"]


def test_cancel_and_advance_race_leaves_a_consistent_state(order_id):
    barrier = threading.Barrier(2)

    def advance():
        with SessionLocal() as session:
            barrier.wait()
            try:
                services.advance_order(session, order_id, OrderStatus.RECEBIDO)
            except (OrderLocked, StaleState):
                pass

    def cancel():
        with SessionLocal() as session:
            barrier.wait()
            try:
                services.cancel_order(session, order_id)
            except Exception:
                pass

    threads = [threading.Thread(target=advance), threading.Thread(target=cancel)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    with SessionLocal() as session:
        assert session.get(Order, order_id).status in (
            OrderStatus.PREPARANDO,
            OrderStatus.CANCELADO,
        )
