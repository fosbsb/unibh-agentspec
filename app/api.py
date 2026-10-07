from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import config, services
from app.database import get_db
from app.domain import (
    InvalidTransition,
    OrderLocked,
    OrderNotFound,
    OrderStatus,
    ProductNotFound,
    StaleState,
)
from app.schemas import AdvanceIn, OrderCreate, OrderOut, PanelOut, ProductOut

router = APIRouter(prefix="/api")


@router.get("/produtos", response_model=list[ProductOut])
def products(db: Session = Depends(get_db)):
    return services.list_products(db)


@router.post("/pedidos", response_model=OrderOut, status_code=201)
def create_order(body: OrderCreate, db: Session = Depends(get_db)):
    items = [(item.product_id, item.quantity) for item in body.items]
    try:
        return services.create_order(db, items, config.today())
    except ProductNotFound as error:
        raise HTTPException(422, f"Produto não encontrado: {error.args[0]}.")


@router.get("/pedidos", response_model=list[OrderOut])
def list_orders(
    estado: list[OrderStatus] | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return services.list_orders(db, estado)


@router.post("/pedidos/{order_id}/avancar", response_model=OrderOut)
def advance(order_id: int, body: AdvanceIn, db: Session = Depends(get_db)):
    try:
        return services.advance_order(db, order_id, body.from_state)
    except OrderNotFound:
        raise HTTPException(404, "Pedido não encontrado.")
    except OrderLocked:
        raise HTTPException(
            409, "Outro atendente está mudando este pedido. Atualize a lista."
        )
    except StaleState:
        raise HTTPException(409, "O pedido já mudou de estado. Atualize a lista.")
    except InvalidTransition:
        raise HTTPException(409, "Este pedido não pode avançar.")


@router.post("/pedidos/{order_id}/cancelar", response_model=OrderOut)
def cancel(order_id: int, db: Session = Depends(get_db)):
    try:
        return services.cancel_order(db, order_id)
    except OrderNotFound:
        raise HTTPException(404, "Pedido não encontrado.")
    except OrderLocked:
        raise HTTPException(
            409, "Outro atendente está mudando este pedido. Atualize a lista."
        )
    except InvalidTransition:
        raise HTTPException(409, "Este pedido não pode mais ser cancelado.")


@router.get("/painel", response_model=PanelOut)
def panel(db: Session = Depends(get_db)):
    return services.panel(db, config.today())
