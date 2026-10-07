from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models import Product

MENU = [
    ("Lanches", "Hambúrguer clássico", "🍔", 2490),
    ("Lanches", "X-Bacon", "🥓", 2990),
    ("Lanches", "Cachorro-quente", "🌭", 1690),
    ("Lanches", "Batata frita", "🍟", 1490),
    ("Crepes", "Crepe de queijo e presunto", "🥞", 1990),
    ("Crepes", "Crepe de chocolate com morango", "🍓", 2190),
    ("Bebidas", "Suco de laranja", "🍊", 990),
    ("Bebidas", "Suco de abacaxi com hortelã", "🍍", 1090),
    ("Bebidas", "Milk shake de chocolate", "🥤", 1890),
    ("Sobremesas", "Sundae de morango", "🍦", 1290),
]


def seed_products(db: Session) -> None:
    rows = [
        {
            "category": category,
            "name": name,
            "icon": icon,
            "price_cents": price_cents,
            "position": position,
        }
        for position, (category, name, icon, price_cents) in enumerate(MENU)
    ]
    db.execute(
        pg_insert(Product).values(rows).on_conflict_do_nothing(index_elements=["name"])
    )
    db.commit()
