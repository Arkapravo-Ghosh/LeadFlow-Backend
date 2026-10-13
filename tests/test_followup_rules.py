"""Calendar boundaries, overlapping overdue/today, and stable filtered grouping."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest
from backend.leads.followups import classify_follow_up

NOW = datetime(2026, 10, 13, 5, 0, tzinfo=UTC)


@pytest.mark.parametrize(
    ("due", "expected"),
    [
        ("2026-10-12T18:29:59+00:00", (False, True)),
        ("2026-10-12T18:30:00+00:00", (True, True)),
        ("2026-10-13T10:30:00+00:00", (True, False)),
        ("2026-10-13T18:29:59+00:00", (True, False)),
        ("2026-10-13T18:30:00+00:00", (False, False)),
    ],
)
def test_kolkata_midnight_boundaries(due, expected):
    assert (
        classify_follow_up(datetime.fromisoformat(due), NOW, ZoneInfo("Asia/Kolkata"))
        == expected
    )


def test_no_schedule_and_dst_transition():
    assert classify_follow_up(None, NOW, ZoneInfo("UTC")) == (False, False)
    now = datetime(2026, 11, 1, 7, 30, tzinfo=UTC)
    repeated_hour = datetime(2026, 11, 1, 6, 30, tzinfo=UTC)
    assert classify_follow_up(repeated_hour, now, ZoneInfo("America/New_York")) == (
        True,
        True,
    )


def test_pinning_search_filter_and_no_duplicates(client):
    ids = []
    for name, schedule in [
        ("Pinned future", "2026-10-13T16:00:00+05:30"),
        ("Pinned overdue", "2026-10-13T09:00:00+05:30"),
        ("Pinned yesterday", "2026-10-12T16:00:00+05:30"),
        ("Pinned tomorrow", "2026-10-14T16:00:00+05:30"),
    ]:
        lead = client.post("/api/v1/leads", json={"name": name}).json()
        ids.append(lead["id"])
        client.post(
            f"/api/v1/leads/{lead['id']}/discussions",
            json={"note": name, "follow_up_at": schedule},
        )
    result = client.get(
        "/api/v1/leads", params={"search": "Pinned", "status": "new"}
    ).json()
    leads = result["leads"]
    assert [lead["id"] for lead in leads] == [ids[1], ids[0], ids[2], ids[3]]
    assert len({lead["id"] for lead in leads}) == 4
    assert leads[0]["is_today"] and leads[0]["is_overdue"]
    assert leads[2]["is_overdue"] and not leads[2]["is_today"]
