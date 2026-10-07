def test_menu_lists_ten_products(client):
    response = client.get("/api/produtos")
    assert response.status_code == 200
    assert len(response.json()) == 10


def test_menu_follows_category_order(client):
    products = client.get("/api/produtos").json()
    order = []
    for product in products:
        if product["category"] not in order:
            order.append(product["category"])
    assert order == ["Lanches", "Crepes", "Bebidas", "Sobremesas"]


def test_lanches_has_four_products(client):
    products = client.get("/api/produtos").json()
    assert [p["name"] for p in products if p["category"] == "Lanches"] == [
        "Hambúrguer clássico",
        "X-Bacon",
        "Cachorro-quente",
        "Batata frita",
    ]


def test_product_payload_shape(client):
    product = client.get("/api/produtos").json()[0]
    assert set(product) == {"id", "category", "name", "icon", "price_cents"}
    assert product["price_cents"] == 2490
