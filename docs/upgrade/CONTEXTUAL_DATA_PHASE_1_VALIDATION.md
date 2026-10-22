# Contextual data Phase 1 validation protocol

## Release position

IOM DTM and UN DESA context remain non-production and non-public until every release gate passes. They cannot modify canonical disease case, death or outbreak totals.

## Four-country pilot

- Democratic Republic of the Congo (`COD`)
- Kenya (`KEN`)
- Nigeria (`NGA`)
- Uganda (`UGA`)

The retrospective evaluation covers selected Ebola and cholera events. The analysis asks whether a contextual source was available, timely, geographically aligned and useful to an analyst. It does not test whether displacement or migration caused an outbreak.

## Four-week validation

### Week 1: access and provenance

- Confirm the DTM v3 endpoint and response contract from the developer portal.
- Store the subscription key in Google Secret Manager.
- Reconfirm API terms, attribution, rate limits, retention and public-display permissions.
- Download UN DESA data from the official Population Division page and record the exact file checksum, table, licence and retrieval date.

### Week 2: data quality

- Reconcile a sample from each country against the provider portal or publication.
- Validate ISO3, Admin 1 and Admin 2 crosswalks.
- Test duplicates, missing dates, negative values, schema changes, pagination and rate limits.
- Record coverage gaps and assessment-round frequency by country.

### Week 3: retrospective utility

- Preselect Ebola and cholera events without looking at contextual results.
- Retrieve only contextual observations available on or before each event review date.
- Have reviewers score whether context changes a defined surveillance action, improves prioritization, or adds no actionable information.
- Prohibit causal and predictive claims.

### Week 4: safety and operational review

- Review privacy, small-area sensitivity and vulnerable-population language.
- Test expired credentials, source downtime, delayed releases and malformed records.
- Conduct public-health expert review of every proposed advisory template.
- Produce a signed release decision for each source and use case.

## Public-release gates

1. Written permission or clearly applicable terms allow the intended public display and derived output.
2. No credential, restricted material or person-level record is stored in the repository.
3. Geographic and temporal reconciliation meets the documented acceptance thresholds.
4. Context remains visually and analytically separate from verified disease surveillance.
5. Advisories state the source, reference period, geographic resolution and limitations.
6. A reviewer can reconstruct every contextual statement from its source record.
7. Failure states remove or label stale context without affecting canonical surveillance.

Until approval, `FYNURA_CONTEXTUAL_DATA_ENABLED` remains `false` and both registry entries remain `operational: false`, `public: false`.
