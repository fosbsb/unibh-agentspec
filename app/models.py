from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app import relogio
from app.database import Base


class Produto(Base):
    __tablename__ = "produtos"
    __table_args__ = (CheckConstraint("preco_centavos > 0"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True)
    categoria: Mapped[str] = mapped_column(String(40))
    icone: Mapped[str] = mapped_column(String(8))
    preco_centavos: Mapped[int]


class ContadorDia(Base):
    __tablename__ = "contador_dia"

    data: Mapped[date] = mapped_column(primary_key=True)
    ultimo: Mapped[int]


class Pedido(Base):
    __tablename__ = "pedidos"
    __table_args__ = (
        UniqueConstraint("data_pedido", "numero"),
        CheckConstraint("estado IN ('recebido','preparando','pronto','entregue')"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[int]
    data_pedido: Mapped[date]
    estado: Mapped[str] = mapped_column(String(12), default="recebido")
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=relogio.agora
    )
    iniciado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pronto_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    entregue_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    itens: Mapped[list["ItemPedido"]] = relationship(
        lazy="selectin", order_by="ItemPedido.id"
    )


class ItemPedido(Base):
    __tablename__ = "itens_pedido"
    __table_args__ = (CheckConstraint("quantidade BETWEEN 1 AND 99"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"))
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"))
    quantidade: Mapped[int]
    preco_unitario_centavos: Mapped[int]
    produto: Mapped[Produto] = relationship(lazy="joined")
