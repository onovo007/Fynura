"""Retrospective validation gates for contextual evidence."""

from collections import Counter
from datetime import date

from backend.models.contextual import ContextObservation


def validate_batch(rows: list[ContextObservation], pilot_iso3: set[str]) -> dict:
    failures = []
    seen = set()
    for row in rows:
        key = (row.source_id, row.context_type, row.geography_code, row.reference_end, row.assessment_round)
        if key in seen:
            failures.append({"code": "duplicate", "record": key})
        seen.add(key)
        if row.geography_code[:3] not in pilot_iso3:
            failures.append({"code": "outside_pilot", "record": key})
        if row.validation_status == "approved":
            failures.append({"code": "premature_approval", "record": key})
    return {
        "records": len(rows), "sources": dict(Counter(row.source_id for row in rows)),
        "geographies": sorted({row.geography_code[:3] for row in rows}),
        "failures": failures, "passed": not failures,
    }


def retrospective_window(rows: list[ContextObservation], event_date: date, days: int = 28) -> list[ContextObservation]:
    """Return contemporaneous context only; this does not estimate causal or predictive effect."""
    return [row for row in rows if 0 <= (event_date - row.reference_end).days <= days]

