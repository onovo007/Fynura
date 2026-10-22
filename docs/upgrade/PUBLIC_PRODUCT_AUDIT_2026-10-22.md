# Fynura public product audit — 22 October 2026

## Routes reviewed in production

The authenticated production experience was reviewed as a user across Monitor, Verify, Detect, Advise and Learn. The audit checked navigation, information hierarchy, filter behavior, evidence traceability, chat ergonomics and public-facing language.

## Changes in this release

- Advise now uses a focused, single-column conversation with a persistent composer, a clear New chat action and four useful starter questions.
- The duplicated Advise introduction was reduced to one concise purpose statement.
- Answers remain concise by default. Sources are grouped into public-health authorities/government and supporting research/reporting.
- Two low-quality domains observed in live testing are excluded from search grounding. Kenya and Uganda health ministries, NCDC, NIH and NCBI are recognized as authoritative publishers.
- Monitor cards now show reporting freshness and whether a figure comes from one reporting authority or agreement across multiple authorities.
- The full epidemiological table is collapsed by default, preserving access without making the primary workflow excessively long.
- Workspace summaries use shorter, task-oriented language.

## Operational source position

- WHO structured surveillance remains operational and supplies current multi-country Ebola observations.
- Kenya Ministry of Health and Uganda Ministry of Health are now explicitly registered as allowlisted national authorities for live research and structured-feed validation.
- Nigeria NCDC weekly reports remain under validation: document discovery, checksums and reviewed normalization are available, but automated PDF-to-observation publication remains disabled until report-specific extraction passes regression and epidemiological review.
- Africa CDC remains a planned structured adapter. Its publications can support live research, but they are not presented as an operational structured feed.

This distinction is intentional: a searchable official page is not labeled as an operational surveillance adapter until retrieval, parsing, provenance and regression checks all pass.
