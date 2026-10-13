"""Lead business operations; services own commit boundaries."""

from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.discussions.models import Discussion
from backend.leads import repository
from backend.leads.followups import classify_follow_up, sort_leads
from backend.leads.models import Lead, LeadStatus
from backend.leads.schemas import LeadCreate, LeadList, LeadSummary, LeadUpdate


def require_lead(session: Session, lead_id: UUID, *, lock: bool = False) -> Lead:
    lead = repository.find_lead(session, lead_id, lock=lock)
    if lead is None:
        raise HTTPException(status_code=404, detail="This lead could not be found.")
    return lead


def summarize(
    lead: Lead, discussion: Discussion | None, now: datetime, timezone: ZoneInfo
) -> LeadSummary:
    today, overdue = classify_follow_up(lead.follow_up_at, now, timezone)
    return LeadSummary(
        id=lead.id,
        name=lead.name,
        company=lead.company,
        phone=lead.phone,
        status=lead.status,
        follow_up_at=lead.follow_up_at,
        created_at=lead.created_at,
        updated_at=lead.updated_at,
        last_note=discussion.note if discussion else None,
        last_discussion_at=discussion.created_at if discussion else None,
        is_today=today,
        is_overdue=overdue,
    )


def get_summary(
    session: Session, lead_id: UUID, now: datetime, timezone: ZoneInfo
) -> LeadSummary:
    lead = require_lead(session, lead_id)
    return summarize(
        lead, repository.latest_discussion(session, lead_id), now, timezone
    )


def list_leads(
    session: Session,
    now: datetime,
    timezone: ZoneInfo,
    status: LeadStatus | None = None,
    search: str = "",
) -> LeadList:
    leads = [
        summarize(lead, note, now, timezone)
        for lead, note in repository.lead_rows(session, status, search)
    ]
    return LeadList(
        leads=sort_leads(leads),
        total=len(leads),
        server_time=now,
        timezone=timezone.key,
    )


def create_lead(
    session: Session, data: LeadCreate, now: datetime, timezone: ZoneInfo
) -> LeadSummary:
    lead = Lead(
        name=data.name,
        company=data.company or None,
        phone=data.phone or None,
        status=LeadStatus.NEW,
        created_at=now,
        updated_at=now,
    )
    session.add(lead)
    session.commit()
    return summarize(lead, None, now, timezone)


def update_lead(
    session: Session, lead_id: UUID, data: LeadUpdate, now: datetime, timezone: ZoneInfo
) -> LeadSummary:
    lead = require_lead(session, lead_id, lock=True)
    lead.status = data.status
    lead.updated_at = now
    session.commit()
    return summarize(
        lead, repository.latest_discussion(session, lead_id), now, timezone
    )
