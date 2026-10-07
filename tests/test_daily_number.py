from concurrent.futures import ThreadPoolExecutor
from datetime import date

from app import services
from app.database import SessionLocal


def test_number_restarts_on_a_new_day(db, ids):
    items = [(ids["Batata frita"], 1)]
    first_day = date(2026, 1, 1)
    second_day = date(2026, 1, 2)

    numbers = [
        services.create_order(db, items, first_day).daily_number,
        services.create_order(db, items, first_day).daily_number,
        services.create_order(db, items, second_day).daily_number,
        services.create_order(db, items, second_day).daily_number,
    ]

    assert numbers == [1, 2, 1, 2]


def test_twenty_parallel_orders_get_unique_continuous_numbers(ids):
    items = [(ids["Batata frita"], 1)]
    day = date(2026, 3, 10)

    def create(_):
        with SessionLocal() as session:
            return services.create_order(session, items, day).daily_number

    with ThreadPoolExecutor(max_workers=20) as pool:
        numbers = list(pool.map(create, range(20)))

    assert sorted(numbers) == list(range(1, 21))


def test_ids_follow_numbers_so_queue_order_matches(ids):
    items = [(ids["Batata frita"], 1)]
    day = date(2026, 3, 11)

    def create(_):
        with SessionLocal() as session:
            order = services.create_order(session, items, day)
            return order.id, order.daily_number

    with ThreadPoolExecutor(max_workers=10) as pool:
        pairs = list(pool.map(create, range(10)))

    by_id = [number for _, number in sorted(pairs)]
    assert by_id == sorted(by_id)
