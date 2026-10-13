"""Migrations read the same private database configuration as the API."""

from alembic import context
from sqlalchemy import text

from backend.db.base import SCHEMA, Base
from backend.db.session import get_engine
from backend.discussions.models import Discussion  # noqa: F401
from backend.leads.models import Lead  # noqa: F401

with get_engine().connect() as connection:
    connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}"'))
    connection.commit()
    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        include_schemas=True,
        version_table_schema=SCHEMA,
    )
    with context.begin_transaction():
        context.run_migrations()
