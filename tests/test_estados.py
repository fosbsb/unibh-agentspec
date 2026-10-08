import pytest

from app.estados import EstadoPedido as E
from app.estados import proximo_estado, transicao_valida


def test_sequencia_completa():
    assert proximo_estado(E.RECEBIDO) == E.PREPARANDO
    assert proximo_estado(E.PREPARANDO) == E.PRONTO
    assert proximo_estado(E.PRONTO) == E.ENTREGUE


def test_entregue_e_o_fim_da_linha():
    assert proximo_estado(E.ENTREGUE) is None


@pytest.mark.parametrize(
    "atual,destino",
    [(E.RECEBIDO, E.PREPARANDO), (E.PREPARANDO, E.PRONTO), (E.PRONTO, E.ENTREGUE)],
)
def test_transicoes_validas(atual, destino):
    assert transicao_valida(atual, destino)


@pytest.mark.parametrize(
    "atual,destino",
    [
        (E.RECEBIDO, E.PRONTO),
        (E.RECEBIDO, E.ENTREGUE),
        (E.PREPARANDO, E.RECEBIDO),
        (E.PRONTO, E.PREPARANDO),
        (E.ENTREGUE, E.RECEBIDO),
        (E.PREPARANDO, E.PREPARANDO),
    ],
)
def test_transicoes_invalidas(atual, destino):
    assert not transicao_valida(atual, destino)
