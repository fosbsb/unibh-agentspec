import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+psycopg://totem:totem@db:5432/totem"
)
