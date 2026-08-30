import asyncio
import logging
import re
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from firebase_admin import auth as firebase_auth
from pydantic import BaseModel, Field, field_validator

from backend.config import get_settings
from backend.models.domain import AskRequest, AskResponse, Watch
from backend.repositories import ProductRepository
from backend.repositories.evidence import EvidenceRepository
from backend.services.analytics import intelligence_snapshot
from backend.services.context import resolve_context
from backend.services.identity import (
    create_session_cookie,
    optional_identity,
    require_identity,
    require_owner,
)
from backend.services.map_data import build_map_data
from backend.services.pipeline import Pipeline
from backend.services.refresh import RefreshService
from backend.services.science import science_answer
from backend.services.sessions import (
    active_session,
    countries,
    country_record,
    end_session,
    start_session,
)
from backend.services.source_registry import network_summary, sources
from backend.services.visualization import select_visualizations
from backend.services.workspace import workspace

logging.basicConfig(
    level=logging.INFO,
    format='{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
)
app = FastAPI(
    title="Fynura",
    version="0.1.0",
    description="Near-real-time, traceable public-health intelligence",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)
repo = EvidenceRepository()
product_repo = ProductRepository(repo)
pipeline = Pipeline(repo)
refresh_service = RefreshService(repo, pipeline)
settings = get_settings()
OwnerIdentity = Annotated[dict, Depends(require_owner)]
SignedInIdentity = Annotated[dict, Depends(require_identity)]
ROOT = Path(__file__).resolve().parents[1]
app.mount("/static", StaticFiles(directory=ROOT / "frontend"), name="static")


@app.middleware("http")
async def frontend_cache_policy(request: Request, call_next):
    path = request.url.path
    if path in {"/static/index.html", "/static/admin.html"}:
        return RedirectResponse("/" if path.endswith("index.html") else "/admin", status_code=307)
    public_api = {"/api/auth/config", "/api/auth/session", "/api/auth/logout", "/api/auth/me", "/api/onboarding", "/api/countries", "/api/product/config"}
    protected = path in {"/", "/admin", "/static/index.html", "/static/admin.html"} or (path.startswith("/api/") and path not in public_api)
    if settings.fynura_onboarding_required and protected and not active_session(request, product_repo):
        if path in {"/", "/admin", "/static/index.html", "/static/admin.html"}:
            return RedirectResponse("/welcome", status_code=307, headers={"Cache-Control": "no-store"})
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Fynura session expired. Please sign in again."}, status_code=401, headers={"Cache-Control": "no-store"})
    response = await call_next(request)
    if request.url.path in {"/", "/welcome", "/admin"} or request.url.path.startswith("/api/auth/"):
        response.headers["Cache-Control"] = "no-store"
    elif request.url.path.startswith("/static/") and request.url.path.endswith((".js", ".css", ".html")):
        response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/", include_in_schema=False)
def home(request: Request):
    if settings.fynura_onboarding_required and not optional_identity(request):
        return RedirectResponse("/welcome", status_code=307)
    return FileResponse(ROOT / "frontend" / "index.html")


@app.get("/docs", include_in_schema=False)
def docs_home():
    return FileResponse(ROOT / "frontend" / "docs.html")


@app.get("/welcome", include_in_schema=False)
def welcome():
    return FileResponse(ROOT / "frontend" / "welcome.html")


@app.get("/admin", include_in_schema=False)
def admin(_: OwnerIdentity):
    return FileResponse(ROOT / "frontend" / "admin.html")


@app.get("/privacy", include_in_schema=False)
def privacy():
    return FileResponse(ROOT / "frontend" / "privacy.html")


class OnboardingRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    country: str = Field(min_length=2, max_length=80)
    privacy_acknowledged: bool
    stakeholder_role: str | None = Field(default=None, max_length=40)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        value = value.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("Enter a valid email address")
        return value

    @field_validator("country")
    @classmethod
    def valid_country(cls, value: str) -> str:
        return country_record(value.strip())["country_name"]


