"""Shared account insertion; callers own commit and legacy ownership decisions."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth.models import User
from backend.auth.passwords import hash_password, normalize_username


class UsernameTakenError(ValueError):
    """A canonical username already belongs to an account."""


def insert_user(session: Session, username: str, password: str) -> User:
    """Stage a hashed account without assigning leads or committing a transaction."""
    username = normalize_username(username)
    if session.scalar(select(User.id).where(User.username == username)):
        raise UsernameTakenError("That username is already in use.")
    user = User(username=username, password_hash=hash_password(password))
    session.add(user)
    session.flush()
    return user
