import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.database import Base, get_db
from app.main import app
from app.seed import carregar_cardapio


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with Sessao() as db:
        carregar_cardapio(db)
        yield db


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def criar(client):
    def _criar(*itens):
        corpo = {"itens": [{"produto_id": p, "quantidade": q} for p, q in itens]}
        resposta = client.post("/api/pedidos", json=corpo)
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return _criar


@pytest.fixture
def mudar(client):
    def _mudar(pedido_id, estado):
        return client.patch(f"/api/pedidos/{pedido_id}/estado", json={"estado": estado})

    return _mudar
