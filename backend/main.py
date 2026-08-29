import asyncio
import logging
import re
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from backend.config import get_settings
from backend.models.domain import AskRequest, AskResponse, Watch
from backend.repositories import MemoryRepository
from backend.services.pipeline import Pipeline
from backend.services.source_registry import network_summary, sources
from backend.services.visualization import select_visualizations

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
repo = MemoryRepository()
pipeline = Pipeline(repo)
settings = get_settings()
ROOT = Path(__file__).resolve().parents[1]
app.mount("/static", StaticFiles(directory=ROOT / "frontend"), name="static")


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(ROOT / "frontend" / "index.html")


@app.get("/docs", include_in_schema=False)
def docs_home():
    return FileResponse(ROOT / "frontend" / "docs.html")


@app.get("/welcome", include_in_schema=False)
def welcome():
    return FileResponse(ROOT / "frontend" / "welcome.html")


@app.get("/privacy", include_in_schema=False)
def privacy():
    return FileResponse(ROOT / "frontend" / "privacy.html")


class OnboardingRequest(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    country: str = Field(min_length=2, max_length=80)
    privacy_acknowledged: bool
    stakeholder_role: str | None = None

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
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z][A-Za-z .,'()-]{1,79}", value):
            raise ValueError("Select a valid country")
        return value


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
        allowed = {"user_registered", "session_started", "threat_viewed", "ask_fynura_submitted", "evidence_opened", "chart_viewed", "map_viewed", "visual_downloaded", "citation_copied", "watch_created", "brief_generated", "docs_viewed"}
        if value not in allowed:
            raise ValueError("Unsupported analytics event")
        return value


@app.get("/api/product/config")
def product_config():
    return {"onboarding_required": settings.fynura_onboarding_required, "privacy_notice_version": settings.fynura_privacy_notice_version, "authentication": "lightweight_onboarding"}


@app.post("/api/onboarding", status_code=201)
def onboard(request: OnboardingRequest):
    if not request.privacy_acknowledged:
        raise HTTPException(422, "Privacy Notice and Responsible Use acknowledgement is required")
    now = datetime.now(UTC).isoformat()
    existing = next((u for u in repo.users.values() if u["email"] == request.email), None)
    user = existing or {"user_id": f"usr_{uuid4().hex}", "email": request.email, "created_at": now, "account_status": "active"}
    user.update({"country": request.country, "last_active_at": now, "stakeholder_role": request.stakeholder_role, "privacy_notice_version": settings.fynura_privacy_notice_version, "privacy_acknowledged_at": now})
    repo.users[user["user_id"]] = user
    return {"user_id": user["user_id"], "country": user["country"], "stakeholder_role": user["stakeholder_role"], "privacy_notice_version": user["privacy_notice_version"]}


@app.post("/api/events", status_code=202)
def record_event(event: AnalyticsEvent):
    payload = event.model_dump()
    payload.update({"event_id": f"evt_{uuid4().hex}", "timestamp": datetime.now(UTC).isoformat()})
    repo.events.append(payload)
    return {"accepted": True}


def require_owner(x_fynura_owner: str | None) -> None:
    if not settings.fynura_owner_email or x_fynura_owner != settings.fynura_owner_email:
        raise HTTPException(403, "Owner authorization required")


@app.get("/api/admin/overview")
def admin_overview(x_fynura_owner: str | None = Header(default=None)):
    require_owner(x_fynura_owner)
    countries = Counter(u["country"] for u in repo.users.values())
    features = Counter(e.get("feature") for e in repo.events if e.get("feature"))
    threats = Counter(e.get("threat_id") for e in repo.events if e.get("threat_id"))
    return {"total_users": len(repo.users), "countries": dict(countries), "features": dict(features), "threats": dict(threats), "event_count": len(repo.events)}


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
        try:
            if threat_id == "measles":
                return await pipeline.assess_measles()
            if threat_id == "ebola":
                return await pipeline.assess_ebola()
            return await pipeline.assess_cholera()
        except Exception:
            logging.getLogger("fynura.bootstrap").exception(
                "initial intelligence refresh failed", extra={"threat_id": threat_id}
            )
            return repo.latest_assessment(threat_id)

    values = await asyncio.gather(*(ensure(x) for x in ("measles", "ebola", "cholera")))
    return {item.threat_id: item for item in values if item}


@app.post("/api/threats/{threat_id}/assess")
async def assess(threat_id: str):
    if threat_id not in {"measles", "ebola", "cholera"}:
        raise HTTPException(404, "Unknown threat")
    try:
        if threat_id == "measles":
            return await pipeline.assess_measles()
        if threat_id == "ebola":
            return await pipeline.assess_ebola()
        return await pipeline.assess_cholera()
    except Exception as exc:
        raise HTTPException(502, str(exc)) from exc


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
    if not request.threat_id:
        return AskResponse(
            answer="Choose a threat so I can retrieve its structured evidence.",
            evidence_ids=[],
            declined=True,
        )
    item = repo.latest_assessment(request.threat_id)
    if not item:
        return AskResponse(
            answer="Fynura has no stored assessment for that threat yet. Refresh its evidence first.",
            evidence_ids=[],
            declined=True,
        )
    q = request.question.lower()
    if "cite" in q or "which source" in q:
        observations = sorted(
            item.observations,
            key=lambda o: (
                o.reporting_period_end or o.event_date or o.retrieved_at.date(),
                o.publication_date or o.retrieved_at.date(),
            ),
        )
        selected = observations[-1]
        return AskResponse(
            answer=f"For this {item.threat_id} claim, cite the World Health Organization source supporting the selected observation. Reporting cutoff: {selected.reporting_period_end or selected.event_date}. Published: {selected.publication_date or 'not stated in the source metadata'}. Source: {selected.source_url}",
            evidence_ids=[selected.observation_id],
            visualization_available=bool(select_visualizations(item)),
        )
    if any(name in q for name in ("africa cdc", "ecdc", "paho", "compare who", "sources agree")):
        named = [s for s in sources() if s["display_name"].lower() in q]
        status = (
            "; ".join(f"{s['display_name']}: {s['integration_status']}" for s in named)
            or "Only WHO currently contributes verified observations for this view"
        )
        return AskResponse(
            answer=f"{status}. Fynura does not count configured or candidate authorities as corroborating evidence, and it never sums overlapping reports. The current canonical {item.threat_id} view is supported by WHO; no independent multi-source consensus is claimed.",
            evidence_ids=sorted({eid for c in item.claims for eid in c.evidence_ids}),
        )
    if any(
        word in q
        for word in (
            "case",
            "death",
            "changed",
            "latest",
            "source",
            "confidence",
            "happening",
            "situation",
            "known",
            "uncertain",
            "limitation",
            "report",
            "outbreak",
        )
    ):
        refs = sorted({eid for claim in item.claims for eid in claim.evidence_ids})
        return AskResponse(
            answer=(
                f"{item.summary} Evidence confidence is {item.evidence_confidence:.0%}. "
                f"{item.claims[0].text}"
            ),
            evidence_ids=refs,
            visualization_available=bool(select_visualizations(item)),
        )
    return AskResponse(
        answer="The structured evidence currently stored does not support a reliable answer to that question.",
        evidence_ids=[],
        declined=True,
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
