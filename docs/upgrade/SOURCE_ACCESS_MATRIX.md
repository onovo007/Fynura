# Source access and terms matrix

Checked: 21 October 2026. Status describes Fynura integration, not publisher availability.

| Source | Official access route | Permitted Phase 1 method | Attribution and retention decision | Fynura status | Fallback |
|---|---|---|---|---|---|
| Nigeria NCDC weekly reports | https://www.ncdc.gov.ng/reports/weekly | Public official PDF; reviewed table normalization | Cite report URL, issue, page/table and retrieval time. Store checksums and normalized aggregate facts; do not republish full report bodies. NCDC terms do not state an open-data licence for bulk republication. | Validation | Preserve last known good record; surface retrieval/parser failure |
| Nigeria NCDC disease situation reports | https://ncdc.gov.ng/diseases/sitreps | Public official report discovery; disease-specific parser required | Same provenance controls as weekly reports | Candidate | Weekly report or explicit unavailable state |
| Nigeria NBS administrative codes | https://microdata.nigerianstat.gov.ng/index.php/catalog/82 | Public metadata used for administrative-name/code review | Retain source URL and review date | State crosswalk reviewed; LGA activation gated | Manual ambiguity queue |
| WHO global surveillance | https://www.who.int/ | Existing official XLSX/HTML/report adapters | Existing source-bound storage and citations | Operational | Last known good assessment |
| Africa CDC | https://africacdc.org/ | Discovery only until a stable permitted structured route is verified | No ingestion claim | Candidate | WHO or national authority shown separately |
| ECDC | https://www.ecdc.europa.eu/ | Public surveillance interface pending adapter-specific verification | Do not mark operational before parser and licence review | Configured | Explicit unavailable state |
| PAHO | https://www.paho.org/ | Official documents pending disease-specific adapter | Cite original documents; no fabricated reconciliation | Configured | Explicit unavailable state |
| GDELT Cloud | https://gdeltcloud.com/api-docs | Phase 3 evaluation only | Metadata/event candidates only; never authority confirmation | Planned | Official newsroom/RSS discovery |
| ReliefWeb API | https://apidoc.reliefweb.int/ | Phase 3 evaluation only | Retain source identity and original links; avoid article-body storage | Planned | Official publisher source |
| IOM DTM / HDX HAPI / UNHCR / WorldPop / ACLED | Publisher documentation listed in the master specification | Phase 4+ evaluation only after access, licence, granularity and privacy review | Aggregate contextual data only; no identifiable movement traces | Planned | Disable layer and explain access state |

robots.txt and publisher terms must be rechecked before automating any retrieval. A public web page is not treated as permission to use undocumented endpoints.
