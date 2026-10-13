"""Real PostgreSQL auth/ownership checks, using disposable test accounts only."""

import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from backend.auth.models import AuthSession, User
from backend.auth.passwords import verify_password
from backend.auth.provision import create_user
from backend.auth.service import token_digest
from backend.leads.models import Lead
from backend.seed import seed
from fastapi.testclient import TestClient
from sqlalchemy import select

AUTH = "/api/v1/auth"
BASE = "/api/v1/leads"
TEST_PASSWORD = "disposable-test-password-only"


@pytest.fixture
def anonymous(app):
    with TestClient(
        app, headers={"X-API-Key": os.environ["BACKEND_API_KEY"]}
    ) as client:
        yield client


def login(client, username, password=TEST_PASSWORD):
    response = client.post(
        f"{AUTH}/login", json={"username": username, "password": password}
    )
    assert response.status_code == 200
    client.headers["Authorization"] = f"Bearer {response.json()['token']}"
    return response.json()


def test_hashing_normalization_and_safe_response(session, anonymous):
    user = create_user(session, "  Test.Account  ", TEST_PASSWORD)
    assert user.password_hash.startswith("$argon2id$")
    assert verify_password(TEST_PASSWORD, user.password_hash)
    assert not verify_password("wrong", user.password_hash)
    response = login(anonymous, "TEST.ACCOUNT")
    assert set(response["user"]) == {"id", "username"}
    assert TEST_PASSWORD not in str(response)
    stored = session.get(AuthSession, token_digest(response["token"]))
    assert stored is not None and stored.token_hash != response["token"]
    assert anonymous.get(f"{AUTH}/me").json()["id"] == str(user.id)


def test_invalid_credentials_have_same_error_and_persistent_limit(session, anonymous):
    create_user(session, "real-account", TEST_PASSWORD)
    failures = []
    for username in ("real-account", "unknown-account"):
        for _ in range(5):
            reply = anonymous.post(
                f"{AUTH}/login", json={"username": username, "password": "wrong"}
            )
            assert reply.status_code == 401
            failures.append(reply.json())
        assert (
            anonymous.post(
                f"{AUTH}/login", json={"username": username, "password": TEST_PASSWORD}
            ).status_code
            == 429
        )
    assert all(item == failures[0] for item in failures)


def test_limit_expires_and_disabled_account_cannot_login(session, anonymous):
    user = create_user(session, "limited-account", TEST_PASSWORD)
    from backend.auth.limits import locked_attempt
    from backend.auth.models import LoginAttempt

    now = datetime(2026, 10, 13, 5, 0, tzinfo=UTC)
    counter = locked_attempt(session, user.username, now - timedelta(minutes=16))
    counter.failures = 5
    session.commit()
    login(anonymous, user.username)
    user.is_active = False
    session.commit()
    assert anonymous.get(BASE).status_code == 401
    assert (
        anonymous.post(
            f"{AUTH}/login", json={"username": user.username, "password": TEST_PASSWORD}
        ).status_code
        == 401
    )
    assert session.scalar(select(LoginAttempt.failures)) == 1


def test_api_key_alone_cannot_access_any_data_or_mutation(anonymous):
    lead_id = uuid4()
    for method, path, body in [
        ("get", BASE, None),
        ("post", BASE, {"name": "Denied"}),
        ("get", f"{BASE}/{lead_id}", None),
        ("patch", f"{BASE}/{lead_id}", {"status": "won"}),
        ("get", f"{BASE}/{lead_id}/discussions", None),
        ("post", f"{BASE}/{lead_id}/discussions", {"note": "Denied"}),
    ]:
        assert anonymous.request(method, path, json=body).status_code == 401
    assert anonymous.get("/api/v1/health").status_code == 200


def test_expiry_and_logout_revoke_session(session, anonymous):
    user = create_user(session, "session-account", TEST_PASSWORD)
    response = login(anonymous, user.username)
    assert anonymous.post(f"{AUTH}/logout").status_code == 204
    assert session.get(AuthSession, token_digest(response["token"])) is None
    assert anonymous.get(BASE).status_code == 401
    response = login(anonymous, user.username)
    stored = session.get(AuthSession, token_digest(response["token"]))
    stored.expires_at = datetime(2026, 10, 13, 5, 0, tzinfo=UTC)
    session.commit()
    assert anonymous.get(BASE).status_code == 401


def test_other_accounts_cannot_read_or_change_leads(session, client, anonymous):
    private = client.post(BASE, json={"name": "Private lead"}).json()
    client.post(f"{BASE}/{private['id']}/discussions", json={"note": "Private note"})
    other = create_user(session, "other-account", TEST_PASSWORD)
    login(anonymous, other.username)
    assert anonymous.get(BASE).json()["leads"] == []
    path = f"{BASE}/{private['id']}"
    assert anonymous.get(path).status_code == 404
    assert anonymous.patch(path, json={"status": "won"}).status_code == 404
    assert anonymous.get(f"{path}/discussions").status_code == 404
    assert (
        anonymous.post(f"{path}/discussions", json={"note": "Attack"}).status_code
        == 404
    )
    owned = anonymous.post(BASE, json={"name": "Other lead"}).json()
    assert session.get(Lead, owned["id"]).owner_id == other.id
    assert client.get(f"{BASE}/{owned['id']}").status_code == 404
    assert client.get(path).json()["status"] == "new"
    assert len(client.get(f"{path}/discussions").json()) == 1
    assert (
        anonymous.post(
            BASE, json={"name": "Spoof", "owner_id": private["id"]}
        ).status_code
        == 422
    )


def test_claim_assigns_only_unowned_legacy_rows(session, user):
    legacy = Lead(name="Legacy")
    owned = Lead(name="Already owned", owner_id=user.id)
    session.add_all([legacy, owned])
    session.commit()
    new = create_user(session, "claim-account", TEST_PASSWORD, claim_unowned=True)
    session.expire_all()
    assert legacy.owner_id == new.id
    assert owned.owner_id == user.id
    assert session.scalar(select(User).where(User.id == new.id)) is not None


def test_seed_is_owned_and_repeatable_per_account(session, user):
    other = create_user(session, "seed-account", TEST_PASSWORD)
    assert seed(session, user.id) == 6
    assert seed(session, other.id) == 6
    assert seed(session, user.id) == 0
    rows = session.scalars(select(Lead)).all()
    assert sum(item.owner_id == user.id for item in rows) == 6
    assert sum(item.owner_id == other.id for item in rows) == 6


def test_short_password_and_duplicate_username_rejected(session, user):
    with pytest.raises(ValueError):
        create_user(session, "new-account", "short")
    with pytest.raises(ValueError):
        create_user(session, user.username.upper(), TEST_PASSWORD)


def test_legacy_seed_does_not_duplicate_after_claim(session):
    from uuid import NAMESPACE_URL, uuid5

    from backend.seed import SAMPLES

    for name, *_ in SAMPLES:
        session.add(Lead(id=uuid5(NAMESPACE_URL, f"leadflow/demo/{name}"), name=name))
    session.commit()
    user = create_user(session, "legacy-seed-owner", TEST_PASSWORD, claim_unowned=True)
    assert seed(session, user.id) == 0
    assert len(session.scalars(select(Lead)).all()) == 6


def test_login_still_requires_private_service_key(session, anonymous):
    create_user(session, "key-check-account", TEST_PASSWORD)
    response = anonymous.post(
        f"{AUTH}/login",
        headers={"X-API-Key": ""},
        json={"username": "key-check-account", "password": TEST_PASSWORD},
    )
    assert response.status_code == 401
    assert TEST_PASSWORD not in response.text
