# WHO measles history: data-readiness milestone

Run date: 30 August 2026. This release adds a standalone historical backfill and country eligibility report. It does not change the live dashboard, enable alerts, or enable forecasting.

## Real-source findings

- The downloaded WHO WEB worksheet contains 24,823 rows across 193 country codes, spanning 2012 to 2026.
- The screening reference is June 2026, the latest completed month with at least 120 countries reporting a valid value. This is a coverage heuristic, not proof of finalized reporting.
- 43 countries pass the 60-month data screen; 150 do not. All statistical alerts and forecasts remain withheld.
- USA has 126 consecutive reported months ending at the reference cutoff; India has 150. Both are candidates for method validation, not validated surveillance models.
- Nigeria has 59 of the recent 60 months and lacks the cutoff month. South Africa has 57, Kenya 55, Uganda 59, and the UK 51. These gaps are not filled with zeros.
- Source SHA-256: `ed9469d22503da09ab4444c932512ecd5e7a60b398fb396e0c9d7951ef4dc84b`.

The full country report and CSV are in `docs/measles-history-report.md` and `docs/measles-history-countries.csv`. Detailed JSON, normalized observations and the original workbook are archived locally under `tmp/measles-history`. These local archives are excluded from Git and are not durable cloud storage.

## Reproduce

From the project root, using the installed Python environment:

```powershell
python -m scripts.backfill_measles_history
```

To replay without network access and compare against an earlier snapshot:

```powershell
python -m scripts.backfill_measles_history --input <archived-source.xlsx> --previous <earlier-normalized.json>
```

Each run produces a timestamped report directory. Raw workbooks and normalized snapshots use content-addressed archive directories. Existing raw archives are checksum-verified, not overwritten. Identical input replay reproduced all 193 country results and 43 candidates. Replaying an identical snapshot tests comparison plumbing, not historical revision stability.

## Safeguards

The parser validates named worksheet columns before extraction. It preserves reported zeros, withholds invalid counts and conflicting duplicate values, never sums duplicate rows, and records country-month evidence IDs tied to workbook hash and source row numbers. Blank or absent months remain missing. Country series are never summed into a synthetic global history.

The data screen requires 60 complete recent months, variation, consistent country/region labels, no unresolved source-row errors, and a reasonably recent reference month. Recent value/status revisions or removed periods block readiness when a previous snapshot is supplied. Current or future months are excluded from cutoff selection. The 60-month window and three-month recency limit are explicit screening rules, not statistically validated epidemiological thresholds.

Country codes and stable labels alone cannot establish stable geographic boundaries, diagnostic practices or surveillance coverage. The WHO total's classification label does not establish case-definition invariance over fourteen years. Such changes require source review. Historical publication dates are not inferred from download timestamps.

## CUSUM readiness decision

There is now enough observed history to investigate candidate series, but no defensible production alert is established by this screen. Candidates receive `LIMITED`, not `ELIGIBLE`; forecasts receive `NOT VALIDATED`. The existing CUSUM seasonal safeguard has not been bypassed.

Next methodological stage: pre-specify a country/indicator, evaluate a seasonal count-data baseline, assess overdispersion and reporting breaks, and calibrate alert thresholds on time-separated validation data. USA is a candidate consistent with the original project demonstrator, not selected because it exhibits an attractive signal. Do not choose a model or country after searching for a desired alert.

The current workbook contains today's revised view of past months. It cannot reconstruct what was known on every historical issue date. Any retrospective experiment must disclose that limitation. Prospective snapshots can build a revision archive going forward. A performance claim also requires suitable outcome labels or a clearly bounded validation design.

Cloud Storage archival, scheduled backfill refresh, production history browsing, result-aware Ask integration and forecasting remain subsequent work. No cloud resources or IAM permissions were changed for this milestone.
