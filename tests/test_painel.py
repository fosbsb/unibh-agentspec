from datetime import datetime, timedelta, timezone

from app import servicos
from app.models import Pedido

BATATA = 4


def test_painel_vazio(client):
    assert client.get("/api/painel").json() == {
        "preparando": [], "pronto": [], "tempo_medio_segundos": None
    }


def test_painel_separa_preparando_e_pronto(criar, mudar, client):
    recebido = criar((BATATA, 1))
    preparando = criar((BATATA, 1))
    pronto = criar((BATATA, 1))
    mudar(preparando["id"], "preparando")
    mudar(pronto["id"], "preparando")
    mudar(pronto["id"], "pronto")
    dados = client.get("/api/painel").json()
    assert [p["numero"] for p in dados["preparando"]] == [preparando["numero"]]
    assert [p["numero"] for p in dados["pronto"]] == [pronto["numero"]]
    todos = dados["preparando"] + dados["pronto"]
    assert recebido["numero"] not in [p["numero"] for p in todos]


def test_entregue_some_do_painel(criar, mudar, client):
    pedido = criar((BATATA, 1))
    for destino in ("preparando", "pronto", "entregue"):
        mudar(pedido["id"], destino)
    dados = client.get("/api/painel").json()
    assert dados["preparando"] == [] and dados["pronto"] == []


def test_tempo_medio_sem_dados(db_session):
    assert servicos.tempo_medio_segundos(db_session) is None


def test_tempo_medio_com_dados(criar, mudar, db_session, client):
    inicio = datetime(2026, 10, 8, 12, 0, tzinfo=timezone.utc)
    for minutos in (2, 4):
        pedido = criar((BATATA, 1))
        mudar(pedido["id"], "preparando")
        mudar(pedido["id"], "pronto")
        registro = db_session.get(Pedido, pedido["id"])
        registro.preparando_em = inicio
        registro.pronto_em = inicio + timedelta(minutes=minutos)
    db_session.commit()
    assert servicos.tempo_medio_segundos(db_session) == 180
    assert client.get("/api/painel").json()["tempo_medio_segundos"] == 180


def test_tempo_medio_aceita_datas_sem_fuso(criar, mudar, db_session):
    pedido = criar((BATATA, 1))
    mudar(pedido["id"], "preparando")
    mudar(pedido["id"], "pronto")
    registro = db_session.get(Pedido, pedido["id"])
    registro.preparando_em = datetime(2026, 10, 8, 12, 0)
    registro.pronto_em = datetime(2026, 10, 8, 12, 1)
    db_session.commit()
    assert servicos.tempo_medio_segundos(db_session) == 60


def test_paginas_sao_servidas(client):
    for rota in ("/totem", "/cozinha", "/painel"):
        resposta = client.get(rota)
        assert resposta.status_code == 200
        assert "text/html" in resposta.headers["content-type"]
