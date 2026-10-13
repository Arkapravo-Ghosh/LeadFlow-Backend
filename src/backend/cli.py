"""Convenience entrypoint; Docker Compose controls normal app startup."""

import uvicorn


def main() -> None:
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000)
