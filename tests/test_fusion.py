from datetime import date

from backend.evidence import fuse_observations
from backend.models.domain import Geography, Observation


def make(value, source, source_type="international_health_authority"):
    return Observation(threat_id="ebola", indicator="confirmed_cases", value=value, unit="persons", geography=Geography(name="Example", level="country"), reporting_period_end=date(2026, 1, 1), publication_date=date(2026, 1, 2), source_id=source, source_url=f"https://example.org/{source}", source_type=source_type, case_definition="confirmed", extraction_method="fixture", extraction_confidence=.99, supporting_excerpt="fixture", run_id="test")
def test_agreement_resolves():
    group = fuse_observations([make(10, "a"), make(10, "b")])[0]
    assert group.status == "resolved" and group.confidence == .95
def test_equal_authority_conflict_is_exposed():
    group = fuse_observations([make(10, "a"), make(12, "b")])[0]
    assert group.status == "conflicted" and group.selected_observation_id is None

