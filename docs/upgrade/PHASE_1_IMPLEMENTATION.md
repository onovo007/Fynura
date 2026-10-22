# Phase 1 — Nigeria NCDC national surveillance foundation

## Delivered locally

1. Registered Nigeria NCDC as `monitored` with `operational: false`, official report routes, permission basis, cadence, parser version and QA status.
2. Added typed observation fields for report provenance, interval type, case status, revision lineage and QA.
3. Added `NCDCWeeklyReportAdapter`, which accepts reviewed normalized CSV derived from an official report and rejects duplicate observation keys.
4. Added a regression fixture for NCDC Weekly Epidemiological Report Volume 16 No. 22 (Week 22, 25–31 May 2026). The fixture preserves incident and year-to-date values as separate observations and cites page/table locations.
5. Added a 36-state-plus-FCT crosswalk and an explicit LGA activation gate.
6. Added `GET /api/countries/nigeria/availability`, which reports validation status without presenting unvalidated counts.

## Go/no-go gate for live operation

NCDC remains non-operational until all conditions pass:

- retrieve through an approved official route with bounded retries and request budget;
- verify content type, document checksum and issue metadata;
- extract report tables without OCR ambiguity or send exceptions to human review;
- validate state/LGA names against NBS codes and reject ambiguous matches;
- compare revised releases without double counting;
- pass fixture, parser-failure, stale-source and last-known-good tests;
- complete epidemiological sign-off and public wording review.

## Reproducibility

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_ncdc_weekly.py tests/test_nigeria_availability.py tests/test_source_registry.py
```

Rollback is additive: remove the NCDC registry record, endpoint, adapter and new optional model fields. Existing WHO data and routes are unchanged.
