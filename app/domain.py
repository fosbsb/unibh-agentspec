from enum import Enum


class OrderStatus(str, Enum):
    RECEBIDO = "recebido"
    PREPARANDO = "preparando"
    PRONTO = "pronto"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"


NEXT = {
    OrderStatus.RECEBIDO: OrderStatus.PREPARANDO,
    OrderStatus.PREPARANDO: OrderStatus.PRONTO,
    OrderStatus.PRONTO: OrderStatus.ENTREGUE,
}
CANCELABLE = {OrderStatus.RECEBIDO, OrderStatus.PREPARANDO}
ACTIVE = (OrderStatus.RECEBIDO, OrderStatus.PREPARANDO, OrderStatus.PRONTO)


class OrderNotFound(Exception):
    pass


class ProductNotFound(Exception):
    pass


class OrderLocked(Exception):
    pass


class StaleState(Exception):
    pass


class InvalidTransition(Exception):
    pass
