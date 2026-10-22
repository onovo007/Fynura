# Fynura production user-experience review

**Review date:** 22 October 2026  
**Environment:** authenticated production application on Google Cloud Run  
**Method:** section-by-section browser review, accessibility-tree inspection, rendered-layout measurement, interaction-state review, and supporting code/test inspection.

## Five-workspace shell increment

Following the browser review, the route-aware application shell was implemented as a parity-preserving adapter around the existing evidence components.

- `/monitor` contains the global map, shared surveillance scope, verified metric cards, epidemiological table, threat trajectories and Nigeria availability.
- `/verify` contains the source registry and harmonization rules.
- `/detect` contains historical evidence and eligible early-signal review.
- `/advise` contains Ask Fynura, evidence-linked answers, briefs and infographic generation.
- `/learn` contains the product explanation, methodology and responsible-use boundaries.

The top navigation uses the History API, supports browser back and forward navigation, retains query parameters, exposes the active workspace with `aria-current`, and focuses the workspace heading after a route transition. Direct workspace URLs use the same authentication gate and no-store cache policy as the existing application. Legacy section hashes are mapped to the closest workspace route.

A persistent Ask Fynura launcher is available from Monitor, Verify, Detect and Learn. The existing evidence dialog remains globally available. Mobile navigation is horizontally scrollable, focus treatment is visible, and reduced-motion preferences are respected.

This increment does not change canonical surveillance values, source selection, epidemiological calculations or Ask Fynura evidence resolution. It reorganizes proven components into task-oriented workspaces. Searchable country selection and deeper shared-context controls remain part of the next Monitor and Verify component migration.

## Review coverage

The walkthrough covered:

- authentication-preserved application entry and sticky navigation;
- product introduction and evidence-network overview;
- global monitoring map, filters, markers, source-check status, and empty-state language;
- “Evidence at a glance” filters, country cards, evidence inspection, and canonical table;
- historical early-signal review and CUSUM explanation;
- disease trajectories and accessible chart tables;
- historical evidence controls, heatmap, provenance, and CSV export;
- Ask Fynura context, stakeholder selection, voice entry, report controls, and conversation reset;
- source registry, harmonization explanation, Nigeria availability, methodology, and footer;
- keyboard semantics exposed through the browser accessibility tree;
- responsive rules and narrow-screen behavior in the production stylesheets.

## Production observations

### Navigation and information architecture

The current application remains a long page measuring approximately 16,500 pixels at the reviewed desktop viewport. Major analytical capabilities are present and ordered coherently, but moving from monitoring to verification or advice requires extensive scrolling. This confirms the need for the approved five-workspace architecture rather than further expansion of the long page.

The current header provides direct access to Signals, Ask Fynura, Methodology, Docs, source status, and sign-out. It does not yet expose the five operational domains or a persistent contextual sidebar. Those changes remain Phase 2 structural work and should not be introduced as an untested patch.

### Global monitoring

The map communicates multi-threat coverage effectively through lettered, segmented markers and exposes threat, WHO region, and compatible metric controls. Disabled metrics explain that compatible source observations are unavailable. The coverage summary distinguishes reporting countries from affected geographies.

The “Latest verified evidence” panel used only a success icon, source names, and page-load time, leaving a large empty area and making the epidemiological cutoff difficult to compare with the source-check time. It has been upgraded to show one concise row per monitored threat, the primary value, reporting cutoff, source, and the last successful evidence check as separate information.

### Evidence at a glance

After refreshing the latest production revision, verified Ebola records appeared separately for the Democratic Republic of the Congo, Uganda, Kenya, and Nigeria. The Nigeria record was technically identified as a preparedness advisory, but rendering its stored signal value as “1 official advisory” could be mistaken for a case count.

The card, canonical table, and evidence drawer now render this as “Official advisory” with “No confirmed Ebola case reported.” Raw source values remain unchanged for deterministic processing and CSV lineage. Source identifiers in user-facing cards and evidence drawers are converted to readable authority names.

### Early-signal review

The dedicated historical review provides country selection, observed-versus-baseline charts, a CUSUM comparison, accessible calculation details, eligibility states, provenance, and an Ask Fynura handoff. The language correctly identifies this as historical screening rather than an outbreak declaration.

A legacy analytics block duplicated the canonical table and early-signal content, adding more than 1,100 pixels to the page. It is now suppressed after the dedicated canonical and signal-review components mount. The unsupported IFR sentence previously requested for removal has also been removed from the rendered signal review.

### Visual intelligence and history

The disease selector, Ebola country/outbreak selector, metric selector, source link, dates, accessible data table, and limitations are clear. Historical evidence correctly separates monthly, annual, and outbreak-frequency data and does not automatically join incompatible series.

The historical country selectors are necessarily long. Searchable comboboxes would improve expert workflows, but replacing native selects requires careful keyboard, screen-reader, and mobile testing. This is assigned to the workspace redesign rather than added as a one-off dependency.

### Ask Fynura

The assistant clearly distinguishes general questions from selected-chart context, requires explicit visual-context inclusion, supports stakeholder modes, preserves bounded conversation memory, shows research progress, and keeps voice dictation reviewable before submission. The message area, input, and follow-up actions are semantically available to assistive technology.

The assistant is visually separated from surveillance content and remains far down the current page. The planned shell will make it persistently accessible and use Advise as its expanded workspace. No change was made to the evidence-grounding architecture during this review.

### Sources and methodology

The source registry differentiates operational, historical, candidate, configured, monitored, and access-limited integrations. The harmonization workflow correctly states that multi-source evidence is not automatically summed. Nigeria’s national source panel describes validation status without claiming operational subnational publication.

The Trust and Methodology label was being reset from section 07 to section 05 by a periodic compatibility function. It now remains section 07, following Source Explorer and Evidence Harmonization.

## Changes applied during this review

1. Added threat-specific verified snapshot rows to the monitoring status panel.
2. Replaced page-load time with the latest successful evidence-check time.
3. Displayed reporting cutoffs separately from source-check time.
4. Removed the unsupported IFR sentence from early-signal review.
5. Suppressed the redundant legacy analytics and early-signal block.
6. Corrected Methodology numbering to section 07.
7. Reworded Nigeria’s Ebola preparedness signal so it cannot be read as a confirmed case count.
8. Replaced internal source IDs with readable authority names in cards and evidence inspection.
9. Added regression tests for the removed IFR text and stable section numbering.

## Scheduled structural improvements

The following work remains part of the previously documented five-workspace migration:

- route-based Monitor, Verify, Detect & Anticipate, Advise, and Learn & Improve workspaces;
- shared context sidebar and URL-persisted filters;
- persistent Ask Fynura launcher and shared evidence inspector;
- searchable country and source controls with complete keyboard support;
- lazy loading so maps, history, and research modules mount only where needed;
- automated browser-level accessibility, direct-route, responsive, and visual regression tests;
- operational and scientific validation dashboards based only on recorded metrics.

The current production application should remain available until Monitor and Verify achieve full functional parity and the rollback revision is recorded.