class AnalyticsEvent(BaseModel):
    anonymous_or_user_id: str = Field(min_length=8, max_length=80)
    event_type: str
    country: str | None = Field(default=None, max_length=80)
    stakeholder_role: str | None = Field(default=None, max_length=40)
    threat_id: str | None = Field(default=None, pattern="^(measles|ebola|cholera)$")
    feature: str | None = Field(default=None, max_length=40)
    session_id: str = Field(min_length=8, max_length=80)

    @field_validator("event_type")
    @classmethod
    def allowed_event(cls, value: str) -> str:
        allowed = {
            "user_registered",
            "session_started",
            "threat_viewed",
            "ask_fynura_submitted",
            "evidence_opened",
            "chart_viewed",
            "map_viewed",
            "visual_downloaded",
            "citation_copied",
            "watch_created",
            "brief_generated",
            "docs_viewed",
            "map_filter_used", "source_opened", "voice_used", "early_signal_viewed",
        }
        if value not in allowed:
            raise ValueError("Unsupported analytics event")
        return value


class SessionRequest(BaseModel):
    id_token: str = Field(min_length=100, max_length=10000)


@app.get("/api/product/config")
def product_config():
    return {
        "onboarding_required": settings.fynura_onboarding_required,
        "privacy_notice_version": settings.fynura_privacy_notice_version,
        "authentication": "google_identity_platform",
    }


@app.get("/api/countries")
def country_options():
    return countries()


@app.get("/api/auth/config")
def auth_config():
    return {
        "enabled": bool(settings.fynura_firebase_api_key),
        "apiKey": settings.fynura_firebase_api_key,
        "authDomain": settings.fynura_auth_domain,
        "projectId": settings.google_cloud_project,
    }


@app.post("/api/auth/session")
def auth_session(payload: SessionRequest, response: Response):
    cookie = create_session_cookie(payload.id_token)
    identity = firebase_auth.verify_id_token(payload.id_token, check_revoked=True)
    response.set_cookie(
        "fynura_session",
        cookie,
        httponly=True,
        secure=settings.fynura_env != "development",
        samesite="lax",
        path="/",
    )
    email = identity.get("email", "").lower()
    return {"email": email, "owner": email == (settings.fynura_owner_email or "").lower()}


@app.post("/api/auth/logout", status_code=204)
def auth_logout(request: Request, response: Response):
    end_session(request, product_repo)
    response.delete_cookie("fynura_session", path="/")
    response.delete_cookie("fynura_access", path="/")


@app.get("/api/auth/me")
def auth_me(identity: SignedInIdentity):
    email = identity.get("email", "").lower()
    return {
        "uid": identity["uid"],
        "email": email,
        "owner": email == (settings.fynura_owner_email or "").lower(),
    }


@app.post("/api/onboarding", status_code=201)
def onboard(request: OnboardingRequest, http_request: Request, response: Response):
    if not request.privacy_acknowledged:
        raise HTTPException(422, "Privacy Notice and Responsible Use acknowledgement is required")
    now = datetime.now(UTC).isoformat()
    identity = optional_identity(http_request)
    if settings.fynura_onboarding_required and not identity:
        raise HTTPException(401, "Google sign-in is required")
    email = identity.get("email", "").lower() if identity else request.email
    user_id = identity["uid"] if identity else f"usr_{uuid4().hex}"
    existing = product_repo.get_user(user_id)
    user = existing or {
        "user_id": user_id,
        "email": email,
        "created_at": now,
        "account_status": "active",
    }
    user.update(
        {
            "country": request.country,
            "last_active_at": now,
            "stakeholder_role": request.stakeholder_role,
            "privacy_notice_version": settings.fynura_privacy_notice_version,
            "privacy_acknowledged_at": now,
        }
    )
    user.update(country_record(request.country))
    product_repo.save_user(user)
    if identity:
        session = start_session(http_request, product_repo, user)
        response.set_cookie("fynura_access", session["session_id"], httponly=True,
                            secure=settings.fynura_env != "development", samesite="lax", path="/")
    return {
        "user_id": user["user_id"],
        "country": user["country"],
        "stakeholder_role": user["stakeholder_role"],
        "privacy_notice_version": user["privacy_notice_version"],
    }


