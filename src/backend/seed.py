"""Repeatable synthetic data. Existing seed leads and user data are untouched."""

from datetime import UTC, datetime, timedelta
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from backend.core.clock import utc_now
from backend.db.session import get_engine
from backend.discussions.models import Discussion
from backend.leads.models import Lead, LeadStatus

SAMPLES = [
    (
        "Sarah Connor",
        "Acme Corp",
        LeadStatus.PROPOSAL_SENT,
        0,
        "Shared the proposal. Review scheduled.",
    ),
    (
        "Hank Scorpio",
        "Globex",
        LeadStatus.NEW,
        None,
        "Inbound enquiry about the advisory platform.",
    ),
    (
        "Bill Lumbergh",
        "Initech",
        LeadStatus.CONTACTED,
        -1,
        "Left a voicemail. Follow up on availability.",
    ),
    (
        "Diana Prince",
        "Themyscira Group",
        LeadStatus.QUALIFIED,
        1,
        "Confirmed requirements and decision makers.",
    ),
    (
        "Bruce Wayne",
        "Wayne Enterprises",
        LeadStatus.WON,
        None,
        "Agreement signed. Onboarding next week.",
    ),
    (
        "Tony Stark",
        "Stark Industries",
        LeadStatus.LOST,
        None,
        "Timing does not align with this quarter.",
    ),
]


def seed(session: Session, now: datetime | None = None) -> int:
    """Insert only absent deterministic IDs, in one transaction."""
    now = now or utc_now()
    local = now.astimezone(ZoneInfo("Asia/Kolkata"))
    inserted = 0
    for index, (name, company, status, days, note) in enumerate(SAMPLES):
        lead_id = uuid5(NAMESPACE_URL, f"leadflow/demo/{name}")
        if session.get(Lead, lead_id):
            continue
        due = (
            (
                local.replace(hour=16, minute=0, second=0, microsecond=0)
                + timedelta(days=days)
            ).astimezone(UTC)
            if days is not None
            else None
        )
        created = now - timedelta(days=7 + index)
        session.add(
            Lead(
                id=lead_id,
                name=name,
                company=company,
                phone=f"+91 90000 0000{index}",
                status=status,
                follow_up_at=due,
                created_at=created,
                updated_at=now,
            )
        )
        session.flush()
        session.add_all(
            [
                Discussion(
                    id=uuid5(lead_id, "first"),
                    lead_id=lead_id,
                    note="Initial introduction and discovery call.",
                    created_at=created + timedelta(hours=1),
                ),
                Discussion(
                    id=uuid5(lead_id, "latest"),
                    lead_id=lead_id,
                    note=note,
                    follow_up_at=due,
                    created_at=now - timedelta(hours=index + 2),
                ),
            ]
        )
        inserted += 1
    session.commit()
    return inserted


def main() -> None:
    with Session(get_engine()) as session:
        print(f"Inserted {seed(session)} synthetic leads; existing data preserved.")


if __name__ == "__main__":
    main()
