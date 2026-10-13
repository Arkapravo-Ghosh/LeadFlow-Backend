# LeadFlow API

FastAPI + SQLAlchemy/psycopg + Alembic, managed by uv. Routes, services and
repositories live in focused domain packages under `src/backend`.

Run via the parent `docker compose up --watch`; it provides local PostgreSQL and
service credentials. `uv run leadflow-seed` explicitly seeds six leads. Production
Docker runs `scripts/start.sh`, applies migrations and honors Render's `PORT`.
See the parent `docs/deployment.md` for Neon/Render settings.

Tests require an isolated PostgreSQL database named `leadflow_test`; use the parent
Compose test profile. Never point test variables at the application database.
