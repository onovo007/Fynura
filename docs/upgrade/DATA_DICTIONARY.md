# Surveillance observation data dictionary

The canonical `Observation` model is additive: existing WHO records remain valid and new fields default safely.

| Field group | Fields | Contract |
|---|---|---|
| Identity | `observation_id`, `run_id`, `outbreak_id`, `revision_id`, `supersedes_observation_id` | Immutable observation identity and explicit revision lineage |
| Epidemiology | `threat_id`, `pathogen_or_variant`, `indicator`, `status`, `value`, `unit`, `case_definition` | Source-defined measures; confirmed, suspected and probable are never merged silently |
| Time | `event_date`, `onset_date`, `reporting_period_start`, `reporting_period_end`, `publication_date`, `retrieved_at`, `interval_type` | Incident and cumulative values remain distinct; retrieval freshness is not epidemiological freshness |
| Geography | `geography.name`, `level`, `code`, `source_name`, ISO and WHO region fields | Unknown or absent rows remain missing, never zero; ambiguous names require review |
| Provenance | `source_id`, `source_url`, `source_type`, `document_checksum`, `document_page`, `document_table` | Every normalized report value can be traced to the exact source document location |
| Extraction and QA | `extraction_method`, `extraction_confidence`, `supporting_excerpt`, `qa_flags`, `confidence_rationale`, raw fields | Parser and reviewer decisions remain inspectable |

Canonical selection must compare compatible geography, case definition, status, unit, interval and reporting cutoff. It must not sum overlapping periods or interpret multiple publications as independent confirmation.
