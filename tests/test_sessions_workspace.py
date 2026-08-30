from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from fastapi.testclient import TestClient
from test_map_data import assessment, observation

from backend.main import app, product_repo, settings
from backend.models.domain import Geography
from backend.services.sessions import (
    active_session,
    countries,
    country_record,
    end_session,
    start_session,
)
from backend.services.workspace import workspace


def test_standardized_countries():
    assert len(countries()) == 249
    assert country_record("Nigeria")["iso3"] == "NGA"
    assert country_record("US")["country_name"] == "United States"
    assert country_record("CD")["iso2"] == "CD"


def test_session_refresh_logout_expiry_and_cookie_binding():
    request = SimpleNamespace(cookies={"fynura_session": "test-cookie"})
    user = {"user_id": "session-test-user", "country": "Nigeria", "iso2": "NG", "iso3": "NGA", "account_status": "active"}
    product_repo.save_user(user)
    row = start_session(request, product_repo, user)
    request.cookies["fynura_access"] = row["session_id"]
    assert start_session(request, product_repo, user)["session_id"] == row["session_id"]
    assert active_session(request, product_repo)
    request.cookies["fynura_session"] = "different-cookie"
    assert active_session(request, product_repo) is None
    request.cookies["fynura_session"] = "test-cookie"
    end_session(request, product_repo)
    assert active_session(request, product_repo) is None
    row = start_session(request, product_repo, user)
    request.cookies["fynura_access"] = row["session_id"]
    row["expires_at"] = (datetime.now(UTC)-timedelta(seconds=1)).isoformat()
    product_repo.save_session(row)
    assert active_session(request, product_repo) is None


def test_gate_blocks_static_bypass_and_api(monkeypatch):
    monkeypatch.setattr(settings, "fynura_onboarding_required", True)
    client = TestClient(app)
    assert client.get("/api/workspace").status_code == 401
    assert client.get("/static/index.html", follow_redirects=False).headers["location"] == "/"
    assert client.get("/", follow_redirects=False).headers["location"] == "/welcome"
    assert client.get("/api/countries").status_code == 200


def test_canonical_scope_conflicts_and_no_false_zero():
    geo = Geography(name="Nigeria", level="country", iso2="NG", iso3="NGA", who_region="Africa")
    row = observation("cholera", "reported_cholera_awd_cases", 100, geo)
    package = assessment("cholera", [row])
    data = workspace([package], country="NGA")
    assert data["metrics"][0]["value"] == 100
    assert data["metrics"][0]["corroborating"] == []
    assert "age" not in data["schema"]["available_dimensions"]
    assert workspace([package], country="USA")["metrics"] == []
    conflict = row.model_copy(update={"observation_id": "conflict", "value": 120})
    package.observations.append(conflict)
    selected = workspace([package], country="NGA")["metrics"][0]
    assert selected["value"] is None
    assert selected["conflicts"]


def test_cookie_logout_revokes_access_record(monkeypatch):
    user = {"user_id": "logout-test", "country": "Nigeria", "iso2": "NG", "iso3": "NGA", "account_status": "active"}
    product_repo.save_user(user)
    req = SimpleNamespace(cookies={"fynura_session": "test-cookie"})
    row = start_session(req, product_repo, user)
    client = TestClient(app)
    client.cookies.set("fynura_session", "test-cookie")
    client.cookies.set("fynura_access", row["session_id"])
    assert client.post("/api/auth/logout").status_code == 204
    assert product_repo.get_session(row["session_id"])["ended_at"]


def test_authenticated_entry_is_once_and_events_cannot_spoof_users(monkeypatch):
    from backend import main
    monkeypatch.setattr(settings, "fynura_onboarding_required", True)
    identity = {"uid": "entry-test", "email": "entry@example.org"}
    monkeypatch.setattr(main, "create_session_cookie", lambda _: "cookie-fixture")
    monkeypatch.setattr(main.firebase_auth, "verify_id_token", lambda *a, **k: identity)
    monkeypatch.setattr("backend.services.identity.verify_token", lambda *a, **k: identity)
    client = TestClient(app)
    login = client.post("/api/auth/session", json={"id_token": "x"*120})
    assert login.status_code == 200
    assert "Max-Age" not in login.headers["set-cookie"]
    assert client.get("/api/workspace").status_code == 401
    profile = {"email": "spoof@example.org", "country": "NG", "privacy_acknowledged": True}
    assert client.post("/api/onboarding", json=profile).status_code == 201
    sid = client.cookies.get("fynura_access")
    assert client.get("/").status_code == 200
    assert client.post("/api/onboarding", json=profile).status_code == 201
    assert client.cookies.get("fynura_access") == sid
    assert product_repo.get_user("entry-test")["email"] == "entry@example.org"
    event = {"anonymous_or_user_id": "forged-user", "session_id": "forged-session",
             "country": "Other country", "event_type": "map_filter_used"}
    assert client.post("/api/events", json=event).status_code == 202
    saved = product_repo.list_events()[-1]
    assert saved["anonymous_or_user_id"] == "entry-test"
    assert saved["session_id"] == sid
    assert saved["country"] == "Nigeria"
    client.post("/api/auth/logout")
    assert client.get("/", follow_redirects=False).status_code == 307


def test_shared_ask_uses_selected_country_not_global():
    from backend.main import repo
    geo = Geography(name="Nigeria", level="country", iso2="NG", iso3="NGA", who_region="Africa")
    row = observation("cholera", "reported_cholera_awd_cases", 100, geo)
    saved = repo.latest_assessment("cholera")
    package = assessment("cholera", [row])
    repo.save_assessment(package)
    try:
        response = TestClient(app).post("/api/ask", json={"question": "What is happening with cholera?",
            "context": {"visual": "shared_workspace", "region": "Africa", "geography": "Nigeria",
                        "visual_context": {"country": "NGA", "period": ""}}})
        assert response.status_code == 200
        assert response.json()["metrics"][0]["value"] == 100
        assert "Nigeria" in response.json()["answer"]
    finally:
        if saved:
            repo.save_assessment(saved)
