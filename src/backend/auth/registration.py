"""Self-service registration creates an empty account and session atomically."""

from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.auth.limits import locked_attempt
from backend.auth.repository import UsernameTakenError, insert_user
from backend.auth.schemas import LoginResult, SignupRequest
from backend.auth.service import issue_session
from backend.core.config import get_settings


def sign_up(
    session: Session, data: SignupRequest, now: datetime, source: str
) -> LoginResult:
    """No seed/claim path is available to registration, including on retries."""
    attempt = locked_attempt(
        session,
        f"signup:{source}",
        now,
        maximum=get_settings().signup_rate_limit,
        message="Too many registration attempts. Try again in 15 minutes.",
    )
    attempt.failures += 1
    # Failed duplicates and rolled-back registrations also consume the budget.
    session.commit()
    try:
        user = insert_user(session, data.username, data.password.get_secret_value())
        result = issue_session(session, user, now)
        session.commit()
        return result
    except UsernameTakenError:
        session.rollback()
        raise HTTPException(409, "That username is already in use.") from None
    except IntegrityError as error:
        session.rollback()
        # The unique index handles concurrent requests for the same username.
        if (
            getattr(getattr(error.orig, "diag", None), "constraint_name", None)
            == "uq_users_username"
        ):
            raise HTTPException(409, "That username is already in use.") from None
        raise
