from fastapi import APIRouter, Depends
from sqlalchemy import case, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Produto
from app.schemas import ProdutoOut

router = APIRouter(tags=["produtos"])

ORDEM_CATEGORIAS = ["Lanches", "Crepes", "Bebidas", "Sobremesas"]


@router.get("/produtos", response_model=list[ProdutoOut])
def listar_produtos(db: Session = Depends(get_db)):
    ordem = case(
        {nome: i for i, nome in enumerate(ORDEM_CATEGORIAS)},
        value=Produto.categoria,
        else_=len(ORDEM_CATEGORIAS),
    )
    return db.scalars(select(Produto).order_by(ordem, Produto.id)).all()
