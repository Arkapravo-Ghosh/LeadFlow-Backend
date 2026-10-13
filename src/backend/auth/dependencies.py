"""Derive ownership from a verified session on every protected request."""

from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.auth.models import User
from backend.auth.service import authenticated_user
from backend.core.dependencies import Database, Now

bearer = HTTPBearer(auto_error=False)


def session_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    if credentials is None or not 40 <= len(credentials.credentials) <= 128:
        raise HTTPException(401, "Please sign in to continue.")
    return credentials.credentials


Token = Annotated[str, Depends(session_token)]


def current_user(session: Database, token: Token, now: Now) -> User:
    return authenticated_user(session, token, now)


CurrentUser = Annotated[User, Depends(current_user)]
