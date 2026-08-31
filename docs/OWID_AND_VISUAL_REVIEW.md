# Historical totals and visual review

## Changes

- Historical charts label the peak and selected endpoints without overlapping nearby labels. Hover, keyboard focus and tap expose the period, value, reporting frequency, geography and source.
- Compatible monthly and annual reports have a deterministic selected-period sum, peak and reporting-coverage count. Incomplete ranges are explicitly partial. No sum is described as an outbreak total without outbreak-specific evidence.
- Historical Ask uses those same calculations and retains all contributing evidence IDs. Existing current Ebola answers explicitly describe the source-reported cumulative outbreak totals, never a sum of cumulative reports.
- WHO-derived OWID annual measles and cholera datasets are separately selectable. Original metadata and source hashes are retained. Current WHO snapshots are not replaced by older annual observations. OWID is not independent corroboration of WHO.
- The measles snapshot supports top ten, all reporting countries and individual country views. US June 2026 is present with 90 reported cases; it was omitted only by the top-ten chart.
- All-threat map metrics use the union of source-supported metrics. Numeric values, units and dates appear in tooltips. Threat-specific unsupported metrics remain disabled with an explanation. Marker size is still not a quantitative encoding.

## Source and refresh

`python -m scripts.backfill_owid` downloads CSV and JSON metadata from OWID Grapher for `reported-cases-of-measles` and `number-reported-cases-of-cholera`. The packaged snapshot contains 9,196 measles observations across 212 countries/territories and 2,785 cholera observations across 165 countries/territories; latest year 2024. Regional aggregates are excluded to avoid overlapping country/region totals. Duplicates and invalid counts fail ingestion.

Sources: https://ourworldindata.org/grapher/reported-cases-of-measles and https://ourworldindata.org/grapher/number-reported-cases-of-cholera . Cite WHO and Our World in Data; source-provider terms apply. Fynura draws its own charts and does not copy Grapher code or branding.

This is a reproducible downloaded snapshot, not a new automated refresh job. No current 2026 observations are supplied by these annual OWID datasets. Ebola retains WHO current surveillance and CDC historical outbreak records. No complete inception-to-present count is inferred from an incomplete period series. More outbreak-specific records are needed for such claims.
