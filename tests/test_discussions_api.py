"""Verify ordered history, schedule preservation, and transaction rollback."""

from datetime import UTC, datetime
from uuid import UUID

from backend.core.clock import utc_now
from backend.discussions.models import Discussion
from backend.leads.models import Lead
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

BASE = "/api/v1/leads"


def test_discussion_summary_order_and_followup_preservation(client, app, session):
    lead = client.post(BASE, json={"name": "Timeline lead"}).json()
    path = f"{BASE}/{lead['id']}/discussions"
    first = client.post(
        path,
        json={
            "note": " First discussion ",
            "follow_up_at": "2026-10-13T16:00:00+05:30",
        },
    )
    assert first.status_code == 201
    assert first.json()["lead"]["follow_up_at"] == "2026-10-13T10:30:00Z"
    assert first.json()["lead"]["is_today"] is True
    app.dependency_overrides[utc_now] = lambda: datetime(2026, 10, 13, 6, 0, tzinfo=UTC)
    second = client.post(path, json={"note": "Second discussion"})
    assert second.json()["lead"]["follow_up_at"] == first.json()["lead"]["follow_up_at"]
    session.expire_all()
    history = client.get(path).json()
    assert [note["note"] for note in history] == [
        "Second discussion",
        "First discussion",
    ]
    assert history[0]["follow_up_at"] is None
    listed = client.get(BASE).json()["leads"][0]
    assert listed["last_note"] == "Second discussion"


def test_invalid_notes_and_naive_timestamps(client):
    lead = client.post(BASE, json={"name": "Validation lead"}).json()
    path = f"{BASE}/{lead['id']}/discussions"
    for payload in [
        {"note": "  "},
        {"note": "x" * 5001},
        {"note": "Valid", "follow_up_at": "2026-10-13T16:00:00"},
    ]:
        assert client.post(path, json=payload).status_code == 422
    assert client.get(path).json() == []


def test_note_and_schedule_rollback_together(client, session, monkeypatch):
    lead = client.post(BASE, json={"name": "Rollback lead"}).json()

    def fail_commit():
        session.flush()
        raise SQLAlchemyError("simulated failure with private information")

    monkeypatch.setattr(session, "commit", fail_commit)
    result = client.post(
        f"{BASE}/{lead['id']}/discussions",
        json={
            "note": "Must not survive",
            "follow_up_at": "2026-10-14T16:00:00+05:30",
        },
    )
    assert result.status_code == 500
    assert "private information" not in result.text
    assert session.get(Lead, UUID(lead["id"])).follow_up_at is None
    assert (
        session.scalars(
            select(Discussion).where(Discussion.lead_id == UUID(lead["id"]))
        ).all()
        == []
    )
