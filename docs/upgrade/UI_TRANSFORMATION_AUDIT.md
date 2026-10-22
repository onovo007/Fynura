# Fynura UI transformation audit

**Audit date:** 22 October 2026  
**Scope:** Phase 1 — frontend, application routes, analytical services, and regression coverage  
**Decision:** preserve the FastAPI and progressive-JavaScript architecture; introduce a route-aware application shell incrementally.

## Current application structure

Fynura is a server-rendered entry point with a progressively enhanced frontend. FastAPI serves `frontend/index.html`, static JavaScript and CSS, and the authenticated JSON APIs. The frontend does not use React, Vue, or another component framework. Existing capabilities are loaded by independent browser modules and many of them insert complete sections into a single long document at runtime.

The scientific and data layers are already separated from presentation:

- canonical surveillance context: `/api/workspace`, `/api/intelligence`, and `/api/analytics`;
- geographic reporting: `/api/map`;
- source registry and health: `/api/sources` and `/api/data-status`;
- observation history: `/api/history` and `/api/history/{threat}`;
- statistical screening: `/api/early-signals`;
- evidence-linked answers: `/api/ask` and `/api/chat/stream`;
- evidence inspection: assessment, evidence, and visualization endpoints;
- product operations: authentication, sessions, watches, events, and owner-only administration.

This separation allows the interface to change without replacing evidence ingestion, fusion, epidemiological calculations, authentication, or provenance.

## Existing workflow

The current authenticated page follows this sequence:

1. introductory product story;
2. global map and shared analytical filters;
3. threat and epidemiological summary cards;
4. Ask Fynura conversation;
5. visual analysis and trajectories;
6. historical evidence and early-signal review;
7. source registry, harmonization, and methodology.

The flow contains the required analytical building blocks, but users must scroll between domains. Runtime insertion order is distributed across `visuals.js`, `production.js`, `workspace.js`, `history.js`, `early-signals.js`, and `network.js`. This makes orientation, bookmarking, keyboard navigation, and selective loading harder than necessary.

## Reusable component inventory

| Existing component | Current implementation | Target workspace | Treatment |
|---|---|---|---|
| Interactive global map and metric filters | `visuals.js`, `map.css`, `/api/map` | Monitor | Retain Leaflet, move to a Monitor mount point, synchronize with shared context. |
| Shared threat, region, country, and period filters | `workspace.js`, `/api/workspace` | Application shell | Refactor into one contextual sidebar; preserve incompatibility handling and explicit empty states. |
| Canonical metric cards and evidence table | `workspace.js`, `/api/workspace` | Monitor | Reuse; split summary cards from the detailed comparison table. |
| Epidemiological snapshot | `production.js`, `/api/analytics` | Monitor | Reuse verified metrics and CSV export; remove duplicated filter controls. |
| Threat visual cards and Ebola trajectory | `visuals.js`, `trajectory.js` | Monitor | Reuse; mount only for the selected threat and scope. |
| Historical archive, heatmap, and trend charts | `history.js`, `history-heatmap.js`, history APIs | Monitor and Detect & Anticipate | Monitor receives descriptive history; Detect receives eligible statistical screening. |
| Early-signal historical review | `early-signals.js`, `/api/early-signals` | Detect & Anticipate | Reuse validated CUSUM output. Label it statistical screening, not forecasting. |
| Source explorer | `network.js`, `/api/sources` | Verify | Reuse registry and operational state in a dedicated source view. |
| Evidence drawer and provenance details | `app.js`, `visuals.js`, `workspace.js` | Verify | Convert to reusable evidence inspector, reachable from every workspace. |
| Harmonization explanation and conflicts | `network.js`, workspace evidence fields | Verify | Retain rules and add compatible/incompatible comparison layouts from canonical evidence. |
| Structured Ask Fynura response | `visuals.js`, `/api/ask` | Advise and persistent assistant | Retain evidence context envelope, citations, limitations, brief generation, and stakeholder mode. |
| Live research conversation | `research-chat.js`, `/api/chat/stream` | Advise and persistent assistant | Reuse streaming progress, bounded memory, explicit visual-context opt-in, and source review. |
| Reports and infographics | `briefs.js`, brief payloads from `/api/ask` | Advise | Retain deterministic previews and downloads; add a report workspace mount point. |
| Voice input and answer playback | `voice.js`, `voice.css` | Persistent assistant | Reuse as an optional accessible input method. |
| Source health and refresh state | `production.js`, `/api/data-status` | Top bar and Learn & Improve | Show compact status globally and operational detail in Learn & Improve. |
| Product event telemetry and watches | `visuals.js`, events/watches APIs | Learn & Improve | Reuse actual recorded metrics only; keep owner-only details role protected. |
| Authentication and account controls | `auth.js`, `session-controls.js` | Application shell | Preserve Google Identity Platform, protected routes, logout, and session expiry behavior. |
| Methodology and responsible-use content | `docs.html`, `docs.js` | Learn & Improve and Docs | Link rather than duplicate; expose relevant method details beside analytical outputs. |

