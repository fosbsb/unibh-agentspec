from app.models import Produto
from app.seed import carregar_cardapio


def test_seed_carrega_10_produtos_em_4_categorias(client):
    produtos = client.get("/api/produtos").json()
    assert len(produtos) == 10
    assert {p["categoria"] for p in produtos} == {
        "Lanches", "Crepes", "Bebidas", "Sobremesas"
    }


def test_produtos_ordenados_por_categoria(client):
    categorias = [p["categoria"] for p in client.get("/api/produtos").json()]
    esperado = ["Lanches"] * 4 + ["Crepes"] * 2 + ["Bebidas"] * 3 + ["Sobremesas"]
    assert categorias == esperado


def test_precos_em_centavos(client):
    precos = {p["nome"]: p["preco_centavos"] for p in client.get("/api/produtos").json()}
    assert precos["Hambúrguer clássico"] == 2490
    assert precos["X-Bacon"] == 2990
    assert precos["Suco de laranja"] == 990
    assert precos["Sundae de morango"] == 1290


def test_seed_e_idempotente(db_session):
    assert carregar_cardapio(db_session) == 0
    assert carregar_cardapio(db_session) == 0
    assert db_session.query(Produto).count() == 10
