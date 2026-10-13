"""Demo seeding is repeatable and preserves user-edited records."""

from backend.discussions.models import Discussion
from backend.leads.models import Lead
from backend.seed import seed
from sqlalchemy import func, select


def test_seed_has_six_leads_history_and_no_duplicate_or_overwrite(session, user):
    assert seed(session, user.id) == 6
    lead = session.scalar(select(Lead).where(Lead.name == "Sarah Connor"))
    lead.name = "Sarah edited"
    session.commit()
    assert seed(session, user.id) == 0
    session.expire_all()
    assert session.scalar(select(func.count()).select_from(Lead)) == 6
    assert session.scalar(select(func.count()).select_from(Discussion)) == 12
    assert session.get(Lead, lead.id).name == "Sarah edited"