@app.post("/api/events", status_code=202)
def record_event(event: AnalyticsEvent, request: Request):
    payload = event.model_dump()
    session = active_session(request, product_repo)
    if settings.fynura_onboarding_required and not session:
        raise HTTPException(401, "Active session required")
    if session:
        payload["verified_session"] = True
        payload.update(anonymous_or_user_id=session["user_id"], session_id=session["session_id"],
                       country=session["country"], stakeholder_role=session.get("stakeholder_role"))
        session["last_active_at"] = datetime.now(UTC).isoformat()
        product_repo.save_session(session)
    payload.update({"event_id": f"evt_{uuid4().hex}", "timestamp": datetime.now(UTC).isoformat()})
    product_repo.save_event(payload)
    return {"accepted": True}


@app.get("/api/admin/overview")
def admin_overview(_: OwnerIdentity):
    users, events = product_repo.list_users(), product_repo.list_events()
    countries = Counter(u.get("country", "Unknown") for u in users)
    features = Counter(e.get("feature") for e in events if e.get("feature"))
    threats = Counter(e.get("threat_id") for e in events if e.get("threat_id"))
    event_types = Counter(e.get("event_type") for e in events if e.get("event_type"))
    now = datetime.now(UTC)

    def active_since(days: int) -> int:
        cutoff = now - timedelta(days=days)
        return sum(
            1
            for u in users
            if datetime.fromisoformat(u.get("last_active_at", u["created_at"])) >= cutoff
        )

    return {
        "total_users": len(users),
        "active_today": active_since(1),
        "active_week": active_since(7),
        "active_month": active_since(30),
        "countries": dict(countries),
        "features": dict(features),
        "threats": dict(threats),
        "event_types": dict(event_types),
        "event_count": len(events),
    }


@app.get("/api/admin/users")
def admin_users(_: OwnerIdentity, search: str = ""):
    needle = search.strip().lower()
    users = product_repo.list_users()
    if needle:
        users = [
            u
            for u in users
            if needle in u.get("email", "").lower() or needle in u.get("country", "").lower()
        ]
    return {"users": sorted(users, key=lambda u: u.get("created_at", ""), reverse=True)[:200]}


@app.post("/api/admin/users/{user_id}/disable")
def admin_disable_user(user_id: str, owner: OwnerIdentity):
    if user_id == owner.get("uid"):
        raise HTTPException(409, "The owner account cannot disable itself")
    try:
        firebase_auth.update_user(user_id, disabled=True)
    except firebase_auth.UserNotFoundError as exc:
        raise HTTPException(404, "User not found") from exc
    user = product_repo.set_account_status(user_id, "disabled")
    return {"user": user, "disabled": True}


@app.delete("/api/admin/users/{user_id}")
def admin_delete_user(user_id: str, owner: OwnerIdentity):
    if user_id == owner.get("uid"):
        raise HTTPException(409, "The owner account cannot delete itself")
    try:
        firebase_auth.delete_user(user_id)
    except firebase_auth.UserNotFoundError as exc:
        raise HTTPException(404, "User not found") from exc
    product_repo.delete_user(user_id)
    return {"deleted": True}


@app.get("/health")
def health():
    return {"status": "ok", "service": "fynura", "cloud_project": "fynura-public-health"}


@app.get("/api/threats")
def threats():
    return [
        {"id": x, "name": x.title(), "supported": True, "assessment": repo.latest_assessment(x)}
        for x in ("measles", "ebola", "cholera")
    ]


@app.get("/api/sources")
def source_registry():
    return {"sources": sources(), "summary": network_summary()}


@app.get("/api/intelligence")
async def intelligence():
    async def ensure(threat_id):
        existing = repo.latest_assessment(threat_id)
        if existing:
            return existing
        return await refresh_service.refresh(threat_id)

    values = await asyncio.gather(*(ensure(x) for x in ("measles", "ebola", "cholera")))
    return {item.threat_id: item for item in values if item}


@app.post('/internal/refresh')
async def scheduled_refresh(request: Request):
    from google.auth.transport.requests import Request as GoogleRequest
    from google.oauth2.id_token import verify_oauth2_token

    token = request.headers.get('authorization', '').removeprefix('Bearer ')
    if not token:
        raise HTTPException(403, 'Authorized scheduler identity required')
    audience = 'https://fynura-g7sjcbc4ua-uc.a.run.app'
    try:
        identity = verify_oauth2_token(token, GoogleRequest(), audience=audience)
        expected = f'fynura-scheduler@{settings.google_cloud_project}.iam.gserviceaccount.com'
        if identity.get('email') != expected or not identity.get('email_verified'):
            raise ValueError('Unapproved caller')
    except Exception as exc:
        raise HTTPException(403, 'Authorized scheduler identity required') from exc
    values = await refresh_service.run()
    return {'available': [item.threat_id for item in values if item]}


