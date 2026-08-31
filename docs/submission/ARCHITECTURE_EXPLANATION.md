# Architecture explanation

## Two connected evidence paths

**Scheduled surveillance** is ordinary deterministic Python. Cloud Scheduler calls `POST /internal/refresh` using OIDC. FastAPI validates the expected caller and audience. RefreshService applies a lease and per-disease due time, then calls Pipeline. WHO adapters retrieve source reports, extract typed observations, group compatible evidence, compute derived indicators and generate stored assessments.

**Interactive intelligence** uses one dispatcher for `POST /api/ask` and `POST /api/chat/stream`. Guardrails and high-confidence intent rules run first; a schema-constrained model classifier resolves remaining intents. Registry and stored-surveillance requests use deterministic application evidence. Scientific questions use Google ADK LlmAgent/Runner, Vertex AI and Google Search independently of chart context. Hybrid explanations and requested outbreak briefs attach separate canonical facts to researched interpretation. A conditional second agent reviews live research. This is sequential research/review, not parallel autonomous specialists.

Scientific questions are not implemented as a list of fixed definitions. When search support is unavailable, a bounded model call may provide established general science with an explicit unverified label and no citations. Current outbreak claims never use that fallback. Source-linked scientific answers have qualitative support, while canonical surveillance retains deterministic confidence. Progress events are request stages, not private model thoughts or token streaming.

## What is deterministic

Both chat endpoints share a maximum of three orchestration attempts for transient
provider errors, jittered delays and one 250-second deadline. Retry stages are
visible in streamed chat. SDK-level retries are disabled to prevent multiplying
attempts. No answer already delivered is replayed. Quotas and service capacity
still constrain availability; see [research chat](../RESEARCH_CHAT.md).

- Source parsing and Pydantic observation validation.
- Geography, indicator, case-definition and reporting-period compatibility grouping.
- Canonical selection/conflict preservation in `evidence/fusion.py`.
- Crude CFR with denominator and compatibility guards.
- Historical period sums with partial-coverage labels; no summing separate Ebola outbreaks.
- Evidence Confidence weighted heuristic.
- Exploratory seasonal CUSUM in `services/early_history.py`.

Gemini does not own canonical numerical extraction, CFR or CUSUM. It may explain externally researched statistics, which remain distinct from the stored surveillance dataset.

## Provenance and storage

Observations retain source URL, supporting excerpt, reporting/publication/retrieval dates, extraction method, run identifier and observation identifier. Derived metrics retain input observation IDs. Firestore stores chunked assessment payloads and atomically updates the latest pointer after writes. Failed source retrieval retains the last successful evidence. This is not a claim of transactionally immutable storage against administrator edits.

Historical WHO/CDC and OWID-derived data are compressed files in `data/history`, loaded by `services/history.py`. Their retrieval dates describe archive snapshots; Scheduler does not continuously rebuild them.

## Serving and identity

One Cloud Run container runs Uvicorn/FastAPI and serves JavaScript, CSS, HTML and APIs. The browser renders Leaflet maps, SVG charts and evidence panels. Firebase Google sign-in establishes a verified cookie plus a durable application access session. Production requires onboarding; administrator-only routes are separately guarded.

Firestore also stores product/session records. No patient records are needed for this demonstration. The application collects verified email and onboarding fields as described in its privacy notice.

## Google Cloud boundary

Verified: Cloud Run, Vertex AI, Firestore, Cloud Scheduler, Firebase Authentication, Secret Manager runtime reference, and Cloud Logging request records. Cloud Build and Artifact Registry support deployment. Build-source storage is not an application data lake. Pub/Sub and Cloud Trace instrumentation were not verified.

## Historical screening

Country-level monthly measles series need 72 consecutive usable months. Five years form a calendar-month baseline; the following 12 months are monitored with one-sided standardized CUSUM, k=0.5 and h=5. A missing/duplicate/invalid period or zero-variance baseline prevents calculation. Reporting changes, seasonality assumptions and pandemic-era disruption limit interpretation. Parameters are not prospectively validated for operational alerts.

## Not on the active path

`backend/agents/root_agent.py` defines a four-role SequentialAgent. Its legacy model accessor now reads the centralized `FYNURA_CHAT_MODEL` setting. No call from the production refresh/API path was found. The diagram deliberately excludes this inactive graph.
