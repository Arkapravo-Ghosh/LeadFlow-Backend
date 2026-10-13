"""API-level validation, status persistence, search, and missing-parent handling."""

from uuid import uuid4

import pytest

BASE = "/api/v1/leads"


def test_create_defaults_and_persistence(client, session):
    response = client.post(
        BASE, json={"name": "  Ada Lovelace  ", "phone": "+44 020 001"}
    )
    assert response.status_code == 201
    lead = response.json()
    assert lead["name"] == "Ada Lovelace"
    assert lead["status"] == "new"
    assert lead["last_note"] is None
    assert lead["phone"] == "+44 020 001"
    session.expire_all()
    loaded = client.get(f"{BASE}/{lead['id']}").json()
    assert loaded["name"] == lead["name"]


@pytest.mark.parametrize(
    "payload",
    [
        {"name": ""},
        {"name": "   "},
        {"name": "x" * 121},
        {"name": "Valid", "phone": "x" * 41},
        {"name": "Valid", "status": "won"},
    ],
)
def test_invalid_leads_return_field_errors(client, payload):
    response = client.post(BASE, json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["fields"]


@pytest.mark.parametrize(
    "status", ["new", "contacted", "qualified", "proposal_sent", "won", "lost"]
)
def test_every_status_persists(client, session, status):
    lead = client.post(BASE, json={"name": f"Status {status}"}).json()
    updated = client.patch(f"{BASE}/{lead['id']}", json={"status": status})
    assert updated.status_code == 200
    session.expire_all()
    assert client.get(f"{BASE}/{lead['id']}").json()["status"] == status


def test_search_status_combination_and_literal_wildcards(client):
    ada = client.post(BASE, json={"name": "Ada_Exact%"}).json()
    client.post(BASE, json={"name": "AdaXExactOther"})
    client.patch(f"{BASE}/{ada['id']}", json={"status": "qualified"})
    result = client.get(
        BASE, params={"search": "ADA_exact%", "status": "qualified"}
    ).json()
    assert [lead["id"] for lead in result["leads"]] == [ada["id"]]
    assert (
        client.get(BASE, params={"search": "Ada", "status": "lost"}).json()["total"]
        == 0
    )


def test_missing_ids_invalid_status_timezone_and_service_auth(client):
    absent = str(uuid4())
    assert client.get(f"{BASE}/{absent}").status_code == 404
    assert client.get(f"{BASE}/{absent}/discussions").status_code == 404
    assert (
        client.post(f"{BASE}/{absent}/discussions", json={"note": "Hello"}).status_code
        == 404
    )
    assert client.patch(f"{BASE}/{absent}", json={"status": "won"}).status_code == 404
    assert client.get(BASE, params={"timezone": "Invalid/Timezone"}).status_code == 422
    assert client.get(BASE, params={"status": "unknown"}).status_code == 422
    assert client.get(BASE, headers={"X-API-Key": ""}).status_code == 401
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404
