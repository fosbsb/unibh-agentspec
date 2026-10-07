from datetime import date

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app import relogio
from app.models import ContadorDia, ItemPedido, Pedido, Produto

PROXIMO = {"recebido": "preparando", "preparando": "pronto", "pronto": "entregue"}
CARIMBO = {"preparando": "iniciado_em", "pronto": "pronto_em", "entregue": "entregue_em"}


class ErroDeDominio(Exception):
    pass


class ProdutoInexistente(ErroDeDominio):
    def __init__(self, produto_id: int):
        super().__init__(f"Produto inexistente: {produto_id}")
        self.produto_id = produto_id


class PedidoNaoEncontrado(ErroDeDominio):
    pass


class ConflitoEstado(ErroDeDominio):
    pass


def listar_cardapio(session: Session) -> list[tuple[str, list[Produto]]]:
    produtos = session.scalars(select(Produto).order_by(Produto.id)).all()
    categorias: dict[str, list[Produto]] = {}
    for produto in produtos:
        categorias.setdefault(produto.categoria, []).append(produto)
    return list(categorias.items())


def proximo_numero(session: Session, dia: date) -> int:
    stmt = (
        pg_insert(ContadorDia)
        .values(data=dia, ultimo=1)
        .on_conflict_do_update(
            index_elements=[ContadorDia.data],
            set_={"ultimo": ContadorDia.ultimo + 1},
        )
        .returning(ContadorDia.ultimo)
    )
    return session.execute(stmt).scalar_one()


def criar_pedido(session: Session, itens: list) -> Pedido:
    ids = {i.produto_id for i in itens}
    produtos = {
        p.id: p for p in session.scalars(select(Produto).where(Produto.id.in_(ids)))
    }
    faltando = ids - produtos.keys()
    if faltando:
        raise ProdutoInexistente(min(faltando))
    hoje = relogio.hoje()
    pedido = Pedido(
        data_pedido=hoje,
        numero=proximo_numero(session, hoje),
        itens=[
            ItemPedido(
                produto_id=i.produto_id,
                quantidade=i.quantidade,
                preco_unitario_centavos=produtos[i.produto_id].preco_centavos,
            )
            for i in itens
        ],
    )
    session.add(pedido)
    session.commit()
    return pedido


def avancar(session: Session, pedido_id: int, estado_atual: str) -> Pedido:
    pedido = session.scalars(
        select(Pedido).where(Pedido.id == pedido_id).with_for_update(skip_locked=True)
    ).one_or_none()
    if pedido is None:
        existe = session.scalar(select(Pedido.id).where(Pedido.id == pedido_id))
        session.rollback()
        raise ConflitoEstado() if existe else PedidoNaoEncontrado()
    if pedido.estado != estado_atual or pedido.estado not in PROXIMO:
        session.rollback()
        raise ConflitoEstado()
    novo = PROXIMO[pedido.estado]
    pedido.estado = novo
    setattr(pedido, CARIMBO[novo], relogio.agora())
    session.commit()
    return pedido


def listar_fila(session: Session) -> list[Pedido]:
    stmt = (
        select(Pedido)
        .where(Pedido.estado != "entregue")
        .order_by(Pedido.data_pedido, Pedido.numero)
    )
    return list(session.scalars(stmt))


def tempo_medio_preparo(session: Session) -> int | None:
    media = session.scalar(
        select(func.avg(func.extract("epoch", Pedido.pronto_em - Pedido.iniciado_em)))
        .where(Pedido.data_pedido == relogio.hoje(), Pedido.pronto_em.is_not(None))
    )
    return None if media is None else round(media)
