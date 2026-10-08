from app.models import Produto

CARDAPIO = [
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


def carregar_cardapio(db) -> int:
    if db.query(Produto).first() is not None:
        return 0
    db.add_all(
        Produto(categoria=c, nome=n, icone=i, preco_centavos=p)
        for c, n, i, p in CARDAPIO
    )
    db.commit()
    return len(CARDAPIO)
