from collections import defaultdict
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.estados import EstadoPedido, transicao_valida
from app.models import ItemPedido, Pedido, Produto, agora

MAX_TENTATIVAS = 5
MAX_POR_PRODUTO = 20
NUMERO_MIN = 100
NUMERO_MAX = 199
CAMPO_HORARIO = {
    EstadoPedido.PREPARANDO: "preparando_em",
    EstadoPedido.PRONTO: "pronto_em",
    EstadoPedido.ENTREGUE: "entregue_em",
}


def proxima_senha(db) -> int:
    ativos = set(
        db.scalars(
            select(Pedido.numero).where(Pedido.estado != EstadoPedido.ENTREGUE.value)
        )
    )
    ultimo = db.scalar(select(Pedido.numero).order_by(Pedido.id.desc()).limit(1))
    faixa = NUMERO_MAX - NUMERO_MIN + 1
    inicio = 0 if ultimo is None else (ultimo - NUMERO_MIN + 1) % faixa
    for passo in range(faixa):
        candidato = NUMERO_MIN + (inicio + passo) % faixa
        if candidato not in ativos:
            return candidato
    raise HTTPException(503, "Todas as senhas estão em uso. Chame um atendente.")


def criar_pedido(db, itens_in) -> Pedido:
    quantidades: dict[int, int] = defaultdict(int)
    for item in itens_in:
        quantidades[item.produto_id] += item.quantidade
    if any(q > MAX_POR_PRODUTO for q in quantidades.values()):
        raise HTTPException(422, f"Quantidade máxima por produto é {MAX_POR_PRODUTO}")

    produtos = {
        p.id: p
        for p in db.scalars(select(Produto).where(Produto.id.in_(quantidades)))
    }
    faltando = set(quantidades) - set(produtos)
    if faltando:
        raise HTTPException(404, f"Produto inexistente: {sorted(faltando)}")

    total = sum(produtos[i].preco_centavos * q for i, q in quantidades.items())

    for _ in range(MAX_TENTATIVAS):
        numero = proxima_senha(db)
        pedido = Pedido(
            numero=numero, total_centavos=total, estado=EstadoPedido.RECEBIDO.value
        )
        pedido.itens = [
            ItemPedido(
                produto_id=i,
                nome=produtos[i].nome,
                preco_centavos=produtos[i].preco_centavos,
                quantidade=q,
            )
            for i, q in quantidades.items()
        ]
        db.add(pedido)
        try:
            db.commit()
            return pedido
        except IntegrityError:
            db.rollback()
    raise HTTPException(503, "Não foi possível gerar o número do pedido")


def mudar_estado(db, pedido_id: int, destino: EstadoPedido) -> Pedido:
    pedido = db.get(Pedido, pedido_id)
    if pedido is None:
        raise HTTPException(404, "Pedido não encontrado")
    atual = EstadoPedido(pedido.estado)
    if not transicao_valida(atual, destino):
        raise HTTPException(409, f"Transição inválida: {atual.value} → {destino.value}")
    pedido.estado = destino.value
    setattr(pedido, CAMPO_HORARIO[destino], agora())
    db.commit()
    return pedido


def listar_pedidos(db, estados: list[EstadoPedido] | None = None) -> list[Pedido]:
    consulta = select(Pedido).order_by(Pedido.id)
    if estados:
        consulta = consulta.where(Pedido.estado.in_([e.value for e in estados]))
    return list(db.scalars(consulta))


def _utc(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def tempo_medio_segundos(db) -> int | None:
    pedidos = db.scalars(
        select(Pedido)
        .where(Pedido.preparando_em.is_not(None), Pedido.pronto_em.is_not(None))
        .order_by(Pedido.id.desc())
        .limit(20)
    ).all()
    if not pedidos:
        return None
    total = sum(
        (_utc(p.pronto_em) - _utc(p.preparando_em)).total_seconds() for p in pedidos
    )
    return round(total / len(pedidos))
