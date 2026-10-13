"""Environment configuration; credentials stay in the API process."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    auth_session_hours: int = Field(default=12, ge=1, le=168)
    database_url: SecretStr
    backend_api_key: SecretStr = Field(min_length=16)


@lru_cache
def get_settings() -> Settings:
    return Settings()
