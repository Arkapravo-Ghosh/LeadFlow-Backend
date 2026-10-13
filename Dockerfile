FROM ghcr.io/astral-sh/uv:0.13.0 AS uv
FROM python:3.14-slim AS base
COPY --from=uv /uv /uvx /usr/local/bin/
WORKDIR /app
ENV UV_LINK_MODE=copy PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY alembic.ini ./
COPY migrations ./migrations
COPY scripts ./scripts
RUN chmod +x scripts/start.sh

FROM base AS development
RUN uv sync --locked
COPY tests ./tests
CMD ["uv", "run", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS production
RUN uv sync --locked --no-dev
CMD ["./scripts/start.sh"]
