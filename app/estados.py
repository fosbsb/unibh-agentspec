from enum import Enum


class EstadoPedido(str, Enum):
    RECEBIDO = "recebido"
    PREPARANDO = "preparando"
    PRONTO = "pronto"
    ENTREGUE = "entregue"


SEQUENCIA = list(EstadoPedido)


def proximo_estado(atual: EstadoPedido) -> EstadoPedido | None:
    i = SEQUENCIA.index(atual)
    return SEQUENCIA[i + 1] if i + 1 < len(SEQUENCIA) else None


def transicao_valida(atual: EstadoPedido, destino: EstadoPedido) -> bool:
    return proximo_estado(atual) == destino
