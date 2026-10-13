"""Lock each normalized username's attempt counter to bound password guessing."""

from datetime import datetime, timedelta
from hashlib import sha256

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from backend.auth.models import LoginAttempt

WINDOW = timedelta(minutes=15)
MAX_FAILURES = 5


def locked_attempt(
    session: Session,
    subject: str,
    now: datetime,
    *,
    maximum: int = MAX_FAILURES,
    message: str = "Too many sign-in attempts. Try again in 15 minutes.",
) -> LoginAttempt:
    """Lock a hashed subject counter; namespaced registration keys remain separate."""
    key = sha256(subject.encode()).hexdigest()
    # Expired counters need no historical audit trail; bound table growth.
    session.execute(
        delete(LoginAttempt).where(LoginAttempt.window_start <= now - WINDOW)
    )
    session.execute(
        insert(LoginAttempt)
        .values(subject_hash=key, failures=0, window_start=now)
        .on_conflict_do_nothing(index_elements=[LoginAttempt.subject_hash])
    )
    attempt = session.scalar(
        select(LoginAttempt).where(LoginAttempt.subject_hash == key).with_for_update()
    )
    assert attempt is not None
    if attempt.failures >= maximum:
        session.commit()
        raise HTTPException(429, message)
    return attempt
