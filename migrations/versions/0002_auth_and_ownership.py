"""Add accounts, hashed sessions and explicit lead ownership; preserve legacy rows."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None
SCHEMA = "leadflow"


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_table(
        "auth_sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("leadflow.users.id"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    for column in ("user_id", "expires_at"):
        op.create_index(
            f"ix_auth_sessions_{column}", "auth_sessions", [column], schema=SCHEMA
        )
    op.create_table(
        "login_attempts",
        sa.Column("subject_hash", sa.String(64), primary_key=True),
        sa.Column("failures", sa.Integer(), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_login_attempts_window_start",
        "login_attempts",
        ["window_start"],
        schema=SCHEMA,
    )
    # A separate, private administrator command claims old data; migrations create no credentials.
    op.add_column(
        "leads", sa.Column("owner_id", UUID(as_uuid=True), nullable=True), schema=SCHEMA
    )
    op.create_foreign_key(
        "fk_leads_owner_id_users",
        "leads",
        "users",
        ["owner_id"],
        ["id"],
        source_schema=SCHEMA,
        referent_schema=SCHEMA,
    )
    op.create_index("ix_leads_owner_id", "leads", ["owner_id"], schema=SCHEMA)


def downgrade() -> None:
    op.drop_index("ix_leads_owner_id", table_name="leads", schema=SCHEMA)
    op.drop_constraint(
        "fk_leads_owner_id_users", "leads", schema=SCHEMA, type_="foreignkey"
    )
    op.drop_column("leads", "owner_id", schema=SCHEMA)
    for table in ("login_attempts", "auth_sessions", "users"):
        op.drop_table(table, schema=SCHEMA)
