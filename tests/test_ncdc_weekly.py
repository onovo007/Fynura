from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from backend.sources.ncdc_weekly import NCDCWeeklyReportAdapter

FIXTURE = Path(__file__).parent / "fixtures" / "ncdc_week22_2026_normalized.csv"
SOURCE_URL = "https://www.ncdc.gov.ng/themes/common/docs/wers/684_1784724692.pdf"
SOURCE_CHECKSUM = "sha256:de0b05432c1c916e442d0bbde9e31c74f76b9548da95c2b109ec494f65e55a9f"


def extract(content: str | None = None):
    return NCDCWeeklyReportAdapter().extract_csv(
        content if content is not None else FIXTURE.read_text(encoding="utf-8"),
        source_url=SOURCE_URL,
        document_checksum=SOURCE_CHECKSUM,
        publication_date=date(2026, 6, 12),
        retrieved_at=datetime(2026, 10, 21, tzinfo=UTC),
        run_id="fixture-run",
        revision_id="wer-v16-n22-2026",
    )


def test_ncdc_weekly_preserves_incident_and_cumulative_observations():
    observations = extract()
    cholera_confirmed = [
        item for item in observations
        if item.threat_id == "cholera" and item.indicator == "confirmed_cases"
    ]
    assert {(item.value, item.interval_type) for item in cholera_confirmed} == {
        (33, "incident"),
        (188, "cumulative"),
    }
    assert all(item.document_page == 7 for item in cholera_confirmed)
    assert {item.document_table for item in cholera_confirmed} == {"Table 8", "Table 9"}
    assert all(item.document_checksum == SOURCE_CHECKSUM for item in cholera_confirmed)


def test_ncdc_weekly_preserves_explicit_zero_but_skips_missing_value():
    content = FIXTURE.read_text(encoding="utf-8")
    observations = extract(content + "\nmeasles,reported_deaths,,persons,reported,incident,2026-05-25,2026-05-31,Nigeria,country,NGA,8,Table 10,NCDC reported death,Missing example,")
    confirmed = next(item for item in observations if item.threat_id == "measles" and item.indicator == "confirmed_cases")
    assert confirmed.value == 0
    assert len(observations) == 9


def test_ncdc_weekly_rejects_duplicate_normalized_observations():
    line = FIXTURE.read_text(encoding="utf-8").splitlines()[1]
    with pytest.raises(ValueError, match="Duplicate NCDC observation"):
        extract(FIXTURE.read_text(encoding="utf-8") + "\n" + line)
