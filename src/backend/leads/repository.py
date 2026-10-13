"""Database queries, including one window query for every latest discussion."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from backend.discussions.models import Discussion
from backend.leads.models import Lead, LeadStatus


def find_lead(
    session: Session, lead_id: UUID, owner_id: UUID, *, lock: bool = False
) -> Lead | None:
    query = select(Lead).where(Lead.id == lead_id, Lead.owner_id == owner_id)
    return session.scalar(query.with_for_update() if lock else query)


def lead_rows(
    session: Session, owner_id: UUID, status: LeadStatus | None = None, search: str = ""
) -> list[tuple[Lead, Discussion | None]]:
    """Avoid an N+1 query when presenting latest-note summaries."""
    ranked = select(
        Discussion,
        func.row_number()
        .over(
            partition_by=Discussion.lead_id,
            order_by=(Discussion.created_at.desc(), Discussion.id.desc()),
        )
        .label("position"),
    ).subquery()
    latest = aliased(Discussion, ranked)
    query = select(Lead, latest).outerjoin(
        latest, (latest.lead_id == Lead.id) & (ranked.c.position == 1)
    )
    query = query.where(Lead.owner_id == owner_id)
    if status is not None:
        query = query.where(Lead.status == status)
    if search.strip():
        escaped = (
            search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        query = query.where(Lead.name.ilike(f"%{escaped}%", escape="\\"))
    return list(session.execute(query).all())


def latest_discussion(session: Session, lead_id: UUID) -> Discussion | None:
    return session.scalar(
        select(Discussion)
        .where(Discussion.lead_id == lead_id)
        .order_by(Discussion.created_at.desc(), Discussion.id.desc())
        .limit(1)
    )
