"""Discussion endpoints under a lead; missing parents consistently return 404."""

from uuid import UUID

from fastapi import APIRouter

from backend.core.dependencies import Database, Now, Timezone
from backend.discussions import repository, service
from backend.discussions.schemas import (
    DiscussionCreate,
    DiscussionRead,
    DiscussionSaved,
)
from backend.leads.service import require_lead

router = APIRouter(prefix="/leads/{lead_id}/discussions", tags=["discussions"])


@router.get("", response_model=list[DiscussionRead])
def list_discussions(lead_id: UUID, session: Database) -> list[DiscussionRead]:
    require_lead(session, lead_id)
    return [
        DiscussionRead.model_validate(note)
        for note in repository.list_discussions(session, lead_id)
    ]


@router.post("", response_model=DiscussionSaved, status_code=201)
def create_discussion(
    lead_id: UUID,
    data: DiscussionCreate,
    session: Database,
    now: Now,
    timezone: Timezone,
) -> DiscussionSaved:
    return service.add_discussion(session, lead_id, data, now, timezone)
