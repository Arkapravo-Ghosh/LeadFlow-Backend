"""Discussion notes retain the follow-up scheduled at the time of the note."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.clock import utc_now
from backend.db.base import SCHEMA, Base


class Discussion(Base):
    __tablename__ = "discussions"
    __table_args__ = (Index("ix_discussions_lead_created", "lead_id", "created_at"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    lead_id: Mapped[UUID] = mapped_column(ForeignKey(f"{SCHEMA}.leads.id"))
    note: Mapped[str] = mapped_column(Text)
    follow_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
