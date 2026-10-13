"""Lead persistence and the six assessment statuses."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.core.clock import utc_now
from backend.db.base import Base


class LeadStatus(StrEnum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL_SENT = "proposal_sent"
    WON = "won"
    LOST = "lost"


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("leadflow.users.id"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    company: Mapped[str | None] = mapped_column(String(120))
    phone: Mapped[str | None] = mapped_column(String(40))
    status: Mapped[LeadStatus] = mapped_column(
        Enum(
            LeadStatus,
            values_callable=lambda enum: [item.value for item in enum],
            native_enum=False,
            create_constraint=True,
            name="lead_status",
        ),
        default=LeadStatus.NEW,
        index=True,
    )
    follow_up_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now
    )
