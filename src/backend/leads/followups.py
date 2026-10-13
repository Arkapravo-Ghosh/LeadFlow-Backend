"""Calendar-date pinning and instant-based overdue classification."""

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import HTTPException

from backend.leads.schemas import LeadSummary


def parse_timezone(value: str) -> ZoneInfo:
    try:
        return ZoneInfo(value)
    except ZoneInfoNotFoundError, ValueError:
        raise HTTPException(
            status_code=422, detail="Choose a valid IANA timezone."
        ) from None


def classify_follow_up(
    scheduled: datetime | None, now: datetime, timezone: ZoneInfo
) -> tuple[bool, bool]:
    if scheduled is None:
        return False, False
    return scheduled.astimezone(timezone).date() == now.astimezone(
        timezone
    ).date(), scheduled < now


def sort_leads(leads: list[LeadSummary]) -> list[LeadSummary]:
    def key(lead: LeadSummary) -> tuple[int, float, str]:
        if lead.is_today:
            return 0, lead.follow_up_at.timestamp(), str(lead.id)
        if lead.is_overdue:
            return 1, lead.follow_up_at.timestamp(), str(lead.id)
        activity = lead.last_discussion_at or lead.created_at
        return 2, -activity.timestamp(), str(lead.id)

    return sorted(leads, key=key)
