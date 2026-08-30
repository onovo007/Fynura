import io
from datetime import date

import openpyxl
import pytest

from backend.sources.measles_history import eligibility_report, extract_history, month_label


def workbook(rows):
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "WEB"
    sheet.append(["Region", "Country", "ISO3", "Year", "Month", "Measles total"])
    for row in rows:
        sheet.append(row)
    output = io.BytesIO()
    book.save(output)
    return output.getvalue()


def history(count=60):
    return [["AFR", "Example", "AAA", *map(int, month_label(2020*12+i).split("-")), 9+i%3]
            for i in range(count)]


def test_history_preserves_all_months_zero_and_missing():
    rows = history()
    rows[0][-1] = 0
    rows[1][-1] = None
    snapshot = extract_history(workbook(rows), "2025-01-01T00:00:00Z")
    points = snapshot["countries"]["AAA"]
    assert len(points) == 60
    assert points[0]["value"] == 0
    assert points[1]["value"] is None
    assert points[0]["source_rows"] == [2]
    assert snapshot["sha256"] in points[0]["evidence_id"]


def test_duplicates_not_summed_and_conflicts_withheld():
    rows = history()
    rows.extend([rows[0][:], rows[1][:-1]+[500]])
    snapshot = extract_history(workbook(rows), "now")
    points = snapshot["countries"]["AAA"]
    assert points[0]["value"] == 9
    assert points[0]["duplicate_rows"] == 1
    assert points[1]["status"] == "conflict"
    assert points[1]["value"] is None


def test_complete_data_is_only_candidate_not_live_signal():
    snapshot = extract_history(workbook(history()), "now")
    report = eligibility_report(snapshot, date(2025, 1, 15), coverage_floor=1)
    row = report["countries"][0]
    assert row["complete_run_ending_at_cutoff"] == 60
    assert report["candidate_count"] == 1
    assert row["cusum_eligibility"] == "LIMITED"
    assert row["forecast_eligibility"] == "NOT VALIDATED"
    assert not report["live_cusum_enabled"]


def test_missing_month_invalid_counts_and_revisions_block_screen():
    rows = history()
    previous = extract_history(workbook(rows), "before")
    rows[2][-1] = -1
    rows[3][-1] = 22
    rows.pop(10)
    snapshot = extract_history(workbook(rows), "after")
    report = eligibility_report(snapshot, date(2025, 1, 15), previous, coverage_floor=1)
    row = report["countries"][0]
    assert row["missing_periods"] == ["2020-11"]
    assert row["invalid_or_missing_value_periods"] == ["2020-03"]
    assert len(row["revisions"]) == 2
    assert row["removed_periods"] == ["2020-11"]
    assert report["candidate_count"] == 0


def test_schema_drift_fails_closed():
    book = openpyxl.Workbook()
    book.active.title = "WEB"
    book.active.append(["Country", "Unexpected total"])
    content = io.BytesIO()
    book.save(content)
    with pytest.raises(ValueError, match="schema changed"):
        extract_history(content.getvalue(), "now")


def test_current_month_excluded_and_stale_reference_blocks():
    snapshot = extract_history(workbook(history(61)), "now")
    report = eligibility_report(snapshot, date(2025, 1, 15), coverage_floor=1)
    assert report["reference_cutoff"] == "2024-12"
    stale = eligibility_report(snapshot, date(2026, 1, 15), coverage_floor=1)
    assert stale["candidate_count"] == 0
