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
    threat_id = request.context.threat_id if request.context else request.threat_id
    if not threat_id:
        available = [repo.latest_assessment(x) for x in ("ebola", "measles", "cholera")]
        available = [item for item in available if item]
        if not available:
            return AskResponse(
                answer="Fynura is monitoring Ebola, Measles and Cholera, but no verified assessments are loaded in this process yet.",
                evidence_ids=[],
                declined=True,
                subject={"label": "GLOBAL INTELLIGENCE", "geography": "Global"},
            )
        answer = "Fynura is currently monitoring three demonstration threats: Ebola, Measles and Cholera. " + " ".join(item.summary for item in available)
        return AskResponse(
            answer=answer,
            evidence_ids=sorted({eid for item in available for claim in item.claims for eid in claim.evidence_ids}),
            subject={"label": "GLOBAL INTELLIGENCE", "geography": "Global"},
            limitations=["Coverage is demonstrative and source reporting periods differ across threats."],
        )
    item = repo.latest_assessment(threat_id)
    if not item:
        return AskResponse(
            answer=f"Fynura has no stored assessment for {threat_id} yet. Refresh that threat's evidence first.",
            evidence_ids=[],
            declined=True,
            subject={"label": threat_id.upper(), "geography": request.context.geography if request.context else "Configured scope"},
        )
    q = request.question.lower()
    latest = max(item.observations, key=lambda o: o.reporting_period_end or o.event_date or o.retrieved_at.date())
    cutoff = request.context.reporting_cutoff if request.context and request.context.reporting_cutoff else latest.reporting_period_end or latest.event_date
    names = {
        "ebola": ("Bundibugyo virus disease outbreak", "Democratic Republic of the Congo", "WHO Disease Outbreak News"),
        "measles": ("WHO provisional monthly measles surveillance", "Global", "WHO provisional measles and rubella data"),
        "cholera": ("global cholera and acute watery diarrhoea surveillance", "Global", "WHO Weekly Epidemiological Record"),
    }
    label, geography, dataset = names[threat_id]
    subject = {"label": label, "disease": threat_id, "geography": geography, "dataset": dataset, "reporting_cutoff": str(cutoff) if cutoff else None}
    latest_rows = [o for o in item.observations if (o.reporting_period_end or o.event_date) == cutoff]
    if threat_id == "measles":
        latest_rows = [o for o in item.observations if o.indicator in {"reported_measles_cases_global", "countries_reporting"}]
    metric_labels = {"confirmed_cases": "Confirmed cases", "reported_measles_cases_global": "Provisional cases", "reported_cholera_awd_cases": "Reported cases", "reported_deaths": "Deaths", "crude_cfr": "Crude reported CFR", "affected_health_zones": "Affected health zones", "affected_provinces": "Affected provinces", "countries_reporting": "Reporting countries", "affected_countries": "Affected countries"}
    metrics = [{"label": metric_labels[o.indicator], "value": o.value, "unit": o.unit, "evidence_id": o.observation_id} for o in latest_rows if o.indicator in metric_labels]
    if threat_id == "cholera":
        metrics += [{"label": "Crude reported CFR", "value": m.value, "unit": m.unit, "evidence_id": m.input_observation_ids[0]} for m in item.derived_metrics if m.value is not None]
    if threat_id == "ebola":
        values = {metric["label"]: metric for metric in metrics}
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
            "published": str(observation.publication_date) if observation.publication_date else None,
            "reporting_cutoff": str(observation.reporting_period_end or observation.event_date) if observation.reporting_period_end or observation.event_date else None,
            "url": str(observation.source_url),
            "source_id": observation.source_id,
        }
    if "cite" in q or "which source" in q:
        opening = f"For the selected {label}, the recommended primary citation is the {dataset} published by the World Health Organization."
    if any(name in q for name in ("africa cdc", "ecdc", "paho", "compare who", "sources agree")):
        opening = f"Only WHO currently contributes verified observations to this {label} view. Configured or candidate authorities are not counted as corroboration, and overlapping reports are never summed."
    refs = sorted({eid for claim in item.claims for eid in claim.evidence_ids})
    return AskResponse(
        answer=opening,
        evidence_ids=refs,
        visualization_available=bool(select_visualizations(item)),
        subject=subject,
        metrics=metrics,
        what_changed=changed,
        limitations=item.limitations,
        sources=list(unique_sources.values()),
        confidence=item.confidence_details or {"score": item.evidence_confidence, "level": "UNSPECIFIED", "model": "legacy"},
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
