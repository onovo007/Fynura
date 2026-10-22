# Phase 1B — NCDC retrieval and geography validation

## Implemented controls

- The retriever accepts only HTTPS links on `ncdc.gov.ng` or `www.ncdc.gov.ng` and only the official weekly-report PDF route.
- Requests use bounded timeouts, do not follow redirects, verify the PDF content type and magic bytes, and reject documents larger than 20 MiB.
- SHA-256 is the document idempotency key. The Firestore ledger stores source, issue, reporting label, retrieval time, checksum, byte length and parser version; it does not republish the PDF body.
- The NBS crosswalk builder extracts 774 LGA codes from the official GHS Panel 2023–2024 metadata variable and fails if the count or code uniqueness changes.
- LGA matching requires a unique normalized name, with optional state-code context. Ambiguous or unmatched names do not become published geography.

## Publication boundary

This increment remains validation-only. Retrieval success does not convert report tables into observations, make NCDC operational, expose subnational values, or alter production traffic. Those changes require report-specific parser regression tests and epidemiological approval.

## Reproducible checks

```powershell
.\.venv\Scripts\python.exe tools\build_nigeria_lga_crosswalk.py
.\.venv\Scripts\python.exe tools\validate_ncdc_live.py
.\.venv\Scripts\python.exe -m pytest -q tests\test_ncdc_weekly.py tests\test_ncdc_retrieval.py tests\test_nigeria_geography.py
```

Official metadata source: https://microdata.nigerianstat.gov.ng/index.php/catalog/82/variable/V2899

Official weekly-report index: https://www.ncdc.gov.ng/reports/weekly