@app.get('/api/data-status')
def data_status():
    snapshots = [repo.latest_assessment(t) for t in ('measles', 'ebola', 'cholera')]
    network = []
    for source in sources():
        status = source['integration_status'].upper().replace('_', ' ')
        if source['source_id'] == 'who_global_surveillance':
            status = 'VERIFIED SNAPSHOT' if any(snapshots) else 'CONFIGURED'
        network.append({'name': source['display_name'], 'status': status})
    return {'network': network, 'verified_snapshots': sum(x is not None for x in snapshots),
            'threats_monitored': 3,
            'refresh': {t: refresh_service.status(t) for t in ('measles', 'ebola', 'cholera')}}


@app.get('/api/admin/source-health')
def admin_source_health(_: OwnerIdentity):
    return {'sources': sources(), 'refresh': data_status()['refresh']}


@app.get('/api/analytics')
def analytics():
    items = [repo.latest_assessment(t) for t in ('measles', 'ebola', 'cholera')]
    return [snapshot for item in items if item for snapshot in [intelligence_snapshot(item)] if snapshot]


@app.get("/api/workspace")
def analytical_workspace(threat: str = "all", region: str = "Global", country: str = "", period: str = ""):
    if threat not in {"all", "measles", "ebola", "cholera"}:
        raise HTTPException(422, "Unsupported threat")
    items = [repo.latest_assessment(t) for t in ("measles", "ebola", "cholera")]
    return workspace([a for a in items if a], threat, region, country, period)


@app.get("/api/admin/usage")
def admin_usage(_: OwnerIdentity):
    sessions, events = product_repo.list_sessions(), product_repo.list_events()
    events = [e for e in events if e.get("verified_session")]
    users = Counter(s["user_id"] for s in sessions)
    durations = [(datetime.fromisoformat(s.get("ended_at") or s["last_active_at"]) - datetime.fromisoformat(s["started_at"])).total_seconds() for s in sessions]
    return {"total_sessions": len(sessions), "unique_users": len(users),
            "returning_users": sum(n > 1 for n in users.values()),
            "average_active_duration_seconds": round(sum(durations) / len(durations)) if durations else 0,
            "sessions_by_country": dict(Counter(s["country"] for s in sessions)),
            "stakeholder_roles": dict(Counter(s.get("stakeholder_role") or "Not supplied" for s in sessions)),
            "events": dict(Counter(e["event_type"] for e in events)),
            "threats": dict(Counter(e["threat_id"] for e in events if e.get("threat_id"))),
            "sample_limit": 5000, "sample_limited": len(sessions) >= 5000 or len(events) >= 5000,
            "duration_definition": "Time from entry to last recorded activity or explicit sign out, not attention time."}


@app.get("/api/map")
def map_data(threat: str = "all", region: str = "Global", metric: str = "signal", country: str = "", period: str = ""):
    if threat not in {"all", "measles", "ebola", "cholera"}:
        raise HTTPException(422, "Unsupported threat filter")
    if region not in {
        "Global",
        "Africa",
        "Americas",
        "Europe",
        "Eastern Mediterranean",
        "South-East Asia",
        "Western Pacific",
    }:
        raise HTTPException(422, "Unsupported WHO region filter")
    assessments = [repo.latest_assessment(item) for item in ("measles", "ebola", "cholera")]
    return build_map_data([item for item in assessments if item], threat, region, metric, country, period)


@app.post("/api/threats/{threat_id}/assess")
async def assess(threat_id: str, _: OwnerIdentity):
    if threat_id not in {"measles", "ebola", "cholera"}:
        raise HTTPException(404, "Unknown threat")
    try:
        if threat_id == "measles":
            return await pipeline.assess_measles()
        if threat_id == "ebola":
            return await pipeline.assess_ebola()
        return await pipeline.assess_cholera()
    except Exception as exc:
        raise HTTPException(502, "Source retrieval could not complete; the latest verified snapshot is retained.") from exc


