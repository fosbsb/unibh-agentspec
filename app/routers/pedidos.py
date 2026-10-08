from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import servicos
from app.database import get_db
from app.estados import EstadoPedido
from app.schemas import EstadoIn, PedidoIn, PedidoOut

router = APIRouter(tags=["pedidos"])


@router.post("/pedidos", response_model=PedidoOut, status_code=201)
def criar_pedido(corpo: PedidoIn, db: Session = Depends(get_db)):
    return servicos.criar_pedido(db, corpo.itens)


@router.get("/pedidos", response_model=list[PedidoOut])
def listar_pedidos(
    estado: Annotated[list[EstadoPedido] | None, Query()] = None,
    db: Session = Depends(get_db),
):
    return servicos.listar_pedidos(db, estado)


@router.patch("/pedidos/{pedido_id}/estado", response_model=PedidoOut)
def mudar_estado(pedido_id: int, corpo: EstadoIn, db: Session = Depends(get_db)):
    return servicos.mudar_estado(db, pedido_id, corpo.estado)
