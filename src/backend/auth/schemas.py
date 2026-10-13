"""Narrow public authentication shapes never serialize stored password hashes."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from backend.auth.passwords import normalize_username


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=64)
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def username_format(cls, value: str) -> str:
        return normalize_username(value)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    username: str


class LoginResult(BaseModel):
    # This internal API response is consumed by Next.js only, never returned to JS.
    token: str
    expires_at: datetime
    user: UserRead
