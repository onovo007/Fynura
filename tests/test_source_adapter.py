from datetime import UTC, datetime

from backend.models.domain import Geography, SourceCandidate
from backend.sources.cdc_measles import CDCMeaslesAdapter


def test_fixture_extracts_without_network():
    c = SourceCandidate(source_id="cdc_measles_cases", url="https://www.cdc.gov/measles/data-research/index.html", publisher="CDC", threat_id="measles", geography=Geography(name="United States", level="country"), source_type="national_health_authority", retrieved_at=datetime.now(UTC))
    result = CDCMeaslesAdapter().extract(c, "As of August 20, 2026, a total of 1,234 measles cases were reported.", "run")
    assert result[0].value == 1234 and result[0].reporting_period_end.isoformat() == "2026-08-20"

