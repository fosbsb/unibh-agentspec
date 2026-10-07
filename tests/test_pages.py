import pytest


@pytest.mark.parametrize("path", ["/", "/totem", "/cozinha", "/painel"])
def test_pages_are_served_as_html(client, path):
    response = client.get(path)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")


def test_totem_has_the_start_screen(client):
    assert "Toque para começar" in client.get("/totem").text


def test_totem_has_the_review_step_before_confirming(client):
    html = client.get("/totem").text
    assert "Revisar pedido" in html
    assert "Revise seu pedido" in html
    assert "Voltar e editar" in html
    assert "Confirmar pedido" in html
    assert "Finalizar pedido" not in html


def test_painel_has_both_columns(client):
    html = client.get("/painel").text
    assert "Preparando" in html
    assert "Pronto" in html


@pytest.mark.parametrize(
    "path",
    [
        "/static/css/tokens.css",
        "/static/css/components.css",
        "/static/js/totem.js",
        "/static/js/cozinha.js",
        "/static/js/painel.js",
        "/static/js/common.js",
        "/static/js/config.js",
        "/static/js/tailwind-config.js",
    ],
)
def test_static_assets_are_served(client, path):
    assert client.get(path).status_code == 200


def test_unknown_page_is_404(client):
    assert client.get("/nao-existe").status_code == 404
