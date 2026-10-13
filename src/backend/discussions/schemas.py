"""Notes require content; follow-up inputs require an explicit timezone offset."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    StringConstraints,
    field_validator,
)

from backend.leads.schemas import LeadSummary


class DiscussionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    note: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)
    ]
    follow_up_at: AwareDatetime | None = None

    @field_validator("follow_up_at")
    @classmethod
    def normalize_date(cls, value: datetime | None) -> datetime | None:
        return value.astimezone(UTC) if value else None


class DiscussionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    lead_id: UUID
    note: str
    follow_up_at: datetime | None
    created_at: datetime


class DiscussionSaved(BaseModel):
    discussion: DiscussionRead
    lead: LeadSummary
