from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import database, models  # noqa: F401
from app.routers import painel, pedidos, produtos
from app.seed import carregar_cardapio

STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.esperar_banco()
    database.Base.metadata.create_all(database.engine)
    with database.SessionLocal() as db:
        carregar_cardapio(db)
    yield


app = FastAPI(title="Totem de Autoatendimento", lifespan=lifespan)
app.include_router(produtos.router, prefix="/api")
app.include_router(pedidos.router, prefix="/api")
app.include_router(painel.router, prefix="/api")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


def _pagina(nome: str):
    return lambda: FileResponse(STATIC / f"{nome}.html")


for _nome in ("totem", "cozinha", "painel"):
    app.add_api_route(f"/{_nome}", _pagina(_nome), include_in_schema=False)
