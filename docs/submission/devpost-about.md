# Fynura
## Inspiration

An outbreak rarely arrives with one complete, comparable evidence file. Public-health professionals, journalists, researchers and communities must navigate reports from WHO, regional agencies and national authorities. Dates, definitions, geography and completeness vary. A recent retrieval can still describe an older reporting period.

Fynura began with a practical question: how can people understand the signal without losing the evidence behind it?

## What Fynura does

Fynura combines automated surveillance processing with an interactive research partner. Its current evidence pipeline retrieves selected WHO reports, extracts structured observations, checks compatibility, computes supported indicators and stores assessments with provenance. Users explore those assessments through a global map, country views, timelines and historical archives.

Ask Fynura adds on-demand research. A Google ADK agent uses Gemini on Vertex AI with Google Search to investigate the actual question. A conditional second agent searches and reviews key claims before the app presents linked sources. General questions are independent of whichever chart the user last selected.

## Why it is agentic

The research workflow does more than fill a response template: it searches for relevant evidence, synthesizes an explanation and can conduct a second source-review pass. It receives recent conversation, an intended audience and optional analytical context. It produces a new source-linked response that the user can question and export.

The background surveillance workflow independently performs repeatable retrieval, parsing, evidence grouping and storage. Those numerical stages are deterministic Python, separate from LLM research. The two paths meet through supplementary stored evidence and the user's explicit context.

## Current demonstration threats

Cholera demonstrates source-defined case totals, deaths and guarded crude case-fatality calculations. Measles demonstrates country comparisons, historical monthly reports and exploratory change screening. Ebola demonstrates sequential reporting cutoffs and separate outbreak histories.

These are three implemented surveillance adapters and demonstrations, not a claim of structured coverage for every disease. Research questions can extend beyond them when sources support an answer.

## Global intelligence map

The map connects country signals to threat, WHO-region and metric filters. Users can inspect reported cases and other available metrics while retaining source scope. Coverage and denominators constrain which measures are available. Missing reports do not establish an absence of cases.

## Epidemiological intelligence

Fynura distinguishes reported cases, deaths, cumulative totals, reporting lags and changes between compatible reports. Crude CFR is calculated only when the inputs pass compatibility checks. A report-to-report increase is not automatically incidence during that interval.

Historical measles screening compares recent monthly reports with the same calendar months in a five-year baseline and displays a one-sided CUSUM. This is exploratory anomaly screening, not an outbreak forecast or a validated operational alert system. Separate Ebola outbreaks and annual cholera records are not forced into a monthly series.

## Ask Fynura

Users can choose an audience, ask a general question or explicitly include a visual, and continue a conversation. Eight recent successful exchanges remain in page memory. Dictation lets users review a transcript before sending; browser speech playback can read a response aloud. Structured report briefs and infographics provide additional ways to communicate selected evidence.

Scientific methods questions can receive an explicitly labeled general explanation when live verification is unavailable, without invented citations. Current outbreak claims do not use that fallback. Research latency and source availability vary; bounded automatic retries and visible progress help recover from temporary provider errors.

## Evidence Confidence

A stored assessment includes an explainable, weighted evidence-quality score based on authority, independence, agreement, recency, consistency and provenance. It is a heuristic, not the probability an answer is correct.

Live research uses separate qualitative evidence support and linked sources. It does not inherit a dashboard percentage as a guarantee of a generated answer.

## Multi-source harmonization

Multi-source does not mean summing every source. Fynura groups observations by compatible disease, indicator, geography, definition, unit and period, then preserves a selected observation or unresolved conflict.

The current canonical surveillance views are WHO-derived. Other agencies appear in the source registry with their actual integration status. Google Search can consult additional authorities, but a registered source is not an operational adapter, and WHO republished through OWID is not independent corroboration.

## Responsible AI

Fynura supports public-health understanding, not individual diagnosis or treatment. Source links, reporting dates, visible gaps and withholding unsupported answers are part of the experience. The application asks users not to enter patient identifiers. Authentication and administrator-only access protect access, but this is not a claim of certified clinical or enterprise security.

## How we built it

FastAPI and Python run in a Cloud Run container and serve a JavaScript/HTML/CSS frontend with Leaflet and OpenStreetMap. Firestore stores evidence and application state. Cloud Scheduler initiates authenticated refresh checks. Firebase provides Google sign-in; Secret Manager supplies runtime configuration; Cloud Logging records service activity.

The active research implementation uses Google ADK and the Google GenAI SDK with **Gemini 3.7 Flash on Vertex AI**. A real production interaction and provider model-version logs verified the upgrade on 31 August 2026. Deterministic code owns canonical surveillance calculations.

## Challenges we ran into

Sources arrive in different formats and can restrict automated retrieval. Reports with different periods or case definitions cannot safely be combined. Historical gaps must stay visible. Country naming must be normalized without losing provenance.

A less obvious challenge was conversational scope: selecting a chart should not cause an unrelated question to receive that chart's summary. Explicit visual context and recent conversational history now serve different roles. Live source-grounding failures remain an area for further hardening.

## Accomplishments that we're proud of

We brought source-linked surveillance, historical comparison, guarded calculations and interactive research into a single deployed workspace. Automated tests cover evidence compatibility, denominator safeguards, history, routing and UI behavior. Users can inspect a reported number instead of accepting a disconnected summary.

## What we learned

Agentic public-health work needs deterministic epidemiology alongside generative explanation. Provenance, reporting lag and missingness materially change interpretation. A source-quality score and a model's confidence are different things. Audience-specific communication can change while the underlying evidence must remain traceable.

## What's next for Fynura

Next steps include validating change-detection methods with public-health partners, expanding operational adapters and subnational coverage, measuring research reliability under broader use, and assessing additional languages. Durable conversation memory and feedback learning are future work, not deployed claims.
