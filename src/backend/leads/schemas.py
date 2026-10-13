"""Explicit contracts, independent of ORM objects."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from backend.leads.models import LeadStatus

Name = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)
]


class LeadCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    name: Name
    company: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)


class LeadUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: LeadStatus


class LeadSummary(BaseModel):
    id: UUID
    name: str
    company: str | None
    phone: str | None
    status: LeadStatus
    follow_up_at: datetime | None
    created_at: datetime
    updated_at: datetime
    last_note: str | None
    last_discussion_at: datetime | None
    is_today: bool
    is_overdue: bool


class LeadList(BaseModel):
    leads: list[LeadSummary]
    total: int
    server_time: datetime
    timezone: str
