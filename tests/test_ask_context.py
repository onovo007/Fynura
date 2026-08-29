from datetime import UTC, date, datetime

from fastapi.testclient import TestClient

from backend.evidence import calculate_confidence, fuse_observations
from backend.main import app, repo
from backend.models.domain import Assessment, Claim, Geography, Observation

client = TestClient(app)


def seed(threat_id, indicator, value, geography):
    item = Observation(
        threat_id=threat_id, indicator=indicator, value=value, unit="persons",
        geography=Geography(name=geography, level="global" if geography == "Global" else "country"),
        reporting_period_end=date(2026, 8, 20), retrieved_at=datetime(2026, 8, 29, tzinfo=UTC),
        source_id=f"who_{threat_id}", source_url=f"https://who.int/{threat_id}",
        source_type="international_health_authority", case_definition="fixture",
        extraction_method="fixture", extraction_confidence=.99, supporting_excerpt="fixture",
        run_id=f"run-{threat_id}",
    )
    groups = fuse_observations([item])
    confidence = calculate_confidence([item], groups)
    repo.save_assessment(Assessment(
        run_id=f"run-{threat_id}", threat_id=threat_id, geography=item.geography,
        evidence_cutoff=item.retrieved_at, headline=f"{threat_id} fixture",
        summary=f"Current verified {threat_id} evidence reports {int(value):,} persons.",
        claims=[Claim(text="fixture", evidence_ids=[item.observation_id])], observations=[item],
        evidence_groups=groups, evidence_confidence=confidence["score"],
        confidence_details=confidence, limitations=["Fixture limitation."], freshness="fresh",
    ))


def ask(question, threat_id):
    return client.post("/api/ask", json={
        "question": question,
        "threat_id": "ebola" if threat_id != "ebola" else "measles",
        "context": {"threat_id": threat_id, "disease": threat_id, "geography": "Global"},
        "stakeholder_mode": "public_health_professional",
    }).json()


def test_context_envelope_isolates_sequential_threats():
    seed("ebola", "confirmed_cases", 100, "DRC")
    seed("measles", "reported_measles_cases_global", 200, "Global")
    seed("cholera", "reported_cholera_awd_cases", 300, "Global")
    for first, second in (("ebola", "measles"), ("measles", "cholera"), ("cholera", "ebola")):
        assert ask("What's happening?", first)["subject"]["disease"] == first
        assert ask("What's happening?", second)["subject"]["disease"] == second


def test_what_changed_does_not_invent_comparison():
    seed("measles", "reported_measles_cases_global", 200, "Global")
    result = ask("What changed?", "measles")
    assert "does not yet have a compatible preceding observation" in result["what_changed"]