## Five-workspace content map

### Monitor

- global and regional map with verified signal, cases, deaths, crude CFR, rate, and recent-change options only where supported;
- canonical KPI cards with reporting cutoff, source, retrieval status, and evidence state;
- country comparison table and compatible time-series views;
- source coverage, freshness, reporting gaps, and watch controls;
- direct paths from a metric to evidence inspection and contextual advice.

### Verify

- source registry, operational state, scope, and extraction method;
- evidence comparison grouped by compatible definition, geography, unit, and period;
- provenance details, source links, revisions, unresolved conflicts, and superseded evidence;
- statuses limited to Verified, Under review, Conflicting, Superseded, and Insufficient evidence;
- deterministic evidence-confidence details only where the documented calculation applies. General research answers retain qualitative coverage rather than a percentage.

### Detect & Anticipate

- eligible historical sequences and validated CUSUM screening;
- observed values, seasonal baseline, threshold, anomaly timing, and method eligibility;
- explicit states for insufficient, irregular, or incompatible history;
- space reserved for experimental models only after model contracts, validation results, uncertainty intervals, and diagnostics exist.

No forecast control will appear operational until its model is validated and the selected evidence meets the minimum data requirements.

### Advise

- evidence-grounded situation assessments and predefined analytical questions;
- stakeholder mode, contextual interpretation, citations, limitations, and review status;
- report and infographic generation from the same evidence IDs used elsewhere;
- structured live research for general scientific questions, independent of chart context unless the user opts in;
- downloadable outputs with reporting period, source attribution, and limitations.

### Learn & Improve

- source checks, ingestion outcomes, reporting lag, document ledger, and refresh reliability derived from recorded operations;
- alert eligibility and analyst adjudication when those records exist;
- model validation panels only for models with stored evaluation results;
- method versions, release history, reproducibility resources, feedback, and documentation links;
- a strict split between operational service health and scientific validation.

## Data and interface gaps

The first release must not visually imply capabilities that the backend does not yet support.

| Requested capability | Current evidence | Release treatment |
|---|---|---|
| Administrative drill-down | Country coordinates and Nigeria crosswalk foundations exist; public subnational observations are limited. | Show geographic levels only when verified records exist. Disable unavailable levels with an explanation. |
| News candidates awaiting verification | Research can use search grounding, but there is no canonical candidate-review queue. | Design a non-operational empty state; add only after a stored review model and role controls exist. |
| Forecasting and uncertainty bands | Historical CUSUM screening exists; validated forecast models and calibration records do not. | Ship Detect with observed history and anomaly screening. Do not render forecasts. |
| Mobility and displacement overlays | No approved canonical overlay contracts are present. | Keep out of the operational UI pending source, licensing, and validation review. |
| Confusion matrices and model drift | No stored ground truth or evaluation series is available. | State that validation metrics are unavailable; never synthesize accuracy. |
| PDF report export | Markdown, SVG, PNG, and CSV paths exist. | Add PDF only after a server or browser export path is tested for citations, pagination, and accessibility. |
| Notifications | Watches exist; no user notification delivery contract was found. | Top bar may link to watches but must not imply delivery of alerts. |

## Engineering findings

- `index.html` is compact, but more than ten JavaScript modules progressively transform it; `visuals.js` is the largest module and owns unrelated map, context, answer, and layout behavior.
- Several modules discover insertion locations through selectors such as `#visuals`, `#trust`, and `.cards`. Workspace routing requires explicit mount points rather than DOM-order coupling.
- Global state is split across `intel`, `state`, local storage, session storage, and DOM values. A single shared context store is required before routes are introduced.
- Existing APIs already return the central surveillance data. A backend rewrite is unnecessary for Monitor, Verify, initial Detect, or most of Advise.
- Loading, empty, and error messages generally distinguish source failure from absent observations. This behavior must be preserved in shared components.
- Current regression coverage is strong for evidence context, maps, history, early signals, source status, authentication, provider reliability, research answers, voice, and public copy. Browser-level accessibility, direct-route, layout, and visual regression coverage must be added.
- The interface currently loads all modules for the long page. Route-specific dynamic imports will reduce initial work and prevent inactive charts from initializing.

## Constraints carried into implementation

1. Canonical observations and their provenance remain the only basis for surveillance displays.
2. Reporting cutoff and latest successful source check remain separate fields and labels.
3. Missing, delayed, inaccessible, or incompatible data are never converted to zero.
4. General scientific questions do not inherit chart context unless the user explicitly includes it.
5. Statistical signals are not confirmed outbreaks, and no unsupported forecast is exposed.
6. Evidence status is descriptive; generic confidence percentages are not added to research or forecast content.
7. Authentication, role checks, source links, data files, and current APIs remain intact throughout migration.

