"""Authenticate service-to-service calls without exposing a browser credential."""

from secrets import compare_digest
from typing import Annotated

from fastapi import Header, HTTPException

from backend.core.config import get_settings


def verify_api_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
    expected = get_settings().backend_api_key.get_secret_value()
    if not x_api_key or not compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid service credential.")
