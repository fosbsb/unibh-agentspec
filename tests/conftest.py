import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

_source_url = make_url(
    os.environ.get("DATABASE_URL", "postgresql+psycopg://totem:totem@db:5432/totem")
)
TEST_DB_NAME = "totem_test"
_test_url = _source_url.set(database=TEST_DB_NAME)


def _ensure_test_database() -> None:
    admin = create_engine(_source_url, isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),
            {"name": TEST_DB_NAME},
        )
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    admin.dispose()


_ensure_test_database()
os.environ["DATABASE_URL"] = _test_url.render_as_string(hide_password=False)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Product  # noqa: E402
from app.seed import seed_products  # noqa: E402


def _assert_test_database() -> None:
    assert engine.url.database.endswith("_test"), "os testes só rodam em bancos *_test"


@pytest.fixture(scope="session", autouse=True)
def schema():
    _assert_test_database()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_database(schema):
    _assert_test_database()
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    with SessionLocal() as db:
        seed_products(db)


@pytest.fixture
def db():
    with SessionLocal() as session:
        yield session


@pytest.fixture
def ids(db):
    return {p.name: p.id for p in db.query(Product).all()}


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def new_order(client, ids):
    def _create(items=None):
        payload = items or [{"product_id": ids["Hambúrguer clássico"], "quantity": 1}]
        response = client.post("/api/pedidos", json={"items": payload})
        assert response.status_code == 201, response.text
        return response.json()

    return _create
