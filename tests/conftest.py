"""Integration tests require a disposable PostgreSQL database, never the user's URL."""

import os
from datetime import UTC, datetime

import pytest
from backend.auth.provision import create_user
from backend.core.clock import utc_now
from backend.db.session import get_session, make_engine
from backend.main import create_app
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture(scope="session")
def engine():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.fail("Run integration tests through the Compose tests service.")
    engine = make_engine(url)
    if engine.url.database != "leadflow_test":
        pytest.fail(
            "TEST_DATABASE_URL must select the disposable leadflow_test database."
        )
    yield engine
    engine.dispose()


@pytest.fixture
def session(engine):
    with engine.connect() as connection:
        transaction = connection.begin()
        with Session(
            connection, join_transaction_mode="create_savepoint", expire_on_commit=False
        ) as session:
            yield session
        transaction.rollback()


@pytest.fixture
def app(session):
    app = create_app()

    def database():
        try:
            yield session
        except Exception:
            session.rollback()
            raise

    app.dependency_overrides[get_session] = database
    app.dependency_overrides[utc_now] = lambda: datetime(2026, 10, 13, 5, 0, tzinfo=UTC)
    return app


@pytest.fixture
def user(session):
    return create_user(session, "integration-user", "integration-password-for-tests")


@pytest.fixture
def client(app, user):
    with TestClient(
        app,
        raise_server_exceptions=False,
        headers={"X-API-Key": os.environ["BACKEND_API_KEY"]},
    ) as client:
        result = client.post(
            "/api/v1/auth/login",
            json={
                "username": user.username,
                "password": "integration-password-for-tests",
            },
        )
        assert result.status_code == 200
        client.headers["Authorization"] = f"Bearer {result.json()['token']}"
        yield client