@app.get("/api/threats/{threat_id}/assessments/latest")
def latest(threat_id: str):
    item = repo.latest_assessment(threat_id)
    if not item:
        raise HTTPException(404, "No assessment has been generated in this process yet.")
    return item


@app.get("/api/assessments/{assessment_id}/evidence")
def evidence(assessment_id: str):
    item = repo.get_assessment(assessment_id)
    if not item:
        raise HTTPException(404, "Assessment not found")
    return {
        "observations": item.observations,
        "evidence_groups": item.evidence_groups,
        "claims": item.claims,
    }


@app.get("/api/assessments/{assessment_id}/visualizations")
def visualizations(assessment_id: str):
    item = repo.get_assessment(assessment_id)
    if not item:
        raise HTTPException(404, "Assessment not found")
    return select_visualizations(item)


@app.post("/api/ask", response_model=AskResponse)
def ask(request: AskRequest):
    educational = science_answer(request.question)
    if educational:
        return AskResponse(answer=educational, evidence_ids=[], subject={'label': 'PUBLIC-HEALTH METHODS', 'geography': 'General explanation'}, limitations=['Educational explanation, not a live surveillance finding.'])
    threat_id, resolved = resolve_context(request)
    request = request.model_copy(update={"context": resolved, "threat_id": threat_id})
    if request.context and request.context.visual == "shared_workspace" and (
        request.context.region not in {None, "Global"} or
        (request.context.visual_context or {}).get("country") or
        (request.context.visual_context or {}).get("period")
    ):
        scope = request.context.visual_context or {}
        selected = analytical_workspace(threat_id or "all", request.context.region or "Global",
                                        scope.get("country", ""), scope.get("period", ""))["metrics"]
        if not selected:
            return AskResponse(answer="No verified observation available for this selection.",
                               evidence_ids=[], declined=True, subject={"geography": request.context.geography})
        usable = [m for m in selected if m["value"] is not None]
        primary = [m for m in usable if m["indicator"] in {"confirmed_cases", "reported_measles_cases", "reported_measles_cases_global", "reported_cholera_awd_cases"}]
        chosen = (primary or usable)[:12]
        return AskResponse(
            answer="Selected verified scope. "+ " ".join(f'{m["threat"].title()} in {m["geography"]["name"]}: {m["value"]:,.0f} {m["unit"]} ({m["indicator"].replace("_", " ")}), reporting through {m["reporting_cutoff"]}.' for m in chosen),
            evidence_ids=[i for m in chosen for i in m["evidence_ids"]],
            subject={"label": "SHARED ANALYTICAL SCOPE", "geography": request.context.geography},
            metrics=[{"label": m["threat"]+" · "+m["geography"]["name"]+" · "+m["indicator"], "value": m["value"], "unit": m["unit"], "evidence_id": m["evidence_ids"][0]} for m in chosen],
            limitations=["Country observations are not summed into a regional total.", "Up to 12 primary observations shown; inspect the shared evidence table for the full selection.", "Unresolved conflicts are excluded from numeric answers."],
            sources=[{"organization": m["primary_source"], "title": m["indicator"], "url": m["source_url"],
                      "published": str(m["publication_date"]) if m["publication_date"] else None,
                      "reporting_cutoff": str(m["reporting_cutoff"])} for m in chosen])
    if threat_id and threat_id not in {"measles", "ebola", "cholera"}:
        raise HTTPException(422, "Unsupported threat")
    if not threat_id:
        available = [repo.latest_assessment(x) for x in ("ebola", "measles", "cholera")]
        available = [item for item in available if item]
        if not available:
            return AskResponse(
                answer="No verified evidence is currently available. View data status for the latest source availability.",
                evidence_ids=[],
                declined=True,
                subject={"label": "GLOBAL INTELLIGENCE", "geography": "Global"},
            )
        answer = (
            "Fynura is currently monitoring three demonstration threats: Ebola, Measles and Cholera. "
            + " ".join(item.summary for item in available)
        )
        return AskResponse(
            answer=answer,
            evidence_ids=sorted(
                {eid for item in available for claim in item.claims for eid in claim.evidence_ids}
            ),
            subject={"label": "GLOBAL INTELLIGENCE", "geography": "Global"},
            limitations=[
                "Coverage is demonstrative and source reporting periods differ across threats."
            ],
        )
    item = repo.latest_assessment(threat_id)
    if not item:
        return AskResponse(
            answer=f"No verified evidence is currently available for {threat_id} in the selected scope. View data status for source availability.",
            evidence_ids=[],
            declined=True,
            subject={
                "label": threat_id.upper(),
                "geography": request.context.geography if request.context else "Configured scope",
            },
        )
    q = request.question.lower()
    from backend.evidence import fuse_observations
    selected_ids = {g.selected_observation_id for g in fuse_observations(item.observations)}
    item = item.model_copy(update={"observations": [o for o in item.observations if o.observation_id in selected_ids]})
    if not item.observations:
        return AskResponse(answer="No resolved canonical evidence is available for this selection. Inspect the evidence conflicts.", evidence_ids=[], declined=True)
    requested_geography = request.context.geography if request.context else "Global"
    geographic_rows = [
        observation
        for observation in item.observations
        if requested_geography.lower() != 'global' and requested_geography.lower()
        in {
            observation.geography.name.lower(),
            (observation.geography.source_name or "").lower(),
            (observation.geography.iso2 or "").lower(),
            (observation.geography.iso3 or observation.geography.code or "").lower(),
        }
    ]
    scoped_rows = geographic_rows or item.observations
    if not geographic_rows and requested_geography not in {'Global', 'Configured scope', item.geography.name}:
        return AskResponse(answer=f'No verified evidence is currently available for {threat_id} in {requested_geography}.', evidence_ids=[], declined=True, subject={'disease': threat_id, 'geography': requested_geography})
    if not geographic_rows:
        scoped_rows = [o for o in item.observations if o.geography.name == item.geography.name] or item.observations
    latest = max(
        scoped_rows,
        key=lambda o: o.reporting_period_end or o.event_date or o.retrieved_at.date(),
    )
    cutoff = (
        request.context.reporting_cutoff
        if request.context and request.context.reporting_cutoff
        else latest.reporting_period_end or latest.event_date
    )
    names = {
        "ebola": (
            "Bundibugyo virus disease outbreak",
            "Democratic Republic of the Congo",
            "WHO Disease Outbreak News",
        ),
        "measles": (
            "WHO provisional monthly measles surveillance",
            "Global",
            "WHO provisional measles and rubella data",
        ),
        "cholera": (
            "global cholera and acute watery diarrhoea surveillance",
            "Global",
            "WHO Weekly Epidemiological Record",
        ),
    }
    label, geography, dataset = names[threat_id]
    if geographic_rows:
        geography = geographic_rows[0].geography.name
        label = f"{threat_id.title()} surveillance in {geography}"
    subject = {
        "label": label,
        "disease": threat_id,
        "geography": geography,
        "dataset": dataset,
        "reporting_cutoff": str(cutoff) if cutoff else None,
    }
    latest_rows = [
        o for o in scoped_rows if (o.reporting_period_end or o.event_date) == cutoff
    ]
    if not latest_rows:
        return AskResponse(answer='No compatible verified observations are available for this reporting cutoff. Select the latest evidence view.', evidence_ids=[], declined=True, subject=subject)
    if threat_id == "measles" and not geographic_rows:
        latest_rows = [
            o
            for o in item.observations
            if o.indicator in {"reported_measles_cases_global", "countries_reporting"}
        ]
    metric_labels = {
        "confirmed_cases": "Confirmed cases",
        "reported_measles_cases_global": "Provisional cases",
        "reported_cholera_awd_cases": "Reported cases",
        "reported_deaths": "Deaths",
        "crude_cfr": "Crude reported CFR",
        "affected_health_zones": "Affected health zones",
        "affected_provinces": "Affected provinces",
        "countries_reporting": "Reporting countries",
        "affected_countries": "Affected countries",
        "cases_per_100k": "Cases per 100,000",
        "recent_reported_cases": "Recent-period cases",
        "recent_reported_deaths": "Recent-period deaths",
        "recent_crude_cfr": "Recent-period CFR",
        "monthly_cases_change": "Monthly cases change",
        "monthly_deaths_change": "Monthly deaths change",
    }
    metrics = [
        {
            "label": metric_labels[o.indicator],
            "value": o.value,
            "unit": o.unit,
            "evidence_id": o.observation_id,
        }
        for o in latest_rows
        if o.indicator in metric_labels
    ]
    if threat_id == "cholera" and not geographic_rows:
        metrics += [
            {
                "label": "Crude reported CFR",
                "value": m.value,
                "unit": m.unit,
                "evidence_id": m.input_observation_ids[0],
            }
            for m in item.derived_metrics
            if m.value is not None
        ]
    if threat_id == "ebola":
        values = {metric["label"]: metric for metric in metrics}
        if not all(key in values for key in ("Confirmed cases", "Deaths")):
            return AskResponse(answer="The selected evidence does not resolve both case and death counts. Inspect the source observations and conflicts; missing values are not zero.", evidence_ids=[o.observation_id for o in latest_rows], declined=True, subject=subject, metrics=metrics)
        cases = int(values.get("Confirmed cases", {}).get("value", 0))
        deaths = int(values.get("Deaths", {}).get("value", 0))
        cfr = values.get("Crude reported CFR", {}).get("value")
        zones = values.get("Affected health zones", {}).get("value")
        opening = (
            f"The current {label} in the {geography} remains a major public-health event. "
            f"WHO reports {cases:,} confirmed cases and {deaths:,} deaths through {cutoff}"
            f"{f', corresponding to a crude reported CFR of {cfr:.1f}%' if cfr is not None else ''}."
            f"{f' Transmission has been reported across {int(zones)} health zones.' if zones is not None else ''}"
        )
    elif geographic_rows:
        primary = next(
            (
                value
                for value in metrics
                if value["label"] in {"Reported cases", "Provisional cases", "Confirmed cases"}
            ),
            metrics[0] if metrics else None,
        )
        opening = f"{label} is represented by the latest compatible WHO country observation through {cutoff}."
        if primary:
            opening += f" The reported {primary['label'].lower()} value is {primary['value']:,.0f} {primary['unit']}."
    elif threat_id == "measles":
        opening = f"The selected view summarizes {label} for the latest sufficiently complete period ending {cutoff}. {item.summary}"
    else:
        opening = f"The selected view summarizes {label} through {cutoff}. {item.summary}"
    changed = None
    if "changed" in q:
        if item.delta and threat_id == "ebola":
            changed = f"Compared with the preceding compatible WHO report, confirmed cases increased by {int(item.delta['confirmed_cases']):,}, from {int(item.delta['previous_cases']):,} to {int(item.delta['current_cases']):,}."
        else:
            changed = "Fynura has the current verified observation but does not yet have a compatible preceding observation for a reliable change calculation."
        opening = f"{opening} {changed}"
    unique_sources = {}
    for observation in latest_rows or [latest]:
        unique_sources[str(observation.source_url)] = {
            "organization": "World Health Organization",
            "title": dataset,
            "published": str(observation.publication_date)
            if observation.publication_date
            else None,
            "reporting_cutoff": str(observation.reporting_period_end or observation.event_date)
            if observation.reporting_period_end or observation.event_date
            else None,
            "url": str(observation.source_url),
            "source_id": observation.source_id,
        }
    if "cite" in q or "which source" in q:
        opening = f"For the selected {label}, the recommended primary citation is the {dataset} published by the World Health Organization."
    if any(name in q for name in ("africa cdc", "ecdc", "paho", "compare who", "sources agree")):
        opening = f"Only WHO currently contributes verified observations to this {label} view. Configured or candidate authorities are not counted as corroboration, and overlapping reports are never summed."
    refs = sorted({o.observation_id for o in latest_rows})
    return AskResponse(
        answer=opening,
        evidence_ids=refs,
        visualization_available=bool(select_visualizations(item)),
        subject=subject,
        metrics=metrics,
        what_changed=changed,
        limitations=item.limitations,
        sources=list(unique_sources.values()),
        confidence=item.confidence_details
        or {"score": item.evidence_confidence, "level": "UNSPECIFIED", "model": "legacy"},
    )


@app.post("/api/watches", response_model=Watch)
def create_watch(watch: Watch):
    return repo.save_watch(watch)


@app.get("/api/watches")
def watches():
    return list(repo.watches.values())


@app.delete("/api/watches/{watch_id}")
def delete_watch(watch_id: str):
    if watch_id not in repo.watches:
        raise HTTPException(404, "Watch not found")
    repo.watches[watch_id].active = False
    return repo.watches[watch_id]
