"""One injectable clock for consistent response-wide date classification."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)
