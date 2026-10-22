# Fynura five-workspace implementation plan

This plan follows the completed frontend audit and introduces the new application incrementally. Each phase must pass its release gate before the next workspace is promoted.

## Target application architecture

### Routes

Authenticated workspace URLs:

- `/monitor`
- `/verify`
- `/detect`
- `/advise`
- `/learn`

FastAPI will serve the same application shell for these paths. A small client router will update the active workspace with the History API, support back/forward navigation, preserve query parameters, and dynamically import only the selected workspace module.

Legacy hash links will temporarily redirect to the closest workspace location so current documentation and bookmarks continue to work.

### Shell regions

1. **Top bar:** Fynura identity, five workspace tabs, evidence-network state, last successful check, watches/account access, and mobile menu.
2. **Context sidebar:** threat, region, country, geographic level, reporting period, source, and indicator controls. Controls appear only when supported by the active workspace.
3. **Workspace outlet:** one mounted workspace at a time, with route-specific loading and error boundaries.
4. **Ask Fynura panel:** persistent launcher and state-preserving drawer. Advise expands it into the primary research workspace.
5. **Evidence inspector:** shared drawer reachable from metrics, maps, charts, answers, and reports.

### Shared context contract

The frontend store will use the existing API vocabulary:

```text
workspace
threat_id
region
country
geographic_level
reporting_period
source_id
indicator
selected_evidence_ids
include_visual_context
stakeholder_mode
```

The active analytical scope will be represented in URL query parameters and session storage. Route transitions will validate each field against the target workspace. Unsupported fields will be retained as inactive context with a visible explanation or removed after explicit notification; they will not be silently applied.

Pydantic response models remain the server source of truth. The existing JavaScript architecture will gain documented JSDoc contracts and runtime validation at API boundaries rather than introducing a framework or TypeScript migration during this redesign.

### Module boundaries

```text
frontend/shell/
  app-shell.js
  router.js
  context-store.js
  api-client.js
  evidence-inspector.js
  ask-drawer.js

frontend/workspaces/
  monitor.js
  verify.js
  detect.js
  advise.js
  learn.js
```

Existing files remain in place while their behavior is migrated behind adapters. A component is removed from the legacy long page only after its workspace replacement passes parity tests.

## Visual system

- Preserve the Fynura mark, forest-green brand recognition, mint accent, and “See the signal sooner.”
- Introduce navy for shell structure, teal for verified analytical actions, cyan for selected context, and restrained amber/red only for evidence states that require attention.
- Use one spacing scale, one card radius family, one focus treatment, and semantic status tokens across all workspaces.
- Minimum text and control contrast will meet WCAG 2.2 AA. Every map or chart will have a text summary or accessible table.
- Motion will be brief and functional, with `prefers-reduced-motion` support.
- Skeletons will preserve final layout dimensions; errors and unavailable data will use distinct language and states.

## Delivery sequence

### Phase 2 — shell and shared state

- add direct authenticated workspace routes;
- build top tabs, responsive sidebar, outlet, persistent Ask Fynura launcher, and evidence inspector;
- create the context store, URL serialization, request cache, and workspace compatibility rules;
- keep the current page available behind a temporary legacy route during parity testing;
- add keyboard, mobile navigation, route, and context persistence tests.

**Release gate:** all five routes load independently; refresh/back/forward work; login and logout remain secure; inactive workspaces are not mounted; Ask Fynura and the evidence inspector preserve state.

### Phase 3 — Monitor and Verify

- migrate the Leaflet map, shared filters, canonical cards, epidemiological table, visuals, trajectories, historical description, and exports into Monitor;
- migrate the registry, source health, provenance, harmonization, evidence comparison, conflicts, and revision detail into Verify;
- add observation-to-evidence and evidence-to-observation navigation;
- confirm every figure displays geography, reporting cutoff, source, and evidence status.

**Release gate:** feature parity with current map, analytics, history, source, and evidence workflows; map/filter tests and scientific regression suite pass; no change to canonical values.

### Phase 4 — Detect & Anticipate

- migrate historical eligibility and CUSUM screening;
- add observed-versus-baseline charts, anomaly timeline, method details, and explicit unsupported states;
- define a forecast plugin contract without exposing forecast controls;
- add forecast controls only after a validated model supplies uncertainty and evaluation records.

**Release gate:** every visible signal is reproducible from stored observations; ineligible series fail closed; signals cannot be mistaken for official outbreak declarations or forecasts.

### Phase 5 — Advise

- make the structured conversation and streaming research interface the primary workspace;
- add predefined analytical prompts and stakeholder modes;
- migrate evidence-linked response cards, source review, briefs, infographic previews, and downloads;
- add review-state metadata for recommendations and preserve explicit visual-context opt-in.

**Release gate:** surveillance answers use canonical evidence; general questions remain scope independent; citations, limitations, evidence IDs, and report exports pass regression tests.

### Phase 6 — Learn & Improve

- expose recorded source checks, refresh results, reporting lag, document ingestion, and system reliability;
- separate operational performance from scientific validation;
- add feedback and adjudication only with authenticated storage and role rules;
- show unavailable validation metrics as unavailable rather than empty scores.

**Release gate:** every metric traces to a stored event, check, assessment, or evaluation record; owner-only data remains protected.

### Phase 7 — validation and production release

- run unit, API, authentication, scientific, and provider reliability tests;
- add automated route, keyboard, accessibility, responsive layout, export, and visual regression tests;
- record desktop, tablet, and mobile parity checks;
- test slow, failed, stale, empty, incompatible, and partially available data states;
- verify Cloud Run image, cache headers, direct routes, rollback, and production health before traffic migration.

## Performance approach

- load shell CSS and router first; dynamically import the active workspace;
- initialize Leaflet and chart modules only inside workspaces that need them;
- cache idempotent GET requests by endpoint plus normalized context and invalidate them after refresh;
- cancel obsolete requests when filters or routes change;
- preserve the last verified snapshot during source failures and label its cutoff;
- avoid duplicate `/api/workspace`, `/api/map`, and `/api/analytics` calls during one context transition;
- measure initial shell load, workspace interaction latency, layout shift, and mobile memory before release.

## First implementation increment

The next code increment should implement Phase 2 only: application routes, shell, context store, workspace outlet, and persistent assistant/evidence surfaces. It should mount thin adapters around existing components without redesigning their analytical internals. Monitor and Verify migration begins only after shell navigation and shared context tests pass.

No production deployment should replace the current long-page application until Monitor and Verify reach functional parity and a rollback revision has been recorded.
