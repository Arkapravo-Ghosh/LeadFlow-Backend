"""Credential verification, expiring sessions and immediate logout revocation."""

import secrets
from datetime import datetime, timedelta
from hashlib import sha256

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.auth.limits import locked_attempt
from backend.auth.models import AuthSession, User
from backend.auth.passwords import verify_and_upgrade
from backend.auth.schemas import LoginRequest, LoginResult, UserRead
from backend.core.config import get_settings


def token_digest(token: str) -> str:
    return sha256(token.encode()).hexdigest()


def sign_in(session: Session, data: LoginRequest, now: datetime) -> LoginResult:
    attempt = locked_attempt(session, data.username, now)
    user = session.scalar(select(User).where(User.username == data.username))
    password = data.password.get_secret_value()
    valid, updated_hash = verify_and_upgrade(
        password, user.password_hash if user else None
    )
    if not valid or user is None or not user.is_active:
        attempt.failures += 1
        session.commit()  # Failed attempts must survive the request's rollback.
        raise HTTPException(401, "Invalid username or password.")
    attempt.failures = 0
    if updated_hash:
        user.password_hash = updated_hash
    session.execute(delete(AuthSession).where(AuthSession.expires_at <= now))
    token = secrets.token_urlsafe(32)
    expires = now + timedelta(hours=get_settings().auth_session_hours)
    session.add(
        AuthSession(
            token_hash=token_digest(token),
            user_id=user.id,
            created_at=now,
            expires_at=expires,
        )
    )
    session.commit()
    return LoginResult(
        token=token, expires_at=expires, user=UserRead.model_validate(user)
    )


def authenticated_user(session: Session, token: str, now: datetime) -> User:
    user = session.scalar(
        select(User)
        .join(AuthSession, AuthSession.user_id == User.id)
        .where(
            AuthSession.token_hash == token_digest(token),
            AuthSession.expires_at > now,
            User.is_active.is_(True),
        )
    )
    if user is None:
        raise HTTPException(401, "Please sign in to continue.")
    return user


def sign_out(session: Session, token: str) -> None:
    session.execute(
        delete(AuthSession).where(AuthSession.token_hash == token_digest(token))
    )
    session.commit()
