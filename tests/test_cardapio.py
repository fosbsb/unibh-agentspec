from sqlalchemy import func, select

from app.models import Produto
from app.seed import carregar_cardapio


def test_carga_idempotente(fabrica_sessao):
    with fabrica_sessao() as s:
        carregar_cardapio(s)
        carregar_cardapio(s)
        assert s.scalar(select(func.count()).select_from(Produto)) == 10


def test_cardapio_agrupado_por_categoria(client):
    corpo = client.get("/api/produtos").json()
    categorias = corpo["categorias"]
    assert [c["nome"] for c in categorias] == ["Lanches", "Crepes", "Bebidas", "Sobremesas"]
    assert [len(c["produtos"]) for c in categorias] == [4, 2, 3, 1]
    precos = {p["nome"]: p["preco_centavos"] for c in categorias for p in c["produtos"]}
    assert precos["Hambúrguer clássico"] == 2490
    assert precos["X-Bacon"] == 2990
    assert precos["Sundae de morango"] == 1290
    assert len(precos) == 10
