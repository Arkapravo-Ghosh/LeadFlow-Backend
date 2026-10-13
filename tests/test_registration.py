"""Self-service account boundaries against a disposable PostgreSQL database."""

import os
from datetime import UTC, datetime, timedelta

import pytest
from backend.auth import registration
from backend.auth.limits import locked_attempt
from backend.auth.models import AuthSession, User
from backend.auth.passwords import verify_password
from backend.auth.provision import create_user
from backend.core.config import get_settings
from backend.leads.models import Lead
from fastapi.testclient import TestClient
from sqlalchemy import func, select

AUTH = "/api/v1/auth"
PASSWORD = "disposable-registration-test-password"


@pytest.fixture
def anonymous(app):
    with TestClient(
        app,
        raise_server_exceptions=False,
        headers={"X-API-Key": os.environ["BACKEND_API_KEY"]},
    ) as client:
        yield client


def signup(client, username="new-account", **extra):
    return client.post(
        f"{AUTH}/signup",
        json={
            "username": username,
            "password": PASSWORD,
            **extra,
        },
    )


def test_registration_hashes_password_and_signs_into_empty_workspace(
    session, anonymous, user
):
    legacy = Lead(name="Legacy")
    owned = Lead(name="Existing", owner_id=user.id)
    session.add_all([legacy, owned])
    session.commit()
    response = signup(anonymous, "New.Account")
    assert response.status_code == 201
    assert response.headers["Cache-Control"] == "no-store"
    result = response.json()
    account = session.scalar(select(User).where(User.username == "new.account"))
    assert account is not None and account.password_hash.startswith("$argon2id$")
    assert verify_password(PASSWORD, account.password_hash)
    assert PASSWORD not in response.text and account.password_hash not in response.text
    anonymous.headers["Authorization"] = f"Bearer {result['token']}"
    assert anonymous.get(f"{AUTH}/me").json() == result["user"]
    assert anonymous.get("/api/v1/leads").json()["leads"] == []
    assert anonymous.get(f"/api/v1/leads/{owned.id}").status_code == 404
    assert legacy.owner_id is None and owned.owner_id == user.id
    created = anonymous.post("/api/v1/leads", json={"name": "My lead"}).json()
    assert session.get(Lead, created["id"]).owner_id == account.id
    assert anonymous.post(f"{AUTH}/logout").status_code == 204
    login = anonymous.post(
        f"{AUTH}/login", json={"username": "NEW.ACCOUNT", "password": PASSWORD}
    )
    assert login.status_code == 200


def test_duplicate_is_case_insensitive_and_preserves_original_password(
    session, anonymous
):
    first = create_user(session, "existing-user", PASSWORD)
    response = signup(anonymous, "EXISTING-USER", password=PASSWORD + "changed")
    assert response.status_code == 409
    assert verify_password(PASSWORD, first.password_hash)
    assert session.scalar(select(func.count()).select_from(User)) == 1
    assert session.scalar(select(func.count()).select_from(AuthSession)) == 0
    assert PASSWORD not in response.text


@pytest.mark.parametrize(
    "extra",
    [
        {"password": "short"},
        {"password": "x" * 129},
        {"username": "bad name"},
        {"claim_unowned": True},
        {"owner_id": "spoof"},
    ],
)
def test_invalid_registration_cannot_create_accounts(session, anonymous, extra):
    response = signup(anonymous, **extra)
    assert response.status_code == 422
    assert session.scalar(select(func.count()).select_from(User)) == 0
    assert PASSWORD not in response.text


def test_registration_requires_private_service_key(anonymous):
    response = anonymous.post(
        f"{AUTH}/signup",
        headers={"X-API-Key": ""},
        json={"username": "new-account", "password": PASSWORD},
    )
    assert response.status_code == 401


def test_account_and_session_roll_back_together(session, anonymous, monkeypatch):
    def unavailable(*_):
        raise RuntimeError("Simulated session storage failure")

    monkeypatch.setattr(registration, "issue_session", unavailable)
    assert signup(anonymous).status_code == 500
    assert session.scalar(select(func.count()).select_from(User)) == 0
    assert session.scalar(select(func.count()).select_from(AuthSession)) == 0


def test_unique_index_conflict_returns_safe_duplicate_error(
    session, anonymous, monkeypatch
):
    existing = create_user(session, "existing-user", PASSWORD)

    def raced_insert(session, username, password):
        # Exercise PostgreSQL's unique-index error, bypassing the preflight lookup.
        session.add(User(username=username, password_hash=existing.password_hash))
        session.flush()

    monkeypatch.setattr(registration, "insert_user", raced_insert)
    response = signup(anonymous, existing.username)
    assert response.status_code == 409
    assert PASSWORD not in response.text and existing.password_hash not in response.text
    assert session.scalar(select(func.count()).select_from(User)) == 1


def test_registration_budget_is_separate_from_login_and_expires(session, anonymous):
    user = create_user(session, "existing-user", PASSWORD)
    now = datetime(2026, 10, 13, 5, 0, tzinfo=UTC)
    counter = locked_attempt(session, "signup:shared", now)
    counter.failures = get_settings().signup_rate_limit - 1
    session.commit()
    assert signup(anonymous, user.username).status_code == 409
    assert signup(anonymous, "another-user").status_code == 429
    assert (
        anonymous.post(
            f"{AUTH}/login", json={"username": user.username, "password": PASSWORD}
        ).status_code
        == 200
    )
    assert (
        anonymous.post(
            f"{AUTH}/signup",
            headers={"X-Registration-Source": "other-source"},
            json={"username": "other-account", "password": PASSWORD},
        ).status_code
        == 201
    )
    counter.window_start = now - timedelta(minutes=16)
    session.commit()
    assert signup(anonymous).status_code == 201
