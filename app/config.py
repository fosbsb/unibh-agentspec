import os
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://totem:totem@db:5432/totem"
)
APP_TIMEZONE = os.environ.get("APP_TIMEZONE", "America/Sao_Paulo")


def today() -> date:
    return datetime.now(ZoneInfo(APP_TIMEZONE)).date()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
