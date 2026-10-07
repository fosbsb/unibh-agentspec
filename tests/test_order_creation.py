def test_order_total_is_sum_of_items(client, ids):
    response = client.post(
        "/api/pedidos",
        json={
            "items": [
                {"product_id": ids["Hambúrguer clássico"], "quantity": 2},
                {"product_id": ids["Suco de laranja"], "quantity": 1},
            ]
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["total_cents"] == 5970
    assert body["status"] == "recebido"
    assert body["number"] == "001"
    assert [(i["name"], i["quantity"]) for i in body["items"]] == [
        ("Hambúrguer clássico", 2),
        ("Suco de laranja", 1),
    ]


def test_numbers_are_sequential_with_three_digits(new_order):
    assert [new_order()["number"] for _ in range(3)] == ["001", "002", "003"]


def test_empty_order_is_rejected(client):
    assert client.post("/api/pedidos", json={"items": []}).status_code == 422


def test_missing_items_is_rejected(client):
    assert client.post("/api/pedidos", json={}).status_code == 422


def test_quantity_must_be_between_1_and_20(client, ids):
    product_id = ids["Batata frita"]
    for quantity in (0, 21, -1):
        response = client.post(
            "/api/pedidos", json={"items": [{"product_id": product_id, "quantity": quantity}]}
        )
        assert response.status_code == 422
    ok = client.post(
        "/api/pedidos", json={"items": [{"product_id": product_id, "quantity": 20}]}
    )
    assert ok.status_code == 201


def test_unknown_product_is_rejected(client):
    response = client.post("/api/pedidos", json={"items": [{"product_id": 9999, "quantity": 1}]})
    assert response.status_code == 422
    assert response.json()["detail"] == "Produto não encontrado: 9999."


def test_client_total_is_ignored(client, ids):
    response = client.post(
        "/api/pedidos",
        json={
            "total_cents": 1,
            "total": 0.01,
            "items": [{"product_id": ids["X-Bacon"], "quantity": 1, "unit_price_cents": 1}],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["total_cents"] == 2990
    assert body["items"][0]["unit_price_cents"] == 2990


def test_repeated_product_lines_are_merged(client, ids):
    product_id = ids["Batata frita"]
    response = client.post(
        "/api/pedidos",
        json={
            "items": [
                {"product_id": product_id, "quantity": 1},
                {"product_id": product_id, "quantity": 2},
            ]
        },
    )
    body = response.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["quantity"] == 3
    assert body["total_cents"] == 4470


def test_failed_order_does_not_consume_a_number(client, new_order):
    assert new_order()["number"] == "001"
    client.post("/api/pedidos", json={"items": [{"product_id": 9999, "quantity": 1}]})
    assert new_order()["number"] == "002"
