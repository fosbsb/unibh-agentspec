from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def agora() -> datetime:
    return datetime.now(timezone.utc)


class Produto(Base):
    __tablename__ = "produtos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80))
    categoria: Mapped[str] = mapped_column(String(30))
    icone: Mapped[str] = mapped_column(String(8))
    preco_centavos: Mapped[int] = mapped_column(Integer)


class Pedido(Base):
    __tablename__ = "pedidos"
    __table_args__ = (
        Index(
            "ix_pedidos_numero_ativo",
            "numero",
            unique=True,
            postgresql_where=text("estado != 'entregue'"),
            sqlite_where=text("estado != 'entregue'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[int] = mapped_column(Integer)
    estado: Mapped[str] = mapped_column(String(15), default="recebido", index=True)
    total_centavos: Mapped[int] = mapped_column(Integer)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=agora)
    preparando_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pronto_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    entregue_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    itens: Mapped[list["ItemPedido"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan", lazy="selectin"
    )


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id: Mapped[int] = mapped_column(primary_key=True)
    pedido_id: Mapped[int] = mapped_column(ForeignKey("pedidos.id"))
    produto_id: Mapped[int] = mapped_column(ForeignKey("produtos.id"))
    nome: Mapped[str] = mapped_column(String(80))
    preco_centavos: Mapped[int] = mapped_column(Integer)
    quantidade: Mapped[int] = mapped_column(Integer)
    pedido: Mapped[Pedido] = relationship(back_populates="itens")
