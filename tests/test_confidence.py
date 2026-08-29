from datetime import UTC, date, datetime

from backend.evidence import calculate_confidence, fuse_observations
from backend.models.domain import Geography, Observation


def observation(value=10, source="who", cutoff=date(2026, 8, 20), excerpt="fixture"):
    return Observation(
        threat_id="ebola",
        indicator="confirmed_cases",
        value=value,
        unit="persons",
        geography=Geography(name="DRC", level="country", code="COD"),
        reporting_period_end=cutoff,
        publication_date=cutoff,
        retrieved_at=datetime(2026, 8, 29, tzinfo=UTC),
        source_id=source,
        source_url=f"https://example.org/{source}",
        source_type="international_health_authority",
        case_definition="confirmed",
        extraction_method="fixture",
        extraction_confidence=0.99,
        supporting_excerpt=excerpt,
        run_id="test",
    )


def score(items):
    return calculate_confidence(items, fuse_observations(items))["score"]


def test_stale_evidence_reduces_confidence():
    assert score([observation()]) > score([observation(cutoff=date(2025, 1, 1))])


def test_independent_agreement_improves_confidence():
    assert score([observation(source="who"), observation(source="national")]) > score(
        [observation()]
    )


def test_unresolved_conflict_reduces_confidence():
    agreement = [observation(source="who"), observation(source="national")]
    conflict = [observation(10, "who"), observation(12, "national")]
    assert score(conflict) < score(agreement)


def test_missing_provenance_reduces_confidence():
    assert score([observation()]) > score([observation(excerpt="")])
