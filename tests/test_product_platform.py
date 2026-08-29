from fastapi.testclient import TestClient

from backend.main import app, repo, settings
from backend.services.identity import require_owner

client = TestClient(app)


def test_docs_and_privacy_are_public():
    assert client.get("/docs").status_code == 200
    assert "Fynura Docs" in client.get("/docs").text
    assert client.get("/privacy").status_code == 200


def test_onboarding_validates_email_country_and_acknowledgement():
    bad = client.post(
        "/api/onboarding",
        json={"email": "not-an-email", "country": "US", "privacy_acknowledged": True},
    )
    assert bad.status_code == 422
    no_ack = client.post(
        "/api/onboarding",
        json={
            "email": "person@example.org",
            "country": "United States",
            "privacy_acknowledged": False,
        },
    )
    assert no_ack.status_code == 422
    good = client.post(
        "/api/onboarding",
        json={
            "email": "person@example.org",
            "country": "United States",
            "privacy_acknowledged": True,
        },
    )
    assert good.status_code == 201
    assert "email" not in good.json()


def test_events_reject_question_text_and_sensitive_fields():
    payload = {
        "anonymous_or_user_id": "anonymous-123",
        "event_type": "ask_fynura_submitted",
        "feature": "ask_fynura",
        "session_id": "session-123",
        "question": "private free text",
        "latitude": 1.2,
    }
    assert client.post("/api/events", json=payload).status_code == 202
    stored = repo.events[-1]
    assert "question" not in stored
    assert "latitude" not in stored


def test_admin_fails_closed_without_server_owner_configuration():
    assert client.get("/api/admin/overview").status_code == 403
    assert (
        client.get(
            "/api/admin/overview", headers={"x-fynura-owner": "ordinary@example.org"}
        ).status_code
        == 403
    )


def test_users_cannot_self_assign_admin():
    response = client.post(
        "/api/onboarding",
        json={
            "email": "normal@example.org",
            "country": "Kenya",
            "privacy_acknowledged": True,
            "role": "owner",
        },
    )
    assert response.status_code == 201
    user = next(u for u in repo.users.values() if u["email"] == "normal@example.org")
    assert "role" not in user


def test_required_login_redirects_to_welcome():
    previous = settings.fynura_onboarding_required
    settings.fynura_onboarding_required = True
    try:
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/welcome"
    finally:
        settings.fynura_onboarding_required = previous


def test_verified_owner_can_load_admin_but_ordinary_user_cannot(monkeypatch):
    monkeypatch.setattr(settings, "fynura_owner_email", "owner@example.org")
    app.dependency_overrides[require_owner] = lambda: {
        "uid": "owner-uid",
        "email": "owner@example.org",
    }
    try:
        assert client.get("/admin").status_code == 200
        assert client.get("/api/admin/overview").status_code == 200
    finally:
        app.dependency_overrides.clear()

    monkeypatch.setattr(
        "backend.services.identity.verify_token",
        lambda *_args, **_kwargs: {"uid": "user-uid", "email": "user@example.org"},
    )
    response = client.get(
        "/api/admin/overview", headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code == 403
