# Fynura source-diversification update

**Date:** 22 October 2026

## Production correction

The Nigeria Ebola preparedness statement dated 6 October 2026 was superseded by an official report of one imported laboratory-confirmed case on 20 October. Fynura now retrieves the WHO emergency country table in addition to the Disease Outbreak News sequence. The table supplies separate, date-labelled country observations and currently covers the Democratic Republic of the Congo, Uganda, France, Kenya and Nigeria.

The application does not sum these country totals. Each observation retains its own geography, reporting cutoff, case definition, source URL and retrieval time. A newer confirmed Nigeria observation prevents the older NCDC preparedness advisory from being presented as the current country status.

The latest-evidence panel now presents Ebola as a set of country reports rather than a single DRC row. This makes the regional spread visible while preserving DRC as the outbreak trajectory used for longitudinal comparison.

## Source architecture

Fynura should use a layered authority model:

1. **National health authorities:** NCDC, Kenya Ministry of Health, Uganda Ministry of Health and other official country publishers for the earliest country-level statements and aggregate reports.
2. **Regional authorities:** Africa CDC and WHO regional offices for cross-border synthesis, response coordination and regional bulletins.
3. **WHO global sources:** emergency tables, Disease Outbreak News, weekly epidemiological records and standardized surveillance datasets for comparable international reporting.
4. **Historical datasets:** WHO-derived OWID series for historical context only, clearly separated from current surveillance.

Sources are compared only when geography, definition, interval and cutoff are compatible. National reports are not automatically replaced by WHO, and records from multiple authorities are not summed.

## Nigeria NCDC integration status

The repository already contains:

- an allowlisted official NCDC weekly-report index and PDF retriever;
- checksum deduplication and document metadata storage;
- a reviewed aggregate-table normalization boundary;
- national, state and 774-LGA crosswalk validation;
- fixtures for incident and year-to-date cholera and measles values.

The NCDC document pipeline is intentionally not labelled as an operational epidemiological feed yet. The remaining requirement is a report-specific PDF table extractor with regression fixtures across changing report layouts, followed by automated QA that prevents incident and cumulative values from being mixed. Until that gate passes, Fynura may retrieve and record documents but must not publish unreviewed counts.

## Recommended integration order

1. Operationalize NCDC national weekly aggregate tables for cholera and measles.
2. Add Kenya Ministry of Health Ebola situation reports and WHO Kenya releases.
3. Add Uganda Ministry of Health Ebola situation reports.
4. Add Africa CDC outbreak bulletins as a regional comparison source.
5. Add explicit freshness and disagreement indicators when national and international sources have different cutoffs.

Every adapter must retain the source document, checksum, table or paragraph location, reporting cutoff, publication date, retrieval time and parser version. Failed retrieval or parsing must preserve the last verified snapshot and display the failure separately from epidemiological activity.
