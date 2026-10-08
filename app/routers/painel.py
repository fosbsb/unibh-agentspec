from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import servicos
from app.database import get_db
from app.estados import EstadoPedido
from app.schemas import PainelOut

router = APIRouter(tags=["painel"])


@router.get("/painel", response_model=PainelOut)
def painel(db: Session = Depends(get_db)):
    preparando = servicos.listar_pedidos(db, [EstadoPedido.PREPARANDO])
    pronto = servicos.listar_pedidos(db, [EstadoPedido.PRONTO])
    return PainelOut(
        preparando=preparando,
        pronto=pronto,
        tempo_medio_segundos=servicos.tempo_medio_segundos(db),
    )
