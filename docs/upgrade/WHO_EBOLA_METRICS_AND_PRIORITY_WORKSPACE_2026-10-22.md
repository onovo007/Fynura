# WHO Ebola metrics and surveillance-priority workspace

## WHO table reconciliation

Fynura now preserves all seven measures in the current WHO affected-country table:

- suspected cases;
- confirmed cases;
- confirmed deaths;
- probable cases;
- probable deaths;
- confirmed-case CFR; and
- recovered cases.

The values are stored as separate observations with their country-specific reporting cutoffs. A dash in the WHO source remains “Not reported”; a reported zero remains zero. The source-published affected-country total remains separate from the country rows because their cutoffs differ.

The Monitor metric selector now exposes the additional Ebola fields. Selecting a sparsely reported measure, such as confirmed CFR, maps only countries with that source-reported value and displays a country metric matrix beneath the map. This prevents France and Nigeria from appearing to have zero CFR and explains their absence from the selected map layer.

## Historical display

The monthly and annual stem chart was replaced with a line-and-point chart. Lines connect consecutive reporting periods only. Missing months or years break the line, so the display does not imply unobserved continuity. The seasonal profile remains below it as a complementary month-of-year summary.

## Surveillance review priorities

The former Learn landing experience has been replaced by a Prioritize workspace. It presents stored observations, reporting dates, and selected data-completeness gaps before offering an Ask Fynura advisory. The deterministic layer does not rank population risk or allocate resources from raw totals. The agent prompt requests current official guidance, citations, and a clear separation between observed evidence and suggested surveillance or control actions.

The workspace is a decision-support review surface. It does not replace national risk assessment, IHR notification, field investigation, or programme decision-making.

## Validation completed

- Complete WHO table parsing, including source-reported zeros and missing values.
- Backward compatibility with earlier stored WHO table markers.
- Map metric availability for the added Ebola indicators.
- JavaScript syntax checks for the metric matrix, historical chart, and priority workspace.
- Focused parser, map, and workspace tests.

