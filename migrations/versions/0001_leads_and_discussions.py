"""Create the two assessment tables inside the LeadFlow schema."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None
SCHEMA = "leadflow"


def upgrade() -> None:
    op.create_table(
        "leads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("company", sa.String(120)),
        sa.Column("phone", sa.String(40)),
        sa.Column("status", sa.String(13), nullable=False),
        sa.Column("follow_up_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('new','contacted','qualified','proposal_sent','won','lost')",
            name="ck_leads_lead_status",
        ),
        schema=SCHEMA,
    )
    op.create_index("ix_leads_status", "leads", ["status"], schema=SCHEMA)
    op.create_index("ix_leads_follow_up_at", "leads", ["follow_up_at"], schema=SCHEMA)
    op.create_table(
        "discussions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "lead_id",
            UUID(as_uuid=True),
            sa.ForeignKey(f"{SCHEMA}.leads.id"),
            nullable=False,
        ),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("follow_up_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema=SCHEMA,
    )
    op.create_index(
        "ix_discussions_lead_created",
        "discussions",
        ["lead_id", "created_at"],
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_table("discussions", schema=SCHEMA)
    op.drop_table("leads", schema=SCHEMA)
