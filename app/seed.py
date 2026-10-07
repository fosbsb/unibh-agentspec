from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models import Produto

CARDAPIO = [
    {"nome": "Hambúrguer clássico", "categoria": "Lanches", "icone": "🍔", "preco_centavos": 2490},
    {"nome": "X-Bacon", "categoria": "Lanches", "icone": "🥓", "preco_centavos": 2990},
    {"nome": "Cachorro-quente", "categoria": "Lanches", "icone": "🌭", "preco_centavos": 1690},
    {"nome": "Batata frita", "categoria": "Lanches", "icone": "🍟", "preco_centavos": 1490},
    {"nome": "Crepe de queijo e presunto", "categoria": "Crepes", "icone": "🥞", "preco_centavos": 1990},
    {"nome": "Crepe de chocolate com morango", "categoria": "Crepes", "icone": "🍓", "preco_centavos": 2190},
    {"nome": "Suco de laranja", "categoria": "Bebidas", "icone": "🍊", "preco_centavos": 990},
    {"nome": "Suco de abacaxi com hortelã", "categoria": "Bebidas", "icone": "🍍", "preco_centavos": 1090},
    {"nome": "Milk shake de chocolate", "categoria": "Bebidas", "icone": "🥤", "preco_centavos": 1890},
    {"nome": "Sundae de morango", "categoria": "Sobremesas", "icone": "🍦", "preco_centavos": 1290},
]


def carregar_cardapio(session: Session) -> None:
    stmt = pg_insert(Produto).values(CARDAPIO).on_conflict_do_nothing(index_elements=["nome"])
    session.execute(stmt)
    session.commit()
