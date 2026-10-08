from sqlalchemy.exc import IntegrityError

from app import servicos
from app.models import Pedido

HAMBURGUER, BATATA = 1, 4


def test_cria_pedido_com_total_calculado(criar):
    pedido = criar((HAMBURGUER, 2), (BATATA, 1))
    assert pedido["total_centavos"] == 6470
    assert pedido["estado"] == "recebido"
    assert pedido["numero"] == 100
    assert {i["nome"] for i in pedido["itens"]} == {"Hambúrguer clássico", "Batata frita"}


def test_ignora_total_enviado_pelo_cliente(client):
    resposta = client.post(
        "/api/pedidos",
        json={"itens": [{"produto_id": BATATA, "quantidade": 1}], "total_centavos": 1},
    )
    assert resposta.status_code == 201
    assert resposta.json()["total_centavos"] == 1490


def test_soma_linhas_repetidas_do_mesmo_produto(criar):
    pedido = criar((BATATA, 2), (BATATA, 3))
    assert len(pedido["itens"]) == 1
    assert pedido["itens"][0]["quantidade"] == 5
    assert pedido["total_centavos"] == 5 * 1490


def test_rejeita_soma_acima_do_limite(client):
    corpo = {"itens": [{"produto_id": BATATA, "quantidade": 20}] * 2}
    assert client.post("/api/pedidos", json=corpo).status_code == 422


def test_produto_inexistente_devolve_404_e_nao_cria(client):
    resposta = client.post(
        "/api/pedidos", json={"itens": [{"produto_id": 999, "quantidade": 1}]}
    )
    assert resposta.status_code == 404
    assert client.get("/api/pedidos").json() == []


def test_quantidade_invalida_devolve_422(client):
    for q in (0, -1, 21):
        corpo = {"itens": [{"produto_id": BATATA, "quantidade": q}]}
        assert client.post("/api/pedidos", json=corpo).status_code == 422
    assert client.get("/api/pedidos").json() == []


def test_lista_vazia_devolve_422(client):
    assert client.post("/api/pedidos", json={"itens": []}).status_code == 422


def test_mais_de_30_linhas_devolve_422(client):
    corpo = {"itens": [{"produto_id": BATATA, "quantidade": 1}] * 31}
    assert client.post("/api/pedidos", json=corpo).status_code == 422


def test_numeros_crescentes_e_ordem_de_chegada(criar, client):
    numeros = [criar((BATATA, 1))["numero"] for _ in range(3)]
    assert numeros == [100, 101, 102]
    listados = [p["numero"] for p in client.get("/api/pedidos").json()]
    assert listados == [100, 101, 102]


def test_item_guarda_copia_do_preco(criar, db_session):
    pedido = criar((BATATA, 1))
    from app.models import Produto

    db_session.get(Produto, BATATA).preco_centavos = 9999
    db_session.commit()
    assert pedido["itens"][0]["preco_centavos"] == 1490


def test_avanca_estados_na_ordem(criar, mudar):
    pedido = criar((BATATA, 1))
    for destino in ("preparando", "pronto", "entregue"):
        resposta = mudar(pedido["id"], destino)
        assert resposta.status_code == 200
        assert resposta.json()["estado"] == destino


def test_pular_estado_devolve_409_e_nao_altera(criar, mudar, client):
    pedido = criar((BATATA, 1))
    assert mudar(pedido["id"], "pronto").status_code == 409
    atual = client.get("/api/pedidos").json()[0]
    assert atual["estado"] == "recebido"


def test_duplo_envio_do_mesmo_estado_devolve_409(criar, mudar):
    pedido = criar((BATATA, 1))
    assert mudar(pedido["id"], "preparando").status_code == 200
    assert mudar(pedido["id"], "preparando").status_code == 409


def test_voltar_estado_devolve_409(criar, mudar):
    pedido = criar((BATATA, 1))
    mudar(pedido["id"], "preparando")
    assert mudar(pedido["id"], "recebido").status_code == 409


def test_pedido_entregue_nao_muda_mais(criar, mudar):
    pedido = criar((BATATA, 1))
    for destino in ("preparando", "pronto", "entregue"):
        mudar(pedido["id"], destino)
    assert mudar(pedido["id"], "entregue").status_code == 409


def test_pedido_inexistente_devolve_404(mudar):
    assert mudar(999, "preparando").status_code == 404


def test_estado_desconhecido_devolve_422(criar, mudar):
    pedido = criar((BATATA, 1))
    assert mudar(pedido["id"], "cancelado").status_code == 422


