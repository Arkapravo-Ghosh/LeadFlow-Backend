"""Shared request dependencies keep routers focused on HTTP."""

from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import Depends, Query
from sqlalchemy.orm import Session

from backend.core.clock import utc_now
from backend.db.session import get_session
from backend.leads.followups import parse_timezone


def display_timezone(
    timezone: Annotated[str, Query(max_length=100)] = "Asia/Kolkata",
) -> ZoneInfo:
    return parse_timezone(timezone)


Database = Annotated[Session, Depends(get_session)]
Now = Annotated[datetime, Depends(utc_now)]
Timezone = Annotated[ZoneInfo, Depends(display_timezone)]
