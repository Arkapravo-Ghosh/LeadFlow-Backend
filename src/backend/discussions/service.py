"""Save the note and lead schedule as a single PostgreSQL transaction."""

from datetime import datetime
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from backend.discussions.models import Discussion
from backend.discussions.schemas import (
    DiscussionCreate,
    DiscussionRead,
    DiscussionSaved,
)
from backend.leads import repository
from backend.leads.service import require_lead, summarize


def add_discussion(
    session: Session,
    lead_id: UUID,
    data: DiscussionCreate,
    owner_id: UUID,
    now: datetime,
    timezone: ZoneInfo,
) -> DiscussionSaved:
    lead = require_lead(session, lead_id, owner_id, lock=True)
    discussion = Discussion(
        lead_id=lead.id,
        note=data.note,
        follow_up_at=data.follow_up_at,
        created_at=now,
    )
    session.add(discussion)
    if data.follow_up_at is not None:
        lead.follow_up_at = data.follow_up_at
    lead.updated_at = now
    session.commit()
    latest = repository.latest_discussion(session, lead_id)
    return DiscussionSaved(
        discussion=DiscussionRead.model_validate(discussion),
        lead=summarize(lead, latest, now, timezone),
    )
