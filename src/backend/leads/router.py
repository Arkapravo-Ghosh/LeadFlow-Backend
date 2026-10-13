"""Lead HTTP endpoints; validation and status codes are explicit."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from backend.auth.dependencies import CurrentUser
from backend.core.dependencies import Database, Now, Timezone
from backend.leads import service
from backend.leads.models import LeadStatus
from backend.leads.schemas import LeadCreate, LeadList, LeadSummary, LeadUpdate

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=LeadList)
def list_leads(
    session: Database,
    user: CurrentUser,
    now: Now,
    timezone: Timezone,
    status: LeadStatus | None = None,
    search: Annotated[str, Query(max_length=120)] = "",
) -> LeadList:
    return service.list_leads(session, user.id, now, timezone, status, search)


@router.post("", response_model=LeadSummary, status_code=201)
def create_lead(
    data: LeadCreate, session: Database, user: CurrentUser, now: Now, timezone: Timezone
) -> LeadSummary:
    return service.create_lead(session, data, user.id, now, timezone)


@router.get("/{lead_id}", response_model=LeadSummary)
def get_lead(
    lead_id: UUID, session: Database, user: CurrentUser, now: Now, timezone: Timezone
) -> LeadSummary:
    return service.get_summary(session, lead_id, user.id, now, timezone)


@router.patch("/{lead_id}", response_model=LeadSummary)
def update_lead(
    lead_id: UUID,
    data: LeadUpdate,
    session: Database,
    user: CurrentUser,
    now: Now,
    timezone: Timezone,
) -> LeadSummary:
    return service.update_lead(session, lead_id, data, user.id, now, timezone)
