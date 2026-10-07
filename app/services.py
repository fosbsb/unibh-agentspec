from datetime import date

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.config import utcnow
from app.domain import (
    ACTIVE,
    CANCELABLE,
    NEXT,
    InvalidTransition,
    OrderLocked,
    OrderNotFound,
    OrderStatus,
    ProductNotFound,
    StaleState,
)
from app.models import DailyCounter, Order, OrderItem, Product


def list_products(db: Session) -> list[Product]:
    return list(db.scalars(select(Product).order_by(Product.position)))


def next_daily_number(db: Session, day: date) -> int:
    stmt = (
        pg_insert(DailyCounter)
        .values(day=day, last_number=1)
        .on_conflict_do_update(
            index_elements=[DailyCounter.day],
            set_={"last_number": DailyCounter.last_number + 1},
        )
        .returning(DailyCounter.last_number)
    )
    return db.execute(stmt).scalar_one()


def create_order(db: Session, items: list[tuple[int, int]], day: date) -> Order:
    wanted: dict[int, int] = {}
    for product_id, quantity in items:
        wanted[product_id] = wanted.get(product_id, 0) + quantity

    products = {
        p.id: p for p in db.scalars(select(Product).where(Product.id.in_(wanted)))
    }
    missing = set(wanted) - set(products)
    if missing:
        raise ProductNotFound(min(missing))

    number = next_daily_number(db, day)
    now = utcnow()
    order = Order(
        order_date=day,
        daily_number=number,
        status=OrderStatus.RECEBIDO,
        total_cents=sum(products[i].price_cents * q for i, q in wanted.items()),
        created_at=now,
        updated_at=now,
    )
    order.items = [
        OrderItem(
            product_id=product_id,
            quantity=quantity,
            unit_price_cents=products[product_id].price_cents,
            product=products[product_id],
        )
        for product_id, quantity in wanted.items()
    ]
    db.add(order)
    db.commit()
    return order


def list_orders(db: Session, states: list[OrderStatus] | None) -> list[Order]:
    wanted = states or list(ACTIVE)
    stmt = select(Order).where(Order.status.in_(wanted)).order_by(Order.id)
    return list(db.scalars(stmt))


def _lock_order(db: Session, order_id: int) -> Order:
    order = db.execute(
        select(Order).where(Order.id == order_id).with_for_update(skip_locked=True)
    ).scalar_one_or_none()
    if order is None:
        if db.scalar(select(Order.id).where(Order.id == order_id)) is None:
            raise OrderNotFound(order_id)
        raise OrderLocked(order_id)
    return order


def advance_order(db: Session, order_id: int, from_state: OrderStatus) -> Order:
    order = _lock_order(db, order_id)
    if order.status != from_state:
        raise StaleState(order_id)
    target = NEXT.get(order.status)
    if target is None:
        raise InvalidTransition(order_id)
    now = utcnow()
    order.status = target
    order.updated_at = now
    if target is OrderStatus.PRONTO:
        order.ready_at = now
    db.commit()
    return order


def cancel_order(db: Session, order_id: int) -> Order:
    order = _lock_order(db, order_id)
    if order.status not in CANCELABLE:
        raise InvalidTransition(order_id)
    order.status = OrderStatus.CANCELADO
    order.updated_at = utcnow()
    db.commit()
    return order


def panel(db: Session, day: date) -> dict:
    preparing = list(
        db.scalars(
            select(Order)
            .where(Order.status == OrderStatus.PREPARANDO)
            .order_by(Order.id)
        )
    )
    ready = list(
        db.scalars(
            select(Order)
            .where(Order.status == OrderStatus.PRONTO)
            .order_by(Order.ready_at.desc(), Order.id.desc())
        )
    )
    average = db.scalar(
        select(
            func.avg(func.extract("epoch", Order.ready_at - Order.created_at))
        ).where(Order.order_date == day, Order.ready_at.is_not(None))
    )
    return {
        "preparing": preparing,
        "ready": ready,
        "avg_prep_seconds": None if average is None else round(float(average)),
    }
