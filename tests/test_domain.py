from app.domain import ACTIVE, CANCELABLE, NEXT, OrderStatus


def test_forward_chain_ends_in_entregue():
    assert NEXT[OrderStatus.RECEBIDO] is OrderStatus.PREPARANDO
    assert NEXT[OrderStatus.PREPARANDO] is OrderStatus.PRONTO
    assert NEXT[OrderStatus.PRONTO] is OrderStatus.ENTREGUE


def test_final_states_have_no_next():
    assert OrderStatus.ENTREGUE not in NEXT
    assert OrderStatus.CANCELADO not in NEXT


def test_only_recebido_and_preparando_can_be_canceled():
    assert CANCELABLE == {OrderStatus.RECEBIDO, OrderStatus.PREPARANDO}


def test_active_states_exclude_final_ones():
    assert set(ACTIVE) == {
        OrderStatus.RECEBIDO,
        OrderStatus.PREPARANDO,
        OrderStatus.PRONTO,
    }
