# Evidence briefs and infographics

Ask Fynura supports requests containing report, brief, briefing or infographic. For example:

- Create a report brief about the latest Ebola outbreak for a journalist.
- Create an infographic about measles in the United States in 2019.
- Create a report brief about annual cholera in Nigeria from 2017 to 2024 via OWID.

Users can also select a dataset in Historical evidence, use Ask about this history, then request a brief. The selected evidence context remains attached.

The response contains an accessible preview and downloadable Markdown report, SVG infographic and PNG infographic. The outputs preserve scope, question, audience, key figures, summary, limitations and source links. Markdown includes all contributing evidence IDs; SVG embeds source metadata and IDs. These are deterministic evidence graphics, not generated photographic imagery or unrestricted AI research.

For historical answers the builder selects the exact historical source used, calculates the same period sum and optionally attaches a canonical latest country observation. It does not sum historical annual figures with monthly reports or cumulative outbreak totals. Missing or incompatible latest evidence is disclosed. Unsupported questions do not generate surveillance artifacts.

Tests cover artifact detection, unsupported refusal, total/evidence-ID reuse and the Ask response integration. The existing statistical limitations and no-medical-advice boundaries remain unchanged.

## Outbreak interpretation and control

Briefs now include geographic interpretation, affected-group evidence availability, disease-specific transmission background and WHO control priorities. General guidance is a reviewed fact-sheet summary (reviewed 30 August 2026), not a live official outbreak recommendation. Original WHO links and publication dates are retained. Missing age, sex or occupation breakdowns are stated explicitly rather than inferred from general risk groups.

Global current briefs can rank up to five countries within one matching source, indicator, unit, case definition and reporting period. Historical and country-specific briefs do not substitute an unrelated global ranking. The infographic uses labelled bars where comparable data exist and numbered action panels. The panels are Fynura originals, not OWID artwork or Grapher code. A heatmap or vaccination-impact graphic requires its own validated dataset and attribution; those reference datasets are not silently mixed into outbreak surveillance.
