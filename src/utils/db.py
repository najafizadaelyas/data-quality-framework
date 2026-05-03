"""Database connection helpers."""
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.utils.config import config


def get_engine(db_name: str | None = None):
    name = db_name or config.db_name
    url = (
        f"postgresql+psycopg2://{config.db_user}:{config.db_password}"
        f"@{config.db_host}:{config.db_port}/{name}"
    )
    return create_engine(url, pool_pre_ping=True)


@contextmanager
def get_connection(db_name: str | None = None):
    engine = get_engine(db_name)
    with engine.connect() as conn:
        yield conn


def table_exists(table: str, schema: str = "public", db_name: str | None = None) -> bool:
    sql = text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = :schema AND table_name = :table)"
    )
    with get_connection(db_name) as conn:
        result = conn.execute(sql, {"schema": schema, "table": table})
        return result.scalar()


def row_count(table: str, schema: str = "public", db_name: str | None = None) -> int:
    with get_connection(db_name) as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {schema}.{table}"))
        return result.scalar()
