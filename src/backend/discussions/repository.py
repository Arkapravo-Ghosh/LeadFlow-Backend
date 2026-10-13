"""Ordered discussion reads; commits belong to the service."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.discussions.models import Discussion


def list_discussions(session: Session, lead_id: UUID) -> list[Discussion]:
    return list(
        session.scalars(
            select(Discussion)
            .where(Discussion.lead_id == lead_id)
            .order_by(Discussion.created_at.desc(), Discussion.id.desc())
        )
    )
