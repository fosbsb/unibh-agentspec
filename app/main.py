from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import api, pages
from app.database import Base, SessionLocal, engine
from app.pages import STATIC_DIR
from app.seed import seed_products


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_products(db)
    yield


app = FastAPI(title="Totem de Autoatendimento", lifespan=lifespan)
app.include_router(api.router)
app.include_router(pages.router)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
