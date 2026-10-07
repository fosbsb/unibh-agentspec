from fastapi import APIRouter

from app.database import SessaoDep
from app.schemas import CardapioSaida
from app.services import pedidos as servico

router = APIRouter(prefix="/api")


@router.get("/produtos", response_model=CardapioSaida)
def cardapio(session: SessaoDep):
    categorias = servico.listar_cardapio(session)
    return {
        "categorias": [{"nome": nome, "produtos": produtos} for nome, produtos in categorias]
    }
