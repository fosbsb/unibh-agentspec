from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.domain import OrderStatus


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(index=True)
    name: Mapped[str] = mapped_column(unique=True)
    icon: Mapped[str]
    price_cents: Mapped[int]
    position: Mapped[int]


class DailyCounter(Base):
    __tablename__ = "daily_counters"

    day: Mapped[date] = mapped_column(primary_key=True)
    last_number: Mapped[int]


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("order_date", "daily_number"),
        Index("ix_orders_status_id", "status", "id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[date]
    daily_number: Mapped[int]
    status: Mapped[OrderStatus] = mapped_column(
        Enum(
            OrderStatus,
            native_enum=False,
            create_constraint=True,
            length=20,
            values_callable=lambda e: [m.value for m in e],
        )
    )
    total_cents: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    items: Mapped[list["OrderItem"]] = relationship(
        lazy="selectin", order_by="OrderItem.id"
    )

    @property
    def number(self) -> str:
        return f"{self.daily_number:03d}"


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (CheckConstraint("quantity > 0"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int]
    unit_price_cents: Mapped[int]

    product: Mapped[Product] = relationship(lazy="joined")

    @property
    def name(self) -> str:
        return self.product.name

    @property
    def icon(self) -> str:
        return self.product.icon
