"""PostgreSQL SQLAlchemy engine and request-scoped unit of work."""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import get_settings


def make_engine(database_url: str) -> Engine:
    """Select psycopg while retaining the supplied SSL and channel binding options."""
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args={"connect_timeout": 10, "options": "-c timezone=UTC"},
    )


@lru_cache
def get_engine() -> Engine:
    return make_engine(get_settings().database_url.get_secret_value())


def get_session() -> Generator[Session]:
    factory = sessionmaker(get_engine(), expire_on_commit=False)
    with factory() as session:
        try:
            yield session
        except Exception:
            session.rollback()
            raise
