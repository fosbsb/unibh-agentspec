from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.database import Base, SessionLocal, engine
from app.routers import pedidos, produtos
from app.seed import carregar_cardapio

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        carregar_cardapio(session)
    yield


app = FastAPI(title="Totem de Atendimento", lifespan=lifespan)
app.include_router(produtos.router)
app.include_router(pedidos.router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def raiz():
    return RedirectResponse("/totem")


def _pagina(nome: str):
    def entregar():
        return FileResponse(STATIC_DIR / f"{nome}.html")

    return entregar


for _nome in ("totem", "cozinha", "painel"):
    app.add_api_route(f"/{_nome}", _pagina(_nome), include_in_schema=False)
