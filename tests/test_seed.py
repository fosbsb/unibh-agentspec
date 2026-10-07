from sqlalchemy import func, select

from app.models import Product
from app.seed import MENU, seed_products

EXPECTED = {
    "Hambúrguer clássico": ("Lanches", 2490),
    "X-Bacon": ("Lanches", 2990),
    "Cachorro-quente": ("Lanches", 1690),
    "Batata frita": ("Lanches", 1490),
    "Crepe de queijo e presunto": ("Crepes", 1990),
    "Crepe de chocolate com morango": ("Crepes", 2190),
    "Suco de laranja": ("Bebidas", 990),
    "Suco de abacaxi com hortelã": ("Bebidas", 1090),
    "Milk shake de chocolate": ("Bebidas", 1890),
    "Sundae de morango": ("Sobremesas", 1290),
}


def test_seed_loads_the_ten_products_with_prices_in_cents(db):
    rows = {p.name: (p.category, p.price_cents) for p in db.scalars(select(Product))}
    assert rows == EXPECTED


def test_seed_is_idempotent(db):
    seed_products(db)
    seed_products(db)
    assert db.scalar(select(func.count()).select_from(Product)) == len(MENU) == 10


def test_every_product_has_an_icon(db):
    assert all(p.icon for p in db.scalars(select(Product)))
