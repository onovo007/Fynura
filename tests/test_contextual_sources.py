import json
from datetime import UTC, date, datetime
from pathlib import Path

import pytest

from backend.services.contextual_registry import (
    contextual_licences,
    contextual_sources,
    validate_contextual_registry,
)
from backend.services.contextual_validation import retrospective_window, validate_batch
from backend.sources.iom_dtm import PILOT_ISO3, IOMDTMAdapter
from backend.sources.undesa_migrant_stock import UNDESAMigrantStockAdapter

FIXTURES = Path(__file__).parent / "fixtures"


def test_contextual_registry_is_non_public_and_non_operational():
    validate_contextual_registry()
    assert all(not row["operational"] and not row["public"] for row in contextual_sources())
    assert all(not item.public_display_allowed for item in contextual_licences().values())


def test_dtm_fixture_is_filtered_to_pilot_and_quarantined():
    records = json.loads((FIXTURES / "iom_dtm_v3_pilot.json").read_text())
    rows = IOMDTMAdapter().parse_records(
        records, source_url="https://api.dtm.iom.int/v3/assessments",
        retrieved_at=datetime(2026, 10, 22, tzinfo=UTC),
    )
    assert {row.geography_code[:3] for row in rows} == PILOT_ISO3
    assert all(row.validation_status == "quarantined" for row in rows)
    assert all(any("does not establish disease transmission" in note for note in row.limitations) for row in rows)
    assert validate_batch(rows, PILOT_ISO3)["passed"] is True


def test_dtm_rejects_non_iom_endpoint_and_missing_fields():
    with pytest.raises(ValueError, match="approved IOM"):
        IOMDTMAdapter().parse_records([], source_url="https://example.com/v3")
    with pytest.raises(ValueError, match="lacks"):
        IOMDTMAdapter().parse_records(
            [{"iso3": "KEN", "assessmentDate": "2026-01-01"}],
            source_url="https://api.dtm.iom.int/v3/assessments",
        )


def test_undesa_fixture_is_structural_context_not_movement():
    rows = UNDESAMigrantStockAdapter().parse_reviewed_csv(
        (FIXTURES / "undesa_migrant_stock_reviewed.csv").read_text()
    )
    assert {row.geography_code for row in rows} == PILOT_ISO3
    assert all(row.context_type == "migrant_stock" for row in rows)
    assert all(any("not a current movement flow" in note for note in row.limitations) for row in rows)


def test_retrospective_window_is_contemporaneous_not_predictive():
    records = json.loads((FIXTURES / "iom_dtm_v3_pilot.json").read_text())
    rows = IOMDTMAdapter().parse_records(records, source_url="https://api.dtm.iom.int/v3/assessments")
    assert len(retrospective_window(rows, date(2026, 10, 20), 28)) == 4
    assert retrospective_window(rows, date(2026, 12, 1), 28) == []