def test_registra_horario_de_cada_transicao(criar, mudar, db_session):
    pedido = criar((BATATA, 1))
    mudar(pedido["id"], "preparando")
    mudar(pedido["id"], "pronto")
    registro = db_session.get(Pedido, pedido["id"])
    assert registro.preparando_em is not None
    assert registro.pronto_em is not None
    assert registro.entregue_em is None


def test_filtro_de_estado_repetivel(criar, mudar, client):
    a, b, c = (criar((BATATA, 1)) for _ in range(3))
    mudar(b["id"], "preparando")
    mudar(c["id"], "preparando")
    mudar(c["id"], "pronto")
    resposta = client.get("/api/pedidos?estado=recebido&estado=pronto").json()
    assert [p["numero"] for p in resposta] == [a["numero"], c["numero"]]


def test_filtro_com_estado_desconhecido_devolve_422(client):
    assert client.get("/api/pedidos?estado=cancelado").status_code == 422


def test_conflito_de_numero_refaz_a_tentativa(client, db_session, monkeypatch):
    original = db_session.commit
    falhas = {"restantes": 2}

    def commit_com_corrida():
        if falhas["restantes"] > 0:
            falhas["restantes"] -= 1
            raise IntegrityError("insert", {}, Exception("numero duplicado"))
        original()

    monkeypatch.setattr(db_session, "commit", commit_com_corrida)
    resposta = client.post(
        "/api/pedidos", json={"itens": [{"produto_id": BATATA, "quantidade": 1}]}
    )
    assert resposta.status_code == 201
    assert falhas["restantes"] == 0


def test_esgotar_tentativas_devolve_503(client, db_session, monkeypatch):
    def sempre_falha():
        raise IntegrityError("insert", {}, Exception("numero duplicado"))

    monkeypatch.setattr(db_session, "commit", sempre_falha)
    resposta = client.post(
        "/api/pedidos", json={"itens": [{"produto_id": BATATA, "quantidade": 1}]}
    )
    assert resposta.status_code == 503
    assert servicos.MAX_TENTATIVAS == 5


def _pedido_direto(db, numero, estado="recebido"):
    pedido = Pedido(numero=numero, estado=estado, total_centavos=0)
    db.add(pedido)
    db.commit()
    return pedido


def test_senha_sempre_com_3_digitos_comecando_com_1(criar):
    for _ in range(5):
        numero = criar((BATATA, 1))["numero"]
        assert 100 <= numero <= 199
        assert str(numero).startswith("1") and len(str(numero)) == 3


def test_depois_da_199_volta_para_100(criar, db_session):
    _pedido_direto(db_session, 199, "entregue")
    assert criar((BATATA, 1))["numero"] == 100


def test_pula_senhas_em_uso(criar, db_session):
    _pedido_direto(db_session, 199, "entregue")
    _pedido_direto(db_session, 100)
    _pedido_direto(db_session, 101, "preparando")
    assert criar((BATATA, 1))["numero"] == 102


def test_senha_de_pedido_entregue_e_reaproveitada_na_volta(criar, mudar, db_session):
    primeiro = criar((BATATA, 1))
    for destino in ("preparando", "pronto", "entregue"):
        mudar(primeiro["id"], destino)
    for n in range(101, 200):
        _pedido_direto(db_session, n, "entregue")
    assert criar((BATATA, 1))["numero"] == 100


def test_com_100_senhas_em_uso_devolve_503_e_nao_cria(client, db_session):
    for n in range(100, 200):
        _pedido_direto(db_session, n)
    resposta = client.post(
        "/api/pedidos", json={"itens": [{"produto_id": BATATA, "quantidade": 1}]}
    )
    assert resposta.status_code == 503
    assert "senhas" in resposta.json()["detail"]
    assert db_session.query(Pedido).count() == 100


def test_indice_parcial_impede_dois_ativos_com_a_mesma_senha(db_session):
    _pedido_direto(db_session, 150)
    try:
        _pedido_direto(db_session, 150, "preparando")
    except IntegrityError:
        db_session.rollback()
    else:
        raise AssertionError("dois pedidos ativos com a mesma senha foram aceitos")


def test_indice_parcial_permite_ativo_e_entregue_com_a_mesma_senha(db_session):
    _pedido_direto(db_session, 150, "entregue")
    _pedido_direto(db_session, 150)
    assert db_session.query(Pedido).filter_by(numero=150).count() == 2
