# Fynura upgrade baseline audit

Audit date: 21 October 2026

## Verified baseline

- FastAPI application on Cloud Run with Firebase authentication, Firestore repositories, Cloud Scheduler refresh, Gemini/Vertex configuration, Leaflet maps and static frontend assets.
- WHO is the only independently operational authority in the visible source registry. OWID supplies WHO-derived historical series and is not independent corroboration.
- Structured production paths currently cover measles, Ebola and cholera.
- The evidence model already retains source URL, reporting period, publication and retrieval dates, geography, case definition, extraction method and run identifier.
- Existing interfaces include global intelligence, historical evidence, Ask Fynura, source explorer, map, early-signal review and administrative analytics.

## Gaps confirmed against the upgrade specification

- No national-authority adapter was operational.
- No explicit observation fields existed for interval type, case status, outbreak identifier, document checksum/page/table, revision lineage or QA flags.
- Source registry records did not consistently carry permission basis, licence, parser version, last successful observation or QA status.
- Nigeria state/LGA availability and source status were not represented through a dedicated API.
- Existing tests collected successfully, but the first integrated Ask Fynura test waits on the model/provider path in this local environment. The new Phase 1 tests are isolated from external providers.
- Forecasting, event-based news, mobility and automatic national-source ingestion remain later gated phases.

## Architectural decision

Phase 1 adds a reviewed report-table normalization boundary. It does not scrape private endpoints or claim that NCDC is a live feed. NCDC becomes operational only after live document retrieval, checksum verification, parser regression checks, epidemiological review and last-known-good fallback tests pass.
