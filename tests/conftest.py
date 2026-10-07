from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app import config, relogio
from app.database import Base, get_session
from app.main import app
from app.seed import carregar_cardapio

TEST_DB = "totem_test"


@pytest.fixture(scope="session")
def engine():
    base = make_url(config.DATABASE_URL)
    admin = create_engine(base.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        existe = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": TEST_DB}
        )
        if not existe:
            conn.execute(text(f"CREATE DATABASE {TEST_DB}"))
    admin.dispose()
    eng = create_engine(base.set(database=TEST_DB))
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture(autouse=True)
def banco_limpo(engine):
    with engine.begin() as conn:
        conn.execute(
            text("TRUNCATE itens_pedido, pedidos, contador_dia, produtos RESTART IDENTITY CASCADE")
        )
    with Session(engine) as session:
        carregar_cardapio(session)


@pytest.fixture
def fabrica_sessao(engine):
    return sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
def client(fabrica_sessao):
    def sessao():
        with fabrica_sessao() as s:
            yield s

    app.dependency_overrides[get_session] = sessao
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def dia(monkeypatch):
    def definir(d: date):
        monkeypatch.setattr(relogio, "hoje", lambda: d)

    return definir


@pytest.fixture
def novo_pedido(client):
    def criar(itens=None):
        itens = itens or [{"produto_id": 1, "quantidade": 1}]
        r = client.post("/api/pedidos", json={"itens": itens})
        assert r.status_code == 201, r.text
        return r.json()

    return criar
