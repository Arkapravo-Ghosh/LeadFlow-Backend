# LeadFlow Backend

[Backend repository](https://github.com/Arkapravo-Ghosh/LeadFlow-Backend) ·
[LeadFlow parent](https://github.com/Arkapravo-Ghosh/LeadFlow) ·
[Frontend repository](https://github.com/Arkapravo-Ghosh/LeadFlow-Frontend)

The FastAPI service for LeadFlow, using SQLAlchemy, psycopg and PostgreSQL.
Dependencies and CLI commands are managed with uv; Alembic owns schema migrations.
The Next.js server calls this API with a private service credential plus the
user’s opaque session. Passwords are hashed with Argon2id; lead ownership is
enforced on every read and write.

## Run the complete app locally

Use the parent repository's Compose setup for the API, frontend and local PostgreSQL:

```sh
git clone --recurse-submodules https://github.com/Arkapravo-Ghosh/LeadFlow.git
cd LeadFlow
cp .env.example .env
# Replace BACKEND_API_KEY and POSTGRES_PASSWORD with random hex values.
docker compose up --build --watch
```

Compose supplies the local database URL and credential. FastAPI and PostgreSQL have
no published host ports. Create an account using private interactive prompts,
then optionally insert six sample leads and twelve discussions for that account:

```sh
docker compose exec backend uv run leadflow-create-user
docker compose exec backend uv run leadflow-seed
# Enter the account username for the seed.
```

The seed is repeatable and preserves existing records. It is not run automatically
in production.

## Deploy this repository to Render

Create a Docker Web Service from
[LeadFlow-Backend](https://github.com/Arkapravo-Ghosh/LeadFlow-Backend), with build
context repository root and `Dockerfile`. Set health check `/api/v1/health`.
The production image runs `scripts/start.sh`, applies migrations, then binds
Uvicorn to Render's `PORT` on `0.0.0.0`.

| Variable | Purpose |
| --- | --- |
| `DATABASE_URL` | Neon PostgreSQL connection string, preserving SSL parameters |
| `BACKEND_API_KEY` | Private credential of at least 16 characters, shared with Vercel |
| `AUTH_SESSION_HOURS` | Fixed session lifetime, default 12, range 1–168 |
| `PORT` | Provided by Render; startup falls back to 8000 locally |

See [.env.example](.env.example) and the parent's
[deployment guide](https://github.com/Arkapravo-Ghosh/LeadFlow/blob/main/docs/deployment.md).
Provision production accounts privately in the Render shell with
`uv run leadflow-create-user`. Migrations never create default credentials.
Read the parent’s [authentication guide](https://github.com/Arkapravo-Ghosh/LeadFlow/blob/main/docs/authentication.md)
for legacy data migration and session behavior. Public interactive API documentation is disabled.

## Code structure and checks

- `src/backend/main.py`: application factory and readiness route.
- `src/backend/auth`: password policy, private provisioning, sessions, login limits and routes.
- `src/backend/core`: configuration, credential checks, errors and clock.
- `src/backend/db`: SQLAlchemy metadata, engine and request sessions.
- `src/backend/leads`: routes, schemas, models, services, queries and follow-up rules.
- `src/backend/discussions`: discussion routes, validation and atomic persistence.
- `migrations`: Alembic schema history.
- `tests`: real PostgreSQL integration tests.

From the parent checkout:

```sh
docker compose --profile test run --build --rm tests
uv run --project backend ruff check backend/src backend/migrations backend/tests
```

Tests require an isolated database named `leadflow_test`; the Compose test profile
provides it. Never point test variables at the application or production database.

[Architecture](https://github.com/Arkapravo-Ghosh/LeadFlow/blob/main/docs/architecture.md) ·
[API contract](https://github.com/Arkapravo-Ghosh/LeadFlow/blob/main/docs/api.md) ·
[Verification](https://github.com/Arkapravo-Ghosh/LeadFlow/blob/main/docs/verification.md)

Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
From the parent checkout, `./scripts/install-hooks.sh` installs the shared hooks.
Commit and push backend changes before updating its submodule pointer in the parent.
